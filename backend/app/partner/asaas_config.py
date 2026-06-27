from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping


ASAAS_SANDBOX_BASE_URL = "https://sandbox.asaas.com/api/v3"
ASAAS_PRODUCTION_BASE_URL = "https://api.asaas.com/v3"

ASAAS_SANDBOX_MANUAL_AUTHORIZATION_PHRASE = (
    "AUTORIZO EXECUTAR PRIMEIRA CHAMADA HTTP ASAAS SANDBOX, "
    "SEM PRODUCAO E SEM DINHEIRO REAL."
)


class AsaasConfigError(RuntimeError):
    """Raised when Asaas Sandbox safety guards reject the configuration."""


@dataclass(frozen=True)
class AsaasSandboxConfig:
    env: str
    base_url: str
    api_key: str
    webhook_token: str
    real_money_enabled: bool
    wallet_mode: str
    wallet_partner_provider: str

    def __repr__(self) -> str:
        return (
            "AsaasSandboxConfig("
            f"env={self.env!r}, "
            f"base_url={self.base_url!r}, "
            "api_key='<masked>', "
            "webhook_token='<masked>', "
            f"real_money_enabled={self.real_money_enabled!r}, "
            f"wallet_mode={self.wallet_mode!r}, "
            f"wallet_partner_provider={self.wallet_partner_provider!r}"
            ")"
        )

    def safe_summary(self) -> dict[str, object]:
        return {
            "env": self.env,
            "base_url": self.base_url,
            "api_key_configured": bool(self.api_key),
            "webhook_token_configured": bool(self.webhook_token),
            "real_money_enabled": self.real_money_enabled,
            "wallet_mode": self.wallet_mode,
            "wallet_partner_provider": self.wallet_partner_provider,
            "http_calls_allowed": False,
        }


@dataclass(frozen=True)
class AsaasFirstHttpCallPreflightResult:
    config: AsaasSandboxConfig
    target_method: str = "POST"
    target_path: str = "/customers"
    target_operation: str = "create_customer"
    manual_authorization_registered: bool = False
    real_money: bool = False
    http_call_executed: bool = False

    def safe_summary(self) -> dict[str, object]:
        return {
            "operation": "first_http_call_preflight",
            "target_method": self.target_method,
            "target_path": self.target_path,
            "target_operation": self.target_operation,
            "environment": self.config.safe_summary(),
            "manual_authorization_registered": self.manual_authorization_registered,
            "real_money": self.real_money,
            "http_call_executed": self.http_call_executed,
            "ready_for_http_execution": False,
            "next_step_required": "manual_review_before_any_sandbox_http_call",
        }


def _get(env: Mapping[str, str], key: str, default: str = "") -> str:
    return (env.get(key, default) or "").strip()


def _normalized_base_url(value: str) -> str:
    return value.strip().rstrip("/")


def _is_placeholder(value: str) -> bool:
    cleaned = value.strip()
    return not cleaned or (cleaned.startswith("<") and cleaned.endswith(">"))


def _is_true(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def load_asaas_sandbox_config(
    env: Mapping[str, str] | None = None,
) -> AsaasSandboxConfig:
    """
    Load and validate Asaas Sandbox configuration.

    This function is intentionally strict and performs no HTTP calls.
    It only approves a configuration that is safe for Sandbox preparation.
    """
    source = os.environ if env is None else env

    wallet_mode = _get(source, "WALLET_MODE", "demo").lower()
    wallet_partner_provider = _get(source, "WALLET_PARTNER_PROVIDER", "").lower()
    real_money_raw = _get(source, "REAL_MONEY_ENABLED", "false")
    asaas_env = _get(source, "ASAAS_ENV", "").lower()
    base_url = _normalized_base_url(_get(source, "ASAAS_BASE_URL", ""))
    api_key = _get(source, "ASAAS_API_KEY", "")
    webhook_token = _get(source, "ASAAS_WEBHOOK_TOKEN", "")

    if wallet_mode != "partner":
        raise AsaasConfigError("WALLET_MODE must be partner for Asaas Sandbox.")

    if wallet_partner_provider != "asaas":
        raise AsaasConfigError("WALLET_PARTNER_PROVIDER must be asaas.")

    if _is_true(real_money_raw):
        raise AsaasConfigError("REAL_MONEY_ENABLED must remain false for Sandbox.")

    if asaas_env != "sandbox":
        raise AsaasConfigError("ASAAS_ENV must be sandbox.")

    if base_url == ASAAS_PRODUCTION_BASE_URL:
        raise AsaasConfigError("Production Asaas base URL is blocked.")

    if base_url != ASAAS_SANDBOX_BASE_URL:
        raise AsaasConfigError("ASAAS_BASE_URL must be the official Sandbox URL.")

    if _is_placeholder(api_key):
        raise AsaasConfigError("ASAAS_API_KEY must be configured outside Git.")

    if _is_placeholder(webhook_token):
        raise AsaasConfigError("ASAAS_WEBHOOK_TOKEN must be configured outside Git.")

    return AsaasSandboxConfig(
        env=asaas_env,
        base_url=base_url,
        api_key=api_key,
        webhook_token=webhook_token,
        real_money_enabled=False,
        wallet_mode=wallet_mode,
        wallet_partner_provider=wallet_partner_provider,
    )


def run_asaas_first_http_call_preflight(
    env: Mapping[str, str] | None = None,
    *,
    manual_authorization_phrase: str = "",
) -> AsaasFirstHttpCallPreflightResult:
    """
    Validate local safety requirements before the first Asaas Sandbox HTTP call.

    This function intentionally performs no HTTP calls.
    It only validates local configuration and records whether the mandatory
    manual authorization phrase was provided.
    """
    config = load_asaas_sandbox_config(env)
    manual_authorization_registered = (
        manual_authorization_phrase.strip() == ASAAS_SANDBOX_MANUAL_AUTHORIZATION_PHRASE
    )

    return AsaasFirstHttpCallPreflightResult(
        config=config,
        manual_authorization_registered=manual_authorization_registered,
    )
