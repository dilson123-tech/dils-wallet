from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Literal

from app.partner.asaas_config import (
    ASAAS_SANDBOX_MANUAL_AUTHORIZATION_PHRASE,
    AsaasSandboxConfig,
    load_asaas_sandbox_config,
)


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
class AsaasFirstCustomerHttpClientGateResult:
    prepared_request: AsaasPreparedRequest
    customer_reference: str = "first-customer-http-client-gate-sandbox"
    manual_authorization_registered: bool = False
    http_transport_enabled: bool = False
    real_money: bool = False
    http_call_executed: bool = False

    def safe_summary(self) -> dict[str, Any]:
        return {
            "operation": "first_customer_http_client_gate",
            "customer_reference": self.customer_reference,
            "prepared_request": self.prepared_request.safe_summary(),
            "manual_authorization_registered": self.manual_authorization_registered,
            "http_transport_enabled": self.http_transport_enabled,
            "real_money": self.real_money,
            "http_call_executed": self.http_call_executed,
            "ready_for_http_execution": False,
            "next_step_required": "manual_transport_review_before_explicit_sandbox_execution",
        }


@dataclass(frozen=True)
class AsaasFirstCustomerHttpTransportSkeletonResult:
    prepared_request: AsaasPreparedRequest
    transport_reference: str = "first-customer-http-transport-skeleton-sandbox"
    manual_authorization_registered: bool = False
    access_token_header_configured: bool = False
    timeout_seconds: int = 30
    retry_enabled: bool = False
    http_transport_implemented: bool = False
    http_transport_enabled: bool = False
    real_money: bool = False
    http_call_executed: bool = False

    def safe_summary(self) -> dict[str, Any]:
        return {
            "operation": "first_customer_http_transport_skeleton",
            "transport_reference": self.transport_reference,
            "prepared_request": self.prepared_request.safe_summary(),
            "manual_authorization_registered": self.manual_authorization_registered,
            "access_token_header_configured": self.access_token_header_configured,
            "timeout_seconds": self.timeout_seconds,
            "retry_enabled": self.retry_enabled,
            "http_transport_implemented": self.http_transport_implemented,
            "http_transport_enabled": self.http_transport_enabled,
            "real_money": self.real_money,
            "http_call_executed": self.http_call_executed,
            "ready_for_http_execution": False,
            "next_step_required": "manual_transport_implementation_review",
        }


@dataclass(frozen=True)
class AsaasFirstCustomerHttpTransportAdapterGateResult:
    prepared_request: AsaasPreparedRequest
    adapter_reference: str = "first-customer-http-transport-adapter-gate-sandbox"
    adapter_name: str = "blocked_sandbox_manual_http_adapter"
    manual_authorization_registered: bool = False
    access_token_header_configured: bool = False
    sandbox_only: bool = True
    target_allowed: bool = True
    adapter_implemented: bool = False
    adapter_enabled: bool = False
    can_send_http: bool = False
    retry_enabled: bool = False
    real_money: bool = False
    http_call_executed: bool = False

    def safe_summary(self) -> dict[str, Any]:
        return {
            "operation": "first_customer_http_transport_adapter_gate",
            "adapter_reference": self.adapter_reference,
            "adapter_name": self.adapter_name,
            "prepared_request": self.prepared_request.safe_summary(),
            "manual_authorization_registered": self.manual_authorization_registered,
            "access_token_header_configured": self.access_token_header_configured,
            "sandbox_only": self.sandbox_only,
            "target_allowed": self.target_allowed,
            "adapter_implemented": self.adapter_implemented,
            "adapter_enabled": self.adapter_enabled,
            "can_send_http": self.can_send_http,
            "retry_enabled": self.retry_enabled,
            "real_money": self.real_money,
            "http_call_executed": self.http_call_executed,
            "ready_for_http_execution": False,
            "next_step_required": "manual_blocked_adapter_review_before_any_http_send",
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


@dataclass(frozen=True)
class AsaasPixQrCodeDryRunResult:
    prepared_request: AsaasPreparedRequest
    qr_code_reference: str = "dry-run-pix-qr-code-sandbox"
    real_money: bool = False
    http_call_executed: bool = False

    def safe_summary(self) -> dict[str, Any]:
        return {
            "operation": "pix_qr_code_dry_run",
            "qr_code_reference": self.qr_code_reference,
            "prepared_request": self.prepared_request.safe_summary(),
            "real_money": self.real_money,
            "http_call_executed": self.http_call_executed,
            "ready_for_http_execution": False,
            "next_step_required": "manual_review_before_any_sandbox_http_call",
        }


@dataclass(frozen=True)
class AsaasPaymentStatusDryRunResult:
    prepared_request: AsaasPreparedRequest
    status_reference: str = "dry-run-payment-status-sandbox"
    real_money: bool = False
    http_call_executed: bool = False

    def safe_summary(self) -> dict[str, Any]:
        return {
            "operation": "payment_status_dry_run",
            "status_reference": self.status_reference,
            "prepared_request": self.prepared_request.safe_summary(),
            "real_money": self.real_money,
            "http_call_executed": self.http_call_executed,
            "ready_for_http_execution": False,
            "next_step_required": "manual_review_before_any_sandbox_http_call",
        }


@dataclass(frozen=True)
class AsaasFullDryRunFlowResult:
    customer: AsaasCustomerDryRunResult
    payment: AsaasPaymentDryRunResult
    pix_qr_code: AsaasPixQrCodeDryRunResult
    payment_status: AsaasPaymentStatusDryRunResult
    flow_reference: str = "dry-run-full-pix-flow-sandbox"
    real_money: bool = False
    http_call_executed: bool = False

    def safe_summary(self) -> dict[str, Any]:
        return {
            "operation": "full_pix_flow_dry_run",
            "flow_reference": self.flow_reference,
            "steps": [
                "customer_dry_run",
                "payment_dry_run",
                "pix_qr_code_dry_run",
                "payment_status_dry_run",
            ],
            "customer": self.customer.safe_summary(),
            "payment": self.payment.safe_summary(),
            "pix_qr_code": self.pix_qr_code.safe_summary(),
            "payment_status": self.payment_status.safe_summary(),
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

    def gate_first_customer_http_call(
        self,
        *,
        name: str,
        cpf_cnpj: str,
        email: str,
        mobile_phone: str,
        manual_authorization_phrase: str = "",
    ) -> AsaasFirstCustomerHttpClientGateResult:
        prepared_request = self.prepare_create_customer(
            name=name,
            cpf_cnpj=cpf_cnpj,
            email=email,
            mobile_phone=mobile_phone,
        )
        manual_authorization_registered = (
            manual_authorization_phrase.strip()
            == ASAAS_SANDBOX_MANUAL_AUTHORIZATION_PHRASE
        )

        return AsaasFirstCustomerHttpClientGateResult(
            prepared_request=prepared_request,
            manual_authorization_registered=manual_authorization_registered,
        )

    def build_first_customer_http_transport_skeleton(
        self,
        *,
        name: str,
        cpf_cnpj: str,
        email: str,
        mobile_phone: str,
        manual_authorization_phrase: str = "",
    ) -> AsaasFirstCustomerHttpTransportSkeletonResult:
        prepared_request = self.prepare_create_customer(
            name=name,
            cpf_cnpj=cpf_cnpj,
            email=email,
            mobile_phone=mobile_phone,
        )
        manual_authorization_registered = (
            manual_authorization_phrase.strip()
            == ASAAS_SANDBOX_MANUAL_AUTHORIZATION_PHRASE
        )

        return AsaasFirstCustomerHttpTransportSkeletonResult(
            prepared_request=prepared_request,
            manual_authorization_registered=manual_authorization_registered,
            access_token_header_configured=prepared_request.headers_configured,
        )

    def gate_first_customer_http_transport_adapter(
        self,
        *,
        name: str,
        cpf_cnpj: str,
        email: str,
        mobile_phone: str,
        manual_authorization_phrase: str = "",
    ) -> AsaasFirstCustomerHttpTransportAdapterGateResult:
        prepared_request = self.prepare_create_customer(
            name=name,
            cpf_cnpj=cpf_cnpj,
            email=email,
            mobile_phone=mobile_phone,
        )
        manual_authorization_registered = (
            manual_authorization_phrase.strip()
            == ASAAS_SANDBOX_MANUAL_AUTHORIZATION_PHRASE
        )
        target_allowed = (
            prepared_request.method == "POST"
            and prepared_request.url == f"{self.base_url}/customers"
            and prepared_request.operation == "create_customer"
        )

        return AsaasFirstCustomerHttpTransportAdapterGateResult(
            prepared_request=prepared_request,
            manual_authorization_registered=manual_authorization_registered,
            access_token_header_configured=prepared_request.headers_configured,
            target_allowed=target_allowed,
        )

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

    def dry_run_get_pix_qr_code(
        self,
        *,
        payment_id: str,
    ) -> AsaasPixQrCodeDryRunResult:
        prepared_request = self.prepare_get_pix_qr_code(payment_id=payment_id)

        return AsaasPixQrCodeDryRunResult(prepared_request=prepared_request)

    def prepare_get_payment_status(self, *, payment_id: str) -> AsaasPreparedRequest:
        return self._prepare(
            method="GET",
            path=f"/payments/{payment_id}",
            operation="get_payment_status",
        )

    def dry_run_get_payment_status(
        self,
        *,
        payment_id: str,
    ) -> AsaasPaymentStatusDryRunResult:
        prepared_request = self.prepare_get_payment_status(payment_id=payment_id)

        return AsaasPaymentStatusDryRunResult(prepared_request=prepared_request)

    def dry_run_full_pix_flow(
        self,
        *,
        name: str,
        cpf_cnpj: str,
        email: str,
        mobile_phone: str,
        value: Decimal,
        due_date: str,
        description: str,
        sandbox_customer_id: str = "cus_dry_run_full_flow",
        sandbox_payment_id: str = "pay_dry_run_full_flow",
    ) -> AsaasFullDryRunFlowResult:
        customer = self.dry_run_create_customer(
            name=name,
            cpf_cnpj=cpf_cnpj,
            email=email,
            mobile_phone=mobile_phone,
        )
        payment = self.dry_run_create_pix_payment(
            customer_id=sandbox_customer_id,
            value=value,
            due_date=due_date,
            description=description,
        )
        pix_qr_code = self.dry_run_get_pix_qr_code(payment_id=sandbox_payment_id)
        payment_status = self.dry_run_get_payment_status(payment_id=sandbox_payment_id)

        return AsaasFullDryRunFlowResult(
            customer=customer,
            payment=payment,
            pix_qr_code=pix_qr_code,
            payment_status=payment_status,
        )

    def execute_prepared_request(self, request: AsaasPreparedRequest) -> None:
        raise RuntimeError(
            "HTTP execution is intentionally blocked in this milestone. "
            f"Operation {request.operation!r} was prepared but not executed."
        )
