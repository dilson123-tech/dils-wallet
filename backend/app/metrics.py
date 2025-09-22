from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from time import perf_counter
from starlette.responses import Response

REQ_COUNT = Counter(
    "http_requests_total", "Total de requests recebidas",
    ["method", "path", "status"]
)
REQ_LATENCY = Histogram(
    "http_request_duration_seconds", "Latência por request (s)",
    ["method", "path"]
)

def prometheus_asgi_app(environ, start_response):
    # WSGI adapter p/ expor /metrics
    data = generate_latest()
    headers = [(b'Content-Type', CONTENT_TYPE_LATEST)]
    start_response(b'200 OK', headers)
    return [data]

def observe_request(method: str, path: str, status_code: int, elapsed_s: float):
    REQ_COUNT.labels(method=method, path=path, status=str(status_code)).inc()
    REQ_LATENCY.labels(method=method, path=path).observe(elapsed_s)

class MetricsMiddleware:
    def __init__(self, app):
        self.app = app
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        method = scope.get("method")
        path = scope.get("path")
        start = perf_counter()
        status_container = {}
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_container["status"] = message["status"]
            await send(message)
        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            elapsed = perf_counter() - start
            status = status_container.get("status", 500)
            try:
                observe_request(method, path, status, elapsed)
            except Exception:
                pass
