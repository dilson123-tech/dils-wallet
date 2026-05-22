from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime, timezone

from app.database import get_db
from app.utils.authz import require_customer
from app.models.transaction import Transaction
from app.models.user_main import User
from app.config import WALLET_MODE, IS_PARTNER_WALLET
from app.partner import get_partner_adapter
from app.services.wallet_partner_service import (
    get_wallet_balance as get_partner_wallet_balance,
    get_wallet_statement as get_partner_wallet_statement,
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


@router.get("/api/v1/wallet/structured-statement")
def get_wallet_structured_statement(
    limit: int = 50,
    current_user: User = Depends(require_customer),
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
        statement = get_partner_wallet_statement(
            user_id=current_user.id,
            limit=safe_limit,
        )
        mode = WALLET_MODE
        source = "partner" if IS_PARTNER_WALLET else "demo"
        real_money_enabled = bool(IS_PARTNER_WALLET)
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

