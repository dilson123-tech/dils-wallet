from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from decimal import Decimal

from app.database import get_db
from app.utils.authz import require_customer
from app.models.transaction import Transaction
from app.models.user_main import User
from app.config import WALLET_MODE, IS_PARTNER_WALLET
from app.partner import get_partner_adapter

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

