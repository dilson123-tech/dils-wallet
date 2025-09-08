import time, threading
from typing import Tuple, Dict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

# Token bucket em memória (por IP + rota)
_BUCKETS: Dict[Tuple[str, str], dict] = {}
_LOCK = threading.Lock()

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Exemplo: 10 req / 10s por (ip, rota) com burst de 10.
    Ajuste via init params.
    """
    def __init__(self, app, capacity: int = 10, refill_time_s: int = 10):
        super().__init__(app)
        self.capacity = capacity
        self.refill_time_s = refill_time_s

    async def dispatch(self, request: Request, call_next):
        ip = request.client.host if request.client else "-"
        route = request.url.path
        key = (ip, route)
        now = time.time()

        with _LOCK:
            b = _BUCKETS.get(key)
            if not b:
                b = {"tokens": self.capacity, "ts": now}
                _BUCKETS[key] = b
            # Refill
            elapsed = now - b["ts"]
            if elapsed >= self.refill_time_s:
                b["tokens"] = self.capacity
                b["ts"] = now

            if b["tokens"] <= 0:
                # 429 Too Many Requests
                retry = max(1, int(self.refill_time_s - elapsed))
                return JSONResponse(
                    {"detail": "Too Many Requests"},
                    status_code=429,
                    headers={
                        "Retry-After": str(retry),
                        "X-RateLimit-Limit": str(self.capacity),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(b["ts"] + self.refill_time_s)),
                    },
                )
            b["tokens"] -= 1

        resp: Response = await call_next(request)
        # Headers informativos
        remaining = max(0, b["tokens"])
        resp.headers["X-RateLimit-Limit"] = str(self.capacity)
        resp.headers["X-RateLimit-Remaining"] = str(remaining)
        resp.headers["X-RateLimit-Window"] = f"{self.refill_time_s}s"
        return resp
