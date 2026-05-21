from __future__ import annotations

from decimal import Decimal

from app.partner import (
    PartnerBalance,
    PartnerWebhookEvent,
    PixPaymentRequest,
    PixPaymentResponse,
    PixSendRequest,
    PixSendResponse,
    StatementItem,
    get_partner_adapter,
)


def get_wallet_balance(*, user_id: int) -> PartnerBalance:
    adapter = get_partner_adapter()
    return adapter.get_balance(user_id=user_id)


def create_wallet_pix_payment(
    *,
    user_id: int,
    amount: Decimal,
    description: str = "PIX",
    external_id: str | None = None,
) -> PixPaymentResponse:
    adapter = get_partner_adapter()
    return adapter.create_pix_payment(
        PixPaymentRequest(
            user_id=user_id,
            amount=Decimal(amount),
            description=description,
            external_id=external_id,
        )
    )


def send_wallet_pix(
    *,
    user_id: int,
    amount: Decimal,
    pix_key: str,
    description: str = "PIX",
    idempotency_key: str | None = None,
) -> PixSendResponse:
    adapter = get_partner_adapter()
    return adapter.send_pix(
        PixSendRequest(
            user_id=user_id,
            amount=Decimal(amount),
            pix_key=pix_key,
            description=description,
            idempotency_key=idempotency_key,
        )
    )


def get_wallet_statement(*, user_id: int, limit: int = 50) -> list[StatementItem]:
    adapter = get_partner_adapter()
    return adapter.get_statement(user_id=user_id, limit=limit)


def handle_wallet_webhook(event: PartnerWebhookEvent) -> dict:
    adapter = get_partner_adapter()
    return adapter.handle_webhook(event)
