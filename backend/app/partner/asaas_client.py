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
class AsaasSandboxSubaccountStructureGuardResult:
    prepared_request: AsaasPreparedRequest
    guard_reference: str = "subaccount-structure-guard-sandbox"
    endpoint_path: str = "/accounts"
    target_operation: str = "create_subaccount"
    sandbox_only: bool = True
    production_blocked: bool = True
    manual_authorization_required: bool = True
    can_create_subaccount: bool = False
    can_send_http: bool = False
    real_money: bool = False
    http_call_executed: bool = False
    sensitive_response_fields: tuple[str, ...] = (
        "apiKey",
        "walletId",
        "id",
        "onboardingUrl",
    )
    sensitive_request_fields: tuple[str, ...] = (
        "cpfCnpj",
        "email",
        "phone",
        "mobilePhone",
        "address",
    )
    future_result_marker: str = "ASAAS_SANDBOX_SUBACCOUNT_STRUCTURE_VALIDATED"

    def safe_summary(self) -> dict[str, Any]:
        return {
            "operation": "subaccount_structure_guard",
            "guard_reference": self.guard_reference,
            "endpoint_path": self.endpoint_path,
            "target_operation": self.target_operation,
            "prepared_request": {
                "method": self.prepared_request.method,
                "url": self.prepared_request.url,
                "operation": self.prepared_request.operation,
                "headers_configured": self.prepared_request.headers_configured,
                "real_money": self.prepared_request.real_money,
                "http_call_executed": self.prepared_request.http_call_executed,
                "json_payload_stored": self.prepared_request.json is not None,
                "raw": self.prepared_request.raw,
            },
            "sandbox_only": self.sandbox_only,
            "production_blocked": self.production_blocked,
            "manual_authorization_required": self.manual_authorization_required,
            "can_create_subaccount": self.can_create_subaccount,
            "can_send_http": self.can_send_http,
            "real_money": self.real_money,
            "http_call_executed": self.http_call_executed,
            "sensitive_response_fields": list(self.sensitive_response_fields),
            "sensitive_request_fields": list(self.sensitive_request_fields),
            "sensitive_response_fields_masked": True,
            "sensitive_request_fields_masked": True,
            "ready_for_http_execution": False,
            "future_result_marker": self.future_result_marker,
            "next_step_required": "manual_subaccount_payload_contract_review",
        }


@dataclass(frozen=True)
class AsaasSandboxSubaccountPayloadContractResult:
    structure_guard: AsaasSandboxSubaccountStructureGuardResult
    contract_reference: str = "subaccount-payload-contract-sandbox"
    endpoint_path: str = "/accounts"
    method: str = "POST"
    target_operation: str = "create_subaccount"
    request_body_build_enabled: bool = False
    payload_values_stored: bool = False
    raw_payload_stored: bool = False
    sandbox_only: bool = True
    production_blocked: bool = True
    manual_authorization_required: bool = True
    can_create_subaccount: bool = False
    can_send_http: bool = False
    real_money: bool = False
    http_call_executed: bool = False
    required_request_fields: tuple[str, ...] = (
        "name",
        "email",
        "cpfCnpj",
        "mobilePhone",
        "incomeValue",
        "address",
        "addressNumber",
        "province",
        "postalCode",
    )
    optional_request_fields: tuple[str, ...] = (
        "loginEmail",
        "birthDate",
        "companyType",
        "phone",
        "site",
        "complement",
    )
    future_review_request_fields: tuple[str, ...] = (
        "webhooks",
    )
    sensitive_request_fields: tuple[str, ...] = (
        "cpfCnpj",
        "email",
        "loginEmail",
        "phone",
        "mobilePhone",
        "address",
        "addressNumber",
        "complement",
        "province",
        "postalCode",
        "birthDate",
        "incomeValue",
    )
    prohibited_request_fields: tuple[str, ...] = (
        "apiKey",
        "walletId",
        "id",
        "onboardingUrl",
        "access_token",
        "asaas-access-token",
        "webhook_token",
        "ASAAS_API_KEY",
        "ASAAS_WEBHOOK_TOKEN",
    )
    sensitive_response_fields: tuple[str, ...] = (
        "apiKey",
        "walletId",
        "id",
        "onboardingUrl",
    )
    future_result_marker: str = "ASAAS_SANDBOX_SUBACCOUNT_PAYLOAD_CONTRACT_READY"

    def safe_summary(self) -> dict[str, Any]:
        return {
            "operation": "subaccount_payload_contract",
            "contract_reference": self.contract_reference,
            "endpoint_path": self.endpoint_path,
            "method": self.method,
            "target_operation": self.target_operation,
            "structure_guard": self.structure_guard.safe_summary(),
            "request_body_build_enabled": self.request_body_build_enabled,
            "payload_values_stored": self.payload_values_stored,
            "raw_payload_stored": self.raw_payload_stored,
            "sandbox_only": self.sandbox_only,
            "production_blocked": self.production_blocked,
            "manual_authorization_required": self.manual_authorization_required,
            "can_create_subaccount": self.can_create_subaccount,
            "can_send_http": self.can_send_http,
            "real_money": self.real_money,
            "http_call_executed": self.http_call_executed,
            "required_request_fields": list(self.required_request_fields),
            "optional_request_fields": list(self.optional_request_fields),
            "future_review_request_fields": list(
                self.future_review_request_fields
            ),
            "sensitive_request_fields": list(self.sensitive_request_fields),
            "prohibited_request_fields": list(self.prohibited_request_fields),
            "sensitive_response_fields": list(self.sensitive_response_fields),
            "field_names_only": True,
            "field_values_masked": True,
            "secret_values_allowed": False,
            "ready_for_http_execution": False,
            "future_result_marker": self.future_result_marker,
            "next_step_required": "manual_subaccount_payload_builder_review",
        }


@dataclass(frozen=True)
class AsaasSandboxSubaccountPayloadBuilderGuardResult:
    payload_contract: AsaasSandboxSubaccountPayloadContractResult
    prepared_request: AsaasPreparedRequest
    builder_reference: str = "subaccount-payload-builder-guard-sandbox"
    endpoint_path: str = "/accounts"
    method: str = "POST"
    target_operation: str = "create_subaccount"
    template_payload_built: bool = True
    synthetic_payload_only: bool = True
    payload_values_stored: bool = False
    raw_payload_stored: bool = False
    sandbox_only: bool = True
    production_blocked: bool = True
    manual_authorization_required: bool = True
    can_create_subaccount: bool = False
    can_send_http: bool = False
    real_money: bool = False
    http_call_executed: bool = False
    future_result_marker: str = "ASAAS_SANDBOX_SUBACCOUNT_PAYLOAD_BUILDER_GUARD_READY"

    def safe_summary(self) -> dict[str, Any]:
        template = self.prepared_request.json or {}
        prohibited_template_fields = sorted(
            set(template).intersection(
                set(self.payload_contract.prohibited_request_fields)
            )
        )

        return {
            "operation": "subaccount_payload_builder_guard",
            "builder_reference": self.builder_reference,
            "endpoint_path": self.endpoint_path,
            "method": self.method,
            "target_operation": self.target_operation,
            "payload_contract": self.payload_contract.safe_summary(),
            "prepared_request": {
                "method": self.prepared_request.method,
                "url": self.prepared_request.url,
                "operation": self.prepared_request.operation,
                "headers_configured": self.prepared_request.headers_configured,
                "real_money": self.prepared_request.real_money,
                "http_call_executed": self.prepared_request.http_call_executed,
                "json_payload_template_stored": self.prepared_request.json
                is not None,
                "raw": self.prepared_request.raw,
            },
            "template_payload_built": self.template_payload_built,
            "synthetic_payload_only": self.synthetic_payload_only,
            "payload_values_stored": self.payload_values_stored,
            "raw_payload_stored": self.raw_payload_stored,
            "sandbox_only": self.sandbox_only,
            "production_blocked": self.production_blocked,
            "manual_authorization_required": self.manual_authorization_required,
            "can_create_subaccount": self.can_create_subaccount,
            "can_send_http": self.can_send_http,
            "real_money": self.real_money,
            "http_call_executed": self.http_call_executed,
            "payload_template_field_names": list(template.keys()),
            "payload_template_values_masked": True,
            "sanitized_payload_preview": {
                field_name: "<masked>" for field_name in template
            },
            "prohibited_template_fields": prohibited_template_fields,
            "ready_for_http_execution": False,
            "future_result_marker": self.future_result_marker,
            "next_step_required": "manual_subaccount_payload_fixture_review",
        }


@dataclass(frozen=True)
class AsaasSandboxSubaccountSanitizedFixtureResult:
    builder_guard: AsaasSandboxSubaccountPayloadBuilderGuardResult
    fixture_reference: str = "subaccount-sanitized-fixture-sandbox"
    fixture_source: str = "synthetic_sandbox_subaccount_response_fixture"
    raw_response_stored: bool = False
    raw_payload_stored: bool = False
    sandbox_only: bool = True
    production_blocked: bool = True
    synthetic_fixture_only: bool = True
    can_create_subaccount: bool = False
    can_send_http: bool = False
    real_money: bool = False
    http_call_executed: bool = False
    api_key_present: bool = True
    wallet_id_present: bool = True
    account_id_present: bool = True
    onboarding_url_present: bool = True
    sensitive_response_fields: tuple[str, ...] = (
        "apiKey",
        "walletId",
        "id",
        "onboardingUrl",
    )
    sanitized_response_fixture: dict[str, Any] = field(
        default_factory=lambda: {
            "object": "account",
            "id": "<masked>",
            "apiKey": "<masked>",
            "walletId": "<masked>",
            "onboardingUrl": "<masked>",
            "status": "sandbox_fixture_only",
        }
    )
    future_result_marker: str = "ASAAS_SANDBOX_SUBACCOUNT_SANITIZED_FIXTURE_READY"

    def safe_summary(self) -> dict[str, Any]:
        return {
            "operation": "subaccount_sanitized_fixture",
            "fixture_reference": self.fixture_reference,
            "fixture_source": self.fixture_source,
            "builder_guard": self.builder_guard.safe_summary(),
            "raw_response_stored": self.raw_response_stored,
            "raw_payload_stored": self.raw_payload_stored,
            "sandbox_only": self.sandbox_only,
            "production_blocked": self.production_blocked,
            "synthetic_fixture_only": self.synthetic_fixture_only,
            "can_create_subaccount": self.can_create_subaccount,
            "can_send_http": self.can_send_http,
            "real_money": self.real_money,
            "http_call_executed": self.http_call_executed,
            "api_key_present": self.api_key_present,
            "wallet_id_present": self.wallet_id_present,
            "account_id_present": self.account_id_present,
            "onboarding_url_present": self.onboarding_url_present,
            "sensitive_response_fields": list(self.sensitive_response_fields),
            "sensitive_response_values_masked": True,
            "sanitized_response_fixture": self.sanitized_response_fixture,
            "ready_for_http_execution": False,
            "future_result_marker": self.future_result_marker,
            "next_step_required": "manual_subaccount_response_sanitizer_review",
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
class AsaasFirstCustomerHttpBlockedAdapterContractResult:
    prepared_request: AsaasPreparedRequest
    contract_reference: str = "first-customer-http-blocked-adapter-contract-sandbox"
    adapter_name: str = "blocked_sandbox_first_customer_http_adapter_contract"
    request_contract: dict[str, Any] = field(
        default_factory=lambda: {
            "method": "POST",
            "path": "/customers",
            "operation": "create_customer",
            "required_header_names": ["access_token"],
            "sensitive_header_values_masked": True,
            "required_json_fields": ["name", "cpfCnpj", "email", "mobilePhone"],
        }
    )
    response_contract: dict[str, Any] = field(
        default_factory=lambda: {
            "expected_success_statuses": [200, 201],
            "expected_safe_fields": ["id", "name", "cpfCnpj", "email", "mobilePhone"],
            "raw_response_blocked": True,
            "secret_values_allowed": False,
        }
    )
    error_contract: dict[str, Any] = field(
        default_factory=lambda: {
            "sanitized_error_fields": [
                "status_code",
                "provider_error_code",
                "safe_message",
                "retryable",
            ],
            "raw_error_blocked": True,
            "secret_values_allowed": False,
        }
    )
    manual_authorization_registered: bool = False
    access_token_header_configured: bool = False
    sandbox_only: bool = True
    target_allowed: bool = True
    adapter_implemented: bool = False
    adapter_enabled: bool = False
    can_send_http: bool = False
    network_call_allowed: bool = False
    retry_enabled: bool = False
    real_money: bool = False
    http_call_executed: bool = False

    def safe_summary(self) -> dict[str, Any]:
        return {
            "operation": "first_customer_http_blocked_adapter_contract",
            "contract_reference": self.contract_reference,
            "adapter_name": self.adapter_name,
            "prepared_request": self.prepared_request.safe_summary(),
            "request_contract": self.request_contract,
            "response_contract": self.response_contract,
            "error_contract": self.error_contract,
            "manual_authorization_registered": self.manual_authorization_registered,
            "access_token_header_configured": self.access_token_header_configured,
            "sandbox_only": self.sandbox_only,
            "target_allowed": self.target_allowed,
            "adapter_implemented": self.adapter_implemented,
            "adapter_enabled": self.adapter_enabled,
            "can_send_http": self.can_send_http,
            "network_call_allowed": self.network_call_allowed,
            "retry_enabled": self.retry_enabled,
            "real_money": self.real_money,
            "http_call_executed": self.http_call_executed,
            "ready_for_http_execution": False,
            "next_step_required": "manual_blocked_adapter_contract_review",
        }


@dataclass(frozen=True)
class AsaasFirstCustomerHttpResponseSanitizerContractResult:
    blocked_adapter_contract: AsaasFirstCustomerHttpBlockedAdapterContractResult
    sanitizer_reference: str = (
        "first-customer-http-response-sanitizer-contract-sandbox"
    )
    success_sanitizer_contract: dict[str, Any] = field(
        default_factory=lambda: {
            "allowed_fields": ["id", "name", "cpfCnpj", "email", "mobilePhone"],
            "blocked_fields": [
                "access_token",
                "api_key",
                "webhook_token",
                "wallet_id",
                "headers",
                "raw",
                "provider_raw",
            ],
            "raw_response_allowed": False,
            "secret_values_allowed": False,
            "safe_fields_only": True,
        }
    )
    error_sanitizer_contract: dict[str, Any] = field(
        default_factory=lambda: {
            "allowed_fields": [
                "status_code",
                "provider_error_code",
                "safe_message",
                "retryable",
            ],
            "blocked_fields": [
                "access_token",
                "api_key",
                "webhook_token",
                "wallet_id",
                "headers",
                "raw",
                "provider_raw",
                "stacktrace",
            ],
            "raw_error_allowed": False,
            "secret_values_allowed": False,
            "safe_fields_only": True,
        }
    )
    sanitizer_contract_defined: bool = True
    sanitizer_implemented: bool = False
    raw_response_retained: bool = False
    raw_error_retained: bool = False
    manual_authorization_registered: bool = False
    sandbox_only: bool = True
    adapter_implemented: bool = False
    adapter_enabled: bool = False
    can_send_http: bool = False
    network_call_allowed: bool = False
    real_money: bool = False
    http_call_executed: bool = False

    @property
    def prepared_request(self) -> AsaasPreparedRequest:
        return self.blocked_adapter_contract.prepared_request

    def safe_summary(self) -> dict[str, Any]:
        return {
            "operation": "first_customer_http_response_sanitizer_contract",
            "sanitizer_reference": self.sanitizer_reference,
            "blocked_adapter_contract": (
                self.blocked_adapter_contract.safe_summary()
            ),
            "prepared_request": self.prepared_request.safe_summary(),
            "success_sanitizer_contract": self.success_sanitizer_contract,
            "error_sanitizer_contract": self.error_sanitizer_contract,
            "sanitizer_contract_defined": self.sanitizer_contract_defined,
            "sanitizer_implemented": self.sanitizer_implemented,
            "raw_response_retained": self.raw_response_retained,
            "raw_error_retained": self.raw_error_retained,
            "manual_authorization_registered": (
                self.manual_authorization_registered
            ),
            "sandbox_only": self.sandbox_only,
            "adapter_implemented": self.adapter_implemented,
            "adapter_enabled": self.adapter_enabled,
            "can_send_http": self.can_send_http,
            "network_call_allowed": self.network_call_allowed,
            "real_money": self.real_money,
            "http_call_executed": self.http_call_executed,
            "ready_for_http_execution": False,
            "next_step_required": "manual_response_sanitizer_contract_review",
        }


@dataclass(frozen=True)
class AsaasFirstCustomerHttpErrorSanitizerContractResult:
    response_sanitizer_contract: AsaasFirstCustomerHttpResponseSanitizerContractResult
    error_sanitizer_reference: str = (
        "first-customer-http-error-sanitizer-contract-sandbox"
    )
    safe_error_shape: dict[str, Any] = field(
        default_factory=lambda: {
            "allowed_fields": [
                "status_code",
                "provider_error_code",
                "safe_message",
                "retryable",
                "category",
            ],
            "blocked_fields": [
                "access_token",
                "api_key",
                "webhook_token",
                "wallet_id",
                "headers",
                "raw",
                "provider_raw",
                "stacktrace",
                "request_body",
            ],
            "raw_error_allowed": False,
            "provider_raw_error_allowed": False,
            "stacktrace_allowed": False,
            "secret_values_allowed": False,
            "safe_fields_only": True,
        }
    )
    safe_error_categories: list[str] = field(
        default_factory=lambda: [
            "provider_validation_error",
            "provider_authentication_error",
            "provider_rate_limit_error",
            "provider_unavailable",
            "unexpected_provider_error",
        ]
    )
    error_sanitizer_contract_defined: bool = True
    error_sanitizer_implemented: bool = False
    raw_error_retained: bool = False
    provider_raw_error_retained: bool = False
    stacktrace_retained: bool = False
    manual_authorization_registered: bool = False
    sandbox_only: bool = True
    adapter_implemented: bool = False
    adapter_enabled: bool = False
    can_send_http: bool = False
    network_call_allowed: bool = False
    real_money: bool = False
    http_call_executed: bool = False

    @property
    def prepared_request(self) -> AsaasPreparedRequest:
        return self.response_sanitizer_contract.prepared_request

    def safe_summary(self) -> dict[str, Any]:
        return {
            "operation": "first_customer_http_error_sanitizer_contract",
            "error_sanitizer_reference": self.error_sanitizer_reference,
            "response_sanitizer_contract": (
                self.response_sanitizer_contract.safe_summary()
            ),
            "prepared_request": self.prepared_request.safe_summary(),
            "safe_error_shape": self.safe_error_shape,
            "safe_error_categories": self.safe_error_categories,
            "error_sanitizer_contract_defined": (
                self.error_sanitizer_contract_defined
            ),
            "error_sanitizer_implemented": self.error_sanitizer_implemented,
            "raw_error_retained": self.raw_error_retained,
            "provider_raw_error_retained": self.provider_raw_error_retained,
            "stacktrace_retained": self.stacktrace_retained,
            "manual_authorization_registered": (
                self.manual_authorization_registered
            ),
            "sandbox_only": self.sandbox_only,
            "adapter_implemented": self.adapter_implemented,
            "adapter_enabled": self.adapter_enabled,
            "can_send_http": self.can_send_http,
            "network_call_allowed": self.network_call_allowed,
            "real_money": self.real_money,
            "http_call_executed": self.http_call_executed,
            "ready_for_http_execution": False,
            "next_step_required": "manual_error_sanitizer_contract_review",
        }


@dataclass(frozen=True)
class AsaasFirstCustomerHttpManualExecutionApprovalGateResult:
    error_sanitizer_contract: AsaasFirstCustomerHttpErrorSanitizerContractResult
    approval_reference: str = (
        "first-customer-http-manual-execution-approval-gate-sandbox"
    )
    approval_checklist: dict[str, Any] = field(
        default_factory=lambda: {
            "sandbox_target_confirmed": True,
            "production_blocked": True,
            "real_money_disabled": True,
            "safe_response_sanitizer_required": True,
            "safe_error_sanitizer_required": True,
            "raw_response_exposure_blocked": True,
            "raw_error_exposure_blocked": True,
            "request_body_exposure_blocked": True,
            "stacktrace_exposure_blocked": True,
            "secret_exposure_blocked": True,
            "adapter_implementation_reviewed": False,
            "final_operator_confirmation_required": True,
        }
    )
    approval_gate_defined: bool = True
    manual_execution_approval_registered: bool = False
    manual_execution_approval_valid: bool = False
    approval_allows_http_execution: bool = False
    execution_enabled: bool = False
    sandbox_only: bool = True
    adapter_implemented: bool = False
    adapter_enabled: bool = False
    can_send_http: bool = False
    network_call_allowed: bool = False
    real_money: bool = False
    http_call_executed: bool = False

    @property
    def prepared_request(self) -> AsaasPreparedRequest:
        return self.error_sanitizer_contract.prepared_request

    def safe_summary(self) -> dict[str, Any]:
        return {
            "operation": "first_customer_http_manual_execution_approval_gate",
            "approval_reference": self.approval_reference,
            "error_sanitizer_contract": (
                self.error_sanitizer_contract.safe_summary()
            ),
            "prepared_request": self.prepared_request.safe_summary(),
            "approval_checklist": self.approval_checklist,
            "approval_gate_defined": self.approval_gate_defined,
            "manual_execution_approval_registered": (
                self.manual_execution_approval_registered
            ),
            "manual_execution_approval_valid": (
                self.manual_execution_approval_valid
            ),
            "approval_allows_http_execution": (
                self.approval_allows_http_execution
            ),
            "execution_enabled": self.execution_enabled,
            "sandbox_only": self.sandbox_only,
            "adapter_implemented": self.adapter_implemented,
            "adapter_enabled": self.adapter_enabled,
            "can_send_http": self.can_send_http,
            "network_call_allowed": self.network_call_allowed,
            "real_money": self.real_money,
            "http_call_executed": self.http_call_executed,
            "ready_for_http_execution": False,
            "next_step_required": "manual_execution_approval_review",
        }


@dataclass(frozen=True)
class AsaasFirstCustomerHttpDisabledAdapterShellResult:
    manual_approval_gate: AsaasFirstCustomerHttpManualExecutionApprovalGateResult
    adapter_shell_reference: str = (
        "first-customer-http-disabled-adapter-shell-sandbox"
    )
    adapter_shell_contract: dict[str, Any] = field(
        default_factory=lambda: {
            "target_method": "POST",
            "target_path": "/customers",
            "target_environment": "sandbox",
            "http_client_library_selected": False,
            "network_binding_created": False,
            "send_method_defined": False,
            "execution_method_defined": False,
            "requires_future_explicit_enablement": True,
        }
    )
    disabled_adapter_shell_defined: bool = True
    adapter_shell_enabled: bool = False
    adapter_implemented: bool = False
    adapter_enabled: bool = False
    execution_enabled: bool = False
    can_send_http: bool = False
    network_call_allowed: bool = False
    real_money: bool = False
    http_call_executed: bool = False
    sandbox_only: bool = True

    @property
    def prepared_request(self) -> AsaasPreparedRequest:
        return self.manual_approval_gate.prepared_request

    def safe_summary(self) -> dict[str, Any]:
        return {
            "operation": "first_customer_http_disabled_adapter_shell",
            "adapter_shell_reference": self.adapter_shell_reference,
            "manual_approval_gate": self.manual_approval_gate.safe_summary(),
            "prepared_request": self.prepared_request.safe_summary(),
            "adapter_shell_contract": self.adapter_shell_contract,
            "disabled_adapter_shell_defined": self.disabled_adapter_shell_defined,
            "adapter_shell_enabled": self.adapter_shell_enabled,
            "adapter_implemented": self.adapter_implemented,
            "adapter_enabled": self.adapter_enabled,
            "execution_enabled": self.execution_enabled,
            "can_send_http": self.can_send_http,
            "network_call_allowed": self.network_call_allowed,
            "real_money": self.real_money,
            "http_call_executed": self.http_call_executed,
            "sandbox_only": self.sandbox_only,
            "ready_for_http_execution": False,
            "next_step_required": "manual_disabled_adapter_shell_review",
        }


@dataclass(frozen=True)
class AsaasFirstCustomerHttpExplicitEnablePreflightResult:
    disabled_adapter_shell: AsaasFirstCustomerHttpDisabledAdapterShellResult
    explicit_enable_reference: str = (
        "first-customer-http-explicit-enable-preflight-sandbox"
    )
    required_explicit_enable_phrase: str = (
        "CONFIRMO PREFLIGHT DE HABILITACAO EXPLICITA ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )
    explicit_enable_preflight_contract: dict[str, Any] = field(
        default_factory=lambda: {
            "target_method": "POST",
            "target_path": "/customers",
            "target_environment": "sandbox",
            "requires_manual_execution_approval": True,
            "requires_disabled_adapter_shell": True,
            "requires_explicit_enable_phrase": True,
            "requires_future_http_adapter_implementation": True,
            "requires_future_runtime_enablement": True,
            "current_preflight_is_non_executing": True,
        }
    )
    explicit_enable_preflight_defined: bool = True
    explicit_enable_phrase_registered: bool = False
    manual_execution_approval_valid: bool = False
    disabled_adapter_shell_defined: bool = True
    explicit_enable_preflight_valid: bool = False
    explicit_enable_allows_adapter_enablement: bool = False
    explicit_enable_allows_http_execution: bool = False
    adapter_shell_enabled: bool = False
    adapter_implemented: bool = False
    adapter_enabled: bool = False
    execution_enabled: bool = False
    can_send_http: bool = False
    network_call_allowed: bool = False
    real_money: bool = False
    http_call_executed: bool = False
    sandbox_only: bool = True

    @property
    def prepared_request(self) -> AsaasPreparedRequest:
        return self.disabled_adapter_shell.prepared_request

    def safe_summary(self) -> dict[str, Any]:
        return {
            "operation": "first_customer_http_explicit_enable_preflight",
            "explicit_enable_reference": self.explicit_enable_reference,
            "disabled_adapter_shell": self.disabled_adapter_shell.safe_summary(),
            "prepared_request": self.prepared_request.safe_summary(),
            "explicit_enable_preflight_contract": (
                self.explicit_enable_preflight_contract
            ),
            "explicit_enable_preflight_defined": (
                self.explicit_enable_preflight_defined
            ),
            "explicit_enable_phrase_required": True,
            "explicit_enable_phrase_registered": (
                self.explicit_enable_phrase_registered
            ),
            "manual_execution_approval_valid": (
                self.manual_execution_approval_valid
            ),
            "disabled_adapter_shell_defined": (
                self.disabled_adapter_shell_defined
            ),
            "explicit_enable_preflight_valid": (
                self.explicit_enable_preflight_valid
            ),
            "explicit_enable_allows_adapter_enablement": (
                self.explicit_enable_allows_adapter_enablement
            ),
            "explicit_enable_allows_http_execution": (
                self.explicit_enable_allows_http_execution
            ),
            "adapter_shell_enabled": self.adapter_shell_enabled,
            "adapter_implemented": self.adapter_implemented,
            "adapter_enabled": self.adapter_enabled,
            "execution_enabled": self.execution_enabled,
            "can_send_http": self.can_send_http,
            "network_call_allowed": self.network_call_allowed,
            "real_money": self.real_money,
            "http_call_executed": self.http_call_executed,
            "sandbox_only": self.sandbox_only,
            "ready_for_http_execution": False,
            "next_step_required": "explicit_enable_preflight_review",
        }


@dataclass(frozen=True)
class AsaasFirstCustomerHttpRuntimeEnableContractResult:
    explicit_enable_preflight: AsaasFirstCustomerHttpExplicitEnablePreflightResult
    runtime_enable_reference: str = (
        "first-customer-http-runtime-enable-contract-sandbox"
    )
    required_runtime_enable_phrase: str = (
        "CONFIRMO CONTRATO DE HABILITACAO RUNTIME ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )
    runtime_enable_contract: dict[str, Any] = field(
        default_factory=lambda: {
            "target_method": "POST",
            "target_path": "/customers",
            "target_environment": "sandbox",
            "requires_manual_execution_approval": True,
            "requires_disabled_adapter_shell": True,
            "requires_explicit_enable_preflight": True,
            "requires_runtime_enable_phrase": True,
            "requires_future_http_adapter_implementation": True,
            "requires_future_runtime_switch": True,
            "current_contract_is_non_executing": True,
        }
    )
    runtime_enable_contract_defined: bool = True
    runtime_enable_phrase_registered: bool = False
    explicit_enable_preflight_valid: bool = False
    runtime_enable_contract_valid: bool = False
    runtime_enable_allows_adapter_enablement: bool = False
    runtime_enable_allows_http_execution: bool = False
    adapter_shell_enabled: bool = False
    adapter_implemented: bool = False
    adapter_enabled: bool = False
    execution_enabled: bool = False
    can_send_http: bool = False
    network_call_allowed: bool = False
    real_money: bool = False
    http_call_executed: bool = False
    sandbox_only: bool = True

    @property
    def prepared_request(self) -> AsaasPreparedRequest:
        return self.explicit_enable_preflight.prepared_request

    def safe_summary(self) -> dict[str, Any]:
        return {
            "operation": "first_customer_http_runtime_enable_contract",
            "runtime_enable_reference": self.runtime_enable_reference,
            "explicit_enable_preflight": (
                self.explicit_enable_preflight.safe_summary()
            ),
            "prepared_request": self.prepared_request.safe_summary(),
            "runtime_enable_contract": self.runtime_enable_contract,
            "runtime_enable_contract_defined": (
                self.runtime_enable_contract_defined
            ),
            "runtime_enable_phrase_required": True,
            "runtime_enable_phrase_registered": (
                self.runtime_enable_phrase_registered
            ),
            "explicit_enable_preflight_valid": (
                self.explicit_enable_preflight_valid
            ),
            "runtime_enable_contract_valid": (
                self.runtime_enable_contract_valid
            ),
            "runtime_enable_allows_adapter_enablement": (
                self.runtime_enable_allows_adapter_enablement
            ),
            "runtime_enable_allows_http_execution": (
                self.runtime_enable_allows_http_execution
            ),
            "adapter_shell_enabled": self.adapter_shell_enabled,
            "adapter_implemented": self.adapter_implemented,
            "adapter_enabled": self.adapter_enabled,
            "execution_enabled": self.execution_enabled,
            "can_send_http": self.can_send_http,
            "network_call_allowed": self.network_call_allowed,
            "real_money": self.real_money,
            "http_call_executed": self.http_call_executed,
            "sandbox_only": self.sandbox_only,
            "ready_for_http_execution": False,
            "next_step_required": "runtime_enable_contract_review",
        }


@dataclass(frozen=True)
class AsaasFirstCustomerHttpRuntimeSwitchGuardResult:
    runtime_enable_contract: AsaasFirstCustomerHttpRuntimeEnableContractResult
    runtime_switch_guard_reference: str = (
        "first-customer-http-runtime-switch-guard-sandbox"
    )
    required_runtime_switch_phrase: str = (
        "CONFIRMO GUARD DO SWITCH RUNTIME ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )
    runtime_switch_guard_contract: dict[str, Any] = field(
        default_factory=lambda: {
            "target_method": "POST",
            "target_path": "/customers",
            "target_environment": "sandbox",
            "requires_manual_execution_approval": True,
            "requires_disabled_adapter_shell": True,
            "requires_explicit_enable_preflight": True,
            "requires_runtime_enable_contract": True,
            "requires_runtime_switch_phrase": True,
            "runtime_switch_default_state": "disabled",
            "requires_future_http_adapter_implementation": True,
            "requires_future_runtime_execution_gate": True,
            "current_guard_is_non_executing": True,
        }
    )
    runtime_switch_guard_defined: bool = True
    runtime_switch_phrase_registered: bool = False
    runtime_enable_contract_valid: bool = False
    runtime_switch_guard_valid: bool = False
    runtime_switch_requested: bool = False
    runtime_switch_allows_adapter_enablement: bool = False
    runtime_switch_allows_http_execution: bool = False
    adapter_shell_enabled: bool = False
    adapter_implemented: bool = False
    adapter_enabled: bool = False
    execution_enabled: bool = False
    can_send_http: bool = False
    network_call_allowed: bool = False
    real_money: bool = False
    http_call_executed: bool = False
    sandbox_only: bool = True

    @property
    def prepared_request(self) -> AsaasPreparedRequest:
        return self.runtime_enable_contract.prepared_request

    def safe_summary(self) -> dict[str, Any]:
        return {
            "operation": "first_customer_http_runtime_switch_guard",
            "runtime_switch_guard_reference": (
                self.runtime_switch_guard_reference
            ),
            "runtime_enable_contract": (
                self.runtime_enable_contract.safe_summary()
            ),
            "prepared_request": self.prepared_request.safe_summary(),
            "runtime_switch_guard_contract": (
                self.runtime_switch_guard_contract
            ),
            "runtime_switch_guard_defined": (
                self.runtime_switch_guard_defined
            ),
            "runtime_switch_phrase_required": True,
            "runtime_switch_phrase_registered": (
                self.runtime_switch_phrase_registered
            ),
            "runtime_enable_contract_valid": (
                self.runtime_enable_contract_valid
            ),
            "runtime_switch_guard_valid": self.runtime_switch_guard_valid,
            "runtime_switch_requested": self.runtime_switch_requested,
            "runtime_switch_allows_adapter_enablement": (
                self.runtime_switch_allows_adapter_enablement
            ),
            "runtime_switch_allows_http_execution": (
                self.runtime_switch_allows_http_execution
            ),
            "adapter_shell_enabled": self.adapter_shell_enabled,
            "adapter_implemented": self.adapter_implemented,
            "adapter_enabled": self.adapter_enabled,
            "execution_enabled": self.execution_enabled,
            "can_send_http": self.can_send_http,
            "network_call_allowed": self.network_call_allowed,
            "real_money": self.real_money,
            "http_call_executed": self.http_call_executed,
            "sandbox_only": self.sandbox_only,
            "ready_for_http_execution": False,
            "next_step_required": "runtime_switch_guard_review",
        }


@dataclass(frozen=True)
class AsaasFirstCustomerHttpExecutionGateContractResult:
    runtime_switch_guard: AsaasFirstCustomerHttpRuntimeSwitchGuardResult
    execution_gate_reference: str = (
        "first-customer-http-execution-gate-contract-sandbox"
    )
    required_execution_gate_phrase: str = (
        "CONFIRMO CONTRATO DO GATE DE EXECUCAO ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )
    execution_gate_contract: dict[str, Any] = field(
        default_factory=lambda: {
            "target_method": "POST",
            "target_path": "/customers",
            "target_environment": "sandbox",
            "requires_manual_execution_approval": True,
            "requires_disabled_adapter_shell": True,
            "requires_explicit_enable_preflight": True,
            "requires_runtime_enable_contract": True,
            "requires_runtime_switch_guard": True,
            "requires_execution_gate_phrase": True,
            "requires_future_http_adapter_implementation": True,
            "requires_future_sanitized_execution_handler": True,
            "current_gate_is_non_executing": True,
        }
    )
    execution_gate_contract_defined: bool = True
    execution_gate_phrase_registered: bool = False
    runtime_switch_guard_valid: bool = False
    execution_gate_contract_valid: bool = False
    execution_gate_allows_adapter_enablement: bool = False
    execution_gate_allows_http_execution: bool = False
    adapter_shell_enabled: bool = False
    adapter_implemented: bool = False
    adapter_enabled: bool = False
    execution_enabled: bool = False
    can_send_http: bool = False
    network_call_allowed: bool = False
    real_money: bool = False
    http_call_executed: bool = False
    sandbox_only: bool = True

    @property
    def prepared_request(self) -> AsaasPreparedRequest:
        return self.runtime_switch_guard.prepared_request

    def safe_summary(self) -> dict[str, Any]:
        return {
            "operation": "first_customer_http_execution_gate_contract",
            "execution_gate_reference": self.execution_gate_reference,
            "runtime_switch_guard": self.runtime_switch_guard.safe_summary(),
            "prepared_request": self.prepared_request.safe_summary(),
            "execution_gate_contract": self.execution_gate_contract,
            "execution_gate_contract_defined": (
                self.execution_gate_contract_defined
            ),
            "execution_gate_phrase_required": True,
            "execution_gate_phrase_registered": (
                self.execution_gate_phrase_registered
            ),
            "runtime_switch_guard_valid": self.runtime_switch_guard_valid,
            "execution_gate_contract_valid": (
                self.execution_gate_contract_valid
            ),
            "execution_gate_allows_adapter_enablement": (
                self.execution_gate_allows_adapter_enablement
            ),
            "execution_gate_allows_http_execution": (
                self.execution_gate_allows_http_execution
            ),
            "adapter_shell_enabled": self.adapter_shell_enabled,
            "adapter_implemented": self.adapter_implemented,
            "adapter_enabled": self.adapter_enabled,
            "execution_enabled": self.execution_enabled,
            "can_send_http": self.can_send_http,
            "network_call_allowed": self.network_call_allowed,
            "real_money": self.real_money,
            "http_call_executed": self.http_call_executed,
            "sandbox_only": self.sandbox_only,
            "ready_for_http_execution": False,
            "next_step_required": "execution_gate_contract_review",
        }


@dataclass(frozen=True)
class AsaasFirstCustomerHttpSanitizedExecutionHandlerContractResult:
    execution_gate_contract: AsaasFirstCustomerHttpExecutionGateContractResult
    sanitized_handler_reference: str = (
        "first-customer-http-sanitized-execution-handler-contract-sandbox"
    )
    sanitized_execution_handler_contract: dict[str, Any] = field(
        default_factory=lambda: {
            "target_method": "POST",
            "target_path": "/customers",
            "target_environment": "sandbox",
            "requires_execution_gate_contract": True,
            "requires_future_http_adapter_implementation": True,
            "requires_sanitized_response_handler": True,
            "requires_sanitized_error_handler": True,
            "raw_provider_response_allowed": False,
            "raw_provider_error_allowed": False,
            "request_body_exposure_allowed": False,
            "stacktrace_exposure_allowed": False,
            "current_handler_is_non_executing": True,
        }
    )
    sanitized_execution_handler_contract_defined: bool = True
    execution_gate_contract_valid: bool = False
    sanitized_response_handler_required: bool = True
    sanitized_error_handler_required: bool = True
    raw_provider_response_allowed: bool = False
    raw_provider_error_allowed: bool = False
    request_body_exposure_allowed: bool = False
    stacktrace_exposure_allowed: bool = False
    sanitized_handler_allows_adapter_enablement: bool = False
    sanitized_handler_allows_http_execution: bool = False
    sanitized_handler_can_process_raw_provider_payload: bool = False
    adapter_shell_enabled: bool = False
    adapter_implemented: bool = False
    adapter_enabled: bool = False
    execution_enabled: bool = False
    can_send_http: bool = False
    network_call_allowed: bool = False
    real_money: bool = False
    http_call_executed: bool = False
    sandbox_only: bool = True

    @property
    def prepared_request(self) -> AsaasPreparedRequest:
        return self.execution_gate_contract.prepared_request

    def safe_summary(self) -> dict[str, Any]:
        return {
            "operation": (
                "first_customer_http_sanitized_execution_handler_contract"
            ),
            "sanitized_handler_reference": self.sanitized_handler_reference,
            "execution_gate_contract": (
                self.execution_gate_contract.safe_summary()
            ),
            "prepared_request": self.prepared_request.safe_summary(),
            "sanitized_execution_handler_contract": (
                self.sanitized_execution_handler_contract
            ),
            "sanitized_execution_handler_contract_defined": (
                self.sanitized_execution_handler_contract_defined
            ),
            "execution_gate_contract_valid": (
                self.execution_gate_contract_valid
            ),
            "sanitized_response_handler_required": (
                self.sanitized_response_handler_required
            ),
            "sanitized_error_handler_required": (
                self.sanitized_error_handler_required
            ),
            "raw_provider_response_allowed": (
                self.raw_provider_response_allowed
            ),
            "raw_provider_error_allowed": self.raw_provider_error_allowed,
            "request_body_exposure_allowed": (
                self.request_body_exposure_allowed
            ),
            "stacktrace_exposure_allowed": self.stacktrace_exposure_allowed,
            "sanitized_handler_allows_adapter_enablement": (
                self.sanitized_handler_allows_adapter_enablement
            ),
            "sanitized_handler_allows_http_execution": (
                self.sanitized_handler_allows_http_execution
            ),
            "sanitized_handler_can_process_raw_provider_payload": (
                self.sanitized_handler_can_process_raw_provider_payload
            ),
            "adapter_shell_enabled": self.adapter_shell_enabled,
            "adapter_implemented": self.adapter_implemented,
            "adapter_enabled": self.adapter_enabled,
            "execution_enabled": self.execution_enabled,
            "can_send_http": self.can_send_http,
            "network_call_allowed": self.network_call_allowed,
            "real_money": self.real_money,
            "http_call_executed": self.http_call_executed,
            "sandbox_only": self.sandbox_only,
            "ready_for_http_execution": False,
            "next_step_required": (
                "sanitized_execution_handler_contract_review"
            ),
        }


@dataclass(frozen=True)
class AsaasFirstCustomerHttpSanitizedResultEnvelopeContractResult:
    sanitized_execution_handler_contract: (
        AsaasFirstCustomerHttpSanitizedExecutionHandlerContractResult
    )
    sanitized_result_envelope_reference: str = (
        "first-customer-http-sanitized-result-envelope-contract-sandbox"
    )
    sanitized_result_envelope_contract: dict[str, Any] = field(
        default_factory=lambda: {
            "target_method": "POST",
            "target_path": "/customers",
            "target_environment": "sandbox",
            "requires_sanitized_execution_handler_contract": True,
            "requires_success_envelope": True,
            "requires_error_envelope": True,
            "requires_no_raw_provider_payload": True,
            "success_envelope_fields": [
                "ok",
                "operation",
                "provider",
                "environment",
                "asaas_customer_id_present",
                "http_status_class",
                "sanitized_customer_reference",
                "raw_provider_payload_included",
            ],
            "error_envelope_fields": [
                "ok",
                "operation",
                "provider",
                "environment",
                "error_category",
                "retryable",
                "http_status_class",
                "raw_provider_error_included",
                "stacktrace_included",
            ],
            "raw_provider_payload_allowed": False,
            "raw_provider_error_allowed": False,
            "request_body_exposure_allowed": False,
            "stacktrace_exposure_allowed": False,
            "current_envelope_is_contract_only": True,
        }
    )
    sanitized_result_envelope_contract_defined: bool = True
    sanitized_execution_handler_contract_valid: bool = False
    success_envelope_required: bool = True
    error_envelope_required: bool = True
    raw_provider_payload_allowed: bool = False
    raw_provider_error_allowed: bool = False
    request_body_exposure_allowed: bool = False
    stacktrace_exposure_allowed: bool = False
    sanitized_result_envelope_allows_adapter_enablement: bool = False
    sanitized_result_envelope_allows_http_execution: bool = False
    sanitized_result_envelope_can_include_raw_payload: bool = False
    adapter_shell_enabled: bool = False
    adapter_implemented: bool = False
    adapter_enabled: bool = False
    execution_enabled: bool = False
    can_send_http: bool = False
    network_call_allowed: bool = False
    real_money: bool = False
    http_call_executed: bool = False
    sandbox_only: bool = True

    @property
    def prepared_request(self) -> AsaasPreparedRequest:
        return self.sanitized_execution_handler_contract.prepared_request

    def safe_summary(self) -> dict[str, Any]:
        return {
            "operation": (
                "first_customer_http_sanitized_result_envelope_contract"
            ),
            "sanitized_result_envelope_reference": (
                self.sanitized_result_envelope_reference
            ),
            "sanitized_execution_handler_contract": (
                self.sanitized_execution_handler_contract.safe_summary()
            ),
            "prepared_request": self.prepared_request.safe_summary(),
            "sanitized_result_envelope_contract": (
                self.sanitized_result_envelope_contract
            ),
            "sanitized_result_envelope_contract_defined": (
                self.sanitized_result_envelope_contract_defined
            ),
            "sanitized_execution_handler_contract_valid": (
                self.sanitized_execution_handler_contract_valid
            ),
            "success_envelope_required": self.success_envelope_required,
            "error_envelope_required": self.error_envelope_required,
            "raw_provider_payload_allowed": (
                self.raw_provider_payload_allowed
            ),
            "raw_provider_error_allowed": self.raw_provider_error_allowed,
            "request_body_exposure_allowed": (
                self.request_body_exposure_allowed
            ),
            "stacktrace_exposure_allowed": self.stacktrace_exposure_allowed,
            "sanitized_result_envelope_allows_adapter_enablement": (
                self.sanitized_result_envelope_allows_adapter_enablement
            ),
            "sanitized_result_envelope_allows_http_execution": (
                self.sanitized_result_envelope_allows_http_execution
            ),
            "sanitized_result_envelope_can_include_raw_payload": (
                self.sanitized_result_envelope_can_include_raw_payload
            ),
            "adapter_shell_enabled": self.adapter_shell_enabled,
            "adapter_implemented": self.adapter_implemented,
            "adapter_enabled": self.adapter_enabled,
            "execution_enabled": self.execution_enabled,
            "can_send_http": self.can_send_http,
            "network_call_allowed": self.network_call_allowed,
            "real_money": self.real_money,
            "http_call_executed": self.http_call_executed,
            "sandbox_only": self.sandbox_only,
            "ready_for_http_execution": False,
            "next_step_required": (
                "sanitized_result_envelope_contract_review"
            ),
        }


@dataclass(frozen=True)
class AsaasFirstCustomerHttpSanitizedSuccessErrorFixtureContractResult:
    sanitized_result_envelope_contract: (
        AsaasFirstCustomerHttpSanitizedResultEnvelopeContractResult
    )
    sanitized_success_error_fixture_reference: str = (
        "first-customer-http-sanitized-success-error-fixture-contract-sandbox"
    )
    sanitized_success_error_fixture_contract: dict[str, Any] = field(
        default_factory=lambda: {
            "target_method": "POST",
            "target_path": "/customers",
            "target_environment": "sandbox",
            "requires_sanitized_result_envelope_contract": True,
            "requires_success_fixture": True,
            "requires_error_fixture": True,
            "fixtures_are_sanitized": True,
            "success_fixture_contains_raw_provider_payload": False,
            "error_fixture_contains_raw_provider_error": False,
            "request_body_exposure_allowed": False,
            "stacktrace_exposure_allowed": False,
            "current_fixtures_are_contract_only": True,
        }
    )
    sanitized_success_fixture: dict[str, Any] = field(
        default_factory=lambda: {
            "ok": True,
            "operation": "create_customer",
            "provider": "asaas",
            "environment": "sandbox",
            "asaas_customer_id_present": True,
            "http_status_class": "2xx",
            "sanitized_customer_reference": (
                "asaas_customer_sandbox_fixture_redacted"
            ),
            "raw_provider_payload_included": False,
        }
    )
    sanitized_error_fixture: dict[str, Any] = field(
        default_factory=lambda: {
            "ok": False,
            "operation": "create_customer",
            "provider": "asaas",
            "environment": "sandbox",
            "error_category": "provider_rejected_or_unavailable",
            "retryable": False,
            "http_status_class": "4xx_or_5xx",
            "raw_provider_error_included": False,
            "stacktrace_included": False,
        }
    )
    sanitized_success_error_fixture_contract_defined: bool = True
    sanitized_result_envelope_contract_valid: bool = False
    sanitized_success_fixture_defined: bool = True
    sanitized_error_fixture_defined: bool = True
    sanitized_fixtures_match_envelope_contract: bool = True
    success_fixture_contains_raw_provider_payload: bool = False
    error_fixture_contains_raw_provider_error: bool = False
    request_body_exposure_allowed: bool = False
    stacktrace_exposure_allowed: bool = False
    fixture_contract_allows_adapter_enablement: bool = False
    fixture_contract_allows_http_execution: bool = False
    fixture_contract_can_include_raw_payload: bool = False
    adapter_shell_enabled: bool = False
    adapter_implemented: bool = False
    adapter_enabled: bool = False
    execution_enabled: bool = False
    can_send_http: bool = False
    network_call_allowed: bool = False
    real_money: bool = False
    http_call_executed: bool = False
    sandbox_only: bool = True

    @property
    def prepared_request(self) -> AsaasPreparedRequest:
        return self.sanitized_result_envelope_contract.prepared_request

    def safe_summary(self) -> dict[str, Any]:
        return {
            "operation": (
                "first_customer_http_sanitized_success_error_fixture_contract"
            ),
            "sanitized_success_error_fixture_reference": (
                self.sanitized_success_error_fixture_reference
            ),
            "sanitized_result_envelope_contract": (
                self.sanitized_result_envelope_contract.safe_summary()
            ),
            "prepared_request": self.prepared_request.safe_summary(),
            "sanitized_success_error_fixture_contract": (
                self.sanitized_success_error_fixture_contract
            ),
            "sanitized_success_fixture": self.sanitized_success_fixture,
            "sanitized_error_fixture": self.sanitized_error_fixture,
            "sanitized_success_error_fixture_contract_defined": (
                self.sanitized_success_error_fixture_contract_defined
            ),
            "sanitized_result_envelope_contract_valid": (
                self.sanitized_result_envelope_contract_valid
            ),
            "sanitized_success_fixture_defined": (
                self.sanitized_success_fixture_defined
            ),
            "sanitized_error_fixture_defined": (
                self.sanitized_error_fixture_defined
            ),
            "sanitized_fixtures_match_envelope_contract": (
                self.sanitized_fixtures_match_envelope_contract
            ),
            "success_fixture_contains_raw_provider_payload": (
                self.success_fixture_contains_raw_provider_payload
            ),
            "error_fixture_contains_raw_provider_error": (
                self.error_fixture_contains_raw_provider_error
            ),
            "request_body_exposure_allowed": (
                self.request_body_exposure_allowed
            ),
            "stacktrace_exposure_allowed": self.stacktrace_exposure_allowed,
            "fixture_contract_allows_adapter_enablement": (
                self.fixture_contract_allows_adapter_enablement
            ),
            "fixture_contract_allows_http_execution": (
                self.fixture_contract_allows_http_execution
            ),
            "fixture_contract_can_include_raw_payload": (
                self.fixture_contract_can_include_raw_payload
            ),
            "adapter_shell_enabled": self.adapter_shell_enabled,
            "adapter_implemented": self.adapter_implemented,
            "adapter_enabled": self.adapter_enabled,
            "execution_enabled": self.execution_enabled,
            "can_send_http": self.can_send_http,
            "network_call_allowed": self.network_call_allowed,
            "real_money": self.real_money,
            "http_call_executed": self.http_call_executed,
            "sandbox_only": self.sandbox_only,
            "ready_for_http_execution": False,
            "next_step_required": (
                "sanitized_success_error_fixture_contract_review"
            ),
        }


@dataclass(frozen=True)
class AsaasFirstCustomerHttpAdapterBoundaryFinalContractResult:
    sanitized_success_error_fixture_contract: (
        AsaasFirstCustomerHttpSanitizedSuccessErrorFixtureContractResult
    )
    adapter_boundary_reference: str = (
        "first-customer-http-adapter-boundary-final-contract-sandbox"
    )
    adapter_boundary_final_contract: dict[str, Any] = field(
        default_factory=lambda: {
            "target_method": "POST",
            "target_path": "/customers",
            "target_environment": "sandbox",
            "allowed_future_caller": (
                "first_customer_http_sanitized_execution_handler"
            ),
            "requires_manual_execution_approval": True,
            "requires_disabled_adapter_shell": True,
            "requires_explicit_enable_preflight": True,
            "requires_runtime_enable_contract": True,
            "requires_runtime_switch_guard": True,
            "requires_execution_gate_contract": True,
            "requires_sanitized_execution_handler_contract": True,
            "requires_sanitized_result_envelope_contract": True,
            "requires_sanitized_success_error_fixtures": True,
            "future_adapter_must_return_sanitized_envelope_only": True,
            "future_adapter_must_not_expose_raw_provider_payload": True,
            "future_adapter_must_not_expose_raw_provider_error": True,
            "future_adapter_must_not_expose_request_body": True,
            "future_adapter_must_not_expose_stacktrace": True,
            "adapter_implementation_present": False,
            "current_boundary_is_contract_only": True,
        }
    )
    adapter_boundary_final_contract_defined: bool = True
    sanitized_success_error_fixture_contract_valid: bool = False
    adapter_boundary_final_contract_valid: bool = False
    future_adapter_must_return_sanitized_envelope_only: bool = True
    raw_provider_payload_allowed: bool = False
    raw_provider_error_allowed: bool = False
    request_body_exposure_allowed: bool = False
    stacktrace_exposure_allowed: bool = False
    adapter_boundary_allows_adapter_implementation: bool = False
    adapter_boundary_allows_adapter_enablement: bool = False
    adapter_boundary_allows_http_execution: bool = False
    adapter_boundary_can_emit_raw_payload: bool = False
    adapter_shell_enabled: bool = False
    adapter_implemented: bool = False
    adapter_enabled: bool = False
    execution_enabled: bool = False
    can_send_http: bool = False
    network_call_allowed: bool = False
    real_money: bool = False
    http_call_executed: bool = False
    sandbox_only: bool = True

    @property
    def prepared_request(self) -> AsaasPreparedRequest:
        return self.sanitized_success_error_fixture_contract.prepared_request

    def safe_summary(self) -> dict[str, Any]:
        return {
            "operation": (
                "first_customer_http_adapter_boundary_final_contract"
            ),
            "adapter_boundary_reference": self.adapter_boundary_reference,
            "sanitized_success_error_fixture_contract": (
                self.sanitized_success_error_fixture_contract.safe_summary()
            ),
            "prepared_request": self.prepared_request.safe_summary(),
            "adapter_boundary_final_contract": (
                self.adapter_boundary_final_contract
            ),
            "adapter_boundary_final_contract_defined": (
                self.adapter_boundary_final_contract_defined
            ),
            "sanitized_success_error_fixture_contract_valid": (
                self.sanitized_success_error_fixture_contract_valid
            ),
            "adapter_boundary_final_contract_valid": (
                self.adapter_boundary_final_contract_valid
            ),
            "future_adapter_must_return_sanitized_envelope_only": (
                self.future_adapter_must_return_sanitized_envelope_only
            ),
            "raw_provider_payload_allowed": (
                self.raw_provider_payload_allowed
            ),
            "raw_provider_error_allowed": self.raw_provider_error_allowed,
            "request_body_exposure_allowed": (
                self.request_body_exposure_allowed
            ),
            "stacktrace_exposure_allowed": self.stacktrace_exposure_allowed,
            "adapter_boundary_allows_adapter_implementation": (
                self.adapter_boundary_allows_adapter_implementation
            ),
            "adapter_boundary_allows_adapter_enablement": (
                self.adapter_boundary_allows_adapter_enablement
            ),
            "adapter_boundary_allows_http_execution": (
                self.adapter_boundary_allows_http_execution
            ),
            "adapter_boundary_can_emit_raw_payload": (
                self.adapter_boundary_can_emit_raw_payload
            ),
            "adapter_shell_enabled": self.adapter_shell_enabled,
            "adapter_implemented": self.adapter_implemented,
            "adapter_enabled": self.adapter_enabled,
            "execution_enabled": self.execution_enabled,
            "can_send_http": self.can_send_http,
            "network_call_allowed": self.network_call_allowed,
            "real_money": self.real_money,
            "http_call_executed": self.http_call_executed,
            "sandbox_only": self.sandbox_only,
            "ready_for_http_execution": False,
            "next_step_required": (
                "final_manual_execution_runbook_readiness_gate"
            ),
        }


@dataclass(frozen=True)
class AsaasFirstCustomerHttpFinalManualExecutionRunbookReadinessGateResult:
    adapter_boundary_final_contract: (
        AsaasFirstCustomerHttpAdapterBoundaryFinalContractResult
    )
    final_readiness_gate_reference: str = (
        "first-customer-http-final-manual-execution-runbook-readiness-gate"
    )
    final_manual_execution_runbook_readiness_gate: dict[str, Any] = field(
        default_factory=lambda: {
            "target_method": "POST",
            "target_path": "/customers",
            "target_environment": "sandbox",
            "requires_adapter_boundary_final_contract": True,
            "requires_manual_operator_review": True,
            "requires_sandbox_only_confirmation": True,
            "requires_no_production_confirmation": True,
            "requires_no_real_money_confirmation": True,
            "requires_sanitized_logging_only": True,
            "requires_no_raw_provider_payload": True,
            "requires_no_raw_provider_error": True,
            "requires_no_request_body_logging": True,
            "requires_no_stacktrace_exposure": True,
            "requires_future_adapter_implementation_review": True,
            "requires_future_manual_execution_approval": True,
            "manual_execution_not_started": True,
            "current_gate_is_review_only": True,
        }
    )
    runbook_review_steps: list[str] = field(
        default_factory=lambda: [
            "confirm_sandbox_environment_only",
            "confirm_no_production_credentials_or_urls",
            "confirm_no_real_money_or_real_pix_flow",
            "confirm_adapter_boundary_contract_valid",
            "confirm_sanitized_result_envelope_only",
            "confirm_no_raw_provider_payload_or_error_logging",
            "confirm_no_request_body_or_stacktrace_exposure",
            "confirm_future_manual_execution_approval_required",
        ]
    )
    final_manual_execution_runbook_readiness_gate_defined: bool = True
    adapter_boundary_final_contract_valid: bool = False
    final_manual_execution_runbook_readiness_gate_valid: bool = False
    manual_operator_review_required: bool = True
    sandbox_only_confirmation_required: bool = True
    no_production_confirmation_required: bool = True
    no_real_money_confirmation_required: bool = True
    sanitized_logging_only_required: bool = True
    future_manual_execution_approval_required: bool = True
    future_adapter_implementation_review_required: bool = True
    raw_provider_payload_allowed: bool = False
    raw_provider_error_allowed: bool = False
    request_body_exposure_allowed: bool = False
    stacktrace_exposure_allowed: bool = False
    final_readiness_gate_allows_adapter_implementation: bool = False
    final_readiness_gate_allows_adapter_enablement: bool = False
    final_readiness_gate_allows_http_execution: bool = False
    final_readiness_gate_can_emit_raw_payload: bool = False
    ready_for_manual_execution_review: bool = False
    manual_execution_started: bool = False
    adapter_shell_enabled: bool = False
    adapter_implemented: bool = False
    adapter_enabled: bool = False
    execution_enabled: bool = False
    can_send_http: bool = False
    network_call_allowed: bool = False
    real_money: bool = False
    http_call_executed: bool = False
    sandbox_only: bool = True

    @property
    def prepared_request(self) -> AsaasPreparedRequest:
        return self.adapter_boundary_final_contract.prepared_request

    def safe_summary(self) -> dict[str, Any]:
        return {
            "operation": (
                "first_customer_http_final_manual_execution_runbook_"
                "readiness_gate"
            ),
            "final_readiness_gate_reference": (
                self.final_readiness_gate_reference
            ),
            "adapter_boundary_final_contract": (
                self.adapter_boundary_final_contract.safe_summary()
            ),
            "prepared_request": self.prepared_request.safe_summary(),
            "final_manual_execution_runbook_readiness_gate": (
                self.final_manual_execution_runbook_readiness_gate
            ),
            "runbook_review_steps": self.runbook_review_steps,
            "final_manual_execution_runbook_readiness_gate_defined": (
                self.final_manual_execution_runbook_readiness_gate_defined
            ),
            "adapter_boundary_final_contract_valid": (
                self.adapter_boundary_final_contract_valid
            ),
            "final_manual_execution_runbook_readiness_gate_valid": (
                self.final_manual_execution_runbook_readiness_gate_valid
            ),
            "manual_operator_review_required": (
                self.manual_operator_review_required
            ),
            "sandbox_only_confirmation_required": (
                self.sandbox_only_confirmation_required
            ),
            "no_production_confirmation_required": (
                self.no_production_confirmation_required
            ),
            "no_real_money_confirmation_required": (
                self.no_real_money_confirmation_required
            ),
            "sanitized_logging_only_required": (
                self.sanitized_logging_only_required
            ),
            "future_manual_execution_approval_required": (
                self.future_manual_execution_approval_required
            ),
            "future_adapter_implementation_review_required": (
                self.future_adapter_implementation_review_required
            ),
            "raw_provider_payload_allowed": (
                self.raw_provider_payload_allowed
            ),
            "raw_provider_error_allowed": self.raw_provider_error_allowed,
            "request_body_exposure_allowed": (
                self.request_body_exposure_allowed
            ),
            "stacktrace_exposure_allowed": self.stacktrace_exposure_allowed,
            "final_readiness_gate_allows_adapter_implementation": (
                self.final_readiness_gate_allows_adapter_implementation
            ),
            "final_readiness_gate_allows_adapter_enablement": (
                self.final_readiness_gate_allows_adapter_enablement
            ),
            "final_readiness_gate_allows_http_execution": (
                self.final_readiness_gate_allows_http_execution
            ),
            "final_readiness_gate_can_emit_raw_payload": (
                self.final_readiness_gate_can_emit_raw_payload
            ),
            "ready_for_manual_execution_review": (
                self.ready_for_manual_execution_review
            ),
            "manual_execution_started": self.manual_execution_started,
            "adapter_shell_enabled": self.adapter_shell_enabled,
            "adapter_implemented": self.adapter_implemented,
            "adapter_enabled": self.adapter_enabled,
            "execution_enabled": self.execution_enabled,
            "can_send_http": self.can_send_http,
            "network_call_allowed": self.network_call_allowed,
            "real_money": self.real_money,
            "http_call_executed": self.http_call_executed,
            "sandbox_only": self.sandbox_only,
            "ready_for_http_execution": False,
            "next_step_required": (
                "manual_review_before_first_sandbox_http_attempt"
            ),
        }


@dataclass(frozen=True)
class AsaasFirstCustomerHttpFirstControlledSandboxAttemptPreparationResult:
    final_manual_execution_runbook_readiness_gate: (
        AsaasFirstCustomerHttpFinalManualExecutionRunbookReadinessGateResult
    )
    first_controlled_attempt_preparation_reference: str = (
        "first-customer-http-first-controlled-sandbox-attempt-preparation"
    )
    first_controlled_sandbox_attempt_preparation: dict[str, Any] = field(
        default_factory=lambda: {
            "target_method": "POST",
            "target_path": "/customers",
            "target_environment": "sandbox",
            "requires_final_manual_execution_runbook_readiness_gate": True,
            "requires_manual_operator_review": True,
            "requires_sandbox_base_url_confirmation": True,
            "requires_environment_secret_loading_only": True,
            "requires_no_production_credentials": True,
            "requires_no_real_money_or_real_pix_flow": True,
            "requires_sanitized_success_envelope": True,
            "requires_sanitized_error_envelope": True,
            "requires_redacted_logs_only": True,
            "requires_single_controlled_attempt_policy": True,
            "requires_no_retry_loop": True,
            "requires_manual_stop_on_unexpected_response": True,
            "requires_no_raw_provider_payload_storage": True,
            "requires_no_request_body_logging": True,
            "requires_no_stacktrace_exposure": True,
            "first_controlled_attempt_not_executed": True,
            "current_preparation_is_non_executing": True,
        }
    )
    first_controlled_attempt_checklist: list[str] = field(
        default_factory=lambda: [
            "confirm_main_branch_clean_and_tagged",
            "confirm_sandbox_environment_variables_exist_locally",
            "confirm_no_production_base_url_or_credentials",
            "confirm_manual_operator_is_present",
            "confirm_single_attempt_only",
            "confirm_sanitized_logging_only",
            "confirm_no_request_body_logging",
            "confirm_no_raw_provider_payload_storage",
            "confirm_stop_on_unexpected_response",
            "confirm_post_attempt_sanitized_record_required",
        ]
    )
    first_controlled_sandbox_attempt_preparation_defined: bool = True
    final_manual_execution_runbook_readiness_gate_valid: bool = False
    first_controlled_sandbox_attempt_preparation_valid: bool = False
    ready_for_first_controlled_sandbox_attempt_review: bool = False
    manual_operator_review_required: bool = True
    sandbox_base_url_confirmation_required: bool = True
    environment_secret_loading_only_required: bool = True
    no_production_credentials_required: bool = True
    no_real_money_or_real_pix_flow_required: bool = True
    sanitized_success_envelope_required: bool = True
    sanitized_error_envelope_required: bool = True
    redacted_logs_only_required: bool = True
    single_controlled_attempt_policy_required: bool = True
    no_retry_loop_required: bool = True
    manual_stop_on_unexpected_response_required: bool = True
    raw_provider_payload_storage_allowed: bool = False
    request_body_logging_allowed: bool = False
    stacktrace_exposure_allowed: bool = False
    first_controlled_attempt_allows_adapter_implementation: bool = False
    first_controlled_attempt_allows_adapter_enablement: bool = False
    first_controlled_attempt_allows_http_execution: bool = False
    first_controlled_attempt_can_emit_raw_payload: bool = False
    first_controlled_attempt_executed: bool = False
    adapter_shell_enabled: bool = False
    adapter_implemented: bool = False
    adapter_enabled: bool = False
    execution_enabled: bool = False
    can_send_http: bool = False
    network_call_allowed: bool = False
    real_money: bool = False
    http_call_executed: bool = False
    sandbox_only: bool = True

    @property
    def prepared_request(self) -> AsaasPreparedRequest:
        return (
            self.final_manual_execution_runbook_readiness_gate
            .prepared_request
        )

    def safe_summary(self) -> dict[str, Any]:
        return {
            "operation": (
                "first_customer_http_first_controlled_sandbox_attempt_"
                "preparation"
            ),
            "first_controlled_attempt_preparation_reference": (
                self.first_controlled_attempt_preparation_reference
            ),
            "final_manual_execution_runbook_readiness_gate": (
                self.final_manual_execution_runbook_readiness_gate
                .safe_summary()
            ),
            "prepared_request": self.prepared_request.safe_summary(),
            "first_controlled_sandbox_attempt_preparation": (
                self.first_controlled_sandbox_attempt_preparation
            ),
            "first_controlled_attempt_checklist": (
                self.first_controlled_attempt_checklist
            ),
            "first_controlled_sandbox_attempt_preparation_defined": (
                self.first_controlled_sandbox_attempt_preparation_defined
            ),
            "final_manual_execution_runbook_readiness_gate_valid": (
                self.final_manual_execution_runbook_readiness_gate_valid
            ),
            "first_controlled_sandbox_attempt_preparation_valid": (
                self.first_controlled_sandbox_attempt_preparation_valid
            ),
            "ready_for_first_controlled_sandbox_attempt_review": (
                self.ready_for_first_controlled_sandbox_attempt_review
            ),
            "manual_operator_review_required": (
                self.manual_operator_review_required
            ),
            "sandbox_base_url_confirmation_required": (
                self.sandbox_base_url_confirmation_required
            ),
            "environment_secret_loading_only_required": (
                self.environment_secret_loading_only_required
            ),
            "no_production_credentials_required": (
                self.no_production_credentials_required
            ),
            "no_real_money_or_real_pix_flow_required": (
                self.no_real_money_or_real_pix_flow_required
            ),
            "sanitized_success_envelope_required": (
                self.sanitized_success_envelope_required
            ),
            "sanitized_error_envelope_required": (
                self.sanitized_error_envelope_required
            ),
            "redacted_logs_only_required": self.redacted_logs_only_required,
            "single_controlled_attempt_policy_required": (
                self.single_controlled_attempt_policy_required
            ),
            "no_retry_loop_required": self.no_retry_loop_required,
            "manual_stop_on_unexpected_response_required": (
                self.manual_stop_on_unexpected_response_required
            ),
            "raw_provider_payload_storage_allowed": (
                self.raw_provider_payload_storage_allowed
            ),
            "request_body_logging_allowed": (
                self.request_body_logging_allowed
            ),
            "stacktrace_exposure_allowed": self.stacktrace_exposure_allowed,
            "first_controlled_attempt_allows_adapter_implementation": (
                self.first_controlled_attempt_allows_adapter_implementation
            ),
            "first_controlled_attempt_allows_adapter_enablement": (
                self.first_controlled_attempt_allows_adapter_enablement
            ),
            "first_controlled_attempt_allows_http_execution": (
                self.first_controlled_attempt_allows_http_execution
            ),
            "first_controlled_attempt_can_emit_raw_payload": (
                self.first_controlled_attempt_can_emit_raw_payload
            ),
            "first_controlled_attempt_executed": (
                self.first_controlled_attempt_executed
            ),
            "adapter_shell_enabled": self.adapter_shell_enabled,
            "adapter_implemented": self.adapter_implemented,
            "adapter_enabled": self.adapter_enabled,
            "execution_enabled": self.execution_enabled,
            "can_send_http": self.can_send_http,
            "network_call_allowed": self.network_call_allowed,
            "real_money": self.real_money,
            "http_call_executed": self.http_call_executed,
            "sandbox_only": self.sandbox_only,
            "ready_for_http_execution": False,
            "next_step_required": (
                "operator_decision_before_any_real_sandbox_http_call"
            ),
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

    def build_subaccount_structure_guard(
        self,
    ) -> AsaasSandboxSubaccountStructureGuardResult:
        prepared_request = self._prepare(
            method="POST",
            path="/accounts",
            operation="create_subaccount_structure_guard",
            json=None,
        )

        return AsaasSandboxSubaccountStructureGuardResult(
            prepared_request=prepared_request,
        )

    def build_subaccount_payload_contract(
        self,
    ) -> AsaasSandboxSubaccountPayloadContractResult:
        structure_guard = self.build_subaccount_structure_guard()

        return AsaasSandboxSubaccountPayloadContractResult(
            structure_guard=structure_guard,
        )

    def build_subaccount_payload_builder_guard(
        self,
    ) -> AsaasSandboxSubaccountPayloadBuilderGuardResult:
        payload_contract = self.build_subaccount_payload_contract()
        sanitized_payload_template: dict[str, Any] = {
            "name": "<sandbox-subaccount-name>",
            "email": "<sandbox-subaccount-email>",
            "cpfCnpj": "<sandbox-subaccount-cpf-cnpj>",
            "mobilePhone": "<sandbox-subaccount-mobile-phone>",
            "incomeValue": 0,
            "address": "<sandbox-subaccount-address>",
            "addressNumber": "<sandbox-subaccount-address-number>",
            "province": "<sandbox-subaccount-province>",
            "postalCode": "<sandbox-subaccount-postal-code>",
        }
        prepared_request = self._prepare(
            method="POST",
            path="/accounts",
            operation="create_subaccount_payload_builder_guard",
            json=sanitized_payload_template,
        )

        return AsaasSandboxSubaccountPayloadBuilderGuardResult(
            payload_contract=payload_contract,
            prepared_request=prepared_request,
        )

    def build_subaccount_sanitized_fixture(
        self,
    ) -> AsaasSandboxSubaccountSanitizedFixtureResult:
        builder_guard = self.build_subaccount_payload_builder_guard()

        return AsaasSandboxSubaccountSanitizedFixtureResult(
            builder_guard=builder_guard,
        )

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

    def build_first_customer_http_blocked_adapter_contract(
        self,
        *,
        name: str,
        cpf_cnpj: str,
        email: str,
        mobile_phone: str,
        manual_authorization_phrase: str = "",
    ) -> AsaasFirstCustomerHttpBlockedAdapterContractResult:
        adapter_gate = self.gate_first_customer_http_transport_adapter(
            name=name,
            cpf_cnpj=cpf_cnpj,
            email=email,
            mobile_phone=mobile_phone,
            manual_authorization_phrase=manual_authorization_phrase,
        )

        return AsaasFirstCustomerHttpBlockedAdapterContractResult(
            prepared_request=adapter_gate.prepared_request,
            manual_authorization_registered=(
                adapter_gate.manual_authorization_registered
            ),
            access_token_header_configured=(
                adapter_gate.access_token_header_configured
            ),
            target_allowed=adapter_gate.target_allowed,
        )

    def build_first_customer_http_response_sanitizer_contract(
        self,
        *,
        name: str,
        cpf_cnpj: str,
        email: str,
        mobile_phone: str,
        manual_authorization_phrase: str = "",
    ) -> AsaasFirstCustomerHttpResponseSanitizerContractResult:
        blocked_adapter_contract = (
            self.build_first_customer_http_blocked_adapter_contract(
                name=name,
                cpf_cnpj=cpf_cnpj,
                email=email,
                mobile_phone=mobile_phone,
                manual_authorization_phrase=manual_authorization_phrase,
            )
        )

        return AsaasFirstCustomerHttpResponseSanitizerContractResult(
            blocked_adapter_contract=blocked_adapter_contract,
            manual_authorization_registered=(
                blocked_adapter_contract.manual_authorization_registered
            ),
            sandbox_only=blocked_adapter_contract.sandbox_only,
            adapter_implemented=blocked_adapter_contract.adapter_implemented,
            adapter_enabled=blocked_adapter_contract.adapter_enabled,
            can_send_http=blocked_adapter_contract.can_send_http,
            network_call_allowed=blocked_adapter_contract.network_call_allowed,
            real_money=blocked_adapter_contract.real_money,
            http_call_executed=blocked_adapter_contract.http_call_executed,
        )

    def build_first_customer_http_error_sanitizer_contract(
        self,
        *,
        name: str,
        cpf_cnpj: str,
        email: str,
        mobile_phone: str,
        manual_authorization_phrase: str = "",
    ) -> AsaasFirstCustomerHttpErrorSanitizerContractResult:
        response_sanitizer_contract = (
            self.build_first_customer_http_response_sanitizer_contract(
                name=name,
                cpf_cnpj=cpf_cnpj,
                email=email,
                mobile_phone=mobile_phone,
                manual_authorization_phrase=manual_authorization_phrase,
            )
        )

        return AsaasFirstCustomerHttpErrorSanitizerContractResult(
            response_sanitizer_contract=response_sanitizer_contract,
            manual_authorization_registered=(
                response_sanitizer_contract.manual_authorization_registered
            ),
            sandbox_only=response_sanitizer_contract.sandbox_only,
            adapter_implemented=response_sanitizer_contract.adapter_implemented,
            adapter_enabled=response_sanitizer_contract.adapter_enabled,
            can_send_http=response_sanitizer_contract.can_send_http,
            network_call_allowed=(
                response_sanitizer_contract.network_call_allowed
            ),
            real_money=response_sanitizer_contract.real_money,
            http_call_executed=response_sanitizer_contract.http_call_executed,
        )

    def gate_first_customer_http_manual_execution_approval(
        self,
        *,
        name: str,
        cpf_cnpj: str,
        email: str,
        mobile_phone: str,
        manual_authorization_phrase: str = "",
    ) -> AsaasFirstCustomerHttpManualExecutionApprovalGateResult:
        error_sanitizer_contract = (
            self.build_first_customer_http_error_sanitizer_contract(
                name=name,
                cpf_cnpj=cpf_cnpj,
                email=email,
                mobile_phone=mobile_phone,
                manual_authorization_phrase=manual_authorization_phrase,
            )
        )
        manual_execution_approval_registered = (
            error_sanitizer_contract.manual_authorization_registered
        )

        return AsaasFirstCustomerHttpManualExecutionApprovalGateResult(
            error_sanitizer_contract=error_sanitizer_contract,
            manual_execution_approval_registered=(
                manual_execution_approval_registered
            ),
            manual_execution_approval_valid=(
                manual_execution_approval_registered
            ),
            sandbox_only=error_sanitizer_contract.sandbox_only,
            adapter_implemented=error_sanitizer_contract.adapter_implemented,
            adapter_enabled=error_sanitizer_contract.adapter_enabled,
            can_send_http=error_sanitizer_contract.can_send_http,
            network_call_allowed=error_sanitizer_contract.network_call_allowed,
            real_money=error_sanitizer_contract.real_money,
            http_call_executed=error_sanitizer_contract.http_call_executed,
        )

    def build_first_customer_http_disabled_adapter_shell(
        self,
        *,
        name: str,
        cpf_cnpj: str,
        email: str,
        mobile_phone: str,
        manual_authorization_phrase: str = "",
    ) -> AsaasFirstCustomerHttpDisabledAdapterShellResult:
        manual_approval_gate = (
            self.gate_first_customer_http_manual_execution_approval(
                name=name,
                cpf_cnpj=cpf_cnpj,
                email=email,
                mobile_phone=mobile_phone,
                manual_authorization_phrase=manual_authorization_phrase,
            )
        )

        return AsaasFirstCustomerHttpDisabledAdapterShellResult(
            manual_approval_gate=manual_approval_gate,
            adapter_implemented=manual_approval_gate.adapter_implemented,
            adapter_enabled=manual_approval_gate.adapter_enabled,
            execution_enabled=manual_approval_gate.execution_enabled,
            can_send_http=manual_approval_gate.can_send_http,
            network_call_allowed=manual_approval_gate.network_call_allowed,
            real_money=manual_approval_gate.real_money,
            http_call_executed=manual_approval_gate.http_call_executed,
            sandbox_only=manual_approval_gate.sandbox_only,
        )

    def build_first_customer_http_explicit_enable_preflight(
        self,
        *,
        name: str,
        cpf_cnpj: str,
        email: str,
        mobile_phone: str,
        manual_authorization_phrase: str = "",
        explicit_enable_phrase: str = "",
    ) -> AsaasFirstCustomerHttpExplicitEnablePreflightResult:
        disabled_adapter_shell = (
            self.build_first_customer_http_disabled_adapter_shell(
                name=name,
                cpf_cnpj=cpf_cnpj,
                email=email,
                mobile_phone=mobile_phone,
                manual_authorization_phrase=manual_authorization_phrase,
            )
        )
        required_explicit_enable_phrase = (
            "CONFIRMO PREFLIGHT DE HABILITACAO EXPLICITA ASAAS SANDBOX, "
            "SEM PRODUCAO E SEM DINHEIRO REAL."
        )
        explicit_enable_phrase_registered = (
            explicit_enable_phrase == required_explicit_enable_phrase
        )
        manual_execution_approval_valid = (
            disabled_adapter_shell.manual_approval_gate
            .manual_execution_approval_valid
        )
        explicit_enable_preflight_valid = (
            explicit_enable_phrase_registered
            and manual_execution_approval_valid
            and disabled_adapter_shell.disabled_adapter_shell_defined
        )

        return AsaasFirstCustomerHttpExplicitEnablePreflightResult(
            disabled_adapter_shell=disabled_adapter_shell,
            required_explicit_enable_phrase=required_explicit_enable_phrase,
            explicit_enable_phrase_registered=(
                explicit_enable_phrase_registered
            ),
            manual_execution_approval_valid=manual_execution_approval_valid,
            disabled_adapter_shell_defined=(
                disabled_adapter_shell.disabled_adapter_shell_defined
            ),
            explicit_enable_preflight_valid=explicit_enable_preflight_valid,
            adapter_shell_enabled=disabled_adapter_shell.adapter_shell_enabled,
            adapter_implemented=disabled_adapter_shell.adapter_implemented,
            adapter_enabled=disabled_adapter_shell.adapter_enabled,
            execution_enabled=disabled_adapter_shell.execution_enabled,
            can_send_http=disabled_adapter_shell.can_send_http,
            network_call_allowed=disabled_adapter_shell.network_call_allowed,
            real_money=disabled_adapter_shell.real_money,
            http_call_executed=disabled_adapter_shell.http_call_executed,
            sandbox_only=disabled_adapter_shell.sandbox_only,
        )

    def build_first_customer_http_runtime_enable_contract(
        self,
        *,
        name: str,
        cpf_cnpj: str,
        email: str,
        mobile_phone: str,
        manual_authorization_phrase: str = "",
        explicit_enable_phrase: str = "",
        runtime_enable_phrase: str = "",
    ) -> AsaasFirstCustomerHttpRuntimeEnableContractResult:
        explicit_enable_preflight = (
            self.build_first_customer_http_explicit_enable_preflight(
                name=name,
                cpf_cnpj=cpf_cnpj,
                email=email,
                mobile_phone=mobile_phone,
                manual_authorization_phrase=manual_authorization_phrase,
                explicit_enable_phrase=explicit_enable_phrase,
            )
        )
        required_runtime_enable_phrase = (
            "CONFIRMO CONTRATO DE HABILITACAO RUNTIME ASAAS SANDBOX, "
            "SEM PRODUCAO E SEM DINHEIRO REAL."
        )
        runtime_enable_phrase_registered = (
            runtime_enable_phrase == required_runtime_enable_phrase
        )
        explicit_enable_preflight_valid = (
            explicit_enable_preflight.explicit_enable_preflight_valid
        )
        runtime_enable_contract_valid = (
            runtime_enable_phrase_registered
            and explicit_enable_preflight_valid
        )

        return AsaasFirstCustomerHttpRuntimeEnableContractResult(
            explicit_enable_preflight=explicit_enable_preflight,
            required_runtime_enable_phrase=required_runtime_enable_phrase,
            runtime_enable_phrase_registered=(
                runtime_enable_phrase_registered
            ),
            explicit_enable_preflight_valid=explicit_enable_preflight_valid,
            runtime_enable_contract_valid=runtime_enable_contract_valid,
            adapter_shell_enabled=explicit_enable_preflight.adapter_shell_enabled,
            adapter_implemented=explicit_enable_preflight.adapter_implemented,
            adapter_enabled=explicit_enable_preflight.adapter_enabled,
            execution_enabled=explicit_enable_preflight.execution_enabled,
            can_send_http=explicit_enable_preflight.can_send_http,
            network_call_allowed=explicit_enable_preflight.network_call_allowed,
            real_money=explicit_enable_preflight.real_money,
            http_call_executed=explicit_enable_preflight.http_call_executed,
            sandbox_only=explicit_enable_preflight.sandbox_only,
        )

    def build_first_customer_http_runtime_switch_guard(
        self,
        *,
        name: str,
        cpf_cnpj: str,
        email: str,
        mobile_phone: str,
        manual_authorization_phrase: str = "",
        explicit_enable_phrase: str = "",
        runtime_enable_phrase: str = "",
        runtime_switch_phrase: str = "",
    ) -> AsaasFirstCustomerHttpRuntimeSwitchGuardResult:
        runtime_enable_contract = (
            self.build_first_customer_http_runtime_enable_contract(
                name=name,
                cpf_cnpj=cpf_cnpj,
                email=email,
                mobile_phone=mobile_phone,
                manual_authorization_phrase=manual_authorization_phrase,
                explicit_enable_phrase=explicit_enable_phrase,
                runtime_enable_phrase=runtime_enable_phrase,
            )
        )
        required_runtime_switch_phrase = (
            "CONFIRMO GUARD DO SWITCH RUNTIME ASAAS SANDBOX, "
            "SEM PRODUCAO E SEM DINHEIRO REAL."
        )
        runtime_switch_phrase_registered = (
            runtime_switch_phrase == required_runtime_switch_phrase
        )
        runtime_enable_contract_valid = (
            runtime_enable_contract.runtime_enable_contract_valid
        )
        runtime_switch_guard_valid = (
            runtime_switch_phrase_registered
            and runtime_enable_contract_valid
        )

        return AsaasFirstCustomerHttpRuntimeSwitchGuardResult(
            runtime_enable_contract=runtime_enable_contract,
            required_runtime_switch_phrase=required_runtime_switch_phrase,
            runtime_switch_phrase_registered=(
                runtime_switch_phrase_registered
            ),
            runtime_enable_contract_valid=runtime_enable_contract_valid,
            runtime_switch_guard_valid=runtime_switch_guard_valid,
            runtime_switch_requested=runtime_switch_phrase_registered,
            adapter_shell_enabled=runtime_enable_contract.adapter_shell_enabled,
            adapter_implemented=runtime_enable_contract.adapter_implemented,
            adapter_enabled=runtime_enable_contract.adapter_enabled,
            execution_enabled=runtime_enable_contract.execution_enabled,
            can_send_http=runtime_enable_contract.can_send_http,
            network_call_allowed=runtime_enable_contract.network_call_allowed,
            real_money=runtime_enable_contract.real_money,
            http_call_executed=runtime_enable_contract.http_call_executed,
            sandbox_only=runtime_enable_contract.sandbox_only,
        )

    def build_first_customer_http_execution_gate_contract(
        self,
        *,
        name: str,
        cpf_cnpj: str,
        email: str,
        mobile_phone: str,
        manual_authorization_phrase: str = "",
        explicit_enable_phrase: str = "",
        runtime_enable_phrase: str = "",
        runtime_switch_phrase: str = "",
        execution_gate_phrase: str = "",
    ) -> AsaasFirstCustomerHttpExecutionGateContractResult:
        runtime_switch_guard = (
            self.build_first_customer_http_runtime_switch_guard(
                name=name,
                cpf_cnpj=cpf_cnpj,
                email=email,
                mobile_phone=mobile_phone,
                manual_authorization_phrase=manual_authorization_phrase,
                explicit_enable_phrase=explicit_enable_phrase,
                runtime_enable_phrase=runtime_enable_phrase,
                runtime_switch_phrase=runtime_switch_phrase,
            )
        )
        required_execution_gate_phrase = (
            "CONFIRMO CONTRATO DO GATE DE EXECUCAO ASAAS SANDBOX, "
            "SEM PRODUCAO E SEM DINHEIRO REAL."
        )
        execution_gate_phrase_registered = (
            execution_gate_phrase == required_execution_gate_phrase
        )
        runtime_switch_guard_valid = (
            runtime_switch_guard.runtime_switch_guard_valid
        )
        execution_gate_contract_valid = (
            execution_gate_phrase_registered
            and runtime_switch_guard_valid
        )

        return AsaasFirstCustomerHttpExecutionGateContractResult(
            runtime_switch_guard=runtime_switch_guard,
            required_execution_gate_phrase=required_execution_gate_phrase,
            execution_gate_phrase_registered=(
                execution_gate_phrase_registered
            ),
            runtime_switch_guard_valid=runtime_switch_guard_valid,
            execution_gate_contract_valid=execution_gate_contract_valid,
            adapter_shell_enabled=runtime_switch_guard.adapter_shell_enabled,
            adapter_implemented=runtime_switch_guard.adapter_implemented,
            adapter_enabled=runtime_switch_guard.adapter_enabled,
            execution_enabled=runtime_switch_guard.execution_enabled,
            can_send_http=runtime_switch_guard.can_send_http,
            network_call_allowed=runtime_switch_guard.network_call_allowed,
            real_money=runtime_switch_guard.real_money,
            http_call_executed=runtime_switch_guard.http_call_executed,
            sandbox_only=runtime_switch_guard.sandbox_only,
        )

    def build_first_customer_http_sanitized_execution_handler_contract(
        self,
        *,
        name: str,
        cpf_cnpj: str,
        email: str,
        mobile_phone: str,
        manual_authorization_phrase: str = "",
        explicit_enable_phrase: str = "",
        runtime_enable_phrase: str = "",
        runtime_switch_phrase: str = "",
        execution_gate_phrase: str = "",
    ) -> AsaasFirstCustomerHttpSanitizedExecutionHandlerContractResult:
        execution_gate_contract = (
            self.build_first_customer_http_execution_gate_contract(
                name=name,
                cpf_cnpj=cpf_cnpj,
                email=email,
                mobile_phone=mobile_phone,
                manual_authorization_phrase=manual_authorization_phrase,
                explicit_enable_phrase=explicit_enable_phrase,
                runtime_enable_phrase=runtime_enable_phrase,
                runtime_switch_phrase=runtime_switch_phrase,
                execution_gate_phrase=execution_gate_phrase,
            )
        )
        execution_gate_contract_valid = (
            execution_gate_contract.execution_gate_contract_valid
        )

        return AsaasFirstCustomerHttpSanitizedExecutionHandlerContractResult(
            execution_gate_contract=execution_gate_contract,
            execution_gate_contract_valid=execution_gate_contract_valid,
            adapter_shell_enabled=execution_gate_contract.adapter_shell_enabled,
            adapter_implemented=execution_gate_contract.adapter_implemented,
            adapter_enabled=execution_gate_contract.adapter_enabled,
            execution_enabled=execution_gate_contract.execution_enabled,
            can_send_http=execution_gate_contract.can_send_http,
            network_call_allowed=execution_gate_contract.network_call_allowed,
            real_money=execution_gate_contract.real_money,
            http_call_executed=execution_gate_contract.http_call_executed,
            sandbox_only=execution_gate_contract.sandbox_only,
        )

    def build_first_customer_http_sanitized_result_envelope_contract(
        self,
        *,
        name: str,
        cpf_cnpj: str,
        email: str,
        mobile_phone: str,
        manual_authorization_phrase: str = "",
        explicit_enable_phrase: str = "",
        runtime_enable_phrase: str = "",
        runtime_switch_phrase: str = "",
        execution_gate_phrase: str = "",
    ) -> AsaasFirstCustomerHttpSanitizedResultEnvelopeContractResult:
        sanitized_execution_handler_contract = (
            self.build_first_customer_http_sanitized_execution_handler_contract(
                name=name,
                cpf_cnpj=cpf_cnpj,
                email=email,
                mobile_phone=mobile_phone,
                manual_authorization_phrase=manual_authorization_phrase,
                explicit_enable_phrase=explicit_enable_phrase,
                runtime_enable_phrase=runtime_enable_phrase,
                runtime_switch_phrase=runtime_switch_phrase,
                execution_gate_phrase=execution_gate_phrase,
            )
        )
        sanitized_execution_handler_contract_valid = (
            sanitized_execution_handler_contract.execution_gate_contract_valid
        )

        return AsaasFirstCustomerHttpSanitizedResultEnvelopeContractResult(
            sanitized_execution_handler_contract=(
                sanitized_execution_handler_contract
            ),
            sanitized_execution_handler_contract_valid=(
                sanitized_execution_handler_contract_valid
            ),
            adapter_shell_enabled=(
                sanitized_execution_handler_contract.adapter_shell_enabled
            ),
            adapter_implemented=(
                sanitized_execution_handler_contract.adapter_implemented
            ),
            adapter_enabled=sanitized_execution_handler_contract.adapter_enabled,
            execution_enabled=(
                sanitized_execution_handler_contract.execution_enabled
            ),
            can_send_http=sanitized_execution_handler_contract.can_send_http,
            network_call_allowed=(
                sanitized_execution_handler_contract.network_call_allowed
            ),
            real_money=sanitized_execution_handler_contract.real_money,
            http_call_executed=(
                sanitized_execution_handler_contract.http_call_executed
            ),
            sandbox_only=sanitized_execution_handler_contract.sandbox_only,
        )

    def build_first_customer_http_sanitized_success_error_fixture_contract(
        self,
        *,
        name: str,
        cpf_cnpj: str,
        email: str,
        mobile_phone: str,
        manual_authorization_phrase: str = "",
        explicit_enable_phrase: str = "",
        runtime_enable_phrase: str = "",
        runtime_switch_phrase: str = "",
        execution_gate_phrase: str = "",
    ) -> AsaasFirstCustomerHttpSanitizedSuccessErrorFixtureContractResult:
        sanitized_result_envelope_contract = (
            self.build_first_customer_http_sanitized_result_envelope_contract(
                name=name,
                cpf_cnpj=cpf_cnpj,
                email=email,
                mobile_phone=mobile_phone,
                manual_authorization_phrase=manual_authorization_phrase,
                explicit_enable_phrase=explicit_enable_phrase,
                runtime_enable_phrase=runtime_enable_phrase,
                runtime_switch_phrase=runtime_switch_phrase,
                execution_gate_phrase=execution_gate_phrase,
            )
        )
        sanitized_result_envelope_contract_valid = (
            sanitized_result_envelope_contract
            .sanitized_execution_handler_contract_valid
        )

        return AsaasFirstCustomerHttpSanitizedSuccessErrorFixtureContractResult(
            sanitized_result_envelope_contract=(
                sanitized_result_envelope_contract
            ),
            sanitized_result_envelope_contract_valid=(
                sanitized_result_envelope_contract_valid
            ),
            adapter_shell_enabled=(
                sanitized_result_envelope_contract.adapter_shell_enabled
            ),
            adapter_implemented=(
                sanitized_result_envelope_contract.adapter_implemented
            ),
            adapter_enabled=sanitized_result_envelope_contract.adapter_enabled,
            execution_enabled=(
                sanitized_result_envelope_contract.execution_enabled
            ),
            can_send_http=sanitized_result_envelope_contract.can_send_http,
            network_call_allowed=(
                sanitized_result_envelope_contract.network_call_allowed
            ),
            real_money=sanitized_result_envelope_contract.real_money,
            http_call_executed=(
                sanitized_result_envelope_contract.http_call_executed
            ),
            sandbox_only=sanitized_result_envelope_contract.sandbox_only,
        )

    def build_first_customer_http_adapter_boundary_final_contract(
        self,
        *,
        name: str,
        cpf_cnpj: str,
        email: str,
        mobile_phone: str,
        manual_authorization_phrase: str = "",
        explicit_enable_phrase: str = "",
        runtime_enable_phrase: str = "",
        runtime_switch_phrase: str = "",
        execution_gate_phrase: str = "",
    ) -> AsaasFirstCustomerHttpAdapterBoundaryFinalContractResult:
        fixture_contract = (
            self.build_first_customer_http_sanitized_success_error_fixture_contract(
                name=name,
                cpf_cnpj=cpf_cnpj,
                email=email,
                mobile_phone=mobile_phone,
                manual_authorization_phrase=manual_authorization_phrase,
                explicit_enable_phrase=explicit_enable_phrase,
                runtime_enable_phrase=runtime_enable_phrase,
                runtime_switch_phrase=runtime_switch_phrase,
                execution_gate_phrase=execution_gate_phrase,
            )
        )
        fixture_chain_valid = (
            fixture_contract.sanitized_result_envelope_contract_valid
        )
        fixtures_match_envelope = (
            fixture_contract.sanitized_fixtures_match_envelope_contract
        )
        final_contract_valid = fixture_chain_valid and fixtures_match_envelope

        return AsaasFirstCustomerHttpAdapterBoundaryFinalContractResult(
            sanitized_success_error_fixture_contract=fixture_contract,
            sanitized_success_error_fixture_contract_valid=(
                final_contract_valid
            ),
            adapter_boundary_final_contract_valid=final_contract_valid,
            adapter_shell_enabled=fixture_contract.adapter_shell_enabled,
            adapter_implemented=fixture_contract.adapter_implemented,
            adapter_enabled=fixture_contract.adapter_enabled,
            execution_enabled=fixture_contract.execution_enabled,
            can_send_http=fixture_contract.can_send_http,
            network_call_allowed=fixture_contract.network_call_allowed,
            real_money=fixture_contract.real_money,
            http_call_executed=fixture_contract.http_call_executed,
            sandbox_only=fixture_contract.sandbox_only,
        )

    def build_first_customer_http_final_manual_execution_runbook_readiness_gate(
        self,
        *,
        name: str,
        cpf_cnpj: str,
        email: str,
        mobile_phone: str,
        manual_authorization_phrase: str = "",
        explicit_enable_phrase: str = "",
        runtime_enable_phrase: str = "",
        runtime_switch_phrase: str = "",
        execution_gate_phrase: str = "",
    ) -> AsaasFirstCustomerHttpFinalManualExecutionRunbookReadinessGateResult:
        adapter_boundary = (
            self.build_first_customer_http_adapter_boundary_final_contract(
                name=name,
                cpf_cnpj=cpf_cnpj,
                email=email,
                mobile_phone=mobile_phone,
                manual_authorization_phrase=manual_authorization_phrase,
                explicit_enable_phrase=explicit_enable_phrase,
                runtime_enable_phrase=runtime_enable_phrase,
                runtime_switch_phrase=runtime_switch_phrase,
                execution_gate_phrase=execution_gate_phrase,
            )
        )
        adapter_boundary_valid = (
            adapter_boundary.adapter_boundary_final_contract_valid
        )

        return AsaasFirstCustomerHttpFinalManualExecutionRunbookReadinessGateResult(
            adapter_boundary_final_contract=adapter_boundary,
            adapter_boundary_final_contract_valid=adapter_boundary_valid,
            final_manual_execution_runbook_readiness_gate_valid=(
                adapter_boundary_valid
            ),
            ready_for_manual_execution_review=adapter_boundary_valid,
            adapter_shell_enabled=adapter_boundary.adapter_shell_enabled,
            adapter_implemented=adapter_boundary.adapter_implemented,
            adapter_enabled=adapter_boundary.adapter_enabled,
            execution_enabled=adapter_boundary.execution_enabled,
            can_send_http=adapter_boundary.can_send_http,
            network_call_allowed=adapter_boundary.network_call_allowed,
            real_money=adapter_boundary.real_money,
            http_call_executed=adapter_boundary.http_call_executed,
            sandbox_only=adapter_boundary.sandbox_only,
        )

    def build_first_customer_http_first_controlled_sandbox_attempt_preparation(
        self,
        *,
        name: str,
        cpf_cnpj: str,
        email: str,
        mobile_phone: str,
        manual_authorization_phrase: str = "",
        explicit_enable_phrase: str = "",
        runtime_enable_phrase: str = "",
        runtime_switch_phrase: str = "",
        execution_gate_phrase: str = "",
    ) -> AsaasFirstCustomerHttpFirstControlledSandboxAttemptPreparationResult:
        readiness_gate = (
            self
            .build_first_customer_http_final_manual_execution_runbook_readiness_gate(
                name=name,
                cpf_cnpj=cpf_cnpj,
                email=email,
                mobile_phone=mobile_phone,
                manual_authorization_phrase=manual_authorization_phrase,
                explicit_enable_phrase=explicit_enable_phrase,
                runtime_enable_phrase=runtime_enable_phrase,
                runtime_switch_phrase=runtime_switch_phrase,
                execution_gate_phrase=execution_gate_phrase,
            )
        )
        readiness_gate_valid = (
            readiness_gate
            .final_manual_execution_runbook_readiness_gate_valid
        )

        return AsaasFirstCustomerHttpFirstControlledSandboxAttemptPreparationResult(
            final_manual_execution_runbook_readiness_gate=readiness_gate,
            final_manual_execution_runbook_readiness_gate_valid=(
                readiness_gate_valid
            ),
            first_controlled_sandbox_attempt_preparation_valid=(
                readiness_gate_valid
            ),
            ready_for_first_controlled_sandbox_attempt_review=(
                readiness_gate_valid
            ),
            adapter_shell_enabled=readiness_gate.adapter_shell_enabled,
            adapter_implemented=readiness_gate.adapter_implemented,
            adapter_enabled=readiness_gate.adapter_enabled,
            execution_enabled=readiness_gate.execution_enabled,
            can_send_http=readiness_gate.can_send_http,
            network_call_allowed=readiness_gate.network_call_allowed,
            real_money=readiness_gate.real_money,
            http_call_executed=readiness_gate.http_call_executed,
            sandbox_only=readiness_gate.sandbox_only,
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
