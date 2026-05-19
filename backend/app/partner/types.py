from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Literal


WalletMode = Literal["demo", "partner"]
PartnerTransactionStatus = Literal[
    "pending",
    "processing",
    "confirmed",
    "failed",
    "canceled",
    "rejected",
]


@dataclass(frozen=True)
class PartnerBalance:
    user_id: int
    available: Decimal
    currency: str = "BRL"
    provider: str = "demo"
    mode: WalletMode = "demo"
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PixPaymentRequest:
    user_id: int
    amount: Decimal
    description: str = "PIX"
    external_id: str | None = None


@dataclass(frozen=True)
class PixPaymentResponse:
    ok: bool
    status: PartnerTransactionStatus
    amount: Decimal
    provider: str
    provider_reference: str | None = None
    qr_code: str | None = None
    copy_paste: str | None = None
    message: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PixSendRequest:
    user_id: int
    amount: Decimal
    pix_key: str
    description: str = "PIX"
    idempotency_key: str | None = None


@dataclass(frozen=True)
class PixSendResponse:
    ok: bool
    status: PartnerTransactionStatus
    amount: Decimal
    provider: str
    provider_reference: str | None = None
    message: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StatementItem:
    provider_reference: str
    amount: Decimal
    direction: Literal["credit", "debit"]
    status: PartnerTransactionStatus
    description: str = "PIX"
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PartnerWebhookEvent:
    provider: str
    event_type: str
    provider_reference: str | None = None
    status: PartnerTransactionStatus | None = None
    raw: dict[str, Any] = field(default_factory=dict)
