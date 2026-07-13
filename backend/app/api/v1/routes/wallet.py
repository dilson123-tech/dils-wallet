from fastapi import APIRouter, Body, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from decimal import Decimal
from datetime import datetime, timezone
import hashlib
import hmac
import json
from pydantic import BaseModel

from app.database import get_db
from app.utils.authz import require_customer
from app.models.transaction import Transaction
from app.models.idempotency import IdempotencyKey
from app.models.user_main import User
from app.config import WALLET_MODE, IS_PARTNER_WALLET
from app.partner import (
    PartnerWebhookEvent,
    StatementItem,
    get_partner_adapter,
)
from app.partner.asaas_config import AsaasConfigError, load_asaas_sandbox_config
from app.services.wallet_partner_service import (
    create_wallet_pix_payment as create_partner_pix_payment,
    get_wallet_balance as get_partner_wallet_balance,
    get_wallet_statement as get_partner_wallet_statement,
    handle_wallet_webhook as handle_partner_wallet_webhook,
)

router = APIRouter()

def _wallet_mode_label() -> str:
    if WALLET_MODE == "partner" and IS_PARTNER_WALLET:
        return "partner"
    return "demo"


def _account_status_payload(current_user: User) -> dict:
    """
    Status de prontidão da conta/wallet para o cliente.

    Este endpoint não movimenta dinheiro.
    Ele deixa explícito se a carteira está em demo, sandbox/parceiro
    ou produção futura, evitando prometer operação financeira real antes
    de um PSP/BaaS homologado.
    """
    wallet_mode = _wallet_mode_label()

    try:
        adapter = get_partner_adapter()
        provider = adapter.provider_name
        adapter_ready = True
        adapter_error = None
    except Exception as exc:
        provider = None
        adapter_ready = False
        adapter_error = str(exc)

    real_money_enabled = bool(IS_PARTNER_WALLET and adapter_ready)

    if real_money_enabled:
        account_status = "partner_ready"
        kyc_status = "provider_required"
        kyb_status = "provider_required"
        limitations = [
            "Operação real depende das regras e limites do parceiro financeiro.",
            "KYC/KYB, saldo, Pix, liquidação e compliance são fornecidos pelo parceiro.",
        ]
        next_steps = [
            "Concluir integração sandbox com o parceiro.",
            "Validar KYC/KYB.",
            "Validar Pix entrada e saída.",
            "Ativar webhooks e reconciliação.",
        ]
    else:
        account_status = "demo_active"
        kyc_status = "not_started"
        kyb_status = "not_started"
        limitations = [
            "Modo demonstração: não movimenta dinheiro real.",
            "Saldo, Pix, QR Code e comprovantes ainda não representam operação financeira real.",
            "A Aurea Gold ainda depende de parceiro financeiro/PSP/BaaS para produção.",
        ]
        next_steps = [
            "Selecionar parceiro financeiro/PSP/BaaS.",
            "Implementar adapter sandbox.",
            "Implementar KYC/KYB.",
            "Implementar Pix real de entrada e saída via parceiro.",
            "Implementar webhooks, comprovantes, limites e reconciliação.",
        ]

    return {
        "ok": True,
        "service": "aurea-wallet",
        "user": {
            "id": getattr(current_user, "id", None),
            "email": getattr(current_user, "email", None),
            "full_name": getattr(current_user, "full_name", None),
            "type": getattr(current_user, "type", None),
            "role": getattr(current_user, "role", None),
        },
        "wallet": {
            "mode": wallet_mode,
            "provider": provider or "not_configured",
            "provider_adapter_ready": adapter_ready,
            "provider_adapter_error": adapter_error,
            "real_money_enabled": real_money_enabled,
            "account_status": account_status,
            "kyc_status": kyc_status,
            "kyb_status": kyb_status,
            "currency": "BRL",
        },
        "limitations": limitations,
        "next_steps": next_steps,
    }


@router.get("/api/v1/wallet/account-status")
def get_wallet_account_status(
    current_user: User = Depends(require_customer),
):
    """
    Status estruturado da conta/wallet do cliente.

    Primeiro bloco da prontidão de carteira real:
    deixa claro o modo atual, provedor, KYC/KYB, dinheiro real
    e próximos passos de ativação.
    """
    return _account_status_payload(current_user)


def _decimal_as_money(value) -> str:
    return f"{Decimal(value or 0):.2f}"


@router.get("/api/v1/wallet/structured-balance")
def get_wallet_structured_balance(
    current_user: User = Depends(require_customer),
):
    """
    Saldo estruturado da wallet.

    Prepara o contrato real da carteira:
    - available: disponível
    - blocked: bloqueado
    - pending: pendente/processando
    - currency: moeda
    - provider/source/mode: origem do saldo

    Em modo demo, não representa dinheiro real.
    """
    try:
        balance = get_partner_wallet_balance(user_id=current_user.id)
        provider = balance.provider
        mode = balance.mode
        source = "partner" if IS_PARTNER_WALLET else "demo"
        adapter_error = None
    except Exception as exc:
        balance = None
        provider = "not_configured"
        mode = WALLET_MODE
        source = "unavailable"
        adapter_error = str(exc)

    return {
        "ok": True,
        "service": "aurea-wallet",
        "user_id": getattr(current_user, "id", None),
        "balance": {
            "available": _decimal_as_money(getattr(balance, "available", Decimal("0.00"))),
            "blocked": _decimal_as_money(getattr(balance, "blocked", Decimal("0.00"))),
            "pending": _decimal_as_money(getattr(balance, "pending", Decimal("0.00"))),
            "currency": getattr(balance, "currency", "BRL") if balance else "BRL",
        },
        "wallet": {
            "mode": mode,
            "provider": provider,
            "source": source,
            "real_money_enabled": bool(IS_PARTNER_WALLET and balance is not None),
            "adapter_error": adapter_error,
        },
        "notice": (
            "Modo demonstração: saldo não representa dinheiro real."
            if not IS_PARTNER_WALLET
            else "Saldo obtido via parceiro financeiro configurado."
        ),
    }


def _statement_item_payload(item, *, source: str, real_money_enabled: bool) -> dict:
    raw = getattr(item, "raw", {}) or {}
    provider_reference = (
        getattr(item, "provider_reference", None)
        or raw.get("provider_reference")
        or raw.get("id")
        or "not_available"
    )

    created_at = (
        getattr(item, "created_at", None)
        or raw.get("created_at")
        or raw.get("timestamp")
        or raw.get("date")
    )

    return {
        "provider_reference": str(provider_reference),
        "direction": getattr(item, "direction", "credit"),
        "amount": _decimal_as_money(getattr(item, "amount", Decimal("0.00"))),
        "status": getattr(item, "status", "pending"),
        "description": getattr(item, "description", None) or "PIX",
        "created_at": created_at,
        "source": source,
        "real_money_enabled": real_money_enabled,
    }


def _sandbox_statement_items_from_webhooks(
    db: Session,
    *,
    user_id: int,
    limit: int,
) -> list[StatementItem]:
    safe_limit = max(1, min(int(limit or 50), 100))
    rows = (
        db.query(IdempotencyKey)
        .filter(IdempotencyKey.key.like("wallet-sandbox-webhook:%"))
        .order_by(IdempotencyKey.created_at.desc())
        .limit(min(safe_limit * 4, 400))
        .all()
    )

    items: list[StatementItem] = []
    seen_references: set[str] = set()

    for row in rows:
        raw_response = getattr(row, "response_json", None)
        if not raw_response:
            continue

        try:
            response = json.loads(raw_response)
        except (TypeError, ValueError):
            continue

        if response.get("user_id") != user_id:
            continue

        event = response.get("event") or {}
        event_type = str(event.get("event_type") or "").strip()
        status = str(event.get("status") or "").strip().lower()

        if event_type != "pix.payment.confirmed" or status != "confirmed":
            continue

        provider_reference = _safe_receipt_part(
            event.get("provider_reference")
        )
        if (
            provider_reference == "not-provided"
            or provider_reference in seen_references
        ):
            continue

        try:
            amount = Decimal(str(event.get("amount") or "0.00"))
        except Exception:
            continue

        if amount <= Decimal("0.00"):
            continue

        seen_references.add(provider_reference)
        items.append(
            StatementItem(
                provider_reference=provider_reference,
                amount=amount,
                direction="credit",
                status="confirmed",
                description="PIX sandbox confirmado",
                created_at=event.get("received_at"),
                raw={
                    "sandbox": True,
                    "real_money": False,
                    "source": "wallet_sandbox_webhook",
                },
            )
        )

        if len(items) >= safe_limit:
            break

    return items



@router.get("/api/v1/wallet/structured-statement")
def get_wallet_structured_statement(
    limit: int = 50,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """
    Extrato estruturado da wallet.

    Prepara o contrato real de transações:
    - provider_reference
    - direction: credit/debit
    - amount
    - status
    - description
    - created_at
    - source
    - real_money_enabled

    Em modo demo, pode retornar lista vazia e nunca representa dinheiro real.
    """
    safe_limit = max(1, min(int(limit or 50), 100))

    try:
        adapter = get_partner_adapter()
        provider = adapter.provider_name
        statement = list(
            get_partner_wallet_statement(
                user_id=current_user.id,
                limit=safe_limit,
            )
        )

        if provider == "sandbox":
            statement.extend(
                _sandbox_statement_items_from_webhooks(
                    db,
                    user_id=current_user.id,
                    limit=safe_limit,
                )
            )
            statement = statement[:safe_limit]

        mode = WALLET_MODE
        source = (
            "sandbox"
            if provider == "sandbox"
            else ("partner" if IS_PARTNER_WALLET else "demo")
        )
        real_money_enabled = bool(
            IS_PARTNER_WALLET and provider != "sandbox"
        )
        adapter_error = None
    except Exception as exc:
        provider = "not_configured"
        statement = []
        mode = WALLET_MODE
        source = "unavailable"
        real_money_enabled = False
        adapter_error = str(exc)

    items = [
        _statement_item_payload(
            item,
            source=source,
            real_money_enabled=real_money_enabled,
        )
        for item in statement
    ]

    return {
        "ok": True,
        "service": "aurea-wallet",
        "user_id": getattr(current_user, "id", None),
        "statement": {
            "items": items,
            "count": len(items),
            "limit": safe_limit,
            "currency": "BRL",
        },
        "wallet": {
            "mode": mode,
            "provider": provider,
            "source": source,
            "real_money_enabled": real_money_enabled,
            "adapter_error": adapter_error,
        },
        "notice": (
            "Modo demonstração: extrato não representa movimentação financeira real."
            if not IS_PARTNER_WALLET
            else "Extrato obtido via parceiro financeiro configurado."
        ),
    }


def _safe_receipt_part(value: str | None) -> str:
    raw = str(value or "not-provided").strip() or "not-provided"
    safe = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in raw)
    return safe[:80] or "not-provided"


@router.get("/api/v1/wallet/receipt-reconciliation")
def get_wallet_receipt_reconciliation(
    provider_reference: str | None = None,
    current_user: User = Depends(require_customer),
):
    """
    Fundação de comprovante, auditoria e reconciliação da wallet.

    Este endpoint NÃO gera comprovante financeiro real.
    Ele prepara o contrato de rastreabilidade para quando houver:
    - transação real via parceiro;
    - provider_reference real;
    - auditoria;
    - reconciliação;
    - emissão de comprovante confiável.

    Em modo demo, retorna status explícito de demonstração.
    """
    safe_reference = _safe_receipt_part(provider_reference)

    try:
        adapter = get_partner_adapter()
        provider = adapter.provider_name
        adapter_error = None
    except Exception as exc:
        provider = "not_configured"
        adapter_error = str(exc)

    real_money_enabled = bool(IS_PARTNER_WALLET and adapter_error is None)
    source = "partner" if real_money_enabled else "demo"

    if real_money_enabled:
        transaction_status = "provider_pending_lookup"
        audit_status = "pending"
        reconciliation_status = "pending"
        notice = "Fundação de comprovante pronta para consultar transação via parceiro financeiro."
        next_steps = [
            "Consultar transação pelo provider_reference no parceiro.",
            "Validar status financeiro da transação.",
            "Registrar trilha de auditoria.",
            "Conciliar valor, status e identificador do provedor.",
            "Emitir comprovante somente após confirmação do parceiro.",
        ]
    else:
        transaction_status = "demo_only"
        audit_status = "demo_recorded"
        reconciliation_status = "not_applicable_demo"
        notice = "Modo demonstração: comprovante e reconciliação não representam movimentação financeira real."
        next_steps = [
            "Conectar adapter sandbox do parceiro financeiro.",
            "Registrar provider_reference real das transações.",
            "Implementar consulta de status no parceiro.",
            "Implementar trilha de auditoria e reconciliação.",
            "Liberar emissão de comprovante apenas para transações confirmadas.",
        ]

    receipt_id = f"aurea-{source}-receipt-{getattr(current_user, 'id', 'user')}-{safe_reference}"

    return {
        "ok": True,
        "service": "aurea-wallet",
        "user_id": getattr(current_user, "id", None),
        "receipt": {
            "receipt_id": receipt_id,
            "provider_reference": provider_reference or "not_provided",
            "transaction_status": transaction_status,
            "audit_status": audit_status,
            "reconciliation_status": reconciliation_status,
            "issued_at": datetime.now(timezone.utc).isoformat(),
            "currency": "BRL",
        },
        "wallet": {
            "mode": WALLET_MODE,
            "provider": provider,
            "source": source,
            "real_money_enabled": real_money_enabled,
            "adapter_error": adapter_error,
        },
        "notice": notice,
        "next_steps": next_steps,
    }


@router.get("/api/v1/wallet/operational-limits")
def get_wallet_operational_limits(
    current_user: User = Depends(require_customer),
):
    """
    Limites e segurança operacional da wallet.

    Este endpoint prepara o contrato de segurança antes de qualquer PIX real:
    - permissão de envio/recebimento;
    - limite por transação;
    - limite diário;
    - limite mensal;
    - confirmação obrigatória;
    - motivo/limitações;
    - origem e modo da carteira.

    Em modo demo, não permite PIX real.
    """
    try:
        adapter = get_partner_adapter()
        provider = adapter.provider_name
        adapter_ready = True
        adapter_error = None
    except Exception as exc:
        provider = "not_configured"
        adapter_ready = False
        adapter_error = str(exc)

    real_money_enabled = bool(IS_PARTNER_WALLET and adapter_ready)
    source = "partner" if real_money_enabled else "demo"

    if real_money_enabled:
        can_send_pix = True
        can_receive_pix = True
        requires_confirmation = True
        reason = "Carteira em modo parceiro: operações reais dependem dos limites e regras do parceiro financeiro."
        limitations = [
            "Limites finais devem ser confirmados pelo PSP/BaaS.",
            "Toda saída de dinheiro deve exigir confirmação sensível.",
            "Operações podem ser bloqueadas por KYC/KYB, antifraude ou compliance do parceiro.",
        ]
        limits = {
            "per_transaction_limit": "provider_defined",
            "daily_limit": "provider_defined",
            "monthly_limit": "provider_defined",
            "currency": "BRL",
        }
        security = {
            "sensitive_action_confirmation_required": True,
            "kyc_required": True,
            "kyb_required_for_business": True,
            "audit_required": True,
            "reconciliation_required": True,
        }
        next_steps = [
            "Buscar limites reais no parceiro financeiro.",
            "Aplicar confirmação antes de envio de PIX.",
            "Validar KYC/KYB antes de habilitar operações.",
            "Registrar auditoria e idempotência para ações sensíveis.",
        ]
    else:
        can_send_pix = False
        can_receive_pix = False
        requires_confirmation = True
        reason = "Modo demonstração: PIX real depende de parceiro financeiro/PSP/BaaS."
        limitations = [
            "Envio de PIX real desativado em modo demo.",
            "Recebimento de PIX real desativado em modo demo.",
            "Limites financeiros reais ainda dependem de integração com parceiro.",
            "Confirmação sensível já deve ser prevista antes de qualquer operação real.",
        ]
        limits = {
            "per_transaction_limit": "0.00",
            "daily_limit": "0.00",
            "monthly_limit": "0.00",
            "currency": "BRL",
        }
        security = {
            "sensitive_action_confirmation_required": True,
            "kyc_required": True,
            "kyb_required_for_business": True,
            "audit_required": True,
            "reconciliation_required": True,
        }
        next_steps = [
            "Selecionar parceiro financeiro/PSP/BaaS.",
            "Implementar limites sandbox.",
            "Implementar confirmação antes de envio de dinheiro.",
            "Conectar limites ao KYC/KYB.",
            "Bloquear PIX real enquanto real_money_enabled for false.",
        ]

    return {
        "ok": True,
        "service": "aurea-wallet",
        "user_id": getattr(current_user, "id", None),
        "wallet": {
            "mode": WALLET_MODE,
            "provider": provider,
            "source": source,
            "adapter_ready": adapter_ready,
            "adapter_error": adapter_error,
            "real_money_enabled": real_money_enabled,
        },
        "permissions": {
            "can_send_pix": can_send_pix,
            "can_receive_pix": can_receive_pix,
            "requires_confirmation": requires_confirmation,
        },
        "limits": limits,
        "security": security,
        "reason": reason,
        "limitations": limitations,
        "next_steps": next_steps,
    }




def _onboarding_status_payload(current_user: User) -> dict:
    """
    Status de onboarding/KYC/KYB da wallet.

    Esta fundação não aprova cliente, não libera Pix e não movimenta dinheiro.
    Ela prepara o contrato de governança necessário antes de qualquer operação
    real via parceiro financeiro/PSP/BaaS.
    """
    wallet_mode = _wallet_mode_label()

    try:
        adapter = get_partner_adapter()
        provider = adapter.provider_name
        adapter_ready = True
        adapter_error = None
    except Exception as exc:
        provider = "not_configured"
        adapter_ready = False
        adapter_error = str(exc)

    real_money_enabled = bool(IS_PARTNER_WALLET and adapter_ready)

    raw_user_type = (
        getattr(current_user, "type", None)
        or getattr(current_user, "account_type", None)
        or getattr(current_user, "role", None)
        or ""
    )
    normalized_user_type = str(raw_user_type).lower()

    if normalized_user_type in {"pj", "business", "company", "merchant", "juridica", "juridical"}:
        customer_type = "pj"
    elif normalized_user_type in {"pf", "customer", "client", "fisica", "individual"}:
        customer_type = "pf"
    else:
        customer_type = "unknown"

    if real_money_enabled:
        onboarding = {
            "customer_type": customer_type,
            "status": "pending",
            "kyc_status": "pending",
            "kyb_status": "pending" if customer_type in {"pj", "unknown"} else "not_required",
            "required_documents": [
                "Documento de identificação do titular",
                "Comprovante de endereço",
                "Telefone/e-mail verificados",
            ] + (
                [
                    "Contrato social/cartão CNPJ",
                    "Dados dos representantes legais",
                ]
                if customer_type in {"pj", "unknown"}
                else []
            ),
            "missing_fields": [
                "Dados cadastrais validados pelo parceiro financeiro",
                "Documentos aprovados pelo parceiro financeiro",
                "Resultado final de KYC/KYB",
            ],
            "can_start_real_operations": False,
            "can_send_pix": False,
            "can_receive_pix": False,
        }
        reason = "Parceiro financeiro configurado, mas KYC/KYB ainda precisa ser validado antes da operação real."
        limitations = [
            "KYC/KYB depende da análise e aprovação do parceiro financeiro.",
            "Pix real permanece bloqueado até onboarding aprovado.",
            "Limites operacionais só devem ser liberados após validação cadastral.",
        ]
        next_steps = [
            "Criar fluxo de envio/coleta de dados cadastrais.",
            "Conectar adapter sandbox do parceiro financeiro.",
            "Validar retorno de aprovação, pendência ou recusa.",
            "Persistir status de onboarding por cliente.",
        ]
    else:
        onboarding = {
            "customer_type": customer_type,
            "status": "not_started",
            "kyc_status": "not_started",
            "kyb_status": "not_started",
            "required_documents": [],
            "missing_fields": [
                "Parceiro financeiro/PSP/BaaS não configurado.",
                "Fluxo real de KYC/KYB ainda não iniciado.",
            ],
            "can_start_real_operations": False,
            "can_send_pix": False,
            "can_receive_pix": False,
        }
        reason = "Modo demonstração: KYC/KYB real depende de parceiro financeiro homologado."
        limitations = [
            "Modo demonstração não aprova cliente para operação financeira real.",
            "Enviar e receber Pix real continuam desativados.",
            "Aurea Gold ainda depende de parceiro financeiro para KYC/KYB, conta transacional e compliance.",
        ]
        next_steps = [
            "Selecionar parceiro financeiro/PSP/BaaS.",
            "Implementar adapter sandbox.",
            "Criar fluxo de onboarding com KYC/KYB.",
            "Validar aprovação antes de liberar Pix real.",
        ]

    return {
        "ok": True,
        "service": "aurea-wallet",
        "user_id": getattr(current_user, "id", None),
        "wallet": {
            "mode": wallet_mode,
            "provider": provider,
            "source": "partner" if real_money_enabled else "demo",
            "adapter_ready": adapter_ready,
            "adapter_error": adapter_error,
            "real_money_enabled": real_money_enabled,
        },
        "onboarding": onboarding,
        "reason": reason,
        "limitations": limitations,
        "next_steps": next_steps,
    }


@router.get("/api/v1/wallet/onboarding-status")
def get_wallet_onboarding_status(
    current_user: User = Depends(require_customer),
):
    """
    Status estruturado de onboarding/KYC/KYB da wallet.

    Fase 6 da preparação da carteira real:
    deixa explícito se o cliente pode iniciar operação real, enviar Pix
    ou receber Pix. Em modo demo, tudo permanece bloqueado.
    """
    return _onboarding_status_payload(current_user)




class WalletPixSandboxPaymentIn(BaseModel):
    amount: Decimal
    description: str = "PIX sandbox Aurea Gold"
    external_id: str | None = None


@router.post("/api/v1/wallet/pix/sandbox-payment")
def create_wallet_pix_sandbox_payment(
    payload: WalletPixSandboxPaymentIn,
    current_user: User = Depends(require_customer),
):
    """
    Cria cobrança PIX sandbox de entrada.

    Segurança:
    - Não movimenta dinheiro real.
    - Não credita saldo real.
    - Não gera comprovante financeiro real.
    - Só funciona quando o adapter ativo for sandbox.
    """
    amount = Decimal(payload.amount or Decimal("0.00"))

    if amount <= Decimal("0.00"):
        raise HTTPException(
            status_code=422,
            detail="Valor da cobrança sandbox deve ser maior que zero.",
        )

    if amount > Decimal("5000.00"):
        raise HTTPException(
            status_code=422,
            detail="Valor da cobrança sandbox excede o limite técnico de simulação.",
        )

    try:
        adapter = get_partner_adapter()
        provider = adapter.provider_name
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Adapter financeiro indisponível para sandbox: {exc}",
        ) from exc

    if provider != "sandbox":
        raise HTTPException(
            status_code=409,
            detail=(
                "PIX sandbox exige WALLET_MODE=partner e "
                "WALLET_PARTNER_PROVIDER=sandbox. Nenhuma cobrança real foi criada."
            ),
        )

    now = datetime.now(timezone.utc)
    external_id = (
        _safe_receipt_part(payload.external_id)
        if payload.external_id
        else f"sandbox-payment-{getattr(current_user, 'id', 'user')}-{int(now.timestamp())}"
    )

    payment = create_partner_pix_payment(
        user_id=getattr(current_user, "id", None),
        amount=amount,
        description=payload.description or "PIX sandbox Aurea Gold",
        external_id=external_id,
    )

    return {
        "ok": True,
        "service": "aurea-wallet",
        "user_id": getattr(current_user, "id", None),
        "payment": {
            "provider": payment.provider,
            "provider_reference": payment.provider_reference,
            "status": payment.status,
            "amount": _decimal_as_money(payment.amount),
            "currency": "BRL",
            "description": payload.description or "PIX sandbox Aurea Gold",
            "qr_code": payment.qr_code,
            "copy_paste": payment.copy_paste,
            "created_at": now.isoformat(),
        },
        "wallet": {
            "mode": WALLET_MODE,
            "provider": provider,
            "source": "sandbox",
            "real_money_enabled": False,
        },
        "can_credit_balance": False,
        "can_generate_real_receipt": False,
        "notice": "Cobrança PIX sandbox criada apenas para simulação técnica. Não representa pagamento real.",
        "limitations": [
            "Não movimenta dinheiro real.",
            "Não altera saldo real da carteira.",
            "Não gera comprovante financeiro real.",
            "Não dispensa homologação com parceiro financeiro/PSP/BaaS.",
        ],
        "next_steps": [
            "Implementar webhook sandbox.",
            "Validar idempotência da cobrança.",
            "Simular confirmação sem creditar saldo real.",
            "Preparar reconciliação sandbox antes de qualquer Pix real.",
        ],
    }




_SANDBOX_WEBHOOK_ALLOWED_STATUSES = {
    "pending",
    "processing",
    "confirmed",
    "failed",
    "canceled",
    "rejected",
}


class WalletPixSandboxWebhookIn(BaseModel):
    provider_reference: str
    event_type: str = "pix.payment.confirmed"
    status: str = "confirmed"
    amount: Decimal | None = None
    idempotency_key: str | None = None
    raw: dict | None = None


def _sandbox_webhook_hash(payload: WalletPixSandboxWebhookIn) -> str:
    body = {
        "provider_reference": str(payload.provider_reference or "").strip(),
        "event_type": str(payload.event_type or "").strip(),
        "status": str(payload.status or "").strip().lower(),
        "amount": str(payload.amount) if payload.amount is not None else None,
        "raw": payload.raw or {},
    }
    encoded = json.dumps(body, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _sandbox_webhook_idempotency_key(
    payload: WalletPixSandboxWebhookIn,
    header_key: str | None,
) -> str:
    raw_key = (
        header_key
        or payload.idempotency_key
        or f"{payload.provider_reference}:{payload.event_type}:{payload.status}"
    )
    digest = hashlib.sha256(str(raw_key).encode("utf-8")).hexdigest()
    return f"wallet-sandbox-webhook:{digest}"




_ASAAS_SANDBOX_WEBHOOK_ACCEPTED_EVENTS = {
    "PAYMENT_RECEIVED",
}


def _asaas_sandbox_webhook_config():
    try:
        return load_asaas_sandbox_config()
    except AsaasConfigError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Configuração Asaas Sandbox inválida para webhook: {exc}",
        ) from exc


def _validate_asaas_sandbox_webhook_token(
    header_value: str | None,
    expected_token: str,
) -> None:
    received_token = str(header_value or "").strip()

    if not received_token:
        raise HTTPException(
            status_code=401,
            detail="Header asaas-access-token é obrigatório.",
        )

    if not hmac.compare_digest(received_token, expected_token):
        raise HTTPException(
            status_code=403,
            detail="Header asaas-access-token inválido.",
        )


def _asaas_sandbox_webhook_event_id(payload: dict) -> str:
    event_id = str(
        payload.get("id")
        or payload.get("eventId")
        or payload.get("event_id")
        or ""
    ).strip()

    if not event_id:
        raise HTTPException(
            status_code=422,
            detail="Identificador único do evento Asaas é obrigatório.",
        )

    return event_id


def _asaas_sandbox_webhook_event_type(payload: dict) -> str:
    event_type = str(payload.get("event") or payload.get("event_type") or "").strip()

    if not event_type:
        raise HTTPException(
            status_code=422,
            detail="Tipo do evento Asaas é obrigatório.",
        )

    return event_type


def _asaas_sandbox_webhook_hash(payload: dict) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _asaas_sandbox_webhook_idempotency_key(event_id: str) -> str:
    digest = hashlib.sha256(event_id.encode("utf-8")).hexdigest()
    return f"asaas-sandbox-webhook:{digest}"


@router.post("/api/v1/partners")
@router.post("/api/v1/partners/")
@router.post("/api/v1/partners/asaas/webhooks/sandbox")
def handle_asaas_sandbox_webhook_receiver(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    asaas_access_token: str | None = Header(default=None, alias="asaas-access-token"),
):
    """
    Recebe webhooks reais do Asaas Sandbox com token e idempotência.

    Segurança:
    - Valida header asaas-access-token.
    - Usa ASAAS_WEBHOOK_TOKEN fora do Git.
    - Exige identificador único do evento para idempotência.
    - Não exige login do cliente.
    - Não salva payload bruto.
    - Não expõe token nem payment_id.
    - Não credita saldo real.
    - Não gera comprovante real.
    - Não marca pagamento como real.
    """
    if not isinstance(payload, dict):
        raise HTTPException(status_code=422, detail="Payload Asaas inválido.")

    config = _asaas_sandbox_webhook_config()
    _validate_asaas_sandbox_webhook_token(
        asaas_access_token,
        config.webhook_token,
    )
    provider = "asaas"

    event_id = _asaas_sandbox_webhook_event_id(payload)
    event_type = _asaas_sandbox_webhook_event_type(payload)
    request_hash = _asaas_sandbox_webhook_hash(payload)
    idem_key = _asaas_sandbox_webhook_idempotency_key(event_id)

    try:
        record = IdempotencyKey(key=idem_key, request_hash=request_hash)
        db.add(record)
        db.flush()
    except IntegrityError:
        db.rollback()
        existing = db.query(IdempotencyKey).filter_by(key=idem_key).first()
        if not existing:
            raise

        if getattr(existing, "request_hash", None) and existing.request_hash != request_hash:
            raise HTTPException(
                status_code=409,
                detail="Evento Asaas reutilizado com payload diferente.",
            )

        if existing.response_json:
            response = json.loads(existing.response_json)
            response["duplicated"] = True
            response.setdefault("idempotency", {})["replayed"] = True
            response["idempotency"]["state"] = "replayed"
            response["idempotency"]["replay_audit_status"] = (
                "asaas_sandbox_webhook_idempotent_replay"
            )

            audit = response.setdefault("audit", {})
            audit["replay"] = {
                "replay_status": "asaas_sandbox_webhook_idempotent_replay",
                "safe_replay": True,
                "duplicated": True,
                "idempotency_replayed": True,
                "raw_payload_stored": False,
                "raw_event_id_stored": False,
                "raw_payment_id_stored": False,
                "can_credit_balance": False,
                "can_generate_real_receipt": False,
                "can_mark_real_paid": False,
                "notice": (
                    "Evento Asaas Sandbox repetido reconhecido por idempotência. "
                    "Nenhum saldo real, comprovante real ou pagamento real foi gerado."
                ),
            }

            response["can_credit_balance"] = False
            response["can_generate_real_receipt"] = False
            response["can_mark_real_paid"] = False
            return response

        raise HTTPException(
            status_code=503,
            detail=(
                "Evento Asaas Sandbox aguardando conclusão "
                "do processamento anterior."
            ),
            headers={"Retry-After": "30"},
        )


    accepted = event_type in _ASAAS_SANDBOX_WEBHOOK_ACCEPTED_EVENTS
    payment_payload = payload.get("payment") if isinstance(payload.get("payment"), dict) else {}
    now = datetime.now(timezone.utc)

    audit_record = {
        "provider": "asaas",
        "environment": "sandbox",
        "source": "asaas_sandbox_webhook_receiver",
        "audit_status": (
            "asaas_sandbox_webhook_recorded"
            if accepted
            else "asaas_sandbox_webhook_ignored_recorded"
        ),
        "event_type": event_type,
        "event_accepted": accepted,
        "event_id_present": True,
        "payment_object_present": bool(payment_payload),
        "payment_id_present": bool(payment_payload.get("id")),
        "payment_status": payment_payload.get("status"),
        "billing_type": payment_payload.get("billingType"),
        "received_at": now.isoformat(),
        "storage": {
            "source": "idempotency_keys",
            "raw_payload_stored": False,
            "raw_event_id_stored": False,
            "raw_payment_id_stored": False,
            "response_json_stored": True,
        },
        "idempotency": {
            "key": idem_key,
            "request_hash": request_hash,
            "state": "stored",
        },
        "real_money_enabled": False,
        "can_credit_balance": False,
        "can_generate_real_receipt": False,
        "can_mark_real_paid": False,
    }

    response = {
        "ok": True,
        "service": "aurea-wallet",
        "duplicated": False,
        "event": {
            "provider": "asaas",
            "environment": "sandbox",
            "event_id_present": True,
            "event_type": event_type,
            "accepted": accepted,
            "ignored": not accepted,
            "received_at": now.isoformat(),
        },
        "payment": {
            "object_present": bool(payment_payload),
            "payment_id_present": bool(payment_payload.get("id")),
            "status": payment_payload.get("status"),
            "billing_type": payment_payload.get("billingType"),
        },
        "wallet": {
            "mode": WALLET_MODE,
            "provider": provider,
            "source": "asaas_sandbox",
            "real_money_enabled": False,
        },
        "audit": audit_record,
        "idempotency": {
            "key": idem_key,
            "request_hash": request_hash,
            "replayed": False,
            "state": "stored",
        },
        "can_credit_balance": False,
        "can_generate_real_receipt": False,
        "can_mark_real_paid": False,
        "notice": (
            "Webhook Asaas Sandbox recebido com segurança. "
            "Nenhum saldo real, comprovante real ou pagamento real foi gerado."
        ),
        "limitations": [
            "Não credita saldo real.",
            "Não gera comprovante financeiro real.",
            "Não marca pagamento real como confirmado.",
            "Não expõe token.",
            "Não expõe payment_id.",
            "Não salva payload bruto.",
        ],
    }

    record.status_code = 200
    record.response_json = json.dumps(
        response,
        ensure_ascii=False,
        default=str,
    )

    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail="Webhook Asaas Sandbox temporariamente indisponível.",
            headers={"Retry-After": "30"},
        ) from None

    return response



@router.post("/api/v1/wallet/pix/sandbox-webhook")
def handle_wallet_pix_sandbox_webhook(
    payload: WalletPixSandboxWebhookIn,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
    x_idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    """
    Recebe evento PIX sandbox com idempotência.

    Segurança:
    - Só funciona com provider sandbox.
    - Bloqueia replay por Idempotency-Key.
    - Não credita saldo real.
    - Não gera comprovante financeiro real.
    - Não marca pagamento real como confirmado.
    """
    provider_reference = str(payload.provider_reference or "").strip()
    event_type = str(payload.event_type or "").strip()
    status = str(payload.status or "").strip().lower()

    if not provider_reference:
        raise HTTPException(status_code=422, detail="provider_reference é obrigatório.")

    if not event_type:
        raise HTTPException(status_code=422, detail="event_type é obrigatório.")

    if status not in _SANDBOX_WEBHOOK_ALLOWED_STATUSES:
        raise HTTPException(
            status_code=422,
            detail="status sandbox inválido.",
        )

    try:
        adapter = get_partner_adapter()
        provider = adapter.provider_name
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Adapter financeiro indisponível para webhook sandbox: {exc}",
        ) from exc

    if provider != "sandbox":
        raise HTTPException(
            status_code=409,
            detail=(
                "Webhook sandbox exige WALLET_MODE=partner e "
                "WALLET_PARTNER_PROVIDER=sandbox. Nenhum evento real foi processado."
            ),
        )

    request_hash = _sandbox_webhook_hash(payload)
    idem_key = _sandbox_webhook_idempotency_key(payload, x_idempotency_key)

    try:
        record = IdempotencyKey(key=idem_key, request_hash=request_hash)
        db.add(record)
        db.flush()
    except IntegrityError:
        db.rollback()
        existing = db.query(IdempotencyKey).filter_by(key=idem_key).first()
        if not existing:
            raise

        if getattr(existing, "request_hash", None) and existing.request_hash != request_hash:
            raise HTTPException(
                status_code=409,
                detail="Idempotency-Key reutilizada com payload diferente.",
            )

        if existing.response_json:
            response = json.loads(existing.response_json)
            response["duplicated"] = True
            response["idempotency"]["replayed"] = True
            return response

        return {
            "ok": True,
            "service": "aurea-wallet",
            "duplicated": True,
            "event": {
                "provider": "sandbox",
                "provider_reference": provider_reference,
                "event_type": event_type,
                "status": "in_progress",
            },
            "wallet": {
                "mode": WALLET_MODE,
                "provider": provider,
                "source": "sandbox",
                "real_money_enabled": False,
            },
            "idempotency": {
                "key": idem_key,
                "request_hash": request_hash,
                "replayed": True,
                "state": "in_progress",
            },
            "can_credit_balance": False,
            "can_generate_real_receipt": False,
            "can_mark_real_paid": False,
            "notice": "Evento sandbox já está em processamento. Nenhum dinheiro real foi movimentado.",
        }

    webhook_result = handle_partner_wallet_webhook(
        PartnerWebhookEvent(
            provider="sandbox",
            event_type=event_type,
            provider_reference=provider_reference,
            status=status,
            raw=payload.raw or {},
        )
    )

    now = datetime.now(timezone.utc)
    response = {
        "ok": True,
        "service": "aurea-wallet",
        "user_id": getattr(current_user, "id", None),
        "duplicated": False,
        "event": {
            "provider": "sandbox",
            "provider_reference": provider_reference,
            "event_type": event_type,
            "status": status,
            "amount": _decimal_as_money(payload.amount) if payload.amount is not None else None,
            "received_at": now.isoformat(),
        },
        "wallet": {
            "mode": WALLET_MODE,
            "provider": provider,
            "source": "sandbox",
            "real_money_enabled": False,
        },
        "webhook": webhook_result,
        "idempotency": {
            "key": idem_key,
            "request_hash": request_hash,
            "replayed": False,
            "state": "stored",
        },
        "can_credit_balance": False,
        "can_generate_real_receipt": False,
        "can_mark_real_paid": False,
        "notice": "Webhook PIX sandbox processado apenas para simulação técnica. Não movimenta dinheiro real.",
        "limitations": [
            "Não credita saldo real.",
            "Não confirma pagamento real.",
            "Não gera comprovante financeiro real.",
            "Não substitui webhook assinado de parceiro financeiro homologado.",
        ],
        "next_steps": [
            "Persistir eventos sandbox em ledger/auditoria própria.",
            "Implementar reconciliação sandbox por provider_reference.",
            "Validar assinatura/token de webhook antes de integração real.",
            "Liberar crédito real somente via parceiro financeiro homologado.",
        ],
    }

    record.status_code = 200
    record.response_json = json.dumps(response, ensure_ascii=False, default=str)
    db.commit()

    return response




def _find_sandbox_webhook_event_by_reference(
    db: Session,
    provider_reference: str,
) -> dict | None:
    """
    Busca evento sandbox registrado pela idempotência.

    Fase 10: fundação de reconciliação sem nova tabela.
    Não consulta PSP real, não credita saldo e não emite comprovante real.
    """
    rows = (
        db.query(IdempotencyKey)
        .filter(IdempotencyKey.key.like("wallet-sandbox-webhook:%"))
        .order_by(IdempotencyKey.created_at.desc())
        .limit(250)
        .all()
    )

    for row in rows:
        raw_response = getattr(row, "response_json", None)
        if not raw_response:
            continue

        try:
            response = json.loads(raw_response)
        except Exception:
            continue

        event = response.get("event") or {}
        if str(event.get("provider_reference") or "").strip() == provider_reference:
            return {
                "idempotency_key": row.key,
                "request_hash": row.request_hash,
                "status_code": row.status_code,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "response": response,
            }

    return None


@router.get("/api/v1/wallet/pix/sandbox-reconciliation/{provider_reference}")
def get_wallet_pix_sandbox_reconciliation(
    provider_reference: str,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """
    Consulta reconciliação sandbox por provider_reference.

    Segurança:
    - Não consulta transação real.
    - Não credita saldo real.
    - Não gera comprovante financeiro real.
    - Não marca pagamento real como confirmado.
    - Usa somente eventos sandbox já registrados por webhook/idempotência.
    """
    safe_reference = _safe_receipt_part(provider_reference)

    if not safe_reference or safe_reference == "not-provided":
        raise HTTPException(status_code=422, detail="provider_reference é obrigatório.")

    try:
        adapter = get_partner_adapter()
        provider = adapter.provider_name
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Adapter financeiro indisponível para reconciliação sandbox: {exc}",
        ) from exc

    if provider != "sandbox":
        raise HTTPException(
            status_code=409,
            detail=(
                "Reconciliação sandbox exige WALLET_MODE=partner e "
                "WALLET_PARTNER_PROVIDER=sandbox. Nenhuma transação real foi consultada."
            ),
        )

    match = _find_sandbox_webhook_event_by_reference(db, safe_reference)

    if not match:
        return {
            "ok": True,
            "service": "aurea-wallet",
            "user_id": getattr(current_user, "id", None),
            "reconciliation": {
                "provider": "sandbox",
                "provider_reference": safe_reference,
                "status": "not_found",
                "event_found": False,
                "audit_status": "not_found",
                "reconciliation_status": "pending_webhook",
                "amount": None,
                "received_at": None,
            },
            "wallet": {
                "mode": WALLET_MODE,
                "provider": provider,
                "source": "sandbox",
                "real_money_enabled": False,
            },
            "can_credit_balance": False,
            "can_generate_real_receipt": False,
            "can_mark_real_paid": False,
            "notice": "Nenhum webhook sandbox encontrado para esta referência. Nenhum dinheiro real foi movimentado.",
            "next_steps": [
                "Receber webhook sandbox para esta provider_reference.",
                "Validar idempotência do evento.",
                "Registrar auditoria/reconciliação sandbox.",
                "Só liberar reconciliação real após parceiro financeiro homologado.",
            ],
        }

    response = match["response"]
    event = response.get("event") or {}
    webhook = response.get("webhook") or {}
    event_status = str(event.get("status") or "unknown")

    return {
        "ok": True,
        "service": "aurea-wallet",
        "user_id": getattr(current_user, "id", None),
        "reconciliation": {
            "provider": "sandbox",
            "provider_reference": safe_reference,
            "status": event_status,
            "event_found": True,
            "audit_status": "sandbox_event_recorded",
            "reconciliation_status": "sandbox_reconciled",
            "amount": event.get("amount"),
            "received_at": event.get("received_at"),
            "event_type": event.get("event_type"),
        },
        "wallet": {
            "mode": WALLET_MODE,
            "provider": provider,
            "source": "sandbox",
            "real_money_enabled": False,
        },
        "webhook": webhook,
        "idempotency": {
            "key": match["idempotency_key"],
            "request_hash": match["request_hash"],
            "status_code": match["status_code"],
            "stored_at": match["created_at"],
        },
        "can_credit_balance": False,
        "can_generate_real_receipt": False,
        "can_mark_real_paid": False,
        "notice": "Reconciliação sandbox localizada. Este status não representa liquidação financeira real.",
        "limitations": [
            "Não credita saldo real.",
            "Não confirma pagamento real em parceiro financeiro.",
            "Não gera comprovante financeiro real.",
            "Não substitui reconciliação oficial de PSP/BaaS homologado.",
        ],
        "next_steps": [
            "Persistir eventos sandbox em tabela própria de auditoria em fase futura.",
            "Implementar consulta real no parceiro financeiro homologado.",
            "Conciliar valor, status, horário e referência do provedor.",
            "Emitir comprovante real somente após confirmação oficial do parceiro.",
        ],
    }




def _list_sandbox_webhook_events(
    db: Session,
    limit: int = 20,
) -> list[dict]:
    """
    Lista eventos sandbox registrados pela idempotência.

    Fase 12: histórico/auditoria sandbox sem nova tabela.
    Não consulta PSP real, não credita saldo e não emite comprovante real.
    """
    safe_limit = max(1, min(int(limit or 20), 100))

    rows = (
        db.query(IdempotencyKey)
        .filter(IdempotencyKey.key.like("wallet-sandbox-webhook:%"))
        .order_by(IdempotencyKey.created_at.desc())
        .limit(safe_limit)
        .all()
    )

    items: list[dict] = []

    for row in rows:
        raw_response = getattr(row, "response_json", None)
        if not raw_response:
            continue

        try:
            response = json.loads(raw_response)
        except Exception:
            continue

        event = response.get("event") or {}
        wallet_payload = response.get("wallet") or {}

        provider_reference = str(event.get("provider_reference") or "").strip()
        if not provider_reference:
            continue

        items.append({
            "provider": "sandbox",
            "provider_reference": provider_reference,
            "event_type": event.get("event_type"),
            "status": event.get("status") or "unknown",
            "amount": event.get("amount"),
            "received_at": event.get("received_at"),
            "audit_status": "sandbox_event_recorded",
            "reconciliation_status": "sandbox_reconciled",
            "real_money_enabled": bool(wallet_payload.get("real_money_enabled", False)),
            "idempotency": {
                "key": row.key,
                "request_hash": row.request_hash,
                "status_code": row.status_code,
                "stored_at": row.created_at.isoformat() if row.created_at else None,
            },
            "can_credit_balance": False,
            "can_generate_real_receipt": False,
            "can_mark_real_paid": False,
        })

    return items


@router.get("/api/v1/wallet/pix/sandbox-audit-history")
def get_wallet_pix_sandbox_audit_history(
    limit: int = 20,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """
    Lista histórico/auditoria de eventos PIX sandbox.

    Segurança:
    - Não consulta transação real.
    - Não credita saldo real.
    - Não gera comprovante financeiro real.
    - Não marca pagamento real como confirmado.
    - Usa somente eventos sandbox já registrados por webhook/idempotência.
    """
    try:
        adapter = get_partner_adapter()
        provider = adapter.provider_name
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Adapter financeiro indisponível para histórico sandbox: {exc}",
        ) from exc

    if provider != "sandbox":
        raise HTTPException(
            status_code=409,
            detail=(
                "Histórico sandbox exige WALLET_MODE=partner e "
                "WALLET_PARTNER_PROVIDER=sandbox. Nenhuma transação real foi consultada."
            ),
        )

    safe_limit = max(1, min(int(limit or 20), 100))
    items = _list_sandbox_webhook_events(db, safe_limit)

    return {
        "ok": True,
        "service": "aurea-wallet",
        "user_id": getattr(current_user, "id", None),
        "history": {
            "provider": "sandbox",
            "source": "idempotency_keys",
            "limit": safe_limit,
            "total_returned": len(items),
            "audit_status": "sandbox_events_listed",
        },
        "wallet": {
            "mode": WALLET_MODE,
            "provider": provider,
            "source": "sandbox",
            "real_money_enabled": False,
        },
        "items": items,
        "can_credit_balance": False,
        "can_generate_real_receipt": False,
        "can_mark_real_paid": False,
        "notice": "Histórico sandbox listado apenas para auditoria técnica. Não representa movimentação financeira real.",
        "limitations": [
            "Não credita saldo real.",
            "Não confirma pagamento real em parceiro financeiro.",
            "Não gera comprovante financeiro real.",
            "Não substitui histórico oficial de PSP/BaaS homologado.",
        ],
        "next_steps": [
            "Exibir últimos eventos sandbox no painel Mais.",
            "Persistir eventos em tabela própria de auditoria em fase futura.",
            "Adicionar filtros por status e provider_reference.",
            "Integrar histórico real somente após parceiro financeiro homologado.",
        ],
    }


def _list_asaas_sandbox_webhook_audit_events(
    db: Session,
    limit: int = 20,
) -> list[dict]:
    """
    Lista auditoria segura de webhooks Asaas Sandbox.

    Fase v0.2.74: histórico sem nova tabela.
    Usa somente response_json seguro em IdempotencyKey.
    Não consulta PSP real, não credita saldo e não emite comprovante real.
    """
    safe_limit = max(1, min(int(limit or 20), 100))

    rows = (
        db.query(IdempotencyKey)
        .filter(IdempotencyKey.key.like("asaas-sandbox-webhook:%"))
        .order_by(IdempotencyKey.created_at.desc())
        .limit(safe_limit)
        .all()
    )

    items: list[dict] = []

    for row in rows:
        raw_response = getattr(row, "response_json", None)
        if not raw_response:
            continue

        try:
            response = json.loads(raw_response)
        except Exception:
            continue

        audit = response.get("audit") or {}
        event = response.get("event") or {}
        payment = response.get("payment") or {}
        wallet_payload = response.get("wallet") or {}

        if audit.get("provider") != "asaas":
            continue

        if audit.get("environment") != "sandbox":
            continue

        items.append({
            "provider": "asaas",
            "environment": "sandbox",
            "source": audit.get("source") or "asaas_sandbox_webhook_receiver",
            "event_type": audit.get("event_type") or event.get("event_type"),
            "event_accepted": bool(audit.get("event_accepted", False)),
            "payment_object_present": bool(
                audit.get("payment_object_present", payment.get("object_present", False))
            ),
            "payment_id_present": bool(
                audit.get("payment_id_present", payment.get("payment_id_present", False))
            ),
            "payment_status": audit.get("payment_status") or payment.get("status"),
            "billing_type": audit.get("billing_type") or payment.get("billing_type"),
            "received_at": audit.get("received_at") or event.get("received_at"),
            "audit_status": audit.get("audit_status") or "asaas_sandbox_webhook_recorded",
            "real_money_enabled": bool(
                audit.get(
                    "real_money_enabled",
                    wallet_payload.get("real_money_enabled", False),
                )
            ),
            "storage": {
                "source": "idempotency_keys",
                "raw_payload_stored": False,
                "raw_event_id_stored": False,
                "raw_payment_id_stored": False,
                "response_json_stored": True,
            },
            "idempotency": {
                "key": row.key,
                "request_hash": row.request_hash,
                "status_code": row.status_code,
                "stored_at": row.created_at.isoformat() if row.created_at else None,
            },
            "can_credit_balance": False,
            "can_generate_real_receipt": False,
            "can_mark_real_paid": False,
        })

    return items


@router.get("/api/v1/partners/asaas/webhooks/sandbox/audit-history")
def get_asaas_sandbox_webhook_audit_history(
    limit: int = 20,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """
    Lista histórico/auditoria segura de webhooks Asaas Sandbox.

    Segurança:
    - Não consulta transação real no Asaas.
    - Não credita saldo real.
    - Não gera comprovante financeiro real.
    - Não marca pagamento real como confirmado.
    - Não expõe token, event_id bruto nem payment_id bruto.
    - Usa somente registros seguros já salvos por idempotência.
    """
    config = _asaas_sandbox_webhook_config()
    safe_limit = max(1, min(int(limit or 20), 100))
    items = _list_asaas_sandbox_webhook_audit_events(db, safe_limit)

    return {
        "ok": True,
        "service": "aurea-wallet",
        "user_id": getattr(current_user, "id", None),
        "history": {
            "provider": "asaas",
            "environment": config.env,
            "source": "idempotency_keys",
            "limit": safe_limit,
            "total_returned": len(items),
            "audit_status": "asaas_sandbox_webhooks_listed",
        },
        "wallet": {
            "mode": WALLET_MODE,
            "provider": "asaas",
            "source": "asaas_sandbox",
            "real_money_enabled": False,
        },
        "items": items,
        "can_credit_balance": False,
        "can_generate_real_receipt": False,
        "can_mark_real_paid": False,
        "notice": "Histórico Asaas Sandbox listado apenas para auditoria técnica. Não representa movimentação financeira real.",
        "limitations": [
            "Não credita saldo real.",
            "Não confirma pagamento real em parceiro financeiro.",
            "Não gera comprovante financeiro real.",
            "Não expõe token.",
            "Não expõe event_id bruto.",
            "Não expõe payment_id bruto.",
            "Não salva payload bruto.",
        ],
        "next_steps": [
            "Exibir últimos webhooks Asaas Sandbox no painel técnico.",
            "Adicionar filtros por event_type e audit_status em fase futura.",
            "Persistir eventos em tabela própria de auditoria em fase futura.",
            "Integrar histórico real somente após parceiro financeiro homologado.",
        ],
    }


@router.get("/api/v1/wallet/balance")
def get_balance(current_user: User = Depends(require_customer),
                db: Session = Depends(get_db)):
    """
    Calcula saldo do usuário = soma(credit) - soma(debit)
    """
    rows = (
        db.query(Transaction)
        .filter(Transaction.user_id == current_user.id)
        .all()
    )

    saldo = Decimal("0.00")
    for tx in rows:
        if tx.kind == "credit":
            saldo += Decimal(tx.amount)
        elif tx.kind == "debit":
            saldo -= Decimal(tx.amount)

    return {
        "user_id": current_user.id,
        "balance": f"{saldo:.2f}"
    }

@router.get("/api/v1/wallet/history")
def get_history(current_user: User = Depends(require_customer),
                db: Session = Depends(get_db)):
    """
    Retorna lista das últimas transações do usuário autenticado.
    """
    rows = (
        db.query(Transaction)
        .filter(Transaction.user_id == current_user.id)
        .order_by(Transaction.created_at.desc())
        .limit(20)
        .all()
    )

    history = []
    for tx in rows:
        history.append({
            "id": tx.id,
            "kind": tx.kind,
            "description": tx.description,
            "amount": str(tx.amount),
            "created_at": tx.created_at.isoformat(),
        })

    return {
        "user_id": current_user.id,
        "history": history
    }

@router.get("/api/v1/wallet/partner/status")
def get_wallet_partner_status():
    """
    Status técnico da camada de parceiro financeiro.

    Não movimenta dinheiro.
    Serve para QA, diagnóstico, apresentação técnica e validação
    de modo demo/partner.
    """
    adapter = get_partner_adapter()

    return {
        "ok": True,
        "service": "aurea-wallet",
        "wallet_mode": WALLET_MODE,
        "provider": adapter.provider_name,
        "real_money": bool(IS_PARTNER_WALLET),
    }

