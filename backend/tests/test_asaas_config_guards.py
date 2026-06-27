import pytest

from app.partner.asaas_config import (
    ASAAS_SANDBOX_BASE_URL,
    ASAAS_SANDBOX_MANUAL_AUTHORIZATION_PHRASE,
    AsaasConfigError,
    load_asaas_sandbox_config,
    run_asaas_first_http_call_preflight,
)


VALID_ENV = {
    "WALLET_MODE": "partner",
    "WALLET_PARTNER_PROVIDER": "asaas",
    "REAL_MONEY_ENABLED": "false",
    "ASAAS_ENV": "sandbox",
    "ASAAS_BASE_URL": ASAAS_SANDBOX_BASE_URL,
    "ASAAS_API_KEY": "sandbox-api-key-for-test-only",
    "ASAAS_WEBHOOK_TOKEN": "sandbox-webhook-token-for-test-only",
}


def test_load_asaas_sandbox_config_accepts_safe_sandbox_env():
    config = load_asaas_sandbox_config(VALID_ENV)

    assert config.env == "sandbox"
    assert config.base_url == ASAAS_SANDBOX_BASE_URL
    assert config.wallet_mode == "partner"
    assert config.wallet_partner_provider == "asaas"
    assert config.real_money_enabled is False


def test_load_asaas_sandbox_config_safe_summary_does_not_leak_secrets():
    config = load_asaas_sandbox_config(VALID_ENV)

    summary = config.safe_summary()

    assert summary["api_key_configured"] is True
    assert summary["webhook_token_configured"] is True
    assert summary["http_calls_allowed"] is False
    assert "sandbox-api-key-for-test-only" not in repr(config)
    assert "sandbox-webhook-token-for-test-only" not in repr(config)


@pytest.mark.parametrize(
    ("key", "value", "message"),
    [
        ("WALLET_MODE", "demo", "WALLET_MODE must be partner"),
        ("WALLET_PARTNER_PROVIDER", "demo", "WALLET_PARTNER_PROVIDER must be asaas"),
        ("REAL_MONEY_ENABLED", "true", "REAL_MONEY_ENABLED must remain false"),
        ("ASAAS_ENV", "production", "ASAAS_ENV must be sandbox"),
        (
            "ASAAS_BASE_URL",
            "https://api.asaas.com/v3",
            "Production Asaas base URL is blocked",
        ),
        (
            "ASAAS_BASE_URL",
            "https://example.com/api/v3",
            "ASAAS_BASE_URL must be the official Sandbox URL",
        ),
        (
            "ASAAS_API_KEY",
            "<DEFINIR_APENAS_NO_ENV_LOCAL_SEGURO>",
            "ASAAS_API_KEY must be configured outside Git",
        ),
        (
            "ASAAS_WEBHOOK_TOKEN",
            "<DEFINIR_APENAS_NO_ENV_LOCAL_SEGURO>",
            "ASAAS_WEBHOOK_TOKEN must be configured outside Git",
        ),
    ],
)
def test_load_asaas_sandbox_config_rejects_unsafe_env(key, value, message):
    env = dict(VALID_ENV)
    env[key] = value

    with pytest.raises(AsaasConfigError, match=message):
        load_asaas_sandbox_config(env)


def test_load_asaas_sandbox_config_normalizes_trailing_slash():
    env = dict(VALID_ENV)
    env["ASAAS_BASE_URL"] = f"{ASAAS_SANDBOX_BASE_URL}/"

    config = load_asaas_sandbox_config(env)

    assert config.base_url == ASAAS_SANDBOX_BASE_URL


def test_first_http_call_preflight_accepts_safe_env_without_executing_http():
    preflight = run_asaas_first_http_call_preflight(VALID_ENV)

    assert preflight.target_method == "POST"
    assert preflight.target_path == "/customers"
    assert preflight.target_operation == "create_customer"
    assert preflight.manual_authorization_registered is False
    assert preflight.real_money is False
    assert preflight.http_call_executed is False


def test_first_http_call_preflight_recognizes_manual_authorization_but_keeps_http_blocked():
    preflight = run_asaas_first_http_call_preflight(
        VALID_ENV,
        manual_authorization_phrase=ASAAS_SANDBOX_MANUAL_AUTHORIZATION_PHRASE,
    )

    summary = preflight.safe_summary()

    assert preflight.manual_authorization_registered is True
    assert summary["operation"] == "first_http_call_preflight"
    assert summary["target_method"] == "POST"
    assert summary["target_path"] == "/customers"
    assert summary["target_operation"] == "create_customer"
    assert summary["manual_authorization_registered"] is True
    assert summary["ready_for_http_execution"] is False
    assert summary["real_money"] is False
    assert summary["http_call_executed"] is False
    assert summary["environment"]["http_calls_allowed"] is False
    assert "sandbox-api-key-for-test-only" not in repr(summary)
    assert "sandbox-webhook-token-for-test-only" not in repr(summary)


def test_first_http_call_preflight_rejects_unsafe_env_before_any_http_call():
    env = dict(VALID_ENV)
    env["ASAAS_BASE_URL"] = "https://api.asaas.com/v3"

    with pytest.raises(AsaasConfigError, match="Production Asaas base URL is blocked"):
        run_asaas_first_http_call_preflight(
            env,
            manual_authorization_phrase=ASAAS_SANDBOX_MANUAL_AUTHORIZATION_PHRASE,
        )
