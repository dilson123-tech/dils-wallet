"""
P0.5: consulta/criação controlada do customer Asaas SANDBOX do usuário.

Fluxo (no máximo 1 POST por tentativa, nunca retry automático):

1. Adquire um lock por usuário (linha em idempotency_keys). Se o lock já
   existe, outra requisição está em andamento OU uma tentativa anterior
   ficou com desfecho incerto: faz apenas GET (nunca POST). Se o GET
   comprovar exatamente 1 customer válido, devolve-o (e remove o lock
   observado); senão, Pending.
2. GET /customers?externalReference=<agcus_...>&limit=2.
   - exatamente 1 customer válido -> devolve o id, sem POST;
   - mais de 1 (ou hasMore) -> Duplicate, sem POST;
   - erro/timeout/corpo inválido -> Unavailable, sem POST.
3. Só com 0 customers comprovados: POST /customers único com dados
   FICTÍCIOS de sandbox (nenhum dado pessoal real do usuário é enviado).
   - 2xx com id/externalReference válidos -> devolve o id;
   - 4xx -> Rejected (desfecho comprovado: não criou);
   - timeout/5xx/corpo inválido -> um único GET de reconsulta:
     exatamente 1 válido -> devolve; qualquer outra coisa ->
     Indeterminate e o lock é MANTIDO (bloqueia novo POST até que um GET
     comprove o customer ou haja revisão manual).

Mensagens de erro são genéricas: nunca incluem corpo de resposta,
headers, chaves ou o externalReference.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.models.idempotency import IdempotencyKey
from app.services.asaas_correlated_pix_payment_service import (
    AsaasHttpCall,
    asaas_sandbox_customer_external_reference,
)


ASAAS_SANDBOX_CUSTOMER_PENDING_LOCK_PREFIX = "asaas-sandbox-customer-pending:"
ASAAS_SANDBOX_CUSTOMER_PENDING_LOCK_CONTRACT = (
    "asaas_sandbox_customer_pending_lock_v1"
)
ASAAS_SANDBOX_CUSTOMER_LIST_LIMIT = 2

_ASAAS_CUSTOMER_ID_PATTERN = re.compile(r"^cus_[A-Za-z0-9]{1,60}$")

# Dados fictícios exclusivos de sandbox. CPF de teste com dígitos
# verificadores válidos; domínio reservado (RFC 2606).
_SANDBOX_CUSTOMER_CPF = "12345678909"
_SANDBOX_CUSTOMER_MOBILE_PHONE = "11987654321"
_SANDBOX_CUSTOMER_EMAIL_DOMAIN = "example.com"


class AsaasSandboxCustomerUnavailableError(RuntimeError):
    """Asaas Sandbox não respondeu de forma confiável. Nenhum POST feito."""


class AsaasSandboxCustomerRejectedError(RuntimeError):
    """Asaas Sandbox recusou a criação (4xx). Customer não foi criado."""


class AsaasSandboxCustomerDuplicateError(RuntimeError):
    """Há mais de um customer para o usuário. Exige revisão manual."""


class AsaasSandboxCustomerIndeterminateError(RuntimeError):
    """
    POST tentado com desfecho incerto e reconsulta inconclusiva. O lock
    do usuário é mantido para impedir um segundo POST.
    """


class AsaasSandboxCustomerPendingError(RuntimeError):
    """Outra tentativa do usuário está em andamento ou ficou incerta."""


class AsaasSandboxCustomerStorageError(RuntimeError):
    """Falha ao registrar/remover o lock local."""


class _InvalidListing(Exception):
    pass


class _DuplicateListing(Exception):
    pass


def _duplicate_error() -> AsaasSandboxCustomerDuplicateError:
    return AsaasSandboxCustomerDuplicateError(
        "Mais de um customer Asaas Sandbox para o usuário."
    )


def _lock_key(user_id: int) -> str:
    digest = hashlib.sha256(str(user_id).encode("utf-8")).hexdigest()
    return f"{ASAAS_SANDBOX_CUSTOMER_PENDING_LOCK_PREFIX}{digest}"


def _lock_json(*, user_id: int) -> str:
    return json.dumps(
        {
            "contract": ASAAS_SANDBOX_CUSTOMER_PENDING_LOCK_CONTRACT,
            "real_money_enabled": False,
            "user_id": user_id,
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def _storage_error() -> AsaasSandboxCustomerStorageError:
    return AsaasSandboxCustomerStorageError(
        "Não foi possível registrar o estado do customer Asaas Sandbox."
    )


def _pending_error() -> AsaasSandboxCustomerPendingError:
    return AsaasSandboxCustomerPendingError(
        "Há criação de customer Asaas Sandbox do usuário em andamento "
        "ou com desfecho incerto."
    )


def _acquire_lock(db, *, user_id: int) -> bool:
    """True se adquiriu; False se o lock já existia."""
    try:
        db.add(
            IdempotencyKey(
                key=_lock_key(user_id),
                response_json=_lock_json(user_id=user_id),
            )
        )
        db.flush()
        db.commit()
    except IntegrityError:
        db.rollback()
        return False
    except SQLAlchemyError:
        db.rollback()
        raise _storage_error() from None
    return True


def _release_lock(db, *, user_id: int, expected_json: str) -> None:
    # CAS-delete: só remove o lock com o conteúdo esperado.
    try:
        (
            db.query(IdempotencyKey)
            .filter(
                IdempotencyKey.key == _lock_key(user_id),
                IdempotencyKey.response_json == expected_json,
            )
            .delete(synchronize_session=False)
        )
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise _storage_error() from None


def _read_lock_json(db, *, user_id: int) -> str | None:
    try:
        row = (
            db.query(IdempotencyKey.response_json)
            .filter(IdempotencyKey.key == _lock_key(user_id))
            .first()
        )
    except SQLAlchemyError:
        db.rollback()
        raise _storage_error() from None
    return None if row is None else row[0]


def _is_valid_customer_id(value) -> bool:
    return isinstance(value, str) and bool(_ASAAS_CUSTOMER_ID_PATTERN.fullmatch(value))


def _classify_listing(status, body, *, external_reference: str) -> list[str]:
    """Ids dos customers ativos do usuário; _InvalidListing se não confiável."""
    if not isinstance(status, int) or isinstance(status, bool):
        raise _InvalidListing
    if not 200 <= status < 300 or not isinstance(body, dict):
        raise _InvalidListing
    data = body.get("data")
    if not isinstance(data, list):
        raise _InvalidListing

    active: list[str] = []
    for item in data:
        # Qualquer item de outro externalReference indica que o filtro não
        # foi aplicado: a listagem não comprova nada.
        if not isinstance(item, dict):
            raise _InvalidListing
        if item.get("externalReference") != external_reference:
            raise _InvalidListing
        if item.get("deleted") is True:
            continue
        if not _is_valid_customer_id(item.get("id")):
            raise _InvalidListing
        active.append(item["id"])

    if body.get("hasMore") is True:
        # Há mais registros do que o limite para o mesmo externalReference:
        # não é possível comprovar unicidade -> revisão manual.
        raise _DuplicateListing
    if len(active) > 1:
        raise _DuplicateListing
    return active


def _list_customers(*, request, http_get: AsaasHttpCall, external_reference: str) -> list[str]:
    try:
        status, body = http_get(request)
    except Exception:
        raise _InvalidListing from None
    return _classify_listing(status, body, external_reference=external_reference)


def _sandbox_customer_payload(external_reference: str) -> dict[str, Any]:
    return {
        "name": f"Aurea Gold Sandbox {external_reference}",
        "cpf_cnpj": _SANDBOX_CUSTOMER_CPF,
        "email": f"{external_reference}@{_SANDBOX_CUSTOMER_EMAIL_DOMAIN}",
        "mobile_phone": _SANDBOX_CUSTOMER_MOBILE_PHONE,
        "external_reference": external_reference,
    }


def ensure_asaas_sandbox_customer(
    db,
    *,
    client,
    user_id: int,
    http_get: AsaasHttpCall,
    http_post: AsaasHttpCall,
) -> str:
    """Devolve o customer_id Asaas Sandbox do usuário, criando se ausente."""
    external_reference = asaas_sandbox_customer_external_reference(user_id)
    list_request = client.prepare_list_customers_by_external_reference(
        external_reference=external_reference,
        limit=ASAAS_SANDBOX_CUSTOMER_LIST_LIMIT,
    )

    def list_customers() -> list[str]:
        return _list_customers(
            request=list_request,
            http_get=http_get,
            external_reference=external_reference,
        )

    # 1) Lock por usuário. Lock já existente => somente GET, nunca POST.
    if not _acquire_lock(db, user_id=user_id):
        held_json = _read_lock_json(db, user_id=user_id)
        if held_json is None:
            # Lock sumiu entre o INSERT e a leitura: corrida; não arrisca.
            raise _pending_error()
        try:
            found = list_customers()
        except _DuplicateListing:
            raise _duplicate_error() from None
        except _InvalidListing:
            raise _pending_error() from None
        if len(found) == 1:
            # Customer comprovado: o lock não protege mais nada.
            _release_lock(db, user_id=user_id, expected_json=held_json)
            return found[0]
        raise _pending_error()

    lock_json = _lock_json(user_id=user_id)

    # 2) Consulta antes de criar.
    try:
        found = list_customers()
    except _DuplicateListing:
        _release_lock(db, user_id=user_id, expected_json=lock_json)
        raise _duplicate_error() from None
    except _InvalidListing:
        _release_lock(db, user_id=user_id, expected_json=lock_json)
        raise AsaasSandboxCustomerUnavailableError(
            "Asaas Sandbox indisponível ao consultar o customer."
        ) from None
    if len(found) == 1:
        _release_lock(db, user_id=user_id, expected_json=lock_json)
        return found[0]

    # 3) Zero customers comprovados: POST único, sem retry.
    create_request = client.prepare_create_customer(
        **_sandbox_customer_payload(external_reference)
    )
    try:
        status, body = http_post(create_request)
    except Exception:
        status, body = None, None

    if isinstance(status, int) and not isinstance(status, bool):
        if 200 <= status < 300 and isinstance(body, dict):
            customer_id = body.get("id")
            if (
                _is_valid_customer_id(customer_id)
                and body.get("externalReference") == external_reference
                and body.get("deleted") is not True
            ):
                _release_lock(db, user_id=user_id, expected_json=lock_json)
                return customer_id
        elif 400 <= status < 500:
            # Recusa explícita: o customer não foi criado.
            _release_lock(db, user_id=user_id, expected_json=lock_json)
            raise AsaasSandboxCustomerRejectedError(
                "Asaas Sandbox recusou a criação do customer."
            )

    # 4) Desfecho incerto (timeout, 5xx, corpo inválido): reconsulta única.
    #    Em qualquer resultado diferente de "exatamente 1", o lock é MANTIDO
    #    para impedir um segundo POST.
    try:
        found = list_customers()
    except _DuplicateListing:
        raise _duplicate_error() from None
    except _InvalidListing:
        found = []
    if len(found) == 1:
        _release_lock(db, user_id=user_id, expected_json=lock_json)
        return found[0]
    raise AsaasSandboxCustomerIndeterminateError(
        "Criação do customer Asaas Sandbox com desfecho incerto."
    )
