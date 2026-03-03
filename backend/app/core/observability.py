from __future__ import annotations

import contextvars
import logging
import os
import time
import uuid
from typing import Optional, Tuple

from fastapi import Request
from fastapi.responses import Response as FastAPIResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pythonjsonlogger import jsonlogger


# ---- Request context (request_id) ----
_request_id_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("request_id", default=None)


def get_request_id() -> str:
    return _request_id_ctx.get() or "-"


class _RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


def _env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}


def setup_logging() -> None:
    """
    Configura logging estruturado (JSON) por padrão.
    Controla via:
      - LOG_LEVEL (default INFO)
      - LOG_JSON (default true)
    """
    root = logging.getLogger()
    if getattr(root, "_aurea_configured", False):
        return

    level = os.getenv("LOG_LEVEL", "INFO").upper()
    root.setLevel(level)

    handler = logging.StreamHandler()
    handler.addFilter(_RequestIdFilter())

    if _env_bool("LOG_JSON", True):
        fmt = "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s"
        handler.setFormatter(jsonlogger.JsonFormatter(fmt))
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s rid=%(request_id)s %(message)s")
        )

    # substitui handlers do root pra evitar logs duplicados
    root.handlers.clear()
    root.addHandler(handler)
    root._aurea_configured = True  # type: ignore[attr-defined]


# ---- Prometheus metrics ----
HTTP_REQUESTS_TOTAL = Counter(
    "aurea_http_requests_total",
    "Total HTTP requests",
    ["method", "route", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "aurea_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "route"],
)


def metrics_response() -> FastAPIResponse:
    return FastAPIResponse(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


def _route_label(request: Request) -> str:
    """
    Evita cardinalidade alta: tenta usar o path do router (ex: /api/v1/cases/{id})
    """
    rt = request.scope.get("route")
    path = getattr(rt, "path", None)
    return path or request.url.path


async def observability_middleware(request: Request, call_next):
    rid = request.headers.get("X-Request-Id") or uuid.uuid4().hex[:12]
    token = _request_id_ctx.set(rid)

    start = time.perf_counter()
    route = _route_label(request)
    method = request.method

    # Debug opcional: PIX balance trace (sem print, log estruturado)
    if _env_bool("AUREA_MW_PIXBAL_TRACE", False) and request.url.path == "/api/v1/pix/balance":
        auth = request.headers.get("authorization")
        origin = request.headers.get("origin")
        referer = request.headers.get("referer")
        extra = {
            "method": method,
            "path": request.url.path,
            "origin": origin,
            "referer": referer,
            "auth_present": bool(auth),
        }
        if _env_bool("AUREA_MW_PIXBAL_TRACE_SHOW_AUTH", False) and auth:
            extra["auth_head"] = auth[:25] + "..."
        logging.getLogger("aurea.pix.balance").info("pix_balance_trace", extra=extra)

    log = logging.getLogger("aurea.http")
    status = "500"

    try:
        resp = await call_next(request)
        # mantém compat: devolve X-Request-Id sempre
        try:
            resp.headers["X-Request-Id"] = rid
        except Exception:
            pass
        status = str(getattr(resp, "status_code", 0))
        return resp
    finally:
        dur = time.perf_counter() - start
        ms = int(dur * 1000)

        HTTP_REQUESTS_TOTAL.labels(method=method, route=route, status=status).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(method=method, route=route).observe(dur)

        log.info(
            "request",
            extra={
                "method": method,
                "route": route,
                "path": request.url.path,
                "status": int(status),
                "duration_ms": ms,
            },
        )

        _request_id_ctx.reset(token)


def attach_request_id_header(response, request_id: str) -> None:
    try:
        response.headers["X-Request-Id"] = request_id
    except Exception:
        pass
