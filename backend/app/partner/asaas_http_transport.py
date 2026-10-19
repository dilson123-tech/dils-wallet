from __future__ import annotations

from typing import Any

import httpx

from app.partner.asaas_config import ASAAS_SANDBOX_BASE_URL, AsaasSandboxConfig


ASAAS_SANDBOX_HTTP_TIMEOUT_SECONDS = 10.0


class AsaasSandboxTransportError(RuntimeError):
    """
    Falha de transporte Asaas Sandbox (config recusada, URL fora do
    Sandbox, timeout, erro de rede). A mensagem é sempre genérica: nunca
    carrega API key, URL completa nem corpo de resposta.
    """


class AsaasSandboxHttpTransport:
    """
    Transporte HTTP real (httpx) restrito ao Asaas SANDBOX.

    - Uma única tentativa por chamada: sem retry, sem seguir redirect.
    - Timeout explícito de 10s.
    - Recusa qualquer config que não seja Sandbox sem dinheiro real e
      qualquer URL fora da base Sandbox oficial.
    - Não registra logs.
    """

    def __init__(
        self,
        config: AsaasSandboxConfig,
        *,
        timeout: float = ASAAS_SANDBOX_HTTP_TIMEOUT_SECONDS,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if (
            config.env != "sandbox"
            or str(config.base_url or "").rstrip("/") != ASAAS_SANDBOX_BASE_URL
            or config.real_money_enabled is not False
            or not str(config.api_key or "").strip()
        ):
            raise AsaasSandboxTransportError(
                "Configuração Asaas recusada para transporte Sandbox."
            )
        self._api_key = config.api_key
        self.timeout = timeout
        self._transport = transport

    def __repr__(self) -> str:
        return (
            "AsaasSandboxHttpTransport("
            f"base_url={ASAAS_SANDBOX_BASE_URL!r}, "
            "api_key='<masked>', "
            f"timeout={self.timeout!r})"
        )

    def post(self, prepared) -> tuple[int, dict[str, Any]]:
        return self._send("POST", prepared)

    def get(self, prepared) -> tuple[int, dict[str, Any]]:
        return self._send("GET", prepared)

    def _send(self, method: str, prepared) -> tuple[int, dict[str, Any]]:
        url = str(getattr(prepared, "url", "") or "")
        if (
            getattr(prepared, "method", None) != method
            or not url.startswith(ASAAS_SANDBOX_BASE_URL + "/")
        ):
            raise AsaasSandboxTransportError(
                "Requisição Asaas recusada: fora do Sandbox."
            )

        headers = {
            "access_token": self._api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        try:
            with httpx.Client(
                timeout=self.timeout,
                follow_redirects=False,
                transport=self._transport,
            ) as client:
                response = client.request(
                    method,
                    url,
                    headers=headers,
                    json=getattr(prepared, "json", None) if method == "POST" else None,
                )
        except httpx.HTTPError:
            raise AsaasSandboxTransportError(
                "Asaas Sandbox indisponível."
            ) from None

        try:
            body = response.json()
        except ValueError:
            body = {}
        if not isinstance(body, dict):
            body = {}
        return response.status_code, body
