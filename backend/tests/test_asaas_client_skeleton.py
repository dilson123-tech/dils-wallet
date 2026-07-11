from decimal import Decimal

import pytest

from app.partner.asaas_client import AsaasSandboxClient
from app.partner.asaas_config import (
    ASAAS_SANDBOX_BASE_URL,
    ASAAS_SANDBOX_MANUAL_AUTHORIZATION_PHRASE,
    AsaasSandboxConfig,
)


TEST_CONFIG = AsaasSandboxConfig(
    env="sandbox",
    base_url=ASAAS_SANDBOX_BASE_URL,
    api_key="sandbox-api-key-for-test-only",
    webhook_token="sandbox-webhook-token-for-test-only",
    real_money_enabled=False,
    wallet_mode="partner",
    wallet_partner_provider="asaas",
)


def make_client() -> AsaasSandboxClient:
    return AsaasSandboxClient(config=TEST_CONFIG)


def test_prepare_create_customer_builds_sandbox_request_without_http_call():
    client = make_client()

    request = client.prepare_create_customer(
        name="Cliente Sandbox Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.sandbox@example.com",
        mobile_phone="11999999999",
    )

    assert request.method == "POST"
    assert request.url == f"{ASAAS_SANDBOX_BASE_URL}/customers"
    assert request.operation == "create_customer"
    assert request.headers_configured is True
    assert request.real_money is False
    assert request.http_call_executed is False
    assert request.json == {
        "name": "Cliente Sandbox Aurea Gold",
        "cpfCnpj": "12345678909",
        "email": "cliente.sandbox@example.com",
        "mobilePhone": "11999999999",
    }


def test_first_customer_http_client_gate_prepares_customer_request_without_http_call():
    client = make_client()

    gate = client.gate_first_customer_http_call(
        name="Cliente Gate Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.gate@example.com",
        mobile_phone="11999999999",
    )

    request = gate.prepared_request

    assert gate.customer_reference == "first-customer-http-client-gate-sandbox"
    assert gate.manual_authorization_registered is False
    assert gate.http_transport_enabled is False
    assert gate.real_money is False
    assert gate.http_call_executed is False

    assert request.method == "POST"
    assert request.url == f"{ASAAS_SANDBOX_BASE_URL}/customers"
    assert request.operation == "create_customer"
    assert request.real_money is False
    assert request.http_call_executed is False
    assert request.json == {
        "name": "Cliente Gate Aurea Gold",
        "cpfCnpj": "12345678909",
        "email": "cliente.gate@example.com",
        "mobilePhone": "11999999999",
    }


def test_first_customer_http_client_gate_recognizes_manual_phrase_but_keeps_transport_off():
    client = make_client()

    gate = client.gate_first_customer_http_call(
        name="Cliente Gate Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.gate@example.com",
        mobile_phone="11999999999",
        manual_authorization_phrase=ASAAS_SANDBOX_MANUAL_AUTHORIZATION_PHRASE,
    )

    summary = gate.safe_summary()

    assert gate.manual_authorization_registered is True
    assert summary["operation"] == "first_customer_http_client_gate"
    assert summary["manual_authorization_registered"] is True
    assert summary["http_transport_enabled"] is False
    assert summary["ready_for_http_execution"] is False
    assert summary["real_money"] is False
    assert summary["http_call_executed"] is False
    assert summary["prepared_request"]["operation"] == "create_customer"
    assert summary["prepared_request"]["http_call_executed"] is False
    assert "sandbox-api-key-for-test-only" not in repr(summary)
    assert "sandbox-webhook-token-for-test-only" not in repr(summary)


def test_first_customer_http_transport_skeleton_is_built_without_http_execution():
    client = make_client()

    transport = client.build_first_customer_http_transport_skeleton(
        name="Cliente Transport Skeleton Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.transport@example.com",
        mobile_phone="11999999999",
    )

    request = transport.prepared_request

    assert transport.transport_reference == (
        "first-customer-http-transport-skeleton-sandbox"
    )
    assert transport.manual_authorization_registered is False
    assert transport.access_token_header_configured is True
    assert transport.timeout_seconds == 30
    assert transport.retry_enabled is False
    assert transport.http_transport_implemented is False
    assert transport.http_transport_enabled is False
    assert transport.real_money is False
    assert transport.http_call_executed is False

    assert request.method == "POST"
    assert request.url == f"{ASAAS_SANDBOX_BASE_URL}/customers"
    assert request.operation == "create_customer"
    assert request.real_money is False
    assert request.http_call_executed is False
    assert request.json == {
        "name": "Cliente Transport Skeleton Aurea Gold",
        "cpfCnpj": "12345678909",
        "email": "cliente.transport@example.com",
        "mobilePhone": "11999999999",
    }


def test_first_customer_http_transport_skeleton_safe_summary_hides_secrets():
    client = make_client()

    transport = client.build_first_customer_http_transport_skeleton(
        name="Cliente Transport Skeleton Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.transport@example.com",
        mobile_phone="11999999999",
        manual_authorization_phrase=ASAAS_SANDBOX_MANUAL_AUTHORIZATION_PHRASE,
    )

    summary = transport.safe_summary()

    assert transport.manual_authorization_registered is True
    assert summary["operation"] == "first_customer_http_transport_skeleton"
    assert summary["manual_authorization_registered"] is True
    assert summary["access_token_header_configured"] is True
    assert summary["retry_enabled"] is False
    assert summary["http_transport_implemented"] is False
    assert summary["http_transport_enabled"] is False
    assert summary["ready_for_http_execution"] is False
    assert summary["real_money"] is False
    assert summary["http_call_executed"] is False
    assert summary["prepared_request"]["operation"] == "create_customer"
    assert summary["prepared_request"]["http_call_executed"] is False
    assert "sandbox-api-key-for-test-only" not in repr(summary)
    assert "sandbox-webhook-token-for-test-only" not in repr(summary)


def test_first_customer_http_transport_adapter_gate_stays_blocked():
    client = make_client()

    adapter = client.gate_first_customer_http_transport_adapter(
        name="Cliente Adapter Gate Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.adapter@example.com",
        mobile_phone="11999999999",
    )

    request = adapter.prepared_request

    assert adapter.adapter_reference == (
        "first-customer-http-transport-adapter-gate-sandbox"
    )
    assert adapter.adapter_name == "blocked_sandbox_manual_http_adapter"
    assert adapter.manual_authorization_registered is False
    assert adapter.access_token_header_configured is True
    assert adapter.sandbox_only is True
    assert adapter.target_allowed is True
    assert adapter.adapter_implemented is False
    assert adapter.adapter_enabled is False
    assert adapter.can_send_http is False
    assert adapter.retry_enabled is False
    assert adapter.real_money is False
    assert adapter.http_call_executed is False

    assert request.method == "POST"
    assert request.url == f"{ASAAS_SANDBOX_BASE_URL}/customers"
    assert request.operation == "create_customer"
    assert request.real_money is False
    assert request.http_call_executed is False
    assert request.json == {
        "name": "Cliente Adapter Gate Aurea Gold",
        "cpfCnpj": "12345678909",
        "email": "cliente.adapter@example.com",
        "mobilePhone": "11999999999",
    }


def test_first_customer_http_transport_adapter_gate_recognizes_phrase_but_cannot_send():
    client = make_client()

    adapter = client.gate_first_customer_http_transport_adapter(
        name="Cliente Adapter Gate Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.adapter@example.com",
        mobile_phone="11999999999",
        manual_authorization_phrase=ASAAS_SANDBOX_MANUAL_AUTHORIZATION_PHRASE,
    )

    summary = adapter.safe_summary()

    assert adapter.manual_authorization_registered is True
    assert summary["operation"] == "first_customer_http_transport_adapter_gate"
    assert summary["manual_authorization_registered"] is True
    assert summary["access_token_header_configured"] is True
    assert summary["sandbox_only"] is True
    assert summary["target_allowed"] is True
    assert summary["adapter_implemented"] is False
    assert summary["adapter_enabled"] is False
    assert summary["can_send_http"] is False
    assert summary["retry_enabled"] is False
    assert summary["ready_for_http_execution"] is False
    assert summary["real_money"] is False
    assert summary["http_call_executed"] is False
    assert summary["prepared_request"]["operation"] == "create_customer"
    assert summary["prepared_request"]["http_call_executed"] is False
    assert "sandbox-api-key-for-test-only" not in repr(summary)
    assert "sandbox-webhook-token-for-test-only" not in repr(summary)


def test_first_customer_http_blocked_adapter_contract_stays_blocked():
    client = make_client()

    contract = client.build_first_customer_http_blocked_adapter_contract(
        name="Cliente Blocked Adapter Contract Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.contract@example.com",
        mobile_phone="11999999999",
    )

    request = contract.prepared_request

    assert contract.contract_reference == (
        "first-customer-http-blocked-adapter-contract-sandbox"
    )
    assert contract.adapter_name == (
        "blocked_sandbox_first_customer_http_adapter_contract"
    )
    assert contract.manual_authorization_registered is False
    assert contract.access_token_header_configured is True
    assert contract.sandbox_only is True
    assert contract.target_allowed is True
    assert contract.adapter_implemented is False
    assert contract.adapter_enabled is False
    assert contract.can_send_http is False
    assert contract.network_call_allowed is False
    assert contract.retry_enabled is False
    assert contract.real_money is False
    assert contract.http_call_executed is False

    assert contract.request_contract == {
        "method": "POST",
        "path": "/customers",
        "operation": "create_customer",
        "required_header_names": ["access_token"],
        "sensitive_header_values_masked": True,
        "required_json_fields": ["name", "cpfCnpj", "email", "mobilePhone"],
    }
    assert contract.response_contract["expected_success_statuses"] == [200, 201]
    assert contract.response_contract["raw_response_blocked"] is True
    assert contract.response_contract["secret_values_allowed"] is False
    assert contract.error_contract["raw_error_blocked"] is True
    assert contract.error_contract["secret_values_allowed"] is False

    assert request.method == "POST"
    assert request.url == f"{ASAAS_SANDBOX_BASE_URL}/customers"
    assert request.operation == "create_customer"
    assert request.real_money is False
    assert request.http_call_executed is False
    assert request.json == {
        "name": "Cliente Blocked Adapter Contract Aurea Gold",
        "cpfCnpj": "12345678909",
        "email": "cliente.contract@example.com",
        "mobilePhone": "11999999999",
    }


def test_first_customer_http_blocked_adapter_contract_recognizes_phrase_but_cannot_send():
    client = make_client()

    contract = client.build_first_customer_http_blocked_adapter_contract(
        name="Cliente Blocked Adapter Contract Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.contract@example.com",
        mobile_phone="11999999999",
        manual_authorization_phrase=ASAAS_SANDBOX_MANUAL_AUTHORIZATION_PHRASE,
    )

    summary = contract.safe_summary()

    assert contract.manual_authorization_registered is True
    assert summary["operation"] == "first_customer_http_blocked_adapter_contract"
    assert summary["manual_authorization_registered"] is True
    assert summary["access_token_header_configured"] is True
    assert summary["sandbox_only"] is True
    assert summary["target_allowed"] is True
    assert summary["adapter_implemented"] is False
    assert summary["adapter_enabled"] is False
    assert summary["can_send_http"] is False
    assert summary["network_call_allowed"] is False
    assert summary["retry_enabled"] is False
    assert summary["ready_for_http_execution"] is False
    assert summary["real_money"] is False
    assert summary["http_call_executed"] is False
    assert summary["request_contract"]["path"] == "/customers"
    assert summary["response_contract"]["raw_response_blocked"] is True
    assert summary["error_contract"]["raw_error_blocked"] is True
    assert summary["prepared_request"]["operation"] == "create_customer"
    assert summary["prepared_request"]["http_call_executed"] is False
    assert "sandbox-api-key-for-test-only" not in repr(summary)
    assert "sandbox-webhook-token-for-test-only" not in repr(summary)


def test_first_customer_http_response_sanitizer_contract_stays_blocked():
    client = make_client()

    sanitizer = client.build_first_customer_http_response_sanitizer_contract(
        name="Cliente Response Sanitizer Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.sanitizer@example.com",
        mobile_phone="11999999999",
    )

    request = sanitizer.prepared_request
    success_contract = sanitizer.success_sanitizer_contract
    error_contract = sanitizer.error_sanitizer_contract

    assert sanitizer.sanitizer_reference == (
        "first-customer-http-response-sanitizer-contract-sandbox"
    )
    assert sanitizer.sanitizer_contract_defined is True
    assert sanitizer.sanitizer_implemented is False
    assert sanitizer.raw_response_retained is False
    assert sanitizer.raw_error_retained is False
    assert sanitizer.manual_authorization_registered is False
    assert sanitizer.sandbox_only is True
    assert sanitizer.adapter_implemented is False
    assert sanitizer.adapter_enabled is False
    assert sanitizer.can_send_http is False
    assert sanitizer.network_call_allowed is False
    assert sanitizer.real_money is False
    assert sanitizer.http_call_executed is False

    assert success_contract["allowed_fields"] == [
        "id",
        "name",
        "cpfCnpj",
        "email",
        "mobilePhone",
    ]
    assert "access_token" in success_contract["blocked_fields"]
    assert "api_key" in success_contract["blocked_fields"]
    assert "webhook_token" in success_contract["blocked_fields"]
    assert "wallet_id" in success_contract["blocked_fields"]
    assert "raw" in success_contract["blocked_fields"]
    assert success_contract["raw_response_allowed"] is False
    assert success_contract["secret_values_allowed"] is False
    assert success_contract["safe_fields_only"] is True

    assert error_contract["allowed_fields"] == [
        "status_code",
        "provider_error_code",
        "safe_message",
        "retryable",
    ]
    assert "access_token" in error_contract["blocked_fields"]
    assert "api_key" in error_contract["blocked_fields"]
    assert "webhook_token" in error_contract["blocked_fields"]
    assert "wallet_id" in error_contract["blocked_fields"]
    assert "provider_raw" in error_contract["blocked_fields"]
    assert "stacktrace" in error_contract["blocked_fields"]
    assert error_contract["raw_error_allowed"] is False
    assert error_contract["secret_values_allowed"] is False
    assert error_contract["safe_fields_only"] is True

    assert request.method == "POST"
    assert request.url == f"{ASAAS_SANDBOX_BASE_URL}/customers"
    assert request.operation == "create_customer"
    assert request.real_money is False
    assert request.http_call_executed is False
    assert request.json == {
        "name": "Cliente Response Sanitizer Aurea Gold",
        "cpfCnpj": "12345678909",
        "email": "cliente.sanitizer@example.com",
        "mobilePhone": "11999999999",
    }


def test_first_customer_http_response_sanitizer_contract_recognizes_phrase_but_cannot_send():
    client = make_client()

    sanitizer = client.build_first_customer_http_response_sanitizer_contract(
        name="Cliente Response Sanitizer Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.sanitizer@example.com",
        mobile_phone="11999999999",
        manual_authorization_phrase=ASAAS_SANDBOX_MANUAL_AUTHORIZATION_PHRASE,
    )

    summary = sanitizer.safe_summary()

    assert sanitizer.manual_authorization_registered is True
    assert summary["operation"] == "first_customer_http_response_sanitizer_contract"
    assert summary["manual_authorization_registered"] is True
    assert summary["sanitizer_contract_defined"] is True
    assert summary["sanitizer_implemented"] is False
    assert summary["raw_response_retained"] is False
    assert summary["raw_error_retained"] is False
    assert summary["sandbox_only"] is True
    assert summary["adapter_implemented"] is False
    assert summary["adapter_enabled"] is False
    assert summary["can_send_http"] is False
    assert summary["network_call_allowed"] is False
    assert summary["ready_for_http_execution"] is False
    assert summary["real_money"] is False
    assert summary["http_call_executed"] is False
    assert summary["success_sanitizer_contract"]["raw_response_allowed"] is False
    assert summary["error_sanitizer_contract"]["raw_error_allowed"] is False
    assert summary["blocked_adapter_contract"]["operation"] == (
        "first_customer_http_blocked_adapter_contract"
    )
    assert summary["prepared_request"]["operation"] == "create_customer"
    assert summary["prepared_request"]["http_call_executed"] is False
    assert "sandbox-api-key-for-test-only" not in repr(summary)
    assert "sandbox-webhook-token-for-test-only" not in repr(summary)
    assert "access_token" not in repr(summary["prepared_request"])
    assert "provider_raw_response" not in repr(summary)
    assert "provider_raw_error" not in repr(summary)


def test_first_customer_http_error_sanitizer_contract_stays_blocked():
    client = make_client()

    sanitizer = client.build_first_customer_http_error_sanitizer_contract(
        name="Cliente Error Sanitizer Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.error.sanitizer@example.com",
        mobile_phone="11999999999",
    )

    request = sanitizer.prepared_request
    safe_error_shape = sanitizer.safe_error_shape

    assert sanitizer.error_sanitizer_reference == (
        "first-customer-http-error-sanitizer-contract-sandbox"
    )
    assert sanitizer.error_sanitizer_contract_defined is True
    assert sanitizer.error_sanitizer_implemented is False
    assert sanitizer.raw_error_retained is False
    assert sanitizer.provider_raw_error_retained is False
    assert sanitizer.stacktrace_retained is False
    assert sanitizer.manual_authorization_registered is False
    assert sanitizer.sandbox_only is True
    assert sanitizer.adapter_implemented is False
    assert sanitizer.adapter_enabled is False
    assert sanitizer.can_send_http is False
    assert sanitizer.network_call_allowed is False
    assert sanitizer.real_money is False
    assert sanitizer.http_call_executed is False

    assert safe_error_shape["allowed_fields"] == [
        "status_code",
        "provider_error_code",
        "safe_message",
        "retryable",
        "category",
    ]
    assert "access_token" in safe_error_shape["blocked_fields"]
    assert "api_key" in safe_error_shape["blocked_fields"]
    assert "webhook_token" in safe_error_shape["blocked_fields"]
    assert "wallet_id" in safe_error_shape["blocked_fields"]
    assert "headers" in safe_error_shape["blocked_fields"]
    assert "raw" in safe_error_shape["blocked_fields"]
    assert "provider_raw" in safe_error_shape["blocked_fields"]
    assert "stacktrace" in safe_error_shape["blocked_fields"]
    assert "request_body" in safe_error_shape["blocked_fields"]
    assert safe_error_shape["raw_error_allowed"] is False
    assert safe_error_shape["provider_raw_error_allowed"] is False
    assert safe_error_shape["stacktrace_allowed"] is False
    assert safe_error_shape["secret_values_allowed"] is False
    assert safe_error_shape["safe_fields_only"] is True

    assert request.method == "POST"
    assert request.url == f"{ASAAS_SANDBOX_BASE_URL}/customers"
    assert request.operation == "create_customer"
    assert request.real_money is False
    assert request.http_call_executed is False


def test_first_customer_http_error_sanitizer_contract_recognizes_phrase_but_cannot_send():
    client = make_client()

    sanitizer = client.build_first_customer_http_error_sanitizer_contract(
        name="Cliente Error Sanitizer Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.error.sanitizer@example.com",
        mobile_phone="11999999999",
        manual_authorization_phrase=ASAAS_SANDBOX_MANUAL_AUTHORIZATION_PHRASE,
    )

    summary = sanitizer.safe_summary()

    assert sanitizer.manual_authorization_registered is True
    assert summary["operation"] == "first_customer_http_error_sanitizer_contract"
    assert summary["manual_authorization_registered"] is True
    assert summary["error_sanitizer_contract_defined"] is True
    assert summary["error_sanitizer_implemented"] is False
    assert summary["raw_error_retained"] is False
    assert summary["provider_raw_error_retained"] is False
    assert summary["stacktrace_retained"] is False
    assert summary["sandbox_only"] is True
    assert summary["adapter_implemented"] is False
    assert summary["adapter_enabled"] is False
    assert summary["can_send_http"] is False
    assert summary["network_call_allowed"] is False
    assert summary["ready_for_http_execution"] is False
    assert summary["real_money"] is False
    assert summary["http_call_executed"] is False
    assert summary["safe_error_shape"]["raw_error_allowed"] is False
    assert summary["safe_error_shape"]["provider_raw_error_allowed"] is False
    assert summary["safe_error_shape"]["stacktrace_allowed"] is False
    assert summary["safe_error_shape"]["secret_values_allowed"] is False
    assert "access_token" in summary["safe_error_shape"]["blocked_fields"]
    assert "api_key" in summary["safe_error_shape"]["blocked_fields"]
    assert "webhook_token" in summary["safe_error_shape"]["blocked_fields"]
    assert "wallet_id" in summary["safe_error_shape"]["blocked_fields"]
    assert "provider_raw" in summary["safe_error_shape"]["blocked_fields"]
    assert "stacktrace" in summary["safe_error_shape"]["blocked_fields"]
    assert "request_body" in summary["safe_error_shape"]["blocked_fields"]
    assert summary["response_sanitizer_contract"]["operation"] == (
        "first_customer_http_response_sanitizer_contract"
    )
    assert summary["prepared_request"]["operation"] == "create_customer"
    assert summary["prepared_request"]["http_call_executed"] is False
    assert "sandbox-api-key-for-test-only" not in repr(summary)
    assert "sandbox-webhook-token-for-test-only" not in repr(summary)


def test_first_customer_http_manual_execution_approval_gate_stays_blocked():
    client = make_client()

    gate = client.gate_first_customer_http_manual_execution_approval(
        name="Cliente Manual Approval Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.manual.approval@example.com",
        mobile_phone="11999999999",
    )

    request = gate.prepared_request
    checklist = gate.approval_checklist

    assert gate.approval_reference == (
        "first-customer-http-manual-execution-approval-gate-sandbox"
    )
    assert gate.approval_gate_defined is True
    assert gate.manual_execution_approval_registered is False
    assert gate.manual_execution_approval_valid is False
    assert gate.approval_allows_http_execution is False
    assert gate.execution_enabled is False
    assert gate.sandbox_only is True
    assert gate.adapter_implemented is False
    assert gate.adapter_enabled is False
    assert gate.can_send_http is False
    assert gate.network_call_allowed is False
    assert gate.real_money is False
    assert gate.http_call_executed is False

    assert checklist["sandbox_target_confirmed"] is True
    assert checklist["production_blocked"] is True
    assert checklist["real_money_disabled"] is True
    assert checklist["safe_response_sanitizer_required"] is True
    assert checklist["safe_error_sanitizer_required"] is True
    assert checklist["raw_response_exposure_blocked"] is True
    assert checklist["raw_error_exposure_blocked"] is True
    assert checklist["request_body_exposure_blocked"] is True
    assert checklist["stacktrace_exposure_blocked"] is True
    assert checklist["secret_exposure_blocked"] is True
    assert checklist["adapter_implementation_reviewed"] is False
    assert checklist["final_operator_confirmation_required"] is True

    assert request.method == "POST"
    assert request.url == f"{ASAAS_SANDBOX_BASE_URL}/customers"
    assert request.operation == "create_customer"
    assert request.real_money is False
    assert request.http_call_executed is False


def test_first_customer_http_manual_execution_approval_gate_recognizes_phrase_but_does_not_enable_http():
    client = make_client()

    gate = client.gate_first_customer_http_manual_execution_approval(
        name="Cliente Manual Approval Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.manual.approval@example.com",
        mobile_phone="11999999999",
        manual_authorization_phrase=ASAAS_SANDBOX_MANUAL_AUTHORIZATION_PHRASE,
    )

    summary = gate.safe_summary()

    assert gate.manual_execution_approval_registered is True
    assert gate.manual_execution_approval_valid is True
    assert gate.approval_allows_http_execution is False
    assert gate.execution_enabled is False
    assert gate.can_send_http is False
    assert gate.network_call_allowed is False
    assert gate.real_money is False
    assert gate.http_call_executed is False

    assert summary["operation"] == (
        "first_customer_http_manual_execution_approval_gate"
    )
    assert summary["manual_execution_approval_registered"] is True
    assert summary["manual_execution_approval_valid"] is True
    assert summary["approval_allows_http_execution"] is False
    assert summary["execution_enabled"] is False
    assert summary["ready_for_http_execution"] is False
    assert summary["adapter_implemented"] is False
    assert summary["adapter_enabled"] is False
    assert summary["can_send_http"] is False
    assert summary["network_call_allowed"] is False
    assert summary["real_money"] is False
    assert summary["http_call_executed"] is False
    assert summary["approval_checklist"]["production_blocked"] is True
    assert summary["approval_checklist"]["real_money_disabled"] is True
    assert summary["approval_checklist"]["secret_exposure_blocked"] is True
    assert summary["approval_checklist"]["adapter_implementation_reviewed"] is False
    assert summary["error_sanitizer_contract"]["operation"] == (
        "first_customer_http_error_sanitizer_contract"
    )
    assert summary["prepared_request"]["operation"] == "create_customer"
    assert summary["prepared_request"]["http_call_executed"] is False
    assert "sandbox-api-key-for-test-only" not in repr(summary)
    assert "sandbox-webhook-token-for-test-only" not in repr(summary)
    assert "access_token" not in repr(summary["prepared_request"])


def test_first_customer_http_disabled_adapter_shell_stays_disabled():
    client = make_client()

    shell = client.build_first_customer_http_disabled_adapter_shell(
        name="Cliente Disabled Adapter Shell Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.disabled.adapter@example.com",
        mobile_phone="11999999999",
    )

    request = shell.prepared_request
    contract = shell.adapter_shell_contract

    assert shell.adapter_shell_reference == (
        "first-customer-http-disabled-adapter-shell-sandbox"
    )
    assert shell.disabled_adapter_shell_defined is True
    assert shell.adapter_shell_enabled is False
    assert shell.adapter_implemented is False
    assert shell.adapter_enabled is False
    assert shell.execution_enabled is False
    assert shell.can_send_http is False
    assert shell.network_call_allowed is False
    assert shell.real_money is False
    assert shell.http_call_executed is False
    assert shell.sandbox_only is True

    assert contract == {
        "target_method": "POST",
        "target_path": "/customers",
        "target_environment": "sandbox",
        "http_client_library_selected": False,
        "network_binding_created": False,
        "send_method_defined": False,
        "execution_method_defined": False,
        "requires_future_explicit_enablement": True,
    }

    assert request.method == "POST"
    assert request.url == f"{ASAAS_SANDBOX_BASE_URL}/customers"
    assert request.operation == "create_customer"
    assert request.real_money is False
    assert request.http_call_executed is False


def test_first_customer_http_disabled_adapter_shell_recognizes_manual_phrase_but_still_cannot_send():
    client = make_client()

    shell = client.build_first_customer_http_disabled_adapter_shell(
        name="Cliente Disabled Adapter Shell Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.disabled.adapter@example.com",
        mobile_phone="11999999999",
        manual_authorization_phrase=ASAAS_SANDBOX_MANUAL_AUTHORIZATION_PHRASE,
    )

    summary = shell.safe_summary()

    assert summary["operation"] == "first_customer_http_disabled_adapter_shell"
    assert summary["disabled_adapter_shell_defined"] is True
    assert summary["adapter_shell_enabled"] is False
    assert summary["adapter_implemented"] is False
    assert summary["adapter_enabled"] is False
    assert summary["execution_enabled"] is False
    assert summary["can_send_http"] is False
    assert summary["network_call_allowed"] is False
    assert summary["real_money"] is False
    assert summary["http_call_executed"] is False
    assert summary["ready_for_http_execution"] is False
    assert summary["adapter_shell_contract"]["http_client_library_selected"] is False
    assert summary["adapter_shell_contract"]["network_binding_created"] is False
    assert summary["adapter_shell_contract"]["send_method_defined"] is False
    assert summary["adapter_shell_contract"]["execution_method_defined"] is False
    assert (
        summary["adapter_shell_contract"]["requires_future_explicit_enablement"]
        is True
    )
    assert summary["manual_approval_gate"]["operation"] == (
        "first_customer_http_manual_execution_approval_gate"
    )
    assert (
        summary["manual_approval_gate"]["manual_execution_approval_registered"]
        is True
    )
    assert summary["manual_approval_gate"]["approval_allows_http_execution"] is False
    assert summary["prepared_request"]["operation"] == "create_customer"
    assert summary["prepared_request"]["http_call_executed"] is False
    assert "sandbox-api-key-for-test-only" not in repr(summary)
    assert "sandbox-webhook-token-for-test-only" not in repr(summary)
    assert "access_token" not in repr(summary["prepared_request"])


def test_first_customer_http_explicit_enable_preflight_stays_blocked_without_phrases():
    client = make_client()

    preflight = client.build_first_customer_http_explicit_enable_preflight(
        name="Cliente Explicit Enable Preflight Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.explicit.preflight@example.com",
        mobile_phone="11999999999",
    )

    contract = preflight.explicit_enable_preflight_contract

    assert preflight.explicit_enable_reference == (
        "first-customer-http-explicit-enable-preflight-sandbox"
    )
    assert preflight.explicit_enable_preflight_defined is True
    assert preflight.explicit_enable_phrase_registered is False
    assert preflight.manual_execution_approval_valid is False
    assert preflight.disabled_adapter_shell_defined is True
    assert preflight.explicit_enable_preflight_valid is False
    assert preflight.explicit_enable_allows_adapter_enablement is False
    assert preflight.explicit_enable_allows_http_execution is False
    assert preflight.adapter_shell_enabled is False
    assert preflight.adapter_implemented is False
    assert preflight.adapter_enabled is False
    assert preflight.execution_enabled is False
    assert preflight.can_send_http is False
    assert preflight.network_call_allowed is False
    assert preflight.real_money is False
    assert preflight.http_call_executed is False
    assert preflight.sandbox_only is True

    assert contract == {
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


def test_first_customer_http_explicit_enable_preflight_requires_manual_approval_too():
    client = make_client()
    explicit_phrase = (
        "CONFIRMO PREFLIGHT DE HABILITACAO EXPLICITA ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )

    preflight = client.build_first_customer_http_explicit_enable_preflight(
        name="Cliente Explicit Enable Preflight Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.explicit.preflight@example.com",
        mobile_phone="11999999999",
        explicit_enable_phrase=explicit_phrase,
    )

    summary = preflight.safe_summary()

    assert summary["operation"] == "first_customer_http_explicit_enable_preflight"
    assert summary["explicit_enable_phrase_required"] is True
    assert summary["explicit_enable_phrase_registered"] is True
    assert summary["manual_execution_approval_valid"] is False
    assert summary["explicit_enable_preflight_valid"] is False
    assert summary["explicit_enable_allows_adapter_enablement"] is False
    assert summary["explicit_enable_allows_http_execution"] is False
    assert summary["adapter_enabled"] is False
    assert summary["can_send_http"] is False
    assert summary["network_call_allowed"] is False
    assert summary["http_call_executed"] is False
    assert summary["ready_for_http_execution"] is False


def test_first_customer_http_explicit_enable_preflight_valid_but_non_executing():
    client = make_client()
    explicit_phrase = (
        "CONFIRMO PREFLIGHT DE HABILITACAO EXPLICITA ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )

    preflight = client.build_first_customer_http_explicit_enable_preflight(
        name="Cliente Explicit Enable Preflight Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.explicit.preflight@example.com",
        mobile_phone="11999999999",
        manual_authorization_phrase=ASAAS_SANDBOX_MANUAL_AUTHORIZATION_PHRASE,
        explicit_enable_phrase=explicit_phrase,
    )

    summary = preflight.safe_summary()

    assert summary["explicit_enable_phrase_registered"] is True
    assert summary["manual_execution_approval_valid"] is True
    assert summary["disabled_adapter_shell_defined"] is True
    assert summary["explicit_enable_preflight_valid"] is True
    assert summary["explicit_enable_allows_adapter_enablement"] is False
    assert summary["explicit_enable_allows_http_execution"] is False
    assert summary["adapter_shell_enabled"] is False
    assert summary["adapter_implemented"] is False
    assert summary["adapter_enabled"] is False
    assert summary["execution_enabled"] is False
    assert summary["can_send_http"] is False
    assert summary["network_call_allowed"] is False
    assert summary["real_money"] is False
    assert summary["http_call_executed"] is False
    assert summary["ready_for_http_execution"] is False
    assert summary["prepared_request"]["operation"] == "create_customer"
    assert summary["prepared_request"]["http_call_executed"] is False
    assert summary["disabled_adapter_shell"]["adapter_shell_enabled"] is False
    assert "sandbox-api-key-for-test-only" not in repr(summary)
    assert "sandbox-webhook-token-for-test-only" not in repr(summary)
    assert "access_token" not in repr(summary["prepared_request"])


def test_first_customer_http_runtime_enable_contract_stays_blocked_without_phrases():
    client = make_client()

    contract_result = client.build_first_customer_http_runtime_enable_contract(
        name="Cliente Runtime Enable Contract Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.runtime.contract@example.com",
        mobile_phone="11999999999",
    )

    contract = contract_result.runtime_enable_contract

    assert contract_result.runtime_enable_reference == (
        "first-customer-http-runtime-enable-contract-sandbox"
    )
    assert contract_result.runtime_enable_contract_defined is True
    assert contract_result.runtime_enable_phrase_registered is False
    assert contract_result.explicit_enable_preflight_valid is False
    assert contract_result.runtime_enable_contract_valid is False
    assert contract_result.runtime_enable_allows_adapter_enablement is False
    assert contract_result.runtime_enable_allows_http_execution is False
    assert contract_result.adapter_shell_enabled is False
    assert contract_result.adapter_implemented is False
    assert contract_result.adapter_enabled is False
    assert contract_result.execution_enabled is False
    assert contract_result.can_send_http is False
    assert contract_result.network_call_allowed is False
    assert contract_result.real_money is False
    assert contract_result.http_call_executed is False
    assert contract_result.sandbox_only is True

    assert contract == {
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


def test_first_customer_http_runtime_enable_contract_requires_valid_preflight_too():
    client = make_client()
    runtime_phrase = (
        "CONFIRMO CONTRATO DE HABILITACAO RUNTIME ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )

    contract_result = client.build_first_customer_http_runtime_enable_contract(
        name="Cliente Runtime Enable Contract Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.runtime.contract@example.com",
        mobile_phone="11999999999",
        runtime_enable_phrase=runtime_phrase,
    )

    summary = contract_result.safe_summary()

    assert summary["operation"] == "first_customer_http_runtime_enable_contract"
    assert summary["runtime_enable_phrase_required"] is True
    assert summary["runtime_enable_phrase_registered"] is True
    assert summary["explicit_enable_preflight_valid"] is False
    assert summary["runtime_enable_contract_valid"] is False
    assert summary["runtime_enable_allows_adapter_enablement"] is False
    assert summary["runtime_enable_allows_http_execution"] is False
    assert summary["adapter_enabled"] is False
    assert summary["can_send_http"] is False
    assert summary["network_call_allowed"] is False
    assert summary["http_call_executed"] is False
    assert summary["ready_for_http_execution"] is False


def test_first_customer_http_runtime_enable_contract_valid_but_non_executing():
    client = make_client()
    explicit_phrase = (
        "CONFIRMO PREFLIGHT DE HABILITACAO EXPLICITA ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )
    runtime_phrase = (
        "CONFIRMO CONTRATO DE HABILITACAO RUNTIME ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )

    contract_result = client.build_first_customer_http_runtime_enable_contract(
        name="Cliente Runtime Enable Contract Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.runtime.contract@example.com",
        mobile_phone="11999999999",
        manual_authorization_phrase=ASAAS_SANDBOX_MANUAL_AUTHORIZATION_PHRASE,
        explicit_enable_phrase=explicit_phrase,
        runtime_enable_phrase=runtime_phrase,
    )

    summary = contract_result.safe_summary()

    assert summary["runtime_enable_phrase_registered"] is True
    assert summary["explicit_enable_preflight_valid"] is True
    assert summary["runtime_enable_contract_valid"] is True
    assert summary["runtime_enable_allows_adapter_enablement"] is False
    assert summary["runtime_enable_allows_http_execution"] is False
    assert summary["adapter_shell_enabled"] is False
    assert summary["adapter_implemented"] is False
    assert summary["adapter_enabled"] is False
    assert summary["execution_enabled"] is False
    assert summary["can_send_http"] is False
    assert summary["network_call_allowed"] is False
    assert summary["real_money"] is False
    assert summary["http_call_executed"] is False
    assert summary["ready_for_http_execution"] is False
    assert summary["prepared_request"]["operation"] == "create_customer"
    assert summary["prepared_request"]["http_call_executed"] is False
    assert (
        summary["explicit_enable_preflight"]["explicit_enable_preflight_valid"]
        is True
    )
    assert "sandbox-api-key-for-test-only" not in repr(summary)
    assert "sandbox-webhook-token-for-test-only" not in repr(summary)
    assert "access_token" not in repr(summary["prepared_request"])


def test_first_customer_http_runtime_switch_guard_stays_blocked_without_phrases():
    client = make_client()

    guard = client.build_first_customer_http_runtime_switch_guard(
        name="Cliente Runtime Switch Guard Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.runtime.switch@example.com",
        mobile_phone="11999999999",
    )

    contract = guard.runtime_switch_guard_contract

    assert guard.runtime_switch_guard_reference == (
        "first-customer-http-runtime-switch-guard-sandbox"
    )
    assert guard.runtime_switch_guard_defined is True
    assert guard.runtime_switch_phrase_registered is False
    assert guard.runtime_enable_contract_valid is False
    assert guard.runtime_switch_guard_valid is False
    assert guard.runtime_switch_requested is False
    assert guard.runtime_switch_allows_adapter_enablement is False
    assert guard.runtime_switch_allows_http_execution is False
    assert guard.adapter_shell_enabled is False
    assert guard.adapter_implemented is False
    assert guard.adapter_enabled is False
    assert guard.execution_enabled is False
    assert guard.can_send_http is False
    assert guard.network_call_allowed is False
    assert guard.real_money is False
    assert guard.http_call_executed is False
    assert guard.sandbox_only is True

    assert contract == {
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


def test_first_customer_http_runtime_switch_guard_requires_valid_runtime_contract_too():
    client = make_client()
    switch_phrase = (
        "CONFIRMO GUARD DO SWITCH RUNTIME ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )

    guard = client.build_first_customer_http_runtime_switch_guard(
        name="Cliente Runtime Switch Guard Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.runtime.switch@example.com",
        mobile_phone="11999999999",
        runtime_switch_phrase=switch_phrase,
    )

    summary = guard.safe_summary()

    assert summary["operation"] == "first_customer_http_runtime_switch_guard"
    assert summary["runtime_switch_phrase_required"] is True
    assert summary["runtime_switch_phrase_registered"] is True
    assert summary["runtime_enable_contract_valid"] is False
    assert summary["runtime_switch_guard_valid"] is False
    assert summary["runtime_switch_requested"] is True
    assert summary["runtime_switch_allows_adapter_enablement"] is False
    assert summary["runtime_switch_allows_http_execution"] is False
    assert summary["adapter_enabled"] is False
    assert summary["can_send_http"] is False
    assert summary["network_call_allowed"] is False
    assert summary["http_call_executed"] is False
    assert summary["ready_for_http_execution"] is False


def test_first_customer_http_runtime_switch_guard_valid_but_non_executing():
    client = make_client()
    explicit_phrase = (
        "CONFIRMO PREFLIGHT DE HABILITACAO EXPLICITA ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )
    runtime_phrase = (
        "CONFIRMO CONTRATO DE HABILITACAO RUNTIME ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )
    switch_phrase = (
        "CONFIRMO GUARD DO SWITCH RUNTIME ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )

    guard = client.build_first_customer_http_runtime_switch_guard(
        name="Cliente Runtime Switch Guard Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.runtime.switch@example.com",
        mobile_phone="11999999999",
        manual_authorization_phrase=ASAAS_SANDBOX_MANUAL_AUTHORIZATION_PHRASE,
        explicit_enable_phrase=explicit_phrase,
        runtime_enable_phrase=runtime_phrase,
        runtime_switch_phrase=switch_phrase,
    )

    summary = guard.safe_summary()

    assert summary["runtime_switch_phrase_registered"] is True
    assert summary["runtime_enable_contract_valid"] is True
    assert summary["runtime_switch_guard_valid"] is True
    assert summary["runtime_switch_requested"] is True
    assert summary["runtime_switch_allows_adapter_enablement"] is False
    assert summary["runtime_switch_allows_http_execution"] is False
    assert summary["adapter_shell_enabled"] is False
    assert summary["adapter_implemented"] is False
    assert summary["adapter_enabled"] is False
    assert summary["execution_enabled"] is False
    assert summary["can_send_http"] is False
    assert summary["network_call_allowed"] is False
    assert summary["real_money"] is False
    assert summary["http_call_executed"] is False
    assert summary["ready_for_http_execution"] is False
    assert summary["prepared_request"]["operation"] == "create_customer"
    assert summary["prepared_request"]["http_call_executed"] is False
    assert (
        summary["runtime_enable_contract"]["runtime_enable_contract_valid"]
        is True
    )
    assert "sandbox-api-key-for-test-only" not in repr(summary)
    assert "sandbox-webhook-token-for-test-only" not in repr(summary)
    assert "access_token" not in repr(summary["prepared_request"])


def test_first_customer_http_execution_gate_contract_stays_blocked_without_phrases():
    client = make_client()

    gate = client.build_first_customer_http_execution_gate_contract(
        name="Cliente Execution Gate Contract Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.execution.gate@example.com",
        mobile_phone="11999999999",
    )

    contract = gate.execution_gate_contract

    assert gate.execution_gate_reference == (
        "first-customer-http-execution-gate-contract-sandbox"
    )
    assert gate.execution_gate_contract_defined is True
    assert gate.execution_gate_phrase_registered is False
    assert gate.runtime_switch_guard_valid is False
    assert gate.execution_gate_contract_valid is False
    assert gate.execution_gate_allows_adapter_enablement is False
    assert gate.execution_gate_allows_http_execution is False
    assert gate.adapter_shell_enabled is False
    assert gate.adapter_implemented is False
    assert gate.adapter_enabled is False
    assert gate.execution_enabled is False
    assert gate.can_send_http is False
    assert gate.network_call_allowed is False
    assert gate.real_money is False
    assert gate.http_call_executed is False
    assert gate.sandbox_only is True

    assert contract == {
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


def test_first_customer_http_execution_gate_contract_requires_valid_switch_guard_too():
    client = make_client()
    execution_phrase = (
        "CONFIRMO CONTRATO DO GATE DE EXECUCAO ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )

    gate = client.build_first_customer_http_execution_gate_contract(
        name="Cliente Execution Gate Contract Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.execution.gate@example.com",
        mobile_phone="11999999999",
        execution_gate_phrase=execution_phrase,
    )

    summary = gate.safe_summary()

    assert summary["operation"] == "first_customer_http_execution_gate_contract"
    assert summary["execution_gate_phrase_required"] is True
    assert summary["execution_gate_phrase_registered"] is True
    assert summary["runtime_switch_guard_valid"] is False
    assert summary["execution_gate_contract_valid"] is False
    assert summary["execution_gate_allows_adapter_enablement"] is False
    assert summary["execution_gate_allows_http_execution"] is False
    assert summary["adapter_enabled"] is False
    assert summary["can_send_http"] is False
    assert summary["network_call_allowed"] is False
    assert summary["http_call_executed"] is False
    assert summary["ready_for_http_execution"] is False


def test_first_customer_http_execution_gate_contract_valid_but_non_executing():
    client = make_client()
    explicit_phrase = (
        "CONFIRMO PREFLIGHT DE HABILITACAO EXPLICITA ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )
    runtime_phrase = (
        "CONFIRMO CONTRATO DE HABILITACAO RUNTIME ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )
    switch_phrase = (
        "CONFIRMO GUARD DO SWITCH RUNTIME ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )
    execution_phrase = (
        "CONFIRMO CONTRATO DO GATE DE EXECUCAO ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )

    gate = client.build_first_customer_http_execution_gate_contract(
        name="Cliente Execution Gate Contract Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.execution.gate@example.com",
        mobile_phone="11999999999",
        manual_authorization_phrase=ASAAS_SANDBOX_MANUAL_AUTHORIZATION_PHRASE,
        explicit_enable_phrase=explicit_phrase,
        runtime_enable_phrase=runtime_phrase,
        runtime_switch_phrase=switch_phrase,
        execution_gate_phrase=execution_phrase,
    )

    summary = gate.safe_summary()

    assert summary["execution_gate_phrase_registered"] is True
    assert summary["runtime_switch_guard_valid"] is True
    assert summary["execution_gate_contract_valid"] is True
    assert summary["execution_gate_allows_adapter_enablement"] is False
    assert summary["execution_gate_allows_http_execution"] is False
    assert summary["adapter_shell_enabled"] is False
    assert summary["adapter_implemented"] is False
    assert summary["adapter_enabled"] is False
    assert summary["execution_enabled"] is False
    assert summary["can_send_http"] is False
    assert summary["network_call_allowed"] is False
    assert summary["real_money"] is False
    assert summary["http_call_executed"] is False
    assert summary["ready_for_http_execution"] is False
    assert summary["prepared_request"]["operation"] == "create_customer"
    assert summary["prepared_request"]["http_call_executed"] is False
    assert summary["runtime_switch_guard"]["runtime_switch_guard_valid"] is True
    assert "sandbox-api-key-for-test-only" not in repr(summary)
    assert "sandbox-webhook-token-for-test-only" not in repr(summary)
    assert "access_token" not in repr(summary["prepared_request"])


def test_first_customer_http_sanitized_execution_handler_contract_stays_blocked_without_phrases():
    client = make_client()

    handler = client.build_first_customer_http_sanitized_execution_handler_contract(
        name="Cliente Sanitized Handler Contract Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.sanitized.handler@example.com",
        mobile_phone="11999999999",
    )

    contract = handler.sanitized_execution_handler_contract

    assert handler.sanitized_handler_reference == (
        "first-customer-http-sanitized-execution-handler-contract-sandbox"
    )
    assert handler.sanitized_execution_handler_contract_defined is True
    assert handler.execution_gate_contract_valid is False
    assert handler.sanitized_response_handler_required is True
    assert handler.sanitized_error_handler_required is True
    assert handler.raw_provider_response_allowed is False
    assert handler.raw_provider_error_allowed is False
    assert handler.request_body_exposure_allowed is False
    assert handler.stacktrace_exposure_allowed is False
    assert handler.sanitized_handler_allows_adapter_enablement is False
    assert handler.sanitized_handler_allows_http_execution is False
    assert handler.sanitized_handler_can_process_raw_provider_payload is False
    assert handler.adapter_shell_enabled is False
    assert handler.adapter_implemented is False
    assert handler.adapter_enabled is False
    assert handler.execution_enabled is False
    assert handler.can_send_http is False
    assert handler.network_call_allowed is False
    assert handler.real_money is False
    assert handler.http_call_executed is False
    assert handler.sandbox_only is True

    assert contract == {
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


def test_first_customer_http_sanitized_execution_handler_contract_requires_valid_execution_gate():
    client = make_client()

    handler = client.build_first_customer_http_sanitized_execution_handler_contract(
        name="Cliente Sanitized Handler Contract Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.sanitized.handler@example.com",
        mobile_phone="11999999999",
    )

    summary = handler.safe_summary()

    assert summary["operation"] == (
        "first_customer_http_sanitized_execution_handler_contract"
    )
    assert summary["execution_gate_contract_valid"] is False
    assert summary["sanitized_response_handler_required"] is True
    assert summary["sanitized_error_handler_required"] is True
    assert summary["raw_provider_response_allowed"] is False
    assert summary["raw_provider_error_allowed"] is False
    assert summary["request_body_exposure_allowed"] is False
    assert summary["stacktrace_exposure_allowed"] is False
    assert summary["sanitized_handler_allows_adapter_enablement"] is False
    assert summary["sanitized_handler_allows_http_execution"] is False
    assert summary["sanitized_handler_can_process_raw_provider_payload"] is False
    assert summary["adapter_enabled"] is False
    assert summary["can_send_http"] is False
    assert summary["network_call_allowed"] is False
    assert summary["http_call_executed"] is False
    assert summary["ready_for_http_execution"] is False


def test_first_customer_http_sanitized_execution_handler_contract_valid_gate_but_non_executing():
    client = make_client()
    explicit_phrase = (
        "CONFIRMO PREFLIGHT DE HABILITACAO EXPLICITA ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )
    runtime_phrase = (
        "CONFIRMO CONTRATO DE HABILITACAO RUNTIME ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )
    switch_phrase = (
        "CONFIRMO GUARD DO SWITCH RUNTIME ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )
    execution_phrase = (
        "CONFIRMO CONTRATO DO GATE DE EXECUCAO ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )

    handler = client.build_first_customer_http_sanitized_execution_handler_contract(
        name="Cliente Sanitized Handler Contract Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.sanitized.handler@example.com",
        mobile_phone="11999999999",
        manual_authorization_phrase=ASAAS_SANDBOX_MANUAL_AUTHORIZATION_PHRASE,
        explicit_enable_phrase=explicit_phrase,
        runtime_enable_phrase=runtime_phrase,
        runtime_switch_phrase=switch_phrase,
        execution_gate_phrase=execution_phrase,
    )

    summary = handler.safe_summary()

    assert summary["execution_gate_contract_valid"] is True
    assert summary["sanitized_response_handler_required"] is True
    assert summary["sanitized_error_handler_required"] is True
    assert summary["raw_provider_response_allowed"] is False
    assert summary["raw_provider_error_allowed"] is False
    assert summary["request_body_exposure_allowed"] is False
    assert summary["stacktrace_exposure_allowed"] is False
    assert summary["sanitized_handler_allows_adapter_enablement"] is False
    assert summary["sanitized_handler_allows_http_execution"] is False
    assert summary["sanitized_handler_can_process_raw_provider_payload"] is False
    assert summary["adapter_shell_enabled"] is False
    assert summary["adapter_implemented"] is False
    assert summary["adapter_enabled"] is False
    assert summary["execution_enabled"] is False
    assert summary["can_send_http"] is False
    assert summary["network_call_allowed"] is False
    assert summary["real_money"] is False
    assert summary["http_call_executed"] is False
    assert summary["ready_for_http_execution"] is False
    assert summary["prepared_request"]["operation"] == "create_customer"
    assert summary["prepared_request"]["http_call_executed"] is False
    assert (
        summary["execution_gate_contract"]["execution_gate_contract_valid"]
        is True
    )
    assert "sandbox-api-key-for-test-only" not in repr(summary)
    assert "sandbox-webhook-token-for-test-only" not in repr(summary)
    assert "access_token" not in repr(summary["prepared_request"])


def test_first_customer_http_sanitized_result_envelope_contract_stays_blocked_without_phrases():
    client = make_client()

    envelope = client.build_first_customer_http_sanitized_result_envelope_contract(
        name="Cliente Result Envelope Contract Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.result.envelope@example.com",
        mobile_phone="11999999999",
    )

    contract = envelope.sanitized_result_envelope_contract

    assert envelope.sanitized_result_envelope_reference == (
        "first-customer-http-sanitized-result-envelope-contract-sandbox"
    )
    assert envelope.sanitized_result_envelope_contract_defined is True
    assert envelope.sanitized_execution_handler_contract_valid is False
    assert envelope.success_envelope_required is True
    assert envelope.error_envelope_required is True
    assert envelope.raw_provider_payload_allowed is False
    assert envelope.raw_provider_error_allowed is False
    assert envelope.request_body_exposure_allowed is False
    assert envelope.stacktrace_exposure_allowed is False
    assert envelope.sanitized_result_envelope_allows_adapter_enablement is False
    assert envelope.sanitized_result_envelope_allows_http_execution is False
    assert envelope.sanitized_result_envelope_can_include_raw_payload is False
    assert envelope.adapter_shell_enabled is False
    assert envelope.adapter_implemented is False
    assert envelope.adapter_enabled is False
    assert envelope.execution_enabled is False
    assert envelope.can_send_http is False
    assert envelope.network_call_allowed is False
    assert envelope.real_money is False
    assert envelope.http_call_executed is False
    assert envelope.sandbox_only is True

    assert contract["target_method"] == "POST"
    assert contract["target_path"] == "/customers"
    assert contract["target_environment"] == "sandbox"
    assert contract["requires_sanitized_execution_handler_contract"] is True
    assert contract["requires_success_envelope"] is True
    assert contract["requires_error_envelope"] is True
    assert contract["requires_no_raw_provider_payload"] is True
    assert contract["raw_provider_payload_allowed"] is False
    assert contract["raw_provider_error_allowed"] is False
    assert contract["request_body_exposure_allowed"] is False
    assert contract["stacktrace_exposure_allowed"] is False
    assert contract["current_envelope_is_contract_only"] is True


def test_first_customer_http_sanitized_result_envelope_contract_defines_safe_fields():
    client = make_client()

    envelope = client.build_first_customer_http_sanitized_result_envelope_contract(
        name="Cliente Result Envelope Contract Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.result.envelope@example.com",
        mobile_phone="11999999999",
    )

    contract = envelope.sanitized_result_envelope_contract

    assert contract["success_envelope_fields"] == [
        "ok",
        "operation",
        "provider",
        "environment",
        "asaas_customer_id_present",
        "http_status_class",
        "sanitized_customer_reference",
        "raw_provider_payload_included",
    ]
    assert contract["error_envelope_fields"] == [
        "ok",
        "operation",
        "provider",
        "environment",
        "error_category",
        "retryable",
        "http_status_class",
        "raw_provider_error_included",
        "stacktrace_included",
    ]


def test_first_customer_http_sanitized_result_envelope_contract_valid_chain_but_non_executing():
    client = make_client()
    explicit_phrase = (
        "CONFIRMO PREFLIGHT DE HABILITACAO EXPLICITA ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )
    runtime_phrase = (
        "CONFIRMO CONTRATO DE HABILITACAO RUNTIME ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )
    switch_phrase = (
        "CONFIRMO GUARD DO SWITCH RUNTIME ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )
    execution_phrase = (
        "CONFIRMO CONTRATO DO GATE DE EXECUCAO ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )

    envelope = client.build_first_customer_http_sanitized_result_envelope_contract(
        name="Cliente Result Envelope Contract Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.result.envelope@example.com",
        mobile_phone="11999999999",
        manual_authorization_phrase=ASAAS_SANDBOX_MANUAL_AUTHORIZATION_PHRASE,
        explicit_enable_phrase=explicit_phrase,
        runtime_enable_phrase=runtime_phrase,
        runtime_switch_phrase=switch_phrase,
        execution_gate_phrase=execution_phrase,
    )

    summary = envelope.safe_summary()

    assert summary["operation"] == (
        "first_customer_http_sanitized_result_envelope_contract"
    )
    assert summary["sanitized_execution_handler_contract_valid"] is True
    assert summary["success_envelope_required"] is True
    assert summary["error_envelope_required"] is True
    assert summary["raw_provider_payload_allowed"] is False
    assert summary["raw_provider_error_allowed"] is False
    assert summary["request_body_exposure_allowed"] is False
    assert summary["stacktrace_exposure_allowed"] is False
    assert summary["sanitized_result_envelope_allows_adapter_enablement"] is False
    assert summary["sanitized_result_envelope_allows_http_execution"] is False
    assert summary["sanitized_result_envelope_can_include_raw_payload"] is False
    assert summary["adapter_shell_enabled"] is False
    assert summary["adapter_implemented"] is False
    assert summary["adapter_enabled"] is False
    assert summary["execution_enabled"] is False
    assert summary["can_send_http"] is False
    assert summary["network_call_allowed"] is False
    assert summary["real_money"] is False
    assert summary["http_call_executed"] is False
    assert summary["ready_for_http_execution"] is False
    assert summary["prepared_request"]["operation"] == "create_customer"
    assert summary["prepared_request"]["http_call_executed"] is False
    assert (
        summary["sanitized_execution_handler_contract"][
            "execution_gate_contract_valid"
        ]
        is True
    )
    assert "sandbox-api-key-for-test-only" not in repr(summary)
    assert "sandbox-webhook-token-for-test-only" not in repr(summary)
    assert "access_token" not in repr(summary["prepared_request"])


def test_first_customer_http_sanitized_success_error_fixture_contract_stays_blocked_without_phrases():
    client = make_client()

    fixture = client.build_first_customer_http_sanitized_success_error_fixture_contract(
        name="Cliente Fixture Contract Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.fixture.contract@example.com",
        mobile_phone="11999999999",
    )

    contract = fixture.sanitized_success_error_fixture_contract

    assert fixture.sanitized_success_error_fixture_reference == (
        "first-customer-http-sanitized-success-error-fixture-contract-sandbox"
    )
    assert fixture.sanitized_success_error_fixture_contract_defined is True
    assert fixture.sanitized_result_envelope_contract_valid is False
    assert fixture.sanitized_success_fixture_defined is True
    assert fixture.sanitized_error_fixture_defined is True
    assert fixture.sanitized_fixtures_match_envelope_contract is True
    assert fixture.success_fixture_contains_raw_provider_payload is False
    assert fixture.error_fixture_contains_raw_provider_error is False
    assert fixture.request_body_exposure_allowed is False
    assert fixture.stacktrace_exposure_allowed is False
    assert fixture.fixture_contract_allows_adapter_enablement is False
    assert fixture.fixture_contract_allows_http_execution is False
    assert fixture.fixture_contract_can_include_raw_payload is False
    assert fixture.adapter_shell_enabled is False
    assert fixture.adapter_implemented is False
    assert fixture.adapter_enabled is False
    assert fixture.execution_enabled is False
    assert fixture.can_send_http is False
    assert fixture.network_call_allowed is False
    assert fixture.real_money is False
    assert fixture.http_call_executed is False
    assert fixture.sandbox_only is True

    assert contract == {
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


def test_first_customer_http_sanitized_success_error_fixture_contract_defines_safe_fixtures():
    client = make_client()

    fixture = client.build_first_customer_http_sanitized_success_error_fixture_contract(
        name="Cliente Fixture Contract Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.fixture.contract@example.com",
        mobile_phone="11999999999",
    )

    assert fixture.sanitized_success_fixture == {
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
    assert fixture.sanitized_error_fixture == {
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


def test_first_customer_http_sanitized_success_error_fixture_contract_valid_chain_but_non_executing():
    client = make_client()
    explicit_phrase = (
        "CONFIRMO PREFLIGHT DE HABILITACAO EXPLICITA ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )
    runtime_phrase = (
        "CONFIRMO CONTRATO DE HABILITACAO RUNTIME ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )
    switch_phrase = (
        "CONFIRMO GUARD DO SWITCH RUNTIME ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )
    execution_phrase = (
        "CONFIRMO CONTRATO DO GATE DE EXECUCAO ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )

    fixture = client.build_first_customer_http_sanitized_success_error_fixture_contract(
        name="Cliente Fixture Contract Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.fixture.contract@example.com",
        mobile_phone="11999999999",
        manual_authorization_phrase=ASAAS_SANDBOX_MANUAL_AUTHORIZATION_PHRASE,
        explicit_enable_phrase=explicit_phrase,
        runtime_enable_phrase=runtime_phrase,
        runtime_switch_phrase=switch_phrase,
        execution_gate_phrase=execution_phrase,
    )

    summary = fixture.safe_summary()

    assert summary["operation"] == (
        "first_customer_http_sanitized_success_error_fixture_contract"
    )
    assert summary["sanitized_result_envelope_contract_valid"] is True
    assert summary["sanitized_success_fixture_defined"] is True
    assert summary["sanitized_error_fixture_defined"] is True
    assert summary["sanitized_fixtures_match_envelope_contract"] is True
    assert summary["success_fixture_contains_raw_provider_payload"] is False
    assert summary["error_fixture_contains_raw_provider_error"] is False
    assert summary["request_body_exposure_allowed"] is False
    assert summary["stacktrace_exposure_allowed"] is False
    assert summary["fixture_contract_allows_adapter_enablement"] is False
    assert summary["fixture_contract_allows_http_execution"] is False
    assert summary["fixture_contract_can_include_raw_payload"] is False
    assert summary["adapter_shell_enabled"] is False
    assert summary["adapter_implemented"] is False
    assert summary["adapter_enabled"] is False
    assert summary["execution_enabled"] is False
    assert summary["can_send_http"] is False
    assert summary["network_call_allowed"] is False
    assert summary["real_money"] is False
    assert summary["http_call_executed"] is False
    assert summary["ready_for_http_execution"] is False
    assert summary["prepared_request"]["operation"] == "create_customer"
    assert summary["prepared_request"]["http_call_executed"] is False
    assert (
        summary["sanitized_result_envelope_contract"][
            "sanitized_execution_handler_contract_valid"
        ]
        is True
    )
    assert summary["sanitized_success_fixture"][
        "raw_provider_payload_included"
    ] is False
    assert summary["sanitized_error_fixture"][
        "raw_provider_error_included"
    ] is False
    assert summary["sanitized_error_fixture"]["stacktrace_included"] is False
    assert "sandbox-api-key-for-test-only" not in repr(summary)
    assert "sandbox-webhook-token-for-test-only" not in repr(summary)
    assert "access_token" not in repr(summary["prepared_request"])


def test_first_customer_http_adapter_boundary_final_contract_stays_blocked_without_phrases():
    client = make_client()

    boundary = client.build_first_customer_http_adapter_boundary_final_contract(
        name="Cliente Adapter Boundary Contract Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.adapter.boundary@example.com",
        mobile_phone="11999999999",
    )

    contract = boundary.adapter_boundary_final_contract

    assert boundary.adapter_boundary_reference == (
        "first-customer-http-adapter-boundary-final-contract-sandbox"
    )
    assert boundary.adapter_boundary_final_contract_defined is True
    assert boundary.sanitized_success_error_fixture_contract_valid is False
    assert boundary.adapter_boundary_final_contract_valid is False
    assert boundary.future_adapter_must_return_sanitized_envelope_only is True
    assert boundary.raw_provider_payload_allowed is False
    assert boundary.raw_provider_error_allowed is False
    assert boundary.request_body_exposure_allowed is False
    assert boundary.stacktrace_exposure_allowed is False
    assert boundary.adapter_boundary_allows_adapter_implementation is False
    assert boundary.adapter_boundary_allows_adapter_enablement is False
    assert boundary.adapter_boundary_allows_http_execution is False
    assert boundary.adapter_boundary_can_emit_raw_payload is False
    assert boundary.adapter_shell_enabled is False
    assert boundary.adapter_implemented is False
    assert boundary.adapter_enabled is False
    assert boundary.execution_enabled is False
    assert boundary.can_send_http is False
    assert boundary.network_call_allowed is False
    assert boundary.real_money is False
    assert boundary.http_call_executed is False
    assert boundary.sandbox_only is True

    assert contract["target_method"] == "POST"
    assert contract["target_path"] == "/customers"
    assert contract["target_environment"] == "sandbox"
    assert contract["allowed_future_caller"] == (
        "first_customer_http_sanitized_execution_handler"
    )
    assert contract["requires_manual_execution_approval"] is True
    assert contract["requires_disabled_adapter_shell"] is True
    assert contract["requires_explicit_enable_preflight"] is True
    assert contract["requires_runtime_enable_contract"] is True
    assert contract["requires_runtime_switch_guard"] is True
    assert contract["requires_execution_gate_contract"] is True
    assert contract["requires_sanitized_execution_handler_contract"] is True
    assert contract["requires_sanitized_result_envelope_contract"] is True
    assert contract["requires_sanitized_success_error_fixtures"] is True
    assert contract["future_adapter_must_return_sanitized_envelope_only"] is True
    assert contract["future_adapter_must_not_expose_raw_provider_payload"] is True
    assert contract["future_adapter_must_not_expose_raw_provider_error"] is True
    assert contract["future_adapter_must_not_expose_request_body"] is True
    assert contract["future_adapter_must_not_expose_stacktrace"] is True
    assert contract["adapter_implementation_present"] is False
    assert contract["current_boundary_is_contract_only"] is True


def test_first_customer_http_adapter_boundary_final_contract_requires_valid_fixture_chain():
    client = make_client()

    boundary = client.build_first_customer_http_adapter_boundary_final_contract(
        name="Cliente Adapter Boundary Contract Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.adapter.boundary@example.com",
        mobile_phone="11999999999",
    )

    summary = boundary.safe_summary()

    assert summary["operation"] == (
        "first_customer_http_adapter_boundary_final_contract"
    )
    assert summary["sanitized_success_error_fixture_contract_valid"] is False
    assert summary["adapter_boundary_final_contract_valid"] is False
    assert summary["future_adapter_must_return_sanitized_envelope_only"] is True
    assert summary["raw_provider_payload_allowed"] is False
    assert summary["raw_provider_error_allowed"] is False
    assert summary["request_body_exposure_allowed"] is False
    assert summary["stacktrace_exposure_allowed"] is False
    assert summary["adapter_boundary_allows_adapter_implementation"] is False
    assert summary["adapter_boundary_allows_adapter_enablement"] is False
    assert summary["adapter_boundary_allows_http_execution"] is False
    assert summary["adapter_boundary_can_emit_raw_payload"] is False
    assert summary["adapter_enabled"] is False
    assert summary["can_send_http"] is False
    assert summary["network_call_allowed"] is False
    assert summary["http_call_executed"] is False
    assert summary["ready_for_http_execution"] is False
    assert summary["next_step_required"] == (
        "final_manual_execution_runbook_readiness_gate"
    )


def test_first_customer_http_adapter_boundary_final_contract_valid_chain_but_non_executing():
    client = make_client()
    explicit_phrase = (
        "CONFIRMO PREFLIGHT DE HABILITACAO EXPLICITA ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )
    runtime_phrase = (
        "CONFIRMO CONTRATO DE HABILITACAO RUNTIME ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )
    switch_phrase = (
        "CONFIRMO GUARD DO SWITCH RUNTIME ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )
    execution_phrase = (
        "CONFIRMO CONTRATO DO GATE DE EXECUCAO ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )

    boundary = client.build_first_customer_http_adapter_boundary_final_contract(
        name="Cliente Adapter Boundary Contract Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.adapter.boundary@example.com",
        mobile_phone="11999999999",
        manual_authorization_phrase=ASAAS_SANDBOX_MANUAL_AUTHORIZATION_PHRASE,
        explicit_enable_phrase=explicit_phrase,
        runtime_enable_phrase=runtime_phrase,
        runtime_switch_phrase=switch_phrase,
        execution_gate_phrase=execution_phrase,
    )

    summary = boundary.safe_summary()

    assert summary["sanitized_success_error_fixture_contract_valid"] is True
    assert summary["adapter_boundary_final_contract_valid"] is True
    assert summary["future_adapter_must_return_sanitized_envelope_only"] is True
    assert summary["raw_provider_payload_allowed"] is False
    assert summary["raw_provider_error_allowed"] is False
    assert summary["request_body_exposure_allowed"] is False
    assert summary["stacktrace_exposure_allowed"] is False
    assert summary["adapter_boundary_allows_adapter_implementation"] is False
    assert summary["adapter_boundary_allows_adapter_enablement"] is False
    assert summary["adapter_boundary_allows_http_execution"] is False
    assert summary["adapter_boundary_can_emit_raw_payload"] is False
    assert summary["adapter_shell_enabled"] is False
    assert summary["adapter_implemented"] is False
    assert summary["adapter_enabled"] is False
    assert summary["execution_enabled"] is False
    assert summary["can_send_http"] is False
    assert summary["network_call_allowed"] is False
    assert summary["real_money"] is False
    assert summary["http_call_executed"] is False
    assert summary["ready_for_http_execution"] is False
    assert summary["prepared_request"]["operation"] == "create_customer"
    assert summary["prepared_request"]["http_call_executed"] is False
    assert (
        summary["sanitized_success_error_fixture_contract"][
            "sanitized_result_envelope_contract_valid"
        ]
        is True
    )
    assert summary["adapter_boundary_final_contract"][
        "adapter_implementation_present"
    ] is False
    assert "sandbox-api-key-for-test-only" not in repr(summary)
    assert "sandbox-webhook-token-for-test-only" not in repr(summary)
    assert "access_token" not in repr(summary["prepared_request"])


def test_first_customer_http_final_manual_execution_runbook_readiness_gate_stays_blocked_without_phrases():
    client = make_client()

    gate = client.build_first_customer_http_final_manual_execution_runbook_readiness_gate(
        name="Cliente Final Readiness Gate Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.final.readiness@example.com",
        mobile_phone="11999999999",
    )

    contract = gate.final_manual_execution_runbook_readiness_gate

    assert gate.final_readiness_gate_reference == (
        "first-customer-http-final-manual-execution-runbook-readiness-gate"
    )
    assert gate.final_manual_execution_runbook_readiness_gate_defined is True
    assert gate.adapter_boundary_final_contract_valid is False
    assert gate.final_manual_execution_runbook_readiness_gate_valid is False
    assert gate.manual_operator_review_required is True
    assert gate.sandbox_only_confirmation_required is True
    assert gate.no_production_confirmation_required is True
    assert gate.no_real_money_confirmation_required is True
    assert gate.sanitized_logging_only_required is True
    assert gate.future_manual_execution_approval_required is True
    assert gate.future_adapter_implementation_review_required is True
    assert gate.raw_provider_payload_allowed is False
    assert gate.raw_provider_error_allowed is False
    assert gate.request_body_exposure_allowed is False
    assert gate.stacktrace_exposure_allowed is False
    assert gate.final_readiness_gate_allows_adapter_implementation is False
    assert gate.final_readiness_gate_allows_adapter_enablement is False
    assert gate.final_readiness_gate_allows_http_execution is False
    assert gate.final_readiness_gate_can_emit_raw_payload is False
    assert gate.ready_for_manual_execution_review is False
    assert gate.manual_execution_started is False
    assert gate.adapter_shell_enabled is False
    assert gate.adapter_implemented is False
    assert gate.adapter_enabled is False
    assert gate.execution_enabled is False
    assert gate.can_send_http is False
    assert gate.network_call_allowed is False
    assert gate.real_money is False
    assert gate.http_call_executed is False
    assert gate.sandbox_only is True

    assert contract["target_method"] == "POST"
    assert contract["target_path"] == "/customers"
    assert contract["target_environment"] == "sandbox"
    assert contract["requires_adapter_boundary_final_contract"] is True
    assert contract["requires_manual_operator_review"] is True
    assert contract["requires_sandbox_only_confirmation"] is True
    assert contract["requires_no_production_confirmation"] is True
    assert contract["requires_no_real_money_confirmation"] is True
    assert contract["requires_sanitized_logging_only"] is True
    assert contract["requires_no_raw_provider_payload"] is True
    assert contract["requires_no_raw_provider_error"] is True
    assert contract["requires_no_request_body_logging"] is True
    assert contract["requires_no_stacktrace_exposure"] is True
    assert contract["requires_future_adapter_implementation_review"] is True
    assert contract["requires_future_manual_execution_approval"] is True
    assert contract["manual_execution_not_started"] is True
    assert contract["current_gate_is_review_only"] is True


def test_first_customer_http_final_manual_execution_runbook_readiness_gate_defines_review_steps():
    client = make_client()

    gate = client.build_first_customer_http_final_manual_execution_runbook_readiness_gate(
        name="Cliente Final Readiness Gate Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.final.readiness@example.com",
        mobile_phone="11999999999",
    )

    assert gate.runbook_review_steps == [
        "confirm_sandbox_environment_only",
        "confirm_no_production_credentials_or_urls",
        "confirm_no_real_money_or_real_pix_flow",
        "confirm_adapter_boundary_contract_valid",
        "confirm_sanitized_result_envelope_only",
        "confirm_no_raw_provider_payload_or_error_logging",
        "confirm_no_request_body_or_stacktrace_exposure",
        "confirm_future_manual_execution_approval_required",
    ]


def test_first_customer_http_final_manual_execution_runbook_readiness_gate_valid_chain_review_only():
    client = make_client()
    explicit_phrase = (
        "CONFIRMO PREFLIGHT DE HABILITACAO EXPLICITA ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )
    runtime_phrase = (
        "CONFIRMO CONTRATO DE HABILITACAO RUNTIME ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )
    switch_phrase = (
        "CONFIRMO GUARD DO SWITCH RUNTIME ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )
    execution_phrase = (
        "CONFIRMO CONTRATO DO GATE DE EXECUCAO ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )

    gate = client.build_first_customer_http_final_manual_execution_runbook_readiness_gate(
        name="Cliente Final Readiness Gate Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.final.readiness@example.com",
        mobile_phone="11999999999",
        manual_authorization_phrase=ASAAS_SANDBOX_MANUAL_AUTHORIZATION_PHRASE,
        explicit_enable_phrase=explicit_phrase,
        runtime_enable_phrase=runtime_phrase,
        runtime_switch_phrase=switch_phrase,
        execution_gate_phrase=execution_phrase,
    )

    summary = gate.safe_summary()

    assert summary["operation"] == (
        "first_customer_http_final_manual_execution_runbook_readiness_gate"
    )
    assert summary["adapter_boundary_final_contract_valid"] is True
    assert summary["final_manual_execution_runbook_readiness_gate_valid"] is True
    assert summary["ready_for_manual_execution_review"] is True
    assert summary["manual_operator_review_required"] is True
    assert summary["sandbox_only_confirmation_required"] is True
    assert summary["no_production_confirmation_required"] is True
    assert summary["no_real_money_confirmation_required"] is True
    assert summary["sanitized_logging_only_required"] is True
    assert summary["future_manual_execution_approval_required"] is True
    assert summary["future_adapter_implementation_review_required"] is True
    assert summary["raw_provider_payload_allowed"] is False
    assert summary["raw_provider_error_allowed"] is False
    assert summary["request_body_exposure_allowed"] is False
    assert summary["stacktrace_exposure_allowed"] is False
    assert summary["final_readiness_gate_allows_adapter_implementation"] is False
    assert summary["final_readiness_gate_allows_adapter_enablement"] is False
    assert summary["final_readiness_gate_allows_http_execution"] is False
    assert summary["final_readiness_gate_can_emit_raw_payload"] is False
    assert summary["manual_execution_started"] is False
    assert summary["adapter_shell_enabled"] is False
    assert summary["adapter_implemented"] is False
    assert summary["adapter_enabled"] is False
    assert summary["execution_enabled"] is False
    assert summary["can_send_http"] is False
    assert summary["network_call_allowed"] is False
    assert summary["real_money"] is False
    assert summary["http_call_executed"] is False
    assert summary["ready_for_http_execution"] is False
    assert summary["next_step_required"] == (
        "manual_review_before_first_sandbox_http_attempt"
    )
    assert summary["prepared_request"]["operation"] == "create_customer"
    assert summary["prepared_request"]["http_call_executed"] is False
    assert (
        summary["adapter_boundary_final_contract"][
            "adapter_boundary_final_contract_valid"
        ]
        is True
    )
    assert "sandbox-api-key-for-test-only" not in repr(summary)
    assert "sandbox-webhook-token-for-test-only" not in repr(summary)
    assert "access_token" not in repr(summary["prepared_request"])


def test_first_customer_http_first_controlled_sandbox_attempt_preparation_stays_blocked_without_phrases():
    client = make_client()

    preparation = (
        client
        .build_first_customer_http_first_controlled_sandbox_attempt_preparation(
            name="Cliente First Controlled Attempt Aurea Gold",
            cpf_cnpj="12345678909",
            email="cliente.first.controlled@example.com",
            mobile_phone="11999999999",
        )
    )

    contract = preparation.first_controlled_sandbox_attempt_preparation

    assert preparation.first_controlled_attempt_preparation_reference == (
        "first-customer-http-first-controlled-sandbox-attempt-preparation"
    )
    assert (
        preparation.first_controlled_sandbox_attempt_preparation_defined
        is True
    )
    assert (
        preparation.final_manual_execution_runbook_readiness_gate_valid
        is False
    )
    assert (
        preparation.first_controlled_sandbox_attempt_preparation_valid
        is False
    )
    assert (
        preparation.ready_for_first_controlled_sandbox_attempt_review
        is False
    )
    assert preparation.manual_operator_review_required is True
    assert preparation.sandbox_base_url_confirmation_required is True
    assert preparation.environment_secret_loading_only_required is True
    assert preparation.no_production_credentials_required is True
    assert preparation.no_real_money_or_real_pix_flow_required is True
    assert preparation.sanitized_success_envelope_required is True
    assert preparation.sanitized_error_envelope_required is True
    assert preparation.redacted_logs_only_required is True
    assert preparation.single_controlled_attempt_policy_required is True
    assert preparation.no_retry_loop_required is True
    assert preparation.manual_stop_on_unexpected_response_required is True
    assert preparation.raw_provider_payload_storage_allowed is False
    assert preparation.request_body_logging_allowed is False
    assert preparation.stacktrace_exposure_allowed is False
    assert (
        preparation.first_controlled_attempt_allows_adapter_implementation
        is False
    )
    assert (
        preparation.first_controlled_attempt_allows_adapter_enablement
        is False
    )
    assert preparation.first_controlled_attempt_allows_http_execution is False
    assert preparation.first_controlled_attempt_can_emit_raw_payload is False
    assert preparation.first_controlled_attempt_executed is False
    assert preparation.adapter_shell_enabled is False
    assert preparation.adapter_implemented is False
    assert preparation.adapter_enabled is False
    assert preparation.execution_enabled is False
    assert preparation.can_send_http is False
    assert preparation.network_call_allowed is False
    assert preparation.real_money is False
    assert preparation.http_call_executed is False
    assert preparation.sandbox_only is True

    assert contract["target_method"] == "POST"
    assert contract["target_path"] == "/customers"
    assert contract["target_environment"] == "sandbox"
    assert (
        contract["requires_final_manual_execution_runbook_readiness_gate"]
        is True
    )
    assert contract["requires_manual_operator_review"] is True
    assert contract["requires_sandbox_base_url_confirmation"] is True
    assert contract["requires_environment_secret_loading_only"] is True
    assert contract["requires_no_production_credentials"] is True
    assert contract["requires_no_real_money_or_real_pix_flow"] is True
    assert contract["requires_sanitized_success_envelope"] is True
    assert contract["requires_sanitized_error_envelope"] is True
    assert contract["requires_redacted_logs_only"] is True
    assert contract["requires_single_controlled_attempt_policy"] is True
    assert contract["requires_no_retry_loop"] is True
    assert contract["requires_manual_stop_on_unexpected_response"] is True
    assert contract["requires_no_raw_provider_payload_storage"] is True
    assert contract["requires_no_request_body_logging"] is True
    assert contract["requires_no_stacktrace_exposure"] is True
    assert contract["first_controlled_attempt_not_executed"] is True
    assert contract["current_preparation_is_non_executing"] is True


def test_first_customer_http_first_controlled_sandbox_attempt_preparation_defines_checklist():
    client = make_client()

    preparation = (
        client
        .build_first_customer_http_first_controlled_sandbox_attempt_preparation(
            name="Cliente First Controlled Attempt Aurea Gold",
            cpf_cnpj="12345678909",
            email="cliente.first.controlled@example.com",
            mobile_phone="11999999999",
        )
    )

    assert preparation.first_controlled_attempt_checklist == [
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


def test_first_customer_http_first_controlled_sandbox_attempt_preparation_valid_chain_non_executing():
    client = make_client()
    explicit_phrase = (
        "CONFIRMO PREFLIGHT DE HABILITACAO EXPLICITA ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )
    runtime_phrase = (
        "CONFIRMO CONTRATO DE HABILITACAO RUNTIME ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )
    switch_phrase = (
        "CONFIRMO GUARD DO SWITCH RUNTIME ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )
    execution_phrase = (
        "CONFIRMO CONTRATO DO GATE DE EXECUCAO ASAAS SANDBOX, "
        "SEM PRODUCAO E SEM DINHEIRO REAL."
    )

    preparation = (
        client
        .build_first_customer_http_first_controlled_sandbox_attempt_preparation(
            name="Cliente First Controlled Attempt Aurea Gold",
            cpf_cnpj="12345678909",
            email="cliente.first.controlled@example.com",
            mobile_phone="11999999999",
            manual_authorization_phrase=(
                ASAAS_SANDBOX_MANUAL_AUTHORIZATION_PHRASE
            ),
            explicit_enable_phrase=explicit_phrase,
            runtime_enable_phrase=runtime_phrase,
            runtime_switch_phrase=switch_phrase,
            execution_gate_phrase=execution_phrase,
        )
    )

    summary = preparation.safe_summary()

    assert summary["operation"] == (
        "first_customer_http_first_controlled_sandbox_attempt_preparation"
    )
    assert (
        summary["final_manual_execution_runbook_readiness_gate_valid"]
        is True
    )
    assert (
        summary["first_controlled_sandbox_attempt_preparation_valid"]
        is True
    )
    assert (
        summary["ready_for_first_controlled_sandbox_attempt_review"]
        is True
    )
    assert summary["manual_operator_review_required"] is True
    assert summary["sandbox_base_url_confirmation_required"] is True
    assert summary["environment_secret_loading_only_required"] is True
    assert summary["no_production_credentials_required"] is True
    assert summary["no_real_money_or_real_pix_flow_required"] is True
    assert summary["sanitized_success_envelope_required"] is True
    assert summary["sanitized_error_envelope_required"] is True
    assert summary["redacted_logs_only_required"] is True
    assert summary["single_controlled_attempt_policy_required"] is True
    assert summary["no_retry_loop_required"] is True
    assert summary["manual_stop_on_unexpected_response_required"] is True
    assert summary["raw_provider_payload_storage_allowed"] is False
    assert summary["request_body_logging_allowed"] is False
    assert summary["stacktrace_exposure_allowed"] is False
    assert (
        summary["first_controlled_attempt_allows_adapter_implementation"]
        is False
    )
    assert summary["first_controlled_attempt_allows_adapter_enablement"] is False
    assert summary["first_controlled_attempt_allows_http_execution"] is False
    assert summary["first_controlled_attempt_can_emit_raw_payload"] is False
    assert summary["first_controlled_attempt_executed"] is False
    assert summary["adapter_shell_enabled"] is False
    assert summary["adapter_implemented"] is False
    assert summary["adapter_enabled"] is False
    assert summary["execution_enabled"] is False
    assert summary["can_send_http"] is False
    assert summary["network_call_allowed"] is False
    assert summary["real_money"] is False
    assert summary["http_call_executed"] is False
    assert summary["ready_for_http_execution"] is False
    assert summary["next_step_required"] == (
        "operator_decision_before_any_real_sandbox_http_call"
    )
    assert summary["prepared_request"]["operation"] == "create_customer"
    assert summary["prepared_request"]["http_call_executed"] is False
    assert (
        summary["final_manual_execution_runbook_readiness_gate"][
            "final_manual_execution_runbook_readiness_gate_valid"
        ]
        is True
    )
    assert "sandbox-api-key-for-test-only" not in repr(summary)
    assert "sandbox-webhook-token-for-test-only" not in repr(summary)
    assert "access_token" not in repr(summary["prepared_request"])


def test_prepare_create_pix_payment_builds_sandbox_request_without_http_call():
    client = make_client()

    request = client.prepare_create_pix_payment(
        customer_id="cus_xxxxxxxx",
        value=Decimal("50.00"),
        due_date="2026-07-10",
        description="Teste cobranca Pix Sandbox Aurea Gold",
    )

    assert request.method == "POST"
    assert request.url == f"{ASAAS_SANDBOX_BASE_URL}/payments"
    assert request.operation == "create_pix_payment"
    assert request.headers_configured is True
    assert request.real_money is False
    assert request.http_call_executed is False
    assert request.json == {
        "customer": "cus_xxxxxxxx",
        "billingType": "PIX",
        "value": 50.0,
        "dueDate": "2026-07-10",
        "description": "Teste cobranca Pix Sandbox Aurea Gold",
    }


def test_prepare_get_pix_qr_code_builds_sandbox_request_without_http_call():
    client = make_client()

    request = client.prepare_get_pix_qr_code(payment_id="pay_xxxxxxxx")

    assert request.method == "GET"
    assert request.url == f"{ASAAS_SANDBOX_BASE_URL}/payments/pay_xxxxxxxx/pixQrCode"
    assert request.operation == "get_pix_qr_code"
    assert request.json is None
    assert request.real_money is False
    assert request.http_call_executed is False


def test_prepare_get_payment_status_builds_sandbox_request_without_http_call():
    client = make_client()

    request = client.prepare_get_payment_status(payment_id="pay_xxxxxxxx")

    assert request.method == "GET"
    assert request.url == f"{ASAAS_SANDBOX_BASE_URL}/payments/pay_xxxxxxxx"
    assert request.operation == "get_payment_status"
    assert request.json is None
    assert request.real_money is False
    assert request.http_call_executed is False


def test_execute_prepared_request_is_blocked_in_this_milestone():
    client = make_client()
    request = client.prepare_get_payment_status(payment_id="pay_xxxxxxxx")

    with pytest.raises(RuntimeError, match="HTTP execution is intentionally blocked"):
        client.execute_prepared_request(request)

    assert request.http_call_executed is False


def test_prepared_request_safe_summary_does_not_include_secrets():
    client = make_client()
    request = client.prepare_get_payment_status(payment_id="pay_xxxxxxxx")

    summary = request.safe_summary()

    assert summary["http_call_executed"] is False
    assert summary["real_money"] is False
    assert "sandbox-api-key-for-test-only" not in repr(summary)
    assert "sandbox-webhook-token-for-test-only" not in repr(summary)


def test_customer_dry_run_reuses_create_customer_request_without_http_call():
    client = make_client()

    dry_run = client.dry_run_create_customer(
        name="Cliente Dry Run Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.dryrun@example.com",
        mobile_phone="11999999999",
    )

    request = dry_run.prepared_request

    assert dry_run.customer_reference == "dry-run-customer-sandbox"
    assert dry_run.real_money is False
    assert dry_run.http_call_executed is False
    assert request.method == "POST"
    assert request.url == f"{ASAAS_SANDBOX_BASE_URL}/customers"
    assert request.operation == "create_customer"
    assert request.real_money is False
    assert request.http_call_executed is False
    assert request.json == {
        "name": "Cliente Dry Run Aurea Gold",
        "cpfCnpj": "12345678909",
        "email": "cliente.dryrun@example.com",
        "mobilePhone": "11999999999",
    }


def test_customer_dry_run_safe_summary_keeps_http_blocked_and_hides_secrets():
    client = make_client()

    dry_run = client.dry_run_create_customer(
        name="Cliente Dry Run Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.dryrun@example.com",
        mobile_phone="11999999999",
    )

    summary = dry_run.safe_summary()

    assert summary["operation"] == "customer_dry_run"
    assert summary["ready_for_http_execution"] is False
    assert summary["real_money"] is False
    assert summary["http_call_executed"] is False
    assert summary["prepared_request"]["operation"] == "create_customer"
    assert summary["prepared_request"]["http_call_executed"] is False
    assert "sandbox-api-key-for-test-only" not in repr(summary)
    assert "sandbox-webhook-token-for-test-only" not in repr(summary)


def test_payment_dry_run_reuses_pix_payment_request_without_http_call():
    client = make_client()

    dry_run = client.dry_run_create_pix_payment(
        customer_id="cus_dry_run_xxxxxxxx",
        value=Decimal("75.50"),
        due_date="2026-07-15",
        description="Dry run cobranca Pix Sandbox Aurea Gold",
    )

    request = dry_run.prepared_request

    assert dry_run.payment_reference == "dry-run-pix-payment-sandbox"
    assert dry_run.billing_type == "PIX"
    assert dry_run.real_money is False
    assert dry_run.http_call_executed is False
    assert request.method == "POST"
    assert request.url == f"{ASAAS_SANDBOX_BASE_URL}/payments"
    assert request.operation == "create_pix_payment"
    assert request.real_money is False
    assert request.http_call_executed is False
    assert request.json == {
        "customer": "cus_dry_run_xxxxxxxx",
        "billingType": "PIX",
        "value": 75.5,
        "dueDate": "2026-07-15",
        "description": "Dry run cobranca Pix Sandbox Aurea Gold",
    }


def test_payment_dry_run_safe_summary_keeps_http_blocked_and_hides_secrets():
    client = make_client()

    dry_run = client.dry_run_create_pix_payment(
        customer_id="cus_dry_run_xxxxxxxx",
        value=Decimal("75.50"),
        due_date="2026-07-15",
        description="Dry run cobranca Pix Sandbox Aurea Gold",
    )

    summary = dry_run.safe_summary()

    assert summary["operation"] == "payment_dry_run"
    assert summary["billing_type"] == "PIX"
    assert summary["ready_for_http_execution"] is False
    assert summary["real_money"] is False
    assert summary["http_call_executed"] is False
    assert summary["prepared_request"]["operation"] == "create_pix_payment"
    assert summary["prepared_request"]["http_call_executed"] is False
    assert "sandbox-api-key-for-test-only" not in repr(summary)
    assert "sandbox-webhook-token-for-test-only" not in repr(summary)


def test_pix_qr_code_dry_run_reuses_qr_code_request_without_http_call():
    client = make_client()

    dry_run = client.dry_run_get_pix_qr_code(payment_id="pay_dry_run_xxxxxxxx")

    request = dry_run.prepared_request

    assert dry_run.qr_code_reference == "dry-run-pix-qr-code-sandbox"
    assert dry_run.real_money is False
    assert dry_run.http_call_executed is False
    assert request.method == "GET"
    assert request.url == f"{ASAAS_SANDBOX_BASE_URL}/payments/pay_dry_run_xxxxxxxx/pixQrCode"
    assert request.operation == "get_pix_qr_code"
    assert request.json is None
    assert request.real_money is False
    assert request.http_call_executed is False


def test_pix_qr_code_dry_run_safe_summary_keeps_http_blocked_and_hides_secrets():
    client = make_client()

    dry_run = client.dry_run_get_pix_qr_code(payment_id="pay_dry_run_xxxxxxxx")

    summary = dry_run.safe_summary()

    assert summary["operation"] == "pix_qr_code_dry_run"
    assert summary["ready_for_http_execution"] is False
    assert summary["real_money"] is False
    assert summary["http_call_executed"] is False
    assert summary["prepared_request"]["operation"] == "get_pix_qr_code"
    assert summary["prepared_request"]["http_call_executed"] is False
    assert "sandbox-api-key-for-test-only" not in repr(summary)
    assert "sandbox-webhook-token-for-test-only" not in repr(summary)


def test_payment_status_dry_run_reuses_status_request_without_http_call():
    client = make_client()

    dry_run = client.dry_run_get_payment_status(payment_id="pay_dry_run_xxxxxxxx")

    request = dry_run.prepared_request

    assert dry_run.status_reference == "dry-run-payment-status-sandbox"
    assert dry_run.real_money is False
    assert dry_run.http_call_executed is False
    assert request.method == "GET"
    assert request.url == f"{ASAAS_SANDBOX_BASE_URL}/payments/pay_dry_run_xxxxxxxx"
    assert request.operation == "get_payment_status"
    assert request.json is None
    assert request.real_money is False
    assert request.http_call_executed is False


def test_payment_status_dry_run_safe_summary_keeps_http_blocked_and_hides_secrets():
    client = make_client()

    dry_run = client.dry_run_get_payment_status(payment_id="pay_dry_run_xxxxxxxx")

    summary = dry_run.safe_summary()

    assert summary["operation"] == "payment_status_dry_run"
    assert summary["ready_for_http_execution"] is False
    assert summary["real_money"] is False
    assert summary["http_call_executed"] is False
    assert summary["prepared_request"]["operation"] == "get_payment_status"
    assert summary["prepared_request"]["http_call_executed"] is False
    assert "sandbox-api-key-for-test-only" not in repr(summary)
    assert "sandbox-webhook-token-for-test-only" not in repr(summary)

def test_full_pix_flow_dry_run_reuses_all_steps_without_http_call():
    client = make_client()

    flow = client.dry_run_full_pix_flow(
        name="Cliente Fluxo Completo Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.fullflow@example.com",
        mobile_phone="11999999999",
        value=Decimal("99.90"),
        due_date="2026-07-20",
        description="Dry run fluxo completo Pix Sandbox Aurea Gold",
    )

    assert flow.flow_reference == "dry-run-full-pix-flow-sandbox"
    assert flow.real_money is False
    assert flow.http_call_executed is False

    assert flow.customer.prepared_request.method == "POST"
    assert flow.customer.prepared_request.url == f"{ASAAS_SANDBOX_BASE_URL}/customers"
    assert flow.customer.prepared_request.operation == "create_customer"
    assert flow.customer.prepared_request.http_call_executed is False

    assert flow.payment.prepared_request.method == "POST"
    assert flow.payment.prepared_request.url == f"{ASAAS_SANDBOX_BASE_URL}/payments"
    assert flow.payment.prepared_request.operation == "create_pix_payment"
    assert flow.payment.prepared_request.json == {
        "customer": "cus_dry_run_full_flow",
        "billingType": "PIX",
        "value": 99.9,
        "dueDate": "2026-07-20",
        "description": "Dry run fluxo completo Pix Sandbox Aurea Gold",
    }
    assert flow.payment.prepared_request.http_call_executed is False

    assert flow.pix_qr_code.prepared_request.method == "GET"
    assert flow.pix_qr_code.prepared_request.url == (
        f"{ASAAS_SANDBOX_BASE_URL}/payments/pay_dry_run_full_flow/pixQrCode"
    )
    assert flow.pix_qr_code.prepared_request.operation == "get_pix_qr_code"
    assert flow.pix_qr_code.prepared_request.http_call_executed is False

    assert flow.payment_status.prepared_request.method == "GET"
    assert flow.payment_status.prepared_request.url == (
        f"{ASAAS_SANDBOX_BASE_URL}/payments/pay_dry_run_full_flow"
    )
    assert flow.payment_status.prepared_request.operation == "get_payment_status"
    assert flow.payment_status.prepared_request.http_call_executed is False


def test_full_pix_flow_dry_run_safe_summary_keeps_every_step_blocked():
    client = make_client()

    flow = client.dry_run_full_pix_flow(
        name="Cliente Fluxo Completo Aurea Gold",
        cpf_cnpj="12345678909",
        email="cliente.fullflow@example.com",
        mobile_phone="11999999999",
        value=Decimal("99.90"),
        due_date="2026-07-20",
        description="Dry run fluxo completo Pix Sandbox Aurea Gold",
    )

    summary = flow.safe_summary()

    assert summary["operation"] == "full_pix_flow_dry_run"
    assert summary["flow_reference"] == "dry-run-full-pix-flow-sandbox"
    assert summary["steps"] == [
        "customer_dry_run",
        "payment_dry_run",
        "pix_qr_code_dry_run",
        "payment_status_dry_run",
    ]
    assert summary["ready_for_http_execution"] is False
    assert summary["real_money"] is False
    assert summary["http_call_executed"] is False
    assert summary["customer"]["prepared_request"]["http_call_executed"] is False
    assert summary["payment"]["prepared_request"]["http_call_executed"] is False
    assert summary["pix_qr_code"]["prepared_request"]["http_call_executed"] is False
    assert summary["payment_status"]["prepared_request"]["http_call_executed"] is False
    assert "sandbox-api-key-for-test-only" not in repr(summary)
    assert "sandbox-webhook-token-for-test-only" not in repr(summary)

def test_subaccount_structure_guard_prepares_accounts_endpoint_without_http_call():
    client = make_client()

    guard = client.build_subaccount_structure_guard()
    request = guard.prepared_request

    assert guard.guard_reference == "subaccount-structure-guard-sandbox"
    assert guard.endpoint_path == "/accounts"
    assert guard.target_operation == "create_subaccount"
    assert guard.sandbox_only is True
    assert guard.production_blocked is True
    assert guard.manual_authorization_required is True
    assert guard.can_create_subaccount is False
    assert guard.can_send_http is False
    assert guard.real_money is False
    assert guard.http_call_executed is False
    assert guard.future_result_marker == "ASAAS_SANDBOX_SUBACCOUNT_STRUCTURE_VALIDATED"

    assert request.method == "POST"
    assert request.url == f"{ASAAS_SANDBOX_BASE_URL}/accounts"
    assert request.operation == "create_subaccount_structure_guard"
    assert request.headers_configured is True
    assert request.real_money is False
    assert request.http_call_executed is False
    assert request.json is None
    assert request.raw["sandbox"] is True
    assert request.raw["provider"] == "asaas"
    assert request.raw["http_execution_blocked"] is True


def test_subaccount_structure_guard_safe_summary_hides_sensitive_values():
    client = make_client()

    guard = client.build_subaccount_structure_guard()
    summary = guard.safe_summary()
    rendered_summary = repr(summary)

    assert summary["operation"] == "subaccount_structure_guard"
    assert summary["prepared_request"]["operation"] == (
        "create_subaccount_structure_guard"
    )
    assert summary["prepared_request"]["json_payload_stored"] is False
    assert summary["sandbox_only"] is True
    assert summary["production_blocked"] is True
    assert summary["can_create_subaccount"] is False
    assert summary["can_send_http"] is False
    assert summary["ready_for_http_execution"] is False
    assert summary["real_money"] is False
    assert summary["http_call_executed"] is False
    assert summary["sensitive_response_fields_masked"] is True
    assert summary["sensitive_request_fields_masked"] is True
    assert "apiKey" in summary["sensitive_response_fields"]
    assert "walletId" in summary["sensitive_response_fields"]
    assert "onboardingUrl" in summary["sensitive_response_fields"]

    assert "sandbox-api-key-for-test-only" not in rendered_summary
    assert "sandbox-webhook-token-for-test-only" not in rendered_summary
    assert "subaccount-api-key-for-test-only" not in rendered_summary
    assert "wallet-id-for-test-only" not in rendered_summary
    assert "https://sandbox.asaas.com/onboarding/test-only" not in rendered_summary

def test_subaccount_payload_contract_maps_required_fields_without_values():
    client = make_client()

    contract = client.build_subaccount_payload_contract()
    summary = contract.safe_summary()

    assert contract.contract_reference == "subaccount-payload-contract-sandbox"
    assert contract.endpoint_path == "/accounts"
    assert contract.method == "POST"
    assert contract.target_operation == "create_subaccount"
    assert contract.request_body_build_enabled is False
    assert contract.payload_values_stored is False
    assert contract.raw_payload_stored is False
    assert contract.sandbox_only is True
    assert contract.production_blocked is True
    assert contract.manual_authorization_required is True
    assert contract.can_create_subaccount is False
    assert contract.can_send_http is False
    assert contract.real_money is False
    assert contract.http_call_executed is False
    assert contract.future_result_marker == (
        "ASAAS_SANDBOX_SUBACCOUNT_PAYLOAD_CONTRACT_READY"
    )

    assert summary["operation"] == "subaccount_payload_contract"
    assert summary["field_names_only"] is True
    assert summary["field_values_masked"] is True
    assert summary["secret_values_allowed"] is False
    assert summary["ready_for_http_execution"] is False
    assert summary["structure_guard"]["operation"] == "subaccount_structure_guard"
    assert summary["structure_guard"]["prepared_request"]["url"] == (
        f"{ASAAS_SANDBOX_BASE_URL}/accounts"
    )

    for field_name in (
        "name",
        "email",
        "cpfCnpj",
        "mobilePhone",
        "incomeValue",
        "address",
        "addressNumber",
        "province",
        "postalCode",
    ):
        assert field_name in summary["required_request_fields"]


def test_subaccount_payload_contract_blocks_secret_and_response_only_fields():
    client = make_client()

    contract = client.build_subaccount_payload_contract()
    summary = contract.safe_summary()
    rendered_summary = repr(summary)

    for field_name in (
        "apiKey",
        "walletId",
        "id",
        "onboardingUrl",
        "access_token",
        "asaas-access-token",
        "webhook_token",
        "ASAAS_API_KEY",
        "ASAAS_WEBHOOK_TOKEN",
    ):
        assert field_name in summary["prohibited_request_fields"]

    for field_name in (
        "apiKey",
        "walletId",
        "id",
        "onboardingUrl",
    ):
        assert field_name in summary["sensitive_response_fields"]

    for field_name in (
        "cpfCnpj",
        "email",
        "loginEmail",
        "mobilePhone",
        "address",
        "postalCode",
        "incomeValue",
    ):
        assert field_name in summary["sensitive_request_fields"]

    assert "webhooks" in summary["future_review_request_fields"]
    assert "sandbox-api-key-for-test-only" not in rendered_summary
    assert "sandbox-webhook-token-for-test-only" not in rendered_summary
    assert "subaccount-api-key-for-test-only" not in rendered_summary
    assert "wallet-id-for-test-only" not in rendered_summary
    assert "https://sandbox.asaas.com/onboarding/test-only" not in rendered_summary

def test_subaccount_payload_builder_guard_builds_template_without_http_call():
    client = make_client()

    builder = client.build_subaccount_payload_builder_guard()
    request = builder.prepared_request
    summary = builder.safe_summary()

    assert builder.builder_reference == "subaccount-payload-builder-guard-sandbox"
    assert builder.endpoint_path == "/accounts"
    assert builder.method == "POST"
    assert builder.target_operation == "create_subaccount"
    assert builder.template_payload_built is True
    assert builder.synthetic_payload_only is True
    assert builder.payload_values_stored is False
    assert builder.raw_payload_stored is False
    assert builder.sandbox_only is True
    assert builder.production_blocked is True
    assert builder.manual_authorization_required is True
    assert builder.can_create_subaccount is False
    assert builder.can_send_http is False
    assert builder.real_money is False
    assert builder.http_call_executed is False
    assert builder.future_result_marker == (
        "ASAAS_SANDBOX_SUBACCOUNT_PAYLOAD_BUILDER_GUARD_READY"
    )

    assert request.method == "POST"
    assert request.url == f"{ASAAS_SANDBOX_BASE_URL}/accounts"
    assert request.operation == "create_subaccount_payload_builder_guard"
    assert request.headers_configured is True
    assert request.real_money is False
    assert request.http_call_executed is False
    assert request.raw["http_execution_blocked"] is True

    assert request.json == {
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

    assert summary["operation"] == "subaccount_payload_builder_guard"
    assert summary["template_payload_built"] is True
    assert summary["synthetic_payload_only"] is True
    assert summary["payload_template_values_masked"] is True
    assert summary["ready_for_http_execution"] is False
    assert summary["prohibited_template_fields"] == []


def test_subaccount_payload_builder_guard_safe_summary_masks_template_values():
    client = make_client()

    builder = client.build_subaccount_payload_builder_guard()
    summary = builder.safe_summary()
    rendered_summary = repr(summary)

    for field_name in (
        "name",
        "email",
        "cpfCnpj",
        "mobilePhone",
        "incomeValue",
        "address",
        "addressNumber",
        "province",
        "postalCode",
    ):
        assert field_name in summary["payload_template_field_names"]
        assert summary["sanitized_payload_preview"][field_name] == "<masked>"

    assert summary["payload_contract"]["operation"] == "subaccount_payload_contract"
    assert summary["payload_contract"]["ready_for_http_execution"] is False
    assert summary["prepared_request"]["operation"] == (
        "create_subaccount_payload_builder_guard"
    )
    assert summary["prepared_request"]["json_payload_template_stored"] is True
    assert summary["prepared_request"]["http_call_executed"] is False

    assert "<sandbox-subaccount-cpf-cnpj>" not in rendered_summary
    assert "<sandbox-subaccount-email>" not in rendered_summary
    assert "<sandbox-subaccount-mobile-phone>" not in rendered_summary
    assert "sandbox-api-key-for-test-only" not in rendered_summary
    assert "sandbox-webhook-token-for-test-only" not in rendered_summary
    assert "subaccount-api-key-for-test-only" not in rendered_summary
    assert "wallet-id-for-test-only" not in rendered_summary
    assert "https://sandbox.asaas.com/onboarding/test-only" not in rendered_summary

def test_subaccount_sanitized_fixture_marks_sensitive_response_fields_present():
    client = make_client()

    fixture = client.build_subaccount_sanitized_fixture()
    summary = fixture.safe_summary()

    assert fixture.fixture_reference == "subaccount-sanitized-fixture-sandbox"
    assert fixture.fixture_source == "synthetic_sandbox_subaccount_response_fixture"
    assert fixture.raw_response_stored is False
    assert fixture.raw_payload_stored is False
    assert fixture.sandbox_only is True
    assert fixture.production_blocked is True
    assert fixture.synthetic_fixture_only is True
    assert fixture.can_create_subaccount is False
    assert fixture.can_send_http is False
    assert fixture.real_money is False
    assert fixture.http_call_executed is False
    assert fixture.api_key_present is True
    assert fixture.wallet_id_present is True
    assert fixture.account_id_present is True
    assert fixture.onboarding_url_present is True
    assert fixture.future_result_marker == (
        "ASAAS_SANDBOX_SUBACCOUNT_SANITIZED_FIXTURE_READY"
    )

    assert summary["operation"] == "subaccount_sanitized_fixture"
    assert summary["builder_guard"]["operation"] == (
        "subaccount_payload_builder_guard"
    )
    assert summary["raw_response_stored"] is False
    assert summary["raw_payload_stored"] is False
    assert summary["sensitive_response_values_masked"] is True
    assert summary["ready_for_http_execution"] is False

    for field_name in ("apiKey", "walletId", "id", "onboardingUrl"):
        assert field_name in summary["sensitive_response_fields"]
        assert summary["sanitized_response_fixture"][field_name] == "<masked>"


def test_subaccount_sanitized_fixture_safe_summary_exposes_no_secret_values():
    client = make_client()

    fixture = client.build_subaccount_sanitized_fixture()
    summary = fixture.safe_summary()
    rendered_summary = repr(summary)

    assert summary["sanitized_response_fixture"] == {
        "object": "account",
        "id": "<masked>",
        "apiKey": "<masked>",
        "walletId": "<masked>",
        "onboardingUrl": "<masked>",
        "status": "sandbox_fixture_only",
    }
    assert summary["can_send_http"] is False
    assert summary["can_create_subaccount"] is False
    assert summary["real_money"] is False
    assert summary["http_call_executed"] is False

    assert "sandbox-api-key-for-test-only" not in rendered_summary
    assert "sandbox-webhook-token-for-test-only" not in rendered_summary
    assert "subaccount-api-key-for-test-only" not in rendered_summary
    assert "wallet-id-for-test-only" not in rendered_summary
    assert "acct_" not in rendered_summary
    assert "https://sandbox.asaas.com/onboarding/test-only" not in rendered_summary
    assert "<sandbox-subaccount-cpf-cnpj>" not in rendered_summary
    assert "<sandbox-subaccount-email>" not in rendered_summary
    assert "<sandbox-subaccount-mobile-phone>" not in rendered_summary


def test_subaccount_response_sanitizer_contract_defines_safe_output_rules():
    client = make_client()

    contract = client.build_subaccount_response_sanitizer_contract()
    summary = contract.safe_summary()

    assert contract.contract_reference == (
        "subaccount-response-sanitizer-contract-sandbox"
    )
    assert contract.sanitizer_reference == "subaccount-response-sanitizer-sandbox"
    assert contract.raw_response_input_expected is True
    assert contract.raw_response_stored is False
    assert contract.raw_payload_stored is False
    assert contract.raw_secret_values_retained is False
    assert contract.sandbox_only is True
    assert contract.production_blocked is True
    assert contract.synthetic_contract_only is True
    assert contract.can_create_subaccount is False
    assert contract.can_send_http is False
    assert contract.real_money is False
    assert contract.http_call_executed is False
    assert contract.future_result_marker == (
        "ASAAS_SANDBOX_SUBACCOUNT_RESPONSE_SANITIZER_CONTRACT_READY"
    )

    assert summary["operation"] == "subaccount_response_sanitizer_contract"
    assert summary["contract_reference"] == contract.contract_reference
    assert summary["sanitizer_reference"] == contract.sanitizer_reference
    assert summary["sanitized_fixture"]["operation"] == "subaccount_sanitized_fixture"
    assert summary["raw_response_input_expected"] is True
    assert summary["raw_response_stored"] is False
    assert summary["raw_payload_stored"] is False
    assert summary["raw_secret_values_retained"] is False
    assert summary["masking_required"] is True
    assert summary["secret_values_allowed"] is False
    assert summary["ready_for_http_execution"] is False
    assert summary["next_step_required"] == (
        "manual_subaccount_response_sanitizer_implementation_review"
    )

    for field_name in (
        "api_key_present",
        "wallet_id_present",
        "account_id_present",
        "onboarding_url_present",
        "sensitive_response_values_masked",
    ):
        assert field_name in summary["safe_output_fields"]


def test_subaccount_response_sanitizer_contract_blocks_raw_secret_storage():
    client = make_client()

    contract = client.build_subaccount_response_sanitizer_contract()
    summary = contract.safe_summary()
    rendered_summary = repr(summary)

    for field_name in ("apiKey", "walletId", "id", "onboardingUrl"):
        assert field_name in summary["sensitive_input_fields"]
        assert field_name in summary["masked_output_fields"]
        assert field_name in summary["blocked_storage_fields"]

    assert "raw_response" in summary["blocked_storage_fields"]
    assert "raw_payload" in summary["blocked_storage_fields"]
    assert summary["raw_response_stored"] is False
    assert summary["raw_payload_stored"] is False
    assert summary["raw_secret_values_retained"] is False
    assert summary["can_send_http"] is False
    assert summary["can_create_subaccount"] is False
    assert summary["real_money"] is False
    assert summary["http_call_executed"] is False

    assert "sandbox-api-key-for-test-only" not in rendered_summary
    assert "sandbox-webhook-token-for-test-only" not in rendered_summary
    assert "subaccount-api-key-for-test-only" not in rendered_summary
    assert "wallet-id-for-test-only" not in rendered_summary
    assert "acct_" not in rendered_summary
    assert "https://sandbox.asaas.com/onboarding/test-only" not in rendered_summary
    assert "<sandbox-subaccount-cpf-cnpj>" not in rendered_summary
    assert "<sandbox-subaccount-email>" not in rendered_summary
    assert "<sandbox-subaccount-mobile-phone>" not in rendered_summary


def test_subaccount_response_sanitizer_implementation_returns_safe_output():
    client = make_client()

    result = client.sanitize_subaccount_response(
        {
            "object": "account",
            "id": "acct_subaccount_for_test_only",
            "apiKey": "subaccount-api-key-for-test-only",
            "walletId": "wallet-id-for-test-only",
            "onboardingUrl": "https://sandbox.asaas.com/onboarding/test-only",
            "status": "sandbox_fixture_only",
        }
    )
    summary = result.safe_summary()
    sanitized_output = summary["sanitized_output"]

    assert result.implementation_reference == (
        "subaccount-response-sanitizer-implementation-sandbox"
    )
    assert result.sanitizer_reference == "subaccount-response-sanitizer-sandbox"
    assert result.raw_response_input_received is True
    assert result.raw_response_stored is False
    assert result.raw_payload_stored is False
    assert result.raw_secret_values_retained is False
    assert result.sanitizer_implemented is True
    assert result.sandbox_only is True
    assert result.production_blocked is True
    assert result.synthetic_input_only is True
    assert result.can_create_subaccount is False
    assert result.can_send_http is False
    assert result.real_money is False
    assert result.http_call_executed is False

    assert summary["operation"] == "subaccount_response_sanitizer_implementation"
    assert summary["contract"]["operation"] == (
        "subaccount_response_sanitizer_contract"
    )
    assert summary["masking_required"] is True
    assert summary["secret_values_allowed"] is False
    assert summary["ready_for_http_execution"] is False
    assert summary["next_step_required"] == (
        "manual_subaccount_response_sanitizer_execution_review"
    )
    assert summary["future_result_marker"] == (
        "ASAAS_SANDBOX_SUBACCOUNT_RESPONSE_SANITIZER_IMPLEMENTATION_READY"
    )

    assert sanitized_output == {
        "object": "account",
        "status": "sandbox_fixture_only",
        "api_key_present": True,
        "wallet_id_present": True,
        "account_id_present": True,
        "onboarding_url_present": True,
        "sensitive_response_values_masked": True,
    }


def test_subaccount_response_sanitizer_implementation_exposes_no_raw_values():
    client = make_client()

    result = client.sanitize_subaccount_response(
        {
            "object": "account",
            "id": "acct_subaccount_for_test_only",
            "apiKey": "subaccount-api-key-for-test-only",
            "walletId": "wallet-id-for-test-only",
            "onboardingUrl": "https://sandbox.asaas.com/onboarding/test-only",
            "status": "sandbox_fixture_only",
            "ignoredRawField": "this-raw-field-must-not-be-exposed",
        }
    )
    summary = result.safe_summary()
    rendered_summary = repr(summary)

    assert summary["raw_response_stored"] is False
    assert summary["raw_payload_stored"] is False
    assert summary["raw_secret_values_retained"] is False
    assert summary["can_send_http"] is False
    assert summary["can_create_subaccount"] is False
    assert summary["real_money"] is False
    assert summary["http_call_executed"] is False

    assert "subaccount-api-key-for-test-only" not in rendered_summary
    assert "wallet-id-for-test-only" not in rendered_summary
    assert "acct_subaccount_for_test_only" not in rendered_summary
    assert "https://sandbox.asaas.com/onboarding/test-only" not in rendered_summary
    assert "this-raw-field-must-not-be-exposed" not in rendered_summary
    assert "sandbox-api-key-for-test-only" not in rendered_summary
    assert "sandbox-webhook-token-for-test-only" not in rendered_summary


def test_subaccount_manual_execution_gate_records_valid_manual_phrase_without_http():
    client = make_client()

    gate = client.gate_subaccount_manual_execution(
        manual_authorization_phrase=ASAAS_SANDBOX_MANUAL_AUTHORIZATION_PHRASE,
    )
    summary = gate.safe_summary()

    assert gate.gate_reference == "subaccount-manual-execution-gate-sandbox"
    assert gate.target_method == "POST"
    assert gate.target_path == "/accounts"
    assert gate.manual_authorization_registered is True
    assert gate.manual_authorization_valid is True
    assert gate.gate_defined is True
    assert gate.gate_allows_http_execution is False
    assert gate.execution_enabled is False
    assert gate.sandbox_only is True
    assert gate.production_blocked is True
    assert gate.synthetic_input_only is True
    assert gate.can_create_subaccount is False
    assert gate.can_send_http is False
    assert gate.network_call_allowed is False
    assert gate.real_money is False
    assert gate.http_call_executed is False

    assert summary["operation"] == "subaccount_manual_execution_gate"
    assert summary["response_sanitizer_result"]["operation"] == (
        "subaccount_response_sanitizer_implementation"
    )
    assert summary["manual_authorization_registered"] is True
    assert summary["manual_authorization_valid"] is True
    assert summary["gate_allows_http_execution"] is False
    assert summary["execution_enabled"] is False
    assert summary["can_send_http"] is False
    assert summary["can_create_subaccount"] is False
    assert summary["network_call_allowed"] is False
    assert summary["real_money"] is False
    assert summary["http_call_executed"] is False
    assert summary["ready_for_http_execution"] is False
    assert summary["future_result_marker"] == (
        "ASAAS_SANDBOX_SUBACCOUNT_MANUAL_EXECUTION_GATE_READY"
    )
    assert summary["next_step_required"] == (
        "manual_subaccount_first_post_runbook_review"
    )


def test_subaccount_manual_execution_gate_blocks_invalid_phrase_and_raw_values():
    client = make_client()

    gate = client.gate_subaccount_manual_execution(
        manual_authorization_phrase="EXECUTAR POST SANDBOX SUBCONTA AGORA",
    )
    summary = gate.safe_summary()
    rendered_summary = repr(summary)

    assert summary["manual_authorization_registered"] is False
    assert summary["manual_authorization_valid"] is False
    assert summary["gate_allows_http_execution"] is False
    assert summary["execution_enabled"] is False
    assert summary["can_send_http"] is False
    assert summary["can_create_subaccount"] is False
    assert summary["network_call_allowed"] is False
    assert summary["real_money"] is False
    assert summary["http_call_executed"] is False
    assert summary["approval_checklist"]["http_execution_still_blocked"] is True
    assert summary["approval_checklist"]["secret_exposure_blocked"] is True

    assert "subaccount-api-key-for-test-only" not in rendered_summary
    assert "wallet-id-for-test-only" not in rendered_summary
    assert "acct_subaccount_for_test_only" not in rendered_summary
    assert "https://sandbox.asaas.com/onboarding/test-only" not in rendered_summary
    assert "sandbox-api-key-for-test-only" not in rendered_summary
    assert "sandbox-webhook-token-for-test-only" not in rendered_summary

def test_subaccount_first_controlled_attempt_preflight_validates_manual_gate_without_http():
    client = make_client()

    preflight = client.build_subaccount_first_controlled_attempt_preflight(
        manual_authorization_phrase=ASAAS_SANDBOX_MANUAL_AUTHORIZATION_PHRASE,
    )
    summary = preflight.safe_summary()

    assert preflight.preflight_reference == (
        "subaccount-first-controlled-attempt-preflight-sandbox"
    )
    assert preflight.target_environment == "sandbox"
    assert preflight.target_method == "POST"
    assert preflight.target_path == "/accounts"
    assert preflight.preflight_defined is True
    assert preflight.manual_execution_gate_valid is True
    assert preflight.first_controlled_attempt_preflight_valid is True
    assert preflight.ready_for_first_controlled_attempt_review is True
    assert preflight.manual_operator_review_required is True
    assert preflight.sandbox_base_url_confirmation_required is True
    assert preflight.environment_secret_loading_only_required is True
    assert preflight.no_production_credentials_required is True
    assert preflight.no_real_money_required is True
    assert preflight.payload_builder_guard_required is True
    assert preflight.response_sanitizer_required is True
    assert preflight.redacted_logs_only_required is True
    assert preflight.single_controlled_attempt_policy_required is True
    assert preflight.no_retry_loop_required is True
    assert preflight.manual_stop_on_unexpected_response_required is True
    assert preflight.sanitized_attempt_record_required is True
    assert preflight.raw_payload_storage_allowed is False
    assert preflight.raw_response_storage_allowed is False
    assert preflight.request_body_logging_allowed is False
    assert preflight.first_controlled_attempt_allows_http_execution is False
    assert preflight.first_controlled_attempt_executed is False
    assert preflight.can_create_subaccount is False
    assert preflight.can_send_http is False
    assert preflight.network_call_allowed is False
    assert preflight.real_money is False
    assert preflight.http_call_executed is False
    assert preflight.sandbox_only is True
    assert preflight.production_blocked is True

    assert summary["operation"] == "subaccount_first_controlled_attempt_preflight"
    assert summary["manual_execution_gate"]["operation"] == (
        "subaccount_manual_execution_gate"
    )
    assert summary["manual_execution_gate_valid"] is True
    assert summary["first_controlled_attempt_preflight_valid"] is True
    assert summary["ready_for_first_controlled_attempt_review"] is True
    assert summary["can_create_subaccount"] is False
    assert summary["can_send_http"] is False
    assert summary["network_call_allowed"] is False
    assert summary["real_money"] is False
    assert summary["http_call_executed"] is False
    assert summary["ready_for_http_execution"] is False
    assert summary["future_result_marker"] == (
        "ASAAS_SANDBOX_SUBACCOUNT_FIRST_CONTROLLED_ATTEMPT_PREFLIGHT_READY"
    )
    assert summary["next_step_required"] == (
        "manual_subaccount_first_controlled_attempt_operator_review"
    )

    for confirmation in (
        "confirm_main_branch_clean_and_tagged",
        "confirm_sandbox_environment_only",
        "confirm_no_secret_in_chat_or_docs",
        "confirm_single_controlled_attempt_only",
    ):
        assert confirmation in summary["required_operator_confirmations"]


def test_subaccount_first_controlled_attempt_preflight_blocks_invalid_phrase_and_raw_values():
    client = make_client()

    preflight = client.build_subaccount_first_controlled_attempt_preflight(
        manual_authorization_phrase="EXECUTAR POST SANDBOX SUBCONTA AGORA",
    )
    summary = preflight.safe_summary()
    rendered_summary = repr(summary)

    assert summary["manual_execution_gate_valid"] is False
    assert summary["first_controlled_attempt_preflight_valid"] is False
    assert summary["ready_for_first_controlled_attempt_review"] is False
    assert summary["first_controlled_attempt_allows_http_execution"] is False
    assert summary["first_controlled_attempt_executed"] is False
    assert summary["raw_payload_storage_allowed"] is False
    assert summary["raw_response_storage_allowed"] is False
    assert summary["request_body_logging_allowed"] is False
    assert summary["can_create_subaccount"] is False
    assert summary["can_send_http"] is False
    assert summary["network_call_allowed"] is False
    assert summary["real_money"] is False
    assert summary["http_call_executed"] is False
    assert summary["preflight_checklist"]["current_preflight_is_non_executing"] is True
    assert summary["preflight_checklist"]["requires_no_retry_loop"] is True
    assert summary["preflight_checklist"]["requires_no_raw_response_storage"] is True

    assert "subaccount-api-key-for-test-only" not in rendered_summary
    assert "wallet-id-for-test-only" not in rendered_summary
    assert "acct_subaccount_for_test_only" not in rendered_summary
    assert "https://sandbox.asaas.com/onboarding/test-only" not in rendered_summary
    assert "sandbox-api-key-for-test-only" not in rendered_summary
    assert "sandbox-webhook-token-for-test-only" not in rendered_summary

def test_subaccount_first_controlled_attempt_record_contract_is_sanitized():
    client = make_client()

    contract = client.build_subaccount_first_controlled_attempt_record_contract(
        manual_authorization_phrase=ASAAS_SANDBOX_MANUAL_AUTHORIZATION_PHRASE,
    )
    summary = contract.safe_summary()

    assert contract.record_contract_reference == (
        "subaccount-first-controlled-attempt-record-contract-sandbox"
    )
    assert contract.record_contract_defined is True
    assert contract.record_contract_valid is True
    assert contract.can_create_record_after_future_attempt is True
    assert contract.raw_payload_storage_allowed is False
    assert contract.raw_response_storage_allowed is False
    assert contract.raw_error_storage_allowed is False
    assert contract.raw_headers_storage_allowed is False
    assert contract.can_create_subaccount is False
    assert contract.can_send_http is False
    assert contract.network_call_allowed is False
    assert contract.real_money is False
    assert contract.http_call_executed is False

    assert summary["operation"] == (
        "subaccount_first_controlled_attempt_record_contract"
    )
    assert summary["record_contract_valid"] is True
    assert summary["ready_for_http_execution"] is False
    assert summary["next_step_required"] == (
        "manual_first_controlled_sandbox_attempt_decision"
    )

    assert "api_key_present" in summary["allowed_record_fields"]
    assert "wallet_id_present" in summary["allowed_record_fields"]
    assert "onboarding_url_present" in summary["allowed_record_fields"]
    assert "raw_payload" in summary["forbidden_record_fields"]
    assert "raw_response" in summary["forbidden_record_fields"]
    assert "raw_headers" in summary["forbidden_record_fields"]

    rendered_summary = repr(summary)
    assert "subaccount-api-key-for-test-only" not in rendered_summary
    assert "wallet-id-for-test-only" not in rendered_summary
    assert "acct_subaccount_for_test_only" not in rendered_summary
    assert "https://sandbox.asaas.com/onboarding/test-only" not in rendered_summary


def test_subaccount_first_controlled_attempt_record_contract_blocks_invalid_gate():
    client = make_client()

    contract = client.build_subaccount_first_controlled_attempt_record_contract(
        manual_authorization_phrase="EXECUTAR POST SANDBOX SUBCONTA AGORA",
    )
    summary = contract.safe_summary()

    assert contract.record_contract_valid is False
    assert contract.can_create_record_after_future_attempt is False
    assert summary["record_contract_valid"] is False
    assert summary["can_create_record_after_future_attempt"] is False
    assert summary["can_create_subaccount"] is False
    assert summary["can_send_http"] is False
    assert summary["network_call_allowed"] is False
    assert summary["http_call_executed"] is False
