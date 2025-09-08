import json, logging, time, uuid
from typing import Any, Dict
from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# contextvar para request_id
_request_id: ContextVar[str] = ContextVar("request_id", default="-")

def get_request_id() -> str:
    return _request_id.get()
class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "ts": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        # Inclui extras comuns se existirem
        for key in ("request_id","method","path","status","duration_ms","client","event"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        return json.dumps(payload, ensure_ascii=False)
def setup_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
class RequestContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self._logger = logging.getLogger("app.http")

    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        token = _request_id.set(rid)
        start = time.perf_counter()
        try:
            response: Response = await call_next(request)
        finally:
            duration_ms = int((time.perf_counter() - start) * 1000)
            self._logger.info(
                "req",
                extra={
                    "event": "http_request",
                    "request_id": rid,
                    "method": request.method,
                    "path": request.url.path,
                    "status": getattr(response, "status_code", 500),
                    "duration_ms": duration_ms,
                    "client": request.client.host if request.client else "-",
                },
            )
            _request_id.reset(token)
        response.headers["X-Request-ID"] = rid
        return response
