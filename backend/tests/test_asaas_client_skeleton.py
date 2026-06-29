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
