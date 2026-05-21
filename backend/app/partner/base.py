from __future__ import annotations

from abc import ABC, abstractmethod

from app.partner.types import (
    PartnerBalance,
    PartnerWebhookEvent,
    PixPaymentRequest,
    PixPaymentResponse,
    PixSendRequest,
    PixSendResponse,
    StatementItem,
)


class PartnerAdapter(ABC):
    """
    Contrato interno da Aurea Gold para PSP/BaaS/parceiro financeiro.

    Regra:
    - Rotas da Aurea não devem depender diretamente de fornecedor específico.
    - Integrações reais futuras devem implementar este contrato.
    - Modo demo/lab fica isolado do modo partner real.
    """

    provider_name: str

    @abstractmethod
    def get_balance(self, *, user_id: int) -> PartnerBalance:
        raise NotImplementedError

    @abstractmethod
    def create_pix_payment(self, request: PixPaymentRequest) -> PixPaymentResponse:
        raise NotImplementedError

    @abstractmethod
    def send_pix(self, request: PixSendRequest) -> PixSendResponse:
        raise NotImplementedError

    @abstractmethod
    def get_statement(self, *, user_id: int, limit: int = 50) -> list[StatementItem]:
        raise NotImplementedError

    @abstractmethod
    def handle_webhook(self, event: PartnerWebhookEvent) -> dict:
        raise NotImplementedError
