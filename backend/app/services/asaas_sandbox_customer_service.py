"""
P0.5: consulta/criação controlada do customer Asaas SANDBOX do usuário.

Fluxo (no máximo 1 POST por tentativa, nunca retry automático):

1. Adquire um lock por usuário (linha em idempotency_keys) com um token
   aleatório único por aquisição. Só o dono (mesmo token) pode removê-lo,
   via DELETE atômico condicionado ao conteúdo exato (CAS): um dono antigo
   nunca remove um lock mais novo (sem ABA) e um concorrente nunca remove
   um lock ativo. Sem TTL: lock órfão só sai por recuperação manual.
   Se o lock já existe, faz apenas GET (nunca POST) e NUNCA remove o lock:
   exatamente 1 customer válido -> devolve-o; senão, Pending.
2. GET /customers?externalReference=<agcus_...>&limit=2, com validação
   estrita da paginação (data, hasMore bool, totalCount, limit, offset e
   consistência entre eles). Listagem malformada nunca conta como ausência.
   - exatamente 1 customer válido -> devolve o id, sem POST;
   - mais de 1 (ou hasMore) -> Duplicate, sem POST;
   - erro/timeout/corpo ou paginação inválidos -> Unavailable, sem POST.
3. Só com 0 customers comprovados: POST /customers único com dados
   FICTÍCIOS de sandbox (nenhum dado pessoal real do usuário é enviado).
   - 2xx com id/externalReference válidos -> devolve o id;
   - qualquer outro desfecho -> um único GET de reconsulta:
     exatamente 1 válido -> devolve; duplicado -> Duplicate (lock mantido);
     0 na reconsulta E POST foi 400 com corpo de erros estruturado ->
     Rejected, com o lock MANTIDO (um GET vazio logo após o 400 não
     comprova ausência de efeito remoto); qualquer outra coisa (4xx
     ambíguo, 5xx, timeout, corpo inválido, reconsulta inválida) ->
     Indeterminate, também com o lock MANTIDO. Em ambos os casos novas
     tentativas só fazem GET (nunca POST) até recuperação manual
     (runbook WALLET_SANDBOX_CYCLE_RUNBOOK.md §9).

Mensagens de erro são genéricas: nunca incluem corpo de resposta,
headers, chaves ou o externalReference.
"""
from __future__ import annotations

import hashlib
import json
import re
import secrets
from typing import Any

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.models.idempotency import IdempotencyKey
from app.services.asaas_correlated_pix_payment_service import (
    AsaasHttpCall,
    asaas_sandbox_customer_external_reference,
)


ASAAS_SANDBOX_CUSTOMER_PENDING_LOCK_PREFIX = "asaas-sandbox-customer-pending:"
ASAAS_SANDBOX_CUSTOMER_PENDING_LOCK_CONTRACT = (
    "asaas_sandbox_customer_pending_lock_v2"
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
    """
    Asaas Sandbox respondeu 400 com erros estruturados e a reconsulta
    retornou 0 customers. Isso NÃO comprova ausência de efeito remoto:
    o lock do usuário é MANTIDO e só sai por recuperação manual.
    """


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


def _lock_json(*, user_id: int, token: str) -> str:
    return json.dumps(
        {
            "contract": ASAAS_SANDBOX_CUSTOMER_PENDING_LOCK_CONTRACT,
            "real_money_enabled": False,
            "token": token,
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


def _acquire_lock(db, *, user_id: int) -> str | None:
    """
    Conteúdo do lock (com token único) se adquiriu; None se já existia.
    O conteúdo devolvido é a prova de posse exigida por _release_lock.
    """
    lock_json = _lock_json(user_id=user_id, token=secrets.token_hex(16))
    try:
        db.add(IdempotencyKey(key=_lock_key(user_id), response_json=lock_json))
        db.flush()
        db.commit()
    except IntegrityError:
        db.rollback()
        return None
    except SQLAlchemyError:
        db.rollback()
        raise _storage_error() from None
    return lock_json


def _release_lock(db, *, user_id: int, lock_json: str) -> bool:
    """
    Remove o lock SOMENTE se ainda for o do dono (DELETE atômico
    condicionado a key + conteúdo com token). Devolve False se o lock já
    não era deste dono (ex.: recuperação manual): nada mais é removido.
    """
    try:
        deleted = (
            db.query(IdempotencyKey)
            .filter(
                IdempotencyKey.key == _lock_key(user_id),
                IdempotencyKey.response_json == lock_json,
            )
            .delete(synchronize_session=False)
        )
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise _storage_error() from None
    return deleted == 1


def _is_valid_customer_id(value) -> bool:
    return isinstance(value, str) and bool(_ASAAS_CUSTOMER_ID_PATTERN.fullmatch(value))


def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _classify_listing(
    status, body, *, external_reference: str, limit: int
) -> list[str]:
    """Ids dos customers ativos do usuário; _InvalidListing se não confiável."""
    if not _is_int(status) or not 200 <= status < 300:
        raise _InvalidListing
    if not isinstance(body, dict):
        raise _InvalidListing
    data = body.get("data")
    has_more = body.get("hasMore")
    total_count = body.get("totalCount")
    page_limit = body.get("limit")
    offset = body.get("offset")
    if not isinstance(data, list) or not isinstance(has_more, bool):
        raise _InvalidListing
    if not _is_int(total_count) or total_count < 0:
        raise _InvalidListing
    if not _is_int(page_limit) or page_limit != limit:
        raise _InvalidListing
    if not _is_int(offset) or offset != 0:
        raise _InvalidListing
    # Paginação coerente: a primeira página traz min(totalCount, limit)
    # itens e hasMore indica exatamente se há registros além dela.
    if len(data) > limit or len(data) != min(total_count, limit):
        raise _InvalidListing
    if has_more != (total_count > len(data)):
        raise _InvalidListing

    active: list[str] = []
    for item in data:
        # Qualquer item de outro externalReference indica que o filtro não
        # foi aplicado: a listagem não comprova nada.
        if not isinstance(item, dict):
            raise _InvalidListing
        if item.get("externalReference") != external_reference:
            raise _InvalidListing
        deleted = item.get("deleted")
        if not isinstance(deleted, bool):
            raise _InvalidListing
        if deleted:
            continue
        if not _is_valid_customer_id(item.get("id")):
            raise _InvalidListing
        active.append(item["id"])

    if has_more:
        # Há mais registros do que o limite para o mesmo externalReference:
        # não é possível comprovar unicidade -> revisão manual.
        raise _DuplicateListing
    if len(active) > 1:
        raise _DuplicateListing
    return active


def _is_definitive_rejection(status, body) -> bool:
    """
    Só um 400 com corpo de erros estruturado do Asaas comprova recusa de
    validação (apenas classifica o erro como Rejected; NUNCA libera o
    lock). Demais 4xx (401/403/404/409/422/429...) ou 400 malformado são
    ambíguos (gateway, proxy, rate limit, conflito) -> Indeterminate.
    """
    if not _is_int(status) or status != 400 or not isinstance(body, dict):
        return False
    errors = body.get("errors")
    if not isinstance(errors, list) or not errors:
        return False
    for error in errors:
        if not isinstance(error, dict):
            return False
        code = error.get("code")
        if not isinstance(code, str) or not code.strip():
            return False
        if not isinstance(error.get("description"), str):
            return False
    return True


def _list_customers(
    *, request, http_get: AsaasHttpCall, external_reference: str, limit: int
) -> list[str]:
    try:
        status, body = http_get(request)
    except Exception:
        raise _InvalidListing from None
    return _classify_listing(
        status, body, external_reference=external_reference, limit=limit
    )


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
            limit=ASAAS_SANDBOX_CUSTOMER_LIST_LIMIT,
        )

    # 1) Lock por usuário. Lock já existente => somente GET, nunca POST, e
    #    o lock alheio NUNCA é removido aqui (só o dono ou recuperação
    #    manual autorizada o removem).
    lock_json = _acquire_lock(db, user_id=user_id)
    if lock_json is None:
        try:
            found = list_customers()
        except _DuplicateListing:
            raise _duplicate_error() from None
        except _InvalidListing:
            raise _pending_error() from None
        if len(found) == 1:
            return found[0]
        raise _pending_error()

    # 2) Consulta antes de criar.
    try:
        found = list_customers()
    except _DuplicateListing:
        _release_lock(db, user_id=user_id, lock_json=lock_json)
        raise _duplicate_error() from None
    except _InvalidListing:
        _release_lock(db, user_id=user_id, lock_json=lock_json)
        raise AsaasSandboxCustomerUnavailableError(
            "Asaas Sandbox indisponível ao consultar o customer."
        ) from None
    if len(found) == 1:
        _release_lock(db, user_id=user_id, lock_json=lock_json)
        return found[0]

    # 3) Zero customers comprovados: POST único, sem retry.
    create_request = client.prepare_create_customer(
        **_sandbox_customer_payload(external_reference)
    )
    try:
        status, body = http_post(create_request)
    except Exception:
        status, body = None, None

    if _is_int(status) and 200 <= status < 300 and isinstance(body, dict):
        customer_id = body.get("id")
        if (
            _is_valid_customer_id(customer_id)
            and body.get("externalReference") == external_reference
            and body.get("deleted") is not True
        ):
            _release_lock(db, user_id=user_id, lock_json=lock_json)
            return customer_id

    # 4) Qualquer outro desfecho: reconsulta única. O lock só é liberado se
    #    exatamente 1 customer válido for comprovado. Em qualquer outro caso
    #    (inclusive 400 estruturado + reconsulta vazia, que não comprova
    #    ausência de efeito remoto) o lock é MANTIDO para impedir um 2º POST.
    try:
        found = list_customers()
    except _DuplicateListing:
        raise _duplicate_error() from None
    except _InvalidListing:
        found = None
    if found is not None and len(found) == 1:
        _release_lock(db, user_id=user_id, lock_json=lock_json)
        return found[0]
    if found == [] and _is_definitive_rejection(status, body):
        raise AsaasSandboxCustomerRejectedError(
            "Asaas Sandbox recusou a criação do customer."
        )
    raise AsaasSandboxCustomerIndeterminateError(
        "Criação do customer Asaas Sandbox com desfecho incerto."
    )
