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
