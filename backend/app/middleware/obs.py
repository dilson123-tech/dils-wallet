import time
import logging
import traceback
from typing import Callable, Awaitable
from starlette.types import ASGIApp
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("obs")

class RequestObsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable]):
        rid = request.headers.get("x-railway-request-id") or request.headers.get("x-request-id") or "-"
        path = request.url.path
        method = request.method
        t0 = time.perf_counter()

        try:
            logger.info(
                "[req] rid=%s method=%s path=%s content_type=%s",
                rid,
                method,
                path,
                request.headers.get("content-type"),
            )

            response = await call_next(request)
            dt = (time.perf_counter() - t0) * 1000.0
            logger.info(
                "[res] rid=%s status=%s duration_ms=%.2f path=%s",
                rid,
                getattr(response, "status_code", "?"),
                dt,
                path,
            )
            return response

        except Exception as exc:
            dt = (time.perf_counter() - t0) * 1000.0
            tb = "".join(traceback.format_exc())
            logger.error(
                "[err] rid=%s duration_ms=%.2f path=%s exc=%r\n%s",
                rid,
                dt,
                path,
                exc,
                tb,
            )
            raise
