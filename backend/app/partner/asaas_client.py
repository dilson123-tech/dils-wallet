from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Literal

from app.partner.asaas_config import AsaasSandboxConfig, load_asaas_sandbox_config


AsaasHttpMethod = Literal["GET", "POST"]


@dataclass(frozen=True)
class AsaasPreparedRequest:
    method: AsaasHttpMethod
    url: str
    operation: str
    json: dict[str, Any] | None = None
    headers_configured: bool = False
    real_money: bool = False
    http_call_executed: bool = False
    raw: dict[str, Any] = field(default_factory=dict)

    def safe_summary(self) -> dict[str, Any]:
        return {
            "method": self.method,
            "url": self.url,
            "operation": self.operation,
            "json": self.json,
            "headers_configured": self.headers_configured,
            "real_money": self.real_money,
            "http_call_executed": self.http_call_executed,
            "raw": self.raw,
        }


@dataclass(frozen=True)
class AsaasCustomerDryRunResult:
    prepared_request: AsaasPreparedRequest
    customer_reference: str = "dry-run-customer-sandbox"
    real_money: bool = False
    http_call_executed: bool = False

    def safe_summary(self) -> dict[str, Any]:
        return {
            "operation": "customer_dry_run",
            "customer_reference": self.customer_reference,
            "prepared_request": self.prepared_request.safe_summary(),
            "real_money": self.real_money,
            "http_call_executed": self.http_call_executed,
            "ready_for_http_execution": False,
            "next_step_required": "manual_review_before_any_sandbox_http_call",
        }


@dataclass(frozen=True)
class AsaasPaymentDryRunResult:
    prepared_request: AsaasPreparedRequest
    payment_reference: str = "dry-run-pix-payment-sandbox"
    billing_type: str = "PIX"
    real_money: bool = False
    http_call_executed: bool = False

    def safe_summary(self) -> dict[str, Any]:
        return {
            "operation": "payment_dry_run",
            "payment_reference": self.payment_reference,
            "billing_type": self.billing_type,
            "prepared_request": self.prepared_request.safe_summary(),
            "real_money": self.real_money,
            "http_call_executed": self.http_call_executed,
            "ready_for_http_execution": False,
            "next_step_required": "manual_review_before_any_sandbox_http_call",
        }


class AsaasSandboxClient:
    """
    Skeleton client for Asaas Sandbox.

    Safety rule:
    - This milestone prepares request metadata only.
    - It does not perform HTTP calls.
    - It does not create real Pix charges.
    - It does not move real money.
    """

    def __init__(self, config: AsaasSandboxConfig | None = None) -> None:
        self.config = config or load_asaas_sandbox_config()

    @property
    def base_url(self) -> str:
        return self.config.base_url.rstrip("/")

    def _prepare(
        self,
        *,
        method: AsaasHttpMethod,
        path: str,
        operation: str,
        json: dict[str, Any] | None = None,
    ) -> AsaasPreparedRequest:
        normalized_path = "/" + path.lstrip("/")

        return AsaasPreparedRequest(
            method=method,
            url=f"{self.base_url}{normalized_path}",
            operation=operation,
            json=json,
            headers_configured=bool(self.config.api_key),
            real_money=False,
            http_call_executed=False,
            raw={
                "sandbox": True,
                "provider": "asaas",
                "env": self.config.env,
                "http_execution_blocked": True,
            },
        )

    def prepare_create_customer(
        self,
        *,
        name: str,
        cpf_cnpj: str,
        email: str,
        mobile_phone: str,
    ) -> AsaasPreparedRequest:
        payload = {
            "name": name,
            "cpfCnpj": cpf_cnpj,
            "email": email,
            "mobilePhone": mobile_phone,
        }

        return self._prepare(
            method="POST",
            path="/customers",
            operation="create_customer",
            json=payload,
        )

    def dry_run_create_customer(
        self,
        *,
        name: str,
        cpf_cnpj: str,
        email: str,
        mobile_phone: str,
    ) -> AsaasCustomerDryRunResult:
        prepared_request = self.prepare_create_customer(
            name=name,
            cpf_cnpj=cpf_cnpj,
            email=email,
            mobile_phone=mobile_phone,
        )

        return AsaasCustomerDryRunResult(prepared_request=prepared_request)

    def prepare_create_pix_payment(
        self,
        *,
        customer_id: str,
        value: Decimal,
        due_date: str,
        description: str,
    ) -> AsaasPreparedRequest:
        payload = {
            "customer": customer_id,
            "billingType": "PIX",
            "value": float(value),
            "dueDate": due_date,
            "description": description,
        }

        return self._prepare(
            method="POST",
            path="/payments",
            operation="create_pix_payment",
            json=payload,
        )

    def dry_run_create_pix_payment(
        self,
        *,
        customer_id: str,
        value: Decimal,
        due_date: str,
        description: str,
    ) -> AsaasPaymentDryRunResult:
        prepared_request = self.prepare_create_pix_payment(
            customer_id=customer_id,
            value=value,
            due_date=due_date,
            description=description,
        )

        return AsaasPaymentDryRunResult(prepared_request=prepared_request)

    def prepare_get_pix_qr_code(self, *, payment_id: str) -> AsaasPreparedRequest:
        return self._prepare(
            method="GET",
            path=f"/payments/{payment_id}/pixQrCode",
            operation="get_pix_qr_code",
        )

    def prepare_get_payment_status(self, *, payment_id: str) -> AsaasPreparedRequest:
        return self._prepare(
            method="GET",
            path=f"/payments/{payment_id}",
            operation="get_payment_status",
        )

    def execute_prepared_request(self, request: AsaasPreparedRequest) -> None:
        raise RuntimeError(
            "HTTP execution is intentionally blocked in this milestone. "
            f"Operation {request.operation!r} was prepared but not executed."
        )
