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
