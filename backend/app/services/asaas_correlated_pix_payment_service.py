from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re
from typing import Any, Callable

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.models.idempotency import IdempotencyKey
from app.partner.asaas_client import (
    AsaasPreparedRequest,
    AsaasSandboxClient,
)
from app.partner.asaas_payment_correlation import (
    ASAAS_PAYMENT_CORRELATION_KEY_PREFIX,
    build_asaas_payment_user_correlation_record,
    generate_asaas_payment_external_reference,
    validate_asaas_payment_external_reference,
)
from app.services.sandbox_namespace_cap import (
    SandboxNamespaceCapExceeded,
    enforce_sandbox_namespace_cap,
)


ASAAS_CORRELATED_PIX_PAYMENT_PREPARATION_CONTRACT = (
    "asaas_correlated_pix_payment_preparation_v1"
)

# P0.4 -- estados persistidos da cobrança HTTP no registro de correlação.
# "attempted" é gravado ANTES do POST e nunca volta atrás: qualquer
# desfecho incerto (timeout, 5xx, resposta inválida, falha ao persistir o
# payment_id) deixa o registro em "attempted" e bloqueia um segundo POST.
ASAAS_CHARGE_HTTP_ATTEMPTED = "attempted"
ASAAS_CHARGE_HTTP_CREATED = "created"
ASAAS_CHARGE_HTTP_REJECTED = "rejected"
# Reconciliação (GET por externalReference) de um "attempted":
# - "not_created": nenhuma cobrança encontrada após a janela conservadora;
# - "conflict": divergência (várias cobranças, campos diferentes, payment_id
#   diferente no webhook). Nunca leva a novo POST; exige revisão manual;
# - "created_late": webhook confirmou cobrança depois de "not_created".
ASAAS_CHARGE_HTTP_NOT_CREATED = "not_created"
ASAAS_CHARGE_HTTP_CONFLICT = "conflict"
ASAAS_CHARGE_HTTP_CREATED_LATE = "created_late"
_ASAAS_CHARGE_HTTP_STATES = frozenset(
    {
        ASAAS_CHARGE_HTTP_ATTEMPTED,
        ASAAS_CHARGE_HTTP_CREATED,
        ASAAS_CHARGE_HTTP_REJECTED,
        ASAAS_CHARGE_HTTP_NOT_CREATED,
        ASAAS_CHARGE_HTTP_CONFLICT,
        ASAAS_CHARGE_HTTP_CREATED_LATE,
    }
)
# Desfechos comprovados: liberam o lock por usuário.
_ASAAS_CHARGE_HTTP_TERMINAL_STATES = frozenset(
    {
        ASAAS_CHARGE_HTTP_CREATED,
        ASAAS_CHARGE_HTTP_REJECTED,
        ASAAS_CHARGE_HTTP_NOT_CREATED,
        ASAAS_CHARGE_HTTP_CREATED_LATE,
    }
)
_ASAAS_PAYMENT_ID_PATTERN = re.compile(r"^pay_[A-Za-z0-9]{1,60}$")
# Diagnóstico de 4xx: só códigos de erro do Asaas documentados oficialmente
# (docs.asaas.com, "Códigos HTTP das respostas"). Código desconhecido é
# descartado: valor externo pode carregar dado pessoal mesmo com formato válido.
# Nunca description, corpo bruto ou headers.
_ASAAS_KNOWN_ERROR_CODES = frozenset({"invalid_value", "invalid_dueDate"})
_ASAAS_ERROR_ITEMS_SCANNED_MAX = 10

# Lock por usuário: no máximo uma cobrança com desfecho incerto por vez.
ASAAS_SANDBOX_CHARGE_PENDING_LOCK_PREFIX = "asaas-sandbox-charge-pending:"
ASAAS_SANDBOX_CHARGE_PENDING_LOCK_CONTRACT = (
    "asaas_sandbox_charge_pending_lock_v1"
)

# Janela mínima, contada de charge_attempted_at, antes de aceitar "lista
# vazia" no GET por externalReference como prova de "not_created". Escolha
# operacional conservadora (atraso de indexação/consistência), NÃO um
# comportamento documentado do Asaas.
ASAAS_SANDBOX_CHARGE_NOT_CREATED_AFTER = timedelta(minutes=10)

_ASAAS_CUSTOMER_EXTERNAL_REFERENCE_PREFIX = "agcus_"


class AsaasCorrelatedPixPaymentConflictError(RuntimeError):
    pass


class AsaasCorrelatedPixPaymentStorageError(RuntimeError):
    pass


class AsaasCorrelatedPixPaymentCapacityError(RuntimeError):
    """
    Levantada quando o namespace sandbox asaas-payment-correlation:
    atingiu o soft cap operacional P0-B (WALLET_SANDBOX_NAMESPACE_MAX_ROWS)
    no momento em que uma preparação genuinamente nova acabou de ser
    inserida. Nunca levantada para replay de uma preparação já
    existente.
    """
    pass


@dataclass(frozen=True)
class AsaasCorrelatedPixPaymentPreparation:
    user_id: int = field(repr=False)
    external_reference: str = field(repr=False)
    correlation_key: str = field(repr=False)
    prepared_request: AsaasPreparedRequest = field(repr=False)
    correlation_replayed: bool = False
    sandbox_only: bool = True
    real_money: bool = False
    http_call_executed: bool = False
    can_send_http: bool = False

    def safe_summary(self) -> dict[str, Any]:
        return {
            "operation": (
                "prepare_asaas_correlated_pix_payment"
            ),
            "provider": "asaas",
            "environment": "sandbox",
            "user_id_present": True,
            "external_reference_present": True,
            "correlation_key_present": True,
            "raw_external_reference_stored": False,
            "correlation_replayed": (
                self.correlation_replayed
            ),
            "prepared_request": {
                "method": self.prepared_request.method,
                "operation": (
                    self.prepared_request.operation
                ),
                "external_reference_present": True,
                "headers_configured": (
                    self.prepared_request.headers_configured
                ),
                "real_money": (
                    self.prepared_request.real_money
                ),
                "http_call_executed": (
                    self.prepared_request.http_call_executed
                ),
            },
            "sandbox_only": self.sandbox_only,
            "real_money": self.real_money,
            "http_call_executed": (
                self.http_call_executed
            ),
            "can_send_http": self.can_send_http,
        }


def _required_text(value, *, field_name: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise ValueError(f"{field_name} é obrigatório.")
    return normalized


def _positive_amount(value) -> Decimal:
    if value is None or isinstance(value, bool):
        raise ValueError(
            "value deve ser maior que zero."
        )

    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(
            "value deve ser um valor monetário válido."
        ) from exc

    if not amount.is_finite() or amount <= Decimal("0.00"):
        raise ValueError(
            "value deve ser maior que zero."
        )

    return amount


def _preparation_hash(
    *,
    user_id: int,
    correlation_key: str,
    customer_id: str,
    value: Decimal,
    due_date: str,
    description: str,
) -> str:
    contract = {
        "contract": (
            ASAAS_CORRELATED_PIX_PAYMENT_PREPARATION_CONTRACT
        ),
        "user_id": user_id,
        "correlation_key": correlation_key,
        "customer_id": customer_id,
        "value": format(value, "f"),
        "due_date": due_date,
        "description": description,
    }
    encoded = json.dumps(
        contract,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _stored_preparation_contract(
    *,
    correlation_record: IdempotencyKey,
    preparation_hash: str,
    value: Decimal,
) -> str:
    stored_contract = json.loads(
        correlation_record.response_json or "{}"
    )
    # P0.3: o valor da cobrança preparada é a única fonte do valor de
    # crédito sandbox. Só é persistido quando já está em centavos exatos;
    # caso contrário fica ausente e o crédito falha fechado.
    quantized_value = value.quantize(Decimal("0.01"))
    if quantized_value == value:
        stored_contract["prepared_amount"] = format(quantized_value, "f")
        stored_contract["prepared_currency"] = "BRL"
    stored_contract.update(
        {
            "preparation_contract": (
                ASAAS_CORRELATED_PIX_PAYMENT_PREPARATION_CONTRACT
            ),
            "prepared_request_hash": preparation_hash,
            "payment_operation": "create_pix_payment",
            "billing_type": "PIX",
            "prepared_request_present": True,
            "external_reference_present": True,
            "raw_external_reference_stored": False,
            "http_call_executed": False,
            "can_send_http": False,
            "real_money_enabled": False,
        }
    )
    return json.dumps(
        stored_contract,
        ensure_ascii=False,
        sort_keys=True,
    )


def _existing_preparation_matches(
    existing: IdempotencyKey,
    *,
    preparation_hash: str,
) -> bool:
    if (
        getattr(existing, "request_hash", None)
        != preparation_hash
    ):
        return False

    try:
        stored_contract = json.loads(
            existing.response_json or "{}"
        )
    except (TypeError, ValueError, json.JSONDecodeError):
        return False

    # P0.4: uma correlação cuja cobrança Sandbox já foi tentada/criada/
    # rejeitada continua sendo um replay válido da mesma preparação; o
    # estado da cobrança decide depois se há (ou não) chamada HTTP.
    charge_state = stored_contract.get("charge_http_state")
    if charge_state is None:
        http_state_valid = (
            stored_contract.get("http_call_executed") is False
        )
    else:
        http_state_valid = (
            charge_state in _ASAAS_CHARGE_HTTP_STATES
            and stored_contract.get("http_call_executed") is True
        )

    return (
        stored_contract.get("preparation_contract")
        == ASAAS_CORRELATED_PIX_PAYMENT_PREPARATION_CONTRACT
        and stored_contract.get("prepared_request_hash")
        == preparation_hash
        and http_state_valid
        and stored_contract.get("real_money_enabled")
        is False
    )


def prepare_asaas_correlated_pix_payment(
    db,
    *,
    client: AsaasSandboxClient,
    user_id: int,
    customer_id: str,
    value: Decimal,
    due_date: str,
    description: str,
    external_reference: str | None = None,
) -> AsaasCorrelatedPixPaymentPreparation:
    normalized_customer_id = _required_text(
        customer_id,
        field_name="customer_id",
    )
    normalized_due_date = _required_text(
        due_date,
        field_name="due_date",
    )
    normalized_description = _required_text(
        description,
        field_name="description",
    )
    normalized_value = _positive_amount(value)

    generated_reference = (
        external_reference
        if external_reference is not None
        else generate_asaas_payment_external_reference()
    )
    normalized_external_reference = (
        validate_asaas_payment_external_reference(
            generated_reference
        )
    )

    correlation_record = (
        build_asaas_payment_user_correlation_record(
            user_id=user_id,
            external_reference=(
                normalized_external_reference
            ),
        )
    )
    stored_correlation = json.loads(
        correlation_record.response_json or "{}"
    )
    normalized_user_id = int(
        stored_correlation["user_id"]
    )

    prepared_request = client.prepare_create_pix_payment(
        customer_id=normalized_customer_id,
        value=normalized_value,
        due_date=normalized_due_date,
        description=normalized_description,
        external_reference=(
            normalized_external_reference
        ),
    )

    preparation_hash = _preparation_hash(
        user_id=normalized_user_id,
        correlation_key=correlation_record.key,
        customer_id=normalized_customer_id,
        value=normalized_value,
        due_date=normalized_due_date,
        description=normalized_description,
    )

    correlation_record.request_hash = preparation_hash
    correlation_record.response_json = (
        _stored_preparation_contract(
            correlation_record=correlation_record,
            preparation_hash=preparation_hash,
            value=normalized_value,
        )
    )

    replayed = False

    try:
        db.add(correlation_record)
        db.flush()
    except IntegrityError:
        db.rollback()
        existing = (
            db.query(IdempotencyKey)
            .filter_by(key=correlation_record.key)
            .first()
        )

        if not existing or not _existing_preparation_matches(
            existing,
            preparation_hash=preparation_hash,
        ):
            raise AsaasCorrelatedPixPaymentConflictError(
                "Referência de correlação já utilizada "
                "por outra preparação."
            ) from None

        replayed = True
    except SQLAlchemyError:
        db.rollback()
        raise AsaasCorrelatedPixPaymentStorageError(
            "Não foi possível registrar a correlação "
            "da cobrança Asaas Sandbox."
        ) from None
    else:
        # Chave genuinamente nova (o branch de IntegrityError acima já
        # cobre replay/conflito) -- soft cap operacional P0-B, nunca
        # interfere em replay.
        try:
            enforce_sandbox_namespace_cap(
                db,
                namespace_prefix=ASAAS_PAYMENT_CORRELATION_KEY_PREFIX,
            )
        except SandboxNamespaceCapExceeded:
            db.rollback()
            raise AsaasCorrelatedPixPaymentCapacityError(
                "Capacidade sandbox temporariamente indisponível."
            ) from None

        try:
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            raise AsaasCorrelatedPixPaymentStorageError(
                "Não foi possível registrar a correlação "
                "da cobrança Asaas Sandbox."
            ) from None

    return AsaasCorrelatedPixPaymentPreparation(
        user_id=normalized_user_id,
        external_reference=(
            normalized_external_reference
        ),
        correlation_key=correlation_record.key,
        prepared_request=prepared_request,
        correlation_replayed=replayed,
    )


# --- P0.4: cobrança PIX real no Asaas SANDBOX -------------------------------


class AsaasCorrelatedPixChargeProviderUnavailableError(RuntimeError):
    """Timeout/erro de rede no Asaas Sandbox. Nunca há retry automático."""


class AsaasCorrelatedPixChargeProviderRejectedError(RuntimeError):
    """Asaas Sandbox respondeu erro (4xx/5xx) ou corpo inválido."""


class AsaasCorrelatedPixChargeIndeterminateError(RuntimeError):
    """
    Um POST já foi tentado para esta correlação e o desfecho é incerto
    (timeout, 5xx, resposta inválida ou payment_id não persistido). Um
    segundo POST poderia criar cobrança duplicada, então fica bloqueado
    até reconciliação manual.
    """


class AsaasCorrelatedPixChargePendingError(RuntimeError):
    """
    Há cobrança do usuário com desfecho ainda incerto (lock por usuário ou
    reconciliação inconclusiva). Nenhum POST é feito.
    """


class AsaasCorrelatedPixChargeConflictError(RuntimeError):
    """
    Reconciliação encontrou divergência. Estado "conflict": nunca há novo
    POST; exige revisão manual.
    """


class AsaasCorrelatedPixChargeCustomerMismatchError(RuntimeError):
    """O customer Asaas não comprova pertencer ao usuário autenticado."""


def asaas_sandbox_customer_external_reference(user_id: int) -> str:
    """externalReference determinístico do customer Asaas Sandbox do usuário."""
    if isinstance(user_id, bool) or not isinstance(user_id, int):
        raise ValueError("user_id inválido.")
    digest = hashlib.sha256(
        f"asaas-sandbox-customer:v1:{user_id}".encode("utf-8")
    ).hexdigest()
    return f"{_ASAAS_CUSTOMER_EXTERNAL_REFERENCE_PREFIX}{digest[:32]}"


AsaasHttpCall = Callable[[AsaasPreparedRequest], "tuple[int, dict[str, Any]]"]


@dataclass(frozen=True)
class AsaasCorrelatedPixCharge:
    preparation: AsaasCorrelatedPixPaymentPreparation = field(repr=False)
    pix_qr_code: dict[str, str] = field(repr=False)
    charge_replayed: bool = False

    def safe_summary(self) -> dict[str, Any]:
        return {
            "operation": "create_asaas_correlated_pix_charge",
            "provider": "asaas",
            "environment": "sandbox",
            "correlation_replayed": (
                self.preparation.correlation_replayed
            ),
            "charge_replayed": self.charge_replayed,
            "payment_id_present": True,
            "payment_id_exposed": False,
            "pix_qr_code_present": True,
            "sandbox_only": True,
            "real_money": False,
            "http_call_executed": True,
        }


def _load_stored_contract(db, *, correlation_key: str) -> tuple[str, dict]:
    raw = (
        db.query(IdempotencyKey.response_json)
        .filter(IdempotencyKey.key == correlation_key)
        .scalar()
    )
    try:
        contract = json.loads(raw or "")
    except (TypeError, ValueError):
        contract = None
    if not isinstance(contract, dict):
        raise AsaasCorrelatedPixChargeIndeterminateError(
            "Estado da cobrança Asaas Sandbox indisponível."
        )
    return raw, contract


def _safe_asaas_error_codes(body) -> list:
    """Extrai de um corpo 4xx apenas os `errors[].code` reconhecidos."""
    errors = body.get("errors") if isinstance(body, dict) else None
    if not isinstance(errors, list):
        return []
    codes = []
    for item in errors[:_ASAAS_ERROR_ITEMS_SCANNED_MAX]:
        code = item.get("code") if isinstance(item, dict) else None
        if (
            isinstance(code, str)
            and code in _ASAAS_KNOWN_ERROR_CODES
            and code not in codes
        ):
            codes.append(code)
    return codes


def _compare_and_set_contract(
    db,
    *,
    correlation_key: str,
    expected_json: str,
    contract: dict,
) -> tuple[bool, str]:
    new_json = json.dumps(contract, ensure_ascii=False, sort_keys=True)
    rowcount = (
        db.query(IdempotencyKey)
        .filter(
            IdempotencyKey.key == correlation_key,
            IdempotencyKey.response_json == expected_json,
        )
        .update(
            {IdempotencyKey.response_json: new_json},
            synchronize_session=False,
        )
    )
    return rowcount == 1, new_json


def _fetch_pix_qr_code(
    *,
    client: AsaasSandboxClient,
    payment_id: str,
    http_get: AsaasHttpCall,
) -> dict[str, str]:
    request = client.prepare_get_pix_qr_code(payment_id=payment_id)
    try:
        status, body = http_get(request)
    except Exception:
        raise AsaasCorrelatedPixChargeProviderUnavailableError(
            "Asaas Sandbox indisponível ao obter o QR Code PIX."
        ) from None

    if not isinstance(status, int) or not 200 <= status < 300 or not isinstance(body, dict):
        raise AsaasCorrelatedPixChargeProviderRejectedError(
            "Asaas Sandbox recusou a consulta do QR Code PIX."
        )

    payload = body.get("payload")
    encoded_image = body.get("encodedImage")
    expiration_date = body.get("expirationDate")
    if (
        not isinstance(payload, str)
        or not payload.strip()
        or not isinstance(encoded_image, str)
        or not isinstance(expiration_date, str)
    ):
        raise AsaasCorrelatedPixChargeProviderRejectedError(
            "Asaas Sandbox devolveu QR Code PIX inválido."
        )

    # Só o necessário para QR/copia-e-cola; qualquer outro campo é descartado.
    return {
        "payload": payload,
        "encoded_image": encoded_image,
        "expiration_date": expiration_date,
    }


def _commit_or_storage_error(db) -> None:
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise AsaasCorrelatedPixPaymentStorageError(
            "Não foi possível registrar o estado "
            "da cobrança Asaas Sandbox."
        ) from None


def _pending_lock_key(user_id: int) -> str:
    digest = hashlib.sha256(str(user_id).encode("utf-8")).hexdigest()
    return f"{ASAAS_SANDBOX_CHARGE_PENDING_LOCK_PREFIX}{digest}"


def _pending_lock_json(*, user_id: int, correlation_key: str) -> str:
    return json.dumps(
        {
            "contract": ASAAS_SANDBOX_CHARGE_PENDING_LOCK_CONTRACT,
            "correlation_key": correlation_key,
            "real_money_enabled": False,
            "user_id": user_id,
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def _release_pending_lock(db, *, user_id: int, correlation_key: str) -> None:
    # CAS-delete: só remove o lock desta correlação. Não commita.
    (
        db.query(IdempotencyKey)
        .filter(
            IdempotencyKey.key == _pending_lock_key(user_id),
            IdempotencyKey.response_json
            == _pending_lock_json(
                user_id=user_id,
                correlation_key=correlation_key,
            ),
        )
        .delete(synchronize_session=False)
    )


def _check_pending_lock(db, *, user_id: int, correlation_key: str) -> None:
    """
    Bloqueia nova cobrança enquanto outra do usuário tem desfecho incerto.
    Lock órfão só é removido se a correlação apontada estiver em estado
    terminal comprovado; qualquer outra situação é Pending (sem POST).
    """
    lock_key = _pending_lock_key(user_id)
    row = (
        db.query(IdempotencyKey.response_json)
        .filter(IdempotencyKey.key == lock_key)
        .first()
    )
    if row is None:
        return

    pending = AsaasCorrelatedPixChargePendingError(
        "Há cobrança Asaas Sandbox do usuário com desfecho incerto."
    )
    lock_raw = row[0]
    try:
        lock = json.loads(lock_raw or "")
    except (TypeError, ValueError):
        raise pending from None
    if (
        not isinstance(lock, dict)
        or lock.get("contract") != ASAAS_SANDBOX_CHARGE_PENDING_LOCK_CONTRACT
        or lock.get("user_id") != user_id
        or lock.get("real_money_enabled") is not False
    ):
        raise pending
    locked_key = lock.get("correlation_key")
    if not isinstance(locked_key, str) or not locked_key:
        raise pending
    if locked_key == correlation_key:
        # Lock desta correlação sem estado "attempted": inconsistente.
        raise pending

    locked_raw = (
        db.query(IdempotencyKey.response_json)
        .filter(IdempotencyKey.key == locked_key)
        .scalar()
    )
    try:
        locked_contract = json.loads(locked_raw or "")
    except (TypeError, ValueError):
        raise pending from None
    if (
        not isinstance(locked_contract, dict)
        or locked_contract.get("user_id") != user_id
        or locked_contract.get("charge_http_state")
        not in _ASAAS_CHARGE_HTTP_TERMINAL_STATES
    ):
        raise pending

    try:
        (
            db.query(IdempotencyKey)
            .filter(
                IdempotencyKey.key == lock_key,
                IdempotencyKey.response_json == lock_raw,
            )
            .delete(synchronize_session=False)
        )
    except SQLAlchemyError:
        db.rollback()
        raise pending from None
    _commit_or_storage_error(db)


def _verify_customer_ownership(
    *,
    customer_request,
    customer_id: str,
    user_id: int,
    http_get: AsaasHttpCall,
) -> None:
    """
    GET /customers/{id} único, sem retry. Só aceita customer cujo
    externalReference é o "agcus_" determinístico do usuário autenticado.
    """
    try:
        status, body = http_get(customer_request)
    except Exception:
        raise AsaasCorrelatedPixChargeProviderUnavailableError(
            "Asaas Sandbox indisponível ao verificar o customer."
        ) from None
    if not isinstance(status, int) or not 200 <= status < 300 or not isinstance(body, dict):
        raise AsaasCorrelatedPixChargeProviderUnavailableError(
            "Asaas Sandbox não confirmou o customer."
        )
    if (
        body.get("id") != customer_id
        or body.get("externalReference")
        != asaas_sandbox_customer_external_reference(user_id)
        or body.get("deleted") is True
    ):
        raise AsaasCorrelatedPixChargeCustomerMismatchError(
            "Customer Asaas Sandbox não pertence ao usuário."
        )


def _parse_charge_attempted_at(raw) -> datetime | None:
    if not isinstance(raw, str):
        return None
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed


def _listed_payment_id_if_matches(
    item,
    *,
    user_id: int,
    correlation_key: str,
    value: Decimal,
    due_date: str,
    description: str,
    external_reference: str,
    prepared_request_hash,
) -> str | None:
    if not isinstance(item, dict):
        return None
    payment_id = item.get("id")
    customer = item.get("customer")
    raw_value = item.get("value")
    if (
        not isinstance(payment_id, str)
        or not _ASAAS_PAYMENT_ID_PATTERN.match(payment_id)
        or item.get("billingType") != "PIX"
        or item.get("externalReference") != external_reference
        or item.get("deleted") is True
        or item.get("dueDate") != due_date
        or item.get("description") != description
        or not isinstance(customer, str)
        or not customer
        or isinstance(raw_value, bool)
        or not isinstance(raw_value, (int, float, str))
    ):
        return None
    try:
        listed_value = Decimal(str(raw_value))
    except InvalidOperation:
        return None
    if listed_value != value:
        return None
    # O customer devolvido precisa reproduzir o hash da preparação.
    if _preparation_hash(
        user_id=user_id,
        correlation_key=correlation_key,
        customer_id=customer,
        value=value,
        due_date=due_date,
        description=description,
    ) != prepared_request_hash:
        return None
    return payment_id


def _reconcile_attempted_charge(
    db,
    *,
    client: AsaasSandboxClient,
    preparation: AsaasCorrelatedPixPaymentPreparation,
    stored_json: str,
    contract: dict,
    user_id: int,
    value: Decimal,
    due_date: str,
    description: str,
    external_reference: str,
    http_get: AsaasHttpCall,
) -> AsaasCorrelatedPixCharge:
    """
    "attempted" nunca gera novo POST. Um único GET por externalReference
    (sem retry) decide: created (1 cobrança idêntica), not_created (lista
    vazia após a janela), conflict (qualquer divergência) ou Pending
    (inconclusivo, sem mudança de estado).
    """
    correlation_key = preparation.correlation_key
    pending = AsaasCorrelatedPixChargePendingError(
        "Cobrança Asaas Sandbox já tentada com desfecho incerto."
    )
    # Mesma normalização da preparação (o hash é recalculado com ela).
    value = _positive_amount(value)
    due_date = _required_text(due_date, field_name="due_date")
    description = _required_text(description, field_name="description")

    request = client.prepare_list_payments_by_external_reference(
        external_reference=external_reference,
        limit=2,
    )
    try:
        status, body = http_get(request)
    except Exception:
        raise pending from None
    if not isinstance(status, int) or not 200 <= status < 300 or not isinstance(body, dict):
        raise pending
    data = body.get("data")
    total_count = body.get("totalCount")
    has_more = body.get("hasMore")
    if not isinstance(data, list) or (
        total_count is not None
        and (isinstance(total_count, bool) or not isinstance(total_count, int))
    ):
        raise pending

    def _transition(new_contract: dict, *, release_lock: bool) -> bool:
        try:
            persisted, _ = _compare_and_set_contract(
                db,
                correlation_key=correlation_key,
                expected_json=stored_json,
                contract=new_contract,
            )
            if not persisted:
                db.rollback()
                return False
            if release_lock:
                _release_pending_lock(
                    db,
                    user_id=user_id,
                    correlation_key=correlation_key,
                )
        except SQLAlchemyError:
            db.rollback()
            return False
        _commit_or_storage_error(db)
        return True

    if not data and has_more is not True and total_count in (None, 0):
        attempted_at = _parse_charge_attempted_at(
            contract.get("charge_attempted_at")
        )
        if (
            attempted_at is None
            or datetime.now(timezone.utc) - attempted_at
            < ASAAS_SANDBOX_CHARGE_NOT_CREATED_AFTER
        ):
            raise pending
        not_created_contract = dict(contract)
        not_created_contract["charge_http_state"] = ASAAS_CHARGE_HTTP_NOT_CREATED
        if not _transition(not_created_contract, release_lock=True):
            raise pending
        raise AsaasCorrelatedPixChargeProviderRejectedError(
            "Cobrança Asaas Sandbox não foi criada."
        )

    payment_id = None
    if len(data) == 1 and has_more is not True and total_count in (None, 1):
        payment_id = _listed_payment_id_if_matches(
            data[0],
            user_id=user_id,
            correlation_key=correlation_key,
            value=value,
            due_date=due_date,
            description=description,
            external_reference=external_reference,
            prepared_request_hash=contract.get("prepared_request_hash"),
        )

    if payment_id is not None:
        created_contract = dict(contract)
        created_contract.update(
            {
                "charge_http_state": ASAAS_CHARGE_HTTP_CREATED,
                "asaas_payment_id": payment_id,
            }
        )
        if not _transition(created_contract, release_lock=True):
            raise pending
        return AsaasCorrelatedPixCharge(
            preparation=preparation,
            pix_qr_code=_fetch_pix_qr_code(
                client=client,
                payment_id=payment_id,
                http_get=http_get,
            ),
            charge_replayed=True,
        )

    # Divergência: conflict mantém o lock (revisão manual, nunca novo POST).
    conflict_contract = dict(contract)
    conflict_contract["charge_http_state"] = ASAAS_CHARGE_HTTP_CONFLICT
    if not _transition(conflict_contract, release_lock=False):
        raise pending
    raise AsaasCorrelatedPixChargeConflictError(
        "Cobrança Asaas Sandbox divergente; requer revisão manual."
    )


# Status de apply_asaas_webhook_charge_transition que permitem crédito.
ASAAS_WEBHOOK_CHARGE_CREDITABLE_STATUSES = frozenset(
    {"untracked", ASAAS_CHARGE_HTTP_CREATED, ASAAS_CHARGE_HTTP_CREATED_LATE}
)


def apply_asaas_webhook_charge_transition(
    db,
    *,
    correlation_key: str,
    user_id: int,
    payment_id,
) -> str:
    """
    Aplica (via CAS, sem commit) a transição de charge_http_state indicada
    por um webhook com payment_id. O chamador commita junto com o crédito.

    Retorna "untracked" (sem charge_http_state: comportamento anterior),
    "created", "created_late", "payment_id_conflict", "conflict",
    "invalid_state" ou "retry_exhausted". Só os de
    ASAAS_WEBHOOK_CHARGE_CREDITABLE_STATUSES permitem crédito.
    """
    for _ in range(3):
        raw = (
            db.query(IdempotencyKey.response_json)
            .filter(IdempotencyKey.key == correlation_key)
            .scalar()
        )
        try:
            contract = json.loads(raw or "")
        except (TypeError, ValueError):
            return "invalid_state"
        if (
            not isinstance(contract, dict)
            or contract.get("real_money_enabled") is not False
            or contract.get("user_id") != user_id
        ):
            return "invalid_state"

        state = contract.get("charge_http_state")
        if state is None:
            return "untracked"
        if not isinstance(payment_id, str) or not _ASAAS_PAYMENT_ID_PATTERN.match(payment_id):
            return "invalid_state"

        if state in (ASAAS_CHARGE_HTTP_CREATED, ASAAS_CHARGE_HTTP_CREATED_LATE):
            if contract.get("asaas_payment_id") == payment_id:
                return state
            if state == ASAAS_CHARGE_HTTP_CREATED_LATE:
                return "payment_id_conflict"
            new_contract = dict(contract)
            new_contract["charge_http_state"] = ASAAS_CHARGE_HTTP_CONFLICT
            result, release_lock = "payment_id_conflict", False
        elif state == ASAAS_CHARGE_HTTP_ATTEMPTED:
            new_contract = dict(contract)
            new_contract.update(
                {
                    "charge_http_state": ASAAS_CHARGE_HTTP_CREATED,
                    "asaas_payment_id": payment_id,
                }
            )
            result, release_lock = ASAAS_CHARGE_HTTP_CREATED, True
        elif state == ASAAS_CHARGE_HTTP_NOT_CREATED:
            # Lock já foi liberado em not_created; não é reaberto.
            new_contract = dict(contract)
            new_contract.update(
                {
                    "charge_http_state": ASAAS_CHARGE_HTTP_CREATED_LATE,
                    "asaas_payment_id": payment_id,
                }
            )
            result, release_lock = ASAAS_CHARGE_HTTP_CREATED_LATE, False
        elif state in (ASAAS_CHARGE_HTTP_REJECTED, ASAAS_CHARGE_HTTP_CONFLICT):
            return "conflict"
        else:
            return "invalid_state"

        persisted, _ = _compare_and_set_contract(
            db,
            correlation_key=correlation_key,
            expected_json=raw,
            contract=new_contract,
        )
        if persisted:
            if release_lock:
                _release_pending_lock(
                    db,
                    user_id=user_id,
                    correlation_key=correlation_key,
                )
            return result
    return "retry_exhausted"


def _require_max_two_decimal_places(value) -> None:
    normalized = _positive_amount(value)
    try:
        has_more_places = normalized != normalized.quantize(Decimal("0.01"))
    except InvalidOperation:
        has_more_places = True
    if has_more_places:
        raise ValueError("amount deve ter no máximo 2 casas decimais.")


def create_asaas_correlated_pix_charge(
    db,
    *,
    client: AsaasSandboxClient,
    user_id: int,
    customer_id: str,
    value: Decimal,
    due_date: str,
    description: str,
    external_reference: str,
    http_post: AsaasHttpCall,
    http_get: AsaasHttpCall,
) -> AsaasCorrelatedPixCharge:
    """
    Cria (no máximo uma vez por correlação) a cobrança PIX no Asaas
    SANDBOX e devolve somente os dados do QR Code.

    Máquina de estados em charge_http_state (registro de correlação):
    - sem estado -> lock por usuário + GET do customer (prova de posse via
      externalReference "agcus_") -> "attempted" com charge_attempted_at
      (CAS + lock + commit ANTES do POST; falha => sem POST)
    - POST 4xx -> "rejected" (cobrança comprovadamente não criada)
    - POST 2xx válido -> "created" + asaas_payment_id
    - timeout/5xx/corpo inválido/falha ao persistir -> fica "attempted"
      (lock mantido); replay só reconcilia por GET, nunca novo POST.
    - "created"/"created_late" -> replay só faz o GET do QR Code.
    - "not_created" -> Rejected; "conflict" -> Conflict (revisão manual).
    """
    if not external_reference:
        raise ValueError("external_reference é obrigatório.")
    # BRL: no máximo 2 casas decimais => ValueError (422) antes de qualquer
    # HTTP/persistência.
    _require_max_two_decimal_places(value)
    # Formato inválido => ValueError (422) antes de qualquer HTTP/persistência.
    customer_request = client.prepare_get_customer(customer_id=customer_id)

    preparation = prepare_asaas_correlated_pix_payment(
        db,
        client=client,
        user_id=user_id,
        customer_id=customer_id,
        value=value,
        due_date=due_date,
        description=description,
        external_reference=external_reference,
    )
    correlation_key = preparation.correlation_key
    stored_json, contract = _load_stored_contract(
        db,
        correlation_key=correlation_key,
    )

    if contract.get("real_money_enabled") is not False:
        raise AsaasCorrelatedPixChargeIndeterminateError(
            "Estado da cobrança Asaas Sandbox inválido."
        )

    state = contract.get("charge_http_state")

    if state in (ASAAS_CHARGE_HTTP_CREATED, ASAAS_CHARGE_HTTP_CREATED_LATE):
        payment_id = contract.get("asaas_payment_id")
        if not isinstance(payment_id, str) or not _ASAAS_PAYMENT_ID_PATTERN.match(payment_id):
            raise AsaasCorrelatedPixChargeIndeterminateError(
                "Estado da cobrança Asaas Sandbox inválido."
            )
        return AsaasCorrelatedPixCharge(
            preparation=preparation,
            pix_qr_code=_fetch_pix_qr_code(
                client=client,
                payment_id=payment_id,
                http_get=http_get,
            ),
            charge_replayed=True,
        )

    if state == ASAAS_CHARGE_HTTP_ATTEMPTED:
        return _reconcile_attempted_charge(
            db,
            client=client,
            preparation=preparation,
            stored_json=stored_json,
            contract=contract,
            user_id=user_id,
            value=value,
            due_date=due_date,
            description=description,
            external_reference=external_reference,
            http_get=http_get,
        )

    if state == ASAAS_CHARGE_HTTP_REJECTED:
        raise AsaasCorrelatedPixChargeProviderRejectedError(
            "Asaas Sandbox recusou a criação da cobrança."
        )

    if state == ASAAS_CHARGE_HTTP_NOT_CREATED:
        raise AsaasCorrelatedPixChargeProviderRejectedError(
            "Cobrança Asaas Sandbox não foi criada."
        )

    if state == ASAAS_CHARGE_HTTP_CONFLICT:
        raise AsaasCorrelatedPixChargeConflictError(
            "Cobrança Asaas Sandbox divergente; requer revisão manual."
        )

    if state is not None:
        raise AsaasCorrelatedPixChargeIndeterminateError(
            "Estado da cobrança Asaas Sandbox inválido."
        )

    # 0) Nenhuma outra cobrança do usuário com desfecho incerto.
    _check_pending_lock(db, user_id=user_id, correlation_key=correlation_key)

    # 0b) Customer precisa comprovar posse (falha => sem claim e sem POST).
    _verify_customer_ownership(
        customer_request=customer_request,
        customer_id=customer_id,
        user_id=user_id,
        http_get=http_get,
    )

    # 1) Reserva a tentativa + lock ANTES do POST. Se não persistir, não há POST.
    attempted_contract = dict(contract)
    attempted_contract.update(
        {
            "charge_http_state": ASAAS_CHARGE_HTTP_ATTEMPTED,
            "charge_attempted_at": datetime.now(timezone.utc).isoformat(),
            "http_call_executed": True,
            "can_send_http": True,
            "real_money_enabled": False,
        }
    )
    try:
        claimed, attempted_json = _compare_and_set_contract(
            db,
            correlation_key=correlation_key,
            expected_json=stored_json,
            contract=attempted_contract,
        )
        if claimed:
            db.add(
                IdempotencyKey(
                    key=_pending_lock_key(user_id),
                    response_json=_pending_lock_json(
                        user_id=user_id,
                        correlation_key=correlation_key,
                    ),
                )
            )
            db.flush()
    except IntegrityError:
        db.rollback()
        raise AsaasCorrelatedPixChargePendingError(
            "Há cobrança Asaas Sandbox do usuário com desfecho incerto."
        ) from None
    except SQLAlchemyError:
        db.rollback()
        raise AsaasCorrelatedPixPaymentStorageError(
            "Não foi possível registrar o estado "
            "da cobrança Asaas Sandbox."
        ) from None
    if not claimed:
        db.rollback()
        raise AsaasCorrelatedPixChargeIndeterminateError(
            "Cobrança Asaas Sandbox em andamento por outra requisição."
        )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AsaasCorrelatedPixChargePendingError(
            "Há cobrança Asaas Sandbox do usuário com desfecho incerto."
        ) from None
    except SQLAlchemyError:
        db.rollback()
        raise AsaasCorrelatedPixPaymentStorageError(
            "Não foi possível registrar o estado "
            "da cobrança Asaas Sandbox."
        ) from None

    # 2) POST único, sem retry.
    try:
        status, body = http_post(preparation.prepared_request)
    except Exception:
        raise AsaasCorrelatedPixChargeProviderUnavailableError(
            "Asaas Sandbox indisponível ao criar a cobrança."
        ) from None

    if isinstance(status, int) and 400 <= status < 500:
        rejected_contract = dict(attempted_contract)
        rejected_contract["charge_http_state"] = ASAAS_CHARGE_HTTP_REJECTED
        rejected_contract["charge_http_status"] = status
        rejected_contract["charge_provider_error_codes"] = (
            _safe_asaas_error_codes(body)
        )
        try:
            rejected, _ = _compare_and_set_contract(
                db,
                correlation_key=correlation_key,
                expected_json=attempted_json,
                contract=rejected_contract,
            )
            if rejected:
                _release_pending_lock(
                    db,
                    user_id=user_id,
                    correlation_key=correlation_key,
                )
                db.commit()
            else:
                db.rollback()
        except SQLAlchemyError:
            # Fica "attempted": continua bloqueando novo POST (fail-closed).
            db.rollback()
        raise AsaasCorrelatedPixChargeProviderRejectedError(
            "Asaas Sandbox recusou a criação da cobrança."
        )

    if not isinstance(status, int) or not 200 <= status < 300:
        raise AsaasCorrelatedPixChargeProviderRejectedError(
            "Asaas Sandbox falhou ao criar a cobrança."
        )

    # Mesmo critério completo da reconciliação (id, PIX, externalReference,
    # deleted, dueDate, description, customer, value e hash da preparação).
    payment_id = _listed_payment_id_if_matches(
        body,
        user_id=user_id,
        correlation_key=correlation_key,
        value=_positive_amount(value),
        due_date=_required_text(due_date, field_name="due_date"),
        description=_required_text(description, field_name="description"),
        external_reference=preparation.external_reference,
        prepared_request_hash=attempted_contract.get("prepared_request_hash"),
    )
    if payment_id is None:
        raise AsaasCorrelatedPixChargeProviderRejectedError(
            "Asaas Sandbox devolveu resposta de cobrança inválida."
        )

    # 3) Persiste o payment_id. Se falhar, fica "attempted" (sem novo POST).
    created_contract = dict(attempted_contract)
    created_contract.update(
        {
            "charge_http_state": ASAAS_CHARGE_HTTP_CREATED,
            "asaas_payment_id": payment_id,
        }
    )
    try:
        persisted, _ = _compare_and_set_contract(
            db,
            correlation_key=correlation_key,
            expected_json=attempted_json,
            contract=created_contract,
        )
        if persisted:
            _release_pending_lock(
                db,
                user_id=user_id,
                correlation_key=correlation_key,
            )
    except SQLAlchemyError:
        db.rollback()
        raise AsaasCorrelatedPixPaymentStorageError(
            "Não foi possível registrar o estado "
            "da cobrança Asaas Sandbox."
        ) from None
    if persisted:
        _commit_or_storage_error(db)
    else:
        db.rollback()
        # O webhook pode ter confirmado o mesmo payment_id antes de nós.
        _, current = _load_stored_contract(db, correlation_key=correlation_key)
        if not (
            current.get("charge_http_state") == ASAAS_CHARGE_HTTP_CREATED
            and current.get("asaas_payment_id") == payment_id
            and current.get("real_money_enabled") is False
        ):
            raise AsaasCorrelatedPixChargeIndeterminateError(
                "Estado da cobrança Asaas Sandbox alterado concorrentemente."
            )

    # 4) QR Code. Falha aqui é recuperável: replay só refaz o GET.
    return AsaasCorrelatedPixCharge(
        preparation=preparation,
        pix_qr_code=_fetch_pix_qr_code(
            client=client,
            payment_id=payment_id,
            http_get=http_get,
        ),
        charge_replayed=False,
    )
