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


class DemoPartnerAdapter(PartnerAdapter):
    """
    Adapter demo/lab.

    Não movimenta dinheiro real.
    Serve para desenvolvimento, QA, apresentação e separação segura
    entre fluxo simulado e fluxo financeiro real via parceiro.
    """

    provider_name = "demo"

    def get_balance(self, *, user_id: int) -> PartnerBalance:
        return PartnerBalance(
            user_id=user_id,
            available=Decimal("0.00"),
            provider=self.provider_name,
            mode="demo",
            raw={"notice": "demo adapter does not represent real funds"},
        )

    def create_pix_payment(self, request: PixPaymentRequest) -> PixPaymentResponse:
        return PixPaymentResponse(
            ok=True,
            status="pending",
            amount=request.amount,
            provider=self.provider_name,
            provider_reference=request.external_id or "demo-pix-payment",
            qr_code="DEMO_QR_CODE_NOT_FOR_REAL_PAYMENT",
            copy_paste="DEMO_COPY_PASTE_NOT_FOR_REAL_PAYMENT",
            message="PIX demo criado. Não representa cobrança real.",
        )

    def send_pix(self, request: PixSendRequest) -> PixSendResponse:
        return PixSendResponse(
            ok=True,
            status="confirmed",
            amount=request.amount,
            provider=self.provider_name,
            provider_reference=request.idempotency_key or "demo-pix-send",
            message="PIX demo confirmado. Não movimenta dinheiro real.",
        )

    def get_statement(self, *, user_id: int, limit: int = 50) -> list[StatementItem]:
        return []

    def handle_webhook(self, event: PartnerWebhookEvent) -> dict:
        return {
            "ok": True,
            "provider": self.provider_name,
            "handled": True,
            "mode": "demo",
            "event_type": event.event_type,
        }
