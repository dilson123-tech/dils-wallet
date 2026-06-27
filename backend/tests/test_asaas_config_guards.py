import pytest

from app.partner.asaas_config import (
    ASAAS_SANDBOX_BASE_URL,
    AsaasConfigError,
    load_asaas_sandbox_config,
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
