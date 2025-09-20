import logging
logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.INFO)

import os
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

# importa o router do auth
from app.api.v1.routes import auth as auth_routes

app = FastAPI(title="Dils Wallet API", version="0.1.0")

@app.get("/healthz")
def health():
    return {"status": "ok"}

# canário simples direto no main (prova de vida do arquivo em prod)

@app.middleware("http")
async def _security_headers(request, call_next):
    resp = await call_next(request)
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "DENY")
    resp.headers.setdefault("Referrer-Policy", "no-referrer")
    # HSTS só faz sentido sob HTTPS (Railway usa HTTPS na borda)
    resp.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    # Trava APIs do navegador que não precisamos
    resp.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
    return resp



# --- lightweight metrics (Prometheus-like) ---
from collections import defaultdict
from fastapi import Request
from fastapi.responses import PlainTextResponse

if not hasattr(app.state, "metrics"):
    app.state.metrics = {
        "requests_total": 0,
        "by_status": defaultdict(int),
    }

@app.middleware("http")
async def _metrics_mw(request: Request, call_next):
    resp = await call_next(request)
    try:
        app.state.metrics["requests_total"] += 1
        app.state.metrics["by_status"][str(resp.status_code)] += 1
    except Exception:
        pass
    return resp

@app.get("/metrics")
def metrics():
    m = app.state.metrics
    lines = []
    lines.append("# TYPE app_requests_total counter")
    lines.append(f"app_requests_total {m['requests_total']}")
    lines.append("# TYPE app_requests_status_total counter")
    for k,v in sorted(m["by_status"].items()):
        lines.append(f'app_requests_status_total{{status="{k}"}} {v}')
    body = "\n".join(lines) + "\n"
    return PlainTextResponse(body, media_type="text/plain")
# --- /metrics ---


# -- safe import for admin routes --
try:
    import os
    if os.getenv("ENABLE_ADMIN_ROUTES") == "1":
        from app.api.v1.routes import admin as admin_routes
        app.include_router(admin_routes.router, prefix="/api/v1/admin", tags=["admin"])
    else:
        raise Exception("admin disabled")
except Exception as e:
    import logging
    logging.warning("admin routes disabled: %s", e)
# -- end safe import --

