from sqlalchemy.exc import IntegrityError
import hashlib
import json
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from app.models.transaction import Transaction
from app.models.pix_ledger import PixLedger


# Comprimento físico da coluna idempotency_keys.key (String(128)).
# A raw key precisa caber nesse limite porque, durante a Fase 1 (M1.1),
# ela ainda é usada como "compatibility bridge" com instâncias antigas
# que gravam o valor cru diretamente.
PIX_SEND_IDEMPOTENCY_KEY_MAX_LENGTH = 128

# Prefixo da chave escopada por usuário. Comprimento final sempre fixo:
# len("pix-send:") + 64 (sha256 hex) = 73 caracteres.
PIX_SEND_SCOPED_KEY_PREFIX = "pix-send:"

# Campos que uma resposta concluída de send_pix sempre possui. Usado para
# validar, de forma estrita, que uma linha de idempotency_keys encontrada
# via a chave crua (bridge) é de fato uma resposta de send_pix — nunca de
# outro fluxo que compartilha a mesma tabela (webhook Asaas, correlação de
# pagamento, etc).
_PIX_SEND_RESPONSE_FIELDS = (
    "id",
    "valor",
    "taxa_percentual",
    "taxa_valor",
    "valor_liquido",
    "status",
)


def _round_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _idem_hash(user_id: int, valor: Decimal, chave_pix: str, descricao: str) -> str:
    # hash estável e auditável (64 hex chars)
    msg = f"{user_id}|{str(valor)}|{chave_pix}|{descricao}".encode("utf-8")
    return hashlib.sha256(msg).hexdigest()


def _pix_send_scoped_key(user_id: int, raw_idempotency_key: str) -> str:
    """Chave de idempotência escopada por usuário, comprimento fixo (73 chars).

    Deriva de sha256(user_id|raw_key), então a mesma combinação usuário+chave
    sempre produz a mesma scoped_key, e usuários diferentes com a mesma
    raw_key produzem chaves totalmente distintas (isolamento cross-user).
    """
    digest = hashlib.sha256(f"{user_id}|{raw_idempotency_key}".encode("utf-8")).hexdigest()
    return f"{PIX_SEND_SCOPED_KEY_PREFIX}{digest}"


def _idempotency_conflict_response() -> dict:
    return {
        "status": "conflict",
        "error": "Idempotency-Key reuse com payload diferente",
        "code": "IDEMPOTENCY_KEY_REUSE_DIFFERENT_PAYLOAD",
    }


def _idempotency_in_progress_response() -> dict:
    return {
        "status": "in_progress",
        "error": "Requisição com este Idempotency-Key ainda está em processamento",
        "code": "IDEMPOTENCY_IN_PROGRESS",
    }


def _parse_pix_send_completed_response(response_json: str | None) -> dict | None:
    """Valida estritamente que response_json é uma resposta concluída de
    send_pix, sem confiar cegamente em nenhum conteúdo vindo da tabela
    compartilhada idempotency_keys (que também é usada por outros fluxos,
    como webhook Asaas e correlação de pagamento).

    Retorna o payload já parseado se for válido, ou None caso contrário
    (fail-closed) — nunca lança exceção.
    """
    if not response_json:
        return None

    try:
        payload = json.loads(response_json)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None

    if not isinstance(payload, dict):
        return None

    if not all(field in payload for field in _PIX_SEND_RESPONSE_FIELDS):
        return None

    tx_id = payload.get("id")
    if not isinstance(tx_id, int) or isinstance(tx_id, bool):
        return None

    return payload


def _resolve_pix_send_completed_owner(db: Session, payload: dict) -> int | None:
    """Resolve o dono real de uma resposta de send_pix já validada
    estruturalmente, consultando Transaction.id -> Transaction.user_id.

    Nunca infere ownership a partir de request_hash (SHA-256 não pode ser
    invertido). Retorna None se o id não resolver a uma Transaction real
    (fail-closed).
    """
    tx = db.query(Transaction).filter(Transaction.id == payload["id"]).first()
    if tx is None:
        return None
    return tx.user_id


def _get_user_balance(db: Session, user_id: int) -> Decimal:
    result = (
        db.query(
            func.coalesce(
                func.sum(
                    case(
                        (PixLedger.kind == "credit", PixLedger.amount),
                        else_=-PixLedger.amount,
                    )
                ),
                0,
            )
        )
        .filter(PixLedger.user_id == user_id)
        .scalar()
    )

    return Decimal(result or 0)


def send_pix(
    db: Session,
    user_id: int,
    valor: Decimal,
    chave_pix: str,
    descricao: str = "PIX",
    idempotency_key: str | None = None,
):
    valor = _round_money(Decimal(valor))
    # -----------------------------
    # Idempotency (fintech-grade) — M1.1 Fase 1
    #
    # Duas chaves coexistem nesta fase:
    #
    # 1) raw bridge (key = idempotency_key, exatamente como o código
    #    anterior a esta correção grava): existe apenas para coordenar
    #    com eventuais instâncias antigas ainda em execução durante um
    #    rolling deploy. Continua usando INSERT + flush + UNIQUE +
    #    IntegrityError — o mesmo mecanismo que instâncias antigas usam,
    #    para que as duas disputem exatamente o mesmo valor de chave.
    #
    # 2) scoped_key (key = "pix-send:" + sha256(user_id|idempotency_key)):
    #    a chave real, escopada por usuário, que corrige a colisão
    #    cross-user do desenho anterior. Usa o mesmo mecanismo de
    #    concorrência (INSERT + flush + UNIQUE + IntegrityError).
    #
    # Ownership de uma linha raw pré-existente NUNCA é inferido por
    # comparação de request_hash (SHA-256 não é reversível). Só é
    # considerado conhecido quando response_json resolve, de forma
    # inequívoca, a uma Transaction real via Transaction.id -> user_id.
    # Qualquer caso indeterminado é fail-closed (IDEMPOTENCY_IN_PROGRESS).
    # -----------------------------
    raw_bridge_record = None
    raw_freshly_claimed = False
    scoped_record = None

    if idempotency_key:
        from app.models.idempotency import IdempotencyKey

        if len(idempotency_key) > PIX_SEND_IDEMPOTENCY_KEY_MAX_LENGTH:
            raise ValueError(
                "Idempotency-Key excede o tamanho máximo permitido "
                f"({PIX_SEND_IDEMPOTENCY_KEY_MAX_LENGTH} caracteres)."
            )

        req_hash = _idem_hash(user_id=user_id, valor=valor, chave_pix=chave_pix, descricao=descricao)
        scoped_key = _pix_send_scoped_key(user_id, idempotency_key)

        # --- 1) Raw compatibility bridge ---
        try:
            raw_bridge_record = IdempotencyKey(key=idempotency_key, request_hash=req_hash)
            db.add(raw_bridge_record)
            db.flush()
            raw_freshly_claimed = True
        except IntegrityError:
            db.rollback()
            raw_bridge_record = None

            existing_raw = db.query(IdempotencyKey).filter_by(key=idempotency_key).first()
            if not existing_raw:
                raise

            existing_payload = _parse_pix_send_completed_response(existing_raw.response_json)
            if existing_payload is None:
                # Sem response_json válido de send_pix (em processamento,
                # malformado, ou pertencente a outro fluxo/purpose que
                # compartilha a tabela) => fail-closed.
                return _idempotency_in_progress_response()

            owner_id = _resolve_pix_send_completed_owner(db, existing_payload)
            if owner_id is None:
                # id presente mas não resolve a nenhuma Transaction real
                # => fail-closed, nunca assumir que pode prosseguir.
                return _idempotency_in_progress_response()

            if owner_id == user_id:
                if existing_raw.request_hash == req_hash:
                    return existing_payload
                return _idempotency_conflict_response()

            # owner_id != user_id: a raw key pertence a outro usuário.
            # Não alteramos essa linha; ela não bloqueia semanticamente o
            # usuário atual — seguimos para a scoped_key própria dele.

        # --- 2) Scoped key (por usuário) ---
        try:
            scoped_record = IdempotencyKey(key=scoped_key, request_hash=req_hash)
            db.add(scoped_record)
            db.flush()
        except IntegrityError:
            db.rollback()
            raw_bridge_record = None
            raw_freshly_claimed = False
            scoped_record = None

            existing_scoped = db.query(IdempotencyKey).filter_by(key=scoped_key).first()
            if not existing_scoped:
                raise

            if getattr(existing_scoped, "request_hash", None) and existing_scoped.request_hash != req_hash:
                return _idempotency_conflict_response()

            if existing_scoped.response_json:
                return json.loads(existing_scoped.response_json)

            return _idempotency_in_progress_response()

    # -----------------------------

    taxa_percentual = Decimal("0.0000")
    taxa_valor = Decimal("0.00")
    valor_liquido = valor

    from sqlalchemy import select
    from app.models.pix_ledger import PixLedger

    db.execute(
        select(PixLedger)
        .where(PixLedger.user_id == user_id)
        .with_for_update()
    )

    saldo_atual = _get_user_balance(db, user_id)

    if saldo_atual < valor:
        raise ValueError("Saldo insuficiente")

    tx = Transaction(
        user_id=user_id,
        tipo="saida",
        valor=float(valor),  # coluna no Postgres é double precision
        referencia=chave_pix,
    )

    db.add(tx)
    db.flush()

    ledger_entry = PixLedger(
        user_id=user_id,
        kind="debit",
        amount=valor,
        ref_tx_id=tx.id,
        description=descricao,
    )

    db.add(ledger_entry)

    if idempotency_key:
        response_payload = json.dumps({
            "id": tx.id,
            "valor": str(tx.valor),
            "taxa_percentual": str(taxa_percentual),
            "taxa_valor": str(taxa_valor),
            "valor_liquido": str(valor_liquido),
            "status": "success"
        })

        if scoped_record is not None:
            scoped_record.status_code = 200
            scoped_record.response_json = response_payload

        if raw_freshly_claimed and raw_bridge_record is not None:
            raw_bridge_record.status_code = 200
            raw_bridge_record.response_json = response_payload

    db.commit()
    db.refresh(tx)

    tx.valor = valor
    tx.taxa_percentual = taxa_percentual
    tx.taxa_valor = taxa_valor
    tx.valor_liquido = valor_liquido
    return tx
