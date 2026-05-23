from __future__ import annotations

from decimal import Decimal

from app.partner.base import PartnerAdapter
from app.partner.types import (
    PartnerBalance,
    PartnerWebhookEvent,
    PixPaymentRequest,
    PixPaymentResponse,
    PixSendRequest,
    PixSendResponse,
    StatementItem,
)


class SandboxPartnerAdapter(PartnerAdapter):
    """
    Adapter sandbox controlado para simular contrato de PSP/BaaS.

    Regra de segurança:
    - Não movimenta dinheiro real.
    - Não confirma envio real de PIX.
    - Não gera comprovante financeiro real.
    - Serve apenas para QA, contrato técnico e evolução segura da wallet.
    """

    provider_name = "sandbox"

    def get_balance(self, *, user_id: int) -> PartnerBalance:
        return PartnerBalance(
            user_id=user_id,
            available=Decimal("0.00"),
            blocked=Decimal("0.00"),
            pending=Decimal("0.00"),
            currency="BRL",
            provider=self.provider_name,
            mode="partner",
            raw={
                "sandbox": True,
                "real_money": False,
                "notice": "sandbox adapter does not represent real funds",
            },
        )

    def create_pix_payment(self, request: PixPaymentRequest) -> PixPaymentResponse:
        return PixPaymentResponse(
            ok=True,
            status="pending",
            amount=request.amount,
            provider=self.provider_name,
            provider_reference=request.external_id or f"sandbox-pix-payment-{request.user_id}",
            qr_code="SANDBOX_QR_CODE_NOT_FOR_REAL_PAYMENT",
            copy_paste="SANDBOX_COPY_PASTE_NOT_FOR_REAL_PAYMENT",
            message="PIX sandbox criado para simulação técnica. Não representa cobrança real.",
            raw={
                "sandbox": True,
                "real_money": False,
                "operation": "create_pix_payment",
            },
        )

    def send_pix(self, request: PixSendRequest) -> PixSendResponse:
        return PixSendResponse(
            ok=False,
            status="rejected",
            amount=request.amount,
            provider=self.provider_name,
            provider_reference=request.idempotency_key or f"sandbox-pix-send-blocked-{request.user_id}",
            message="Envio de PIX bloqueado no sandbox. Não movimenta dinheiro real.",
            raw={
                "sandbox": True,
                "real_money": False,
                "operation": "send_pix",
                "blocked_reason": "real_pix_disabled_without_homologated_financial_partner",
            },
        )

    def get_statement(self, *, user_id: int, limit: int = 50) -> list[StatementItem]:
        return []

    def handle_webhook(self, event: PartnerWebhookEvent) -> dict:
        return {
            "ok": True,
            "provider": self.provider_name,
            "handled": True,
            "mode": "partner",
            "sandbox": True,
            "real_money": False,
            "event_type": event.event_type,
            "provider_reference": event.provider_reference,
            "status": event.status,
        }
