from fastapi import FastAPI
app = FastAPI()


from hashlib import sha256
@app.middleware("http")
async def protect_metrics(request: Request, call_next):
    if request.url.path.startswith("/metrics"):
        from os import getenv
        hdr = (request.headers.get("X-Stats-Secret") or request.headers.get("x-stats-secret") or "").strip()
        env = getenv("METRICS_SECRET", "").strip()
        try:
            print(f"[metrics] probe hdr len={len(hdr)} sha8={sha256(hdr.encode()).hexdigest()[:8]} env len={len(env)} env_sha8={sha256(env.encode()).hexdigest()[:8]}")
        except Exception as e:
            print("[metrics] probe error:", e)
        if not env or hdr != env:
            from fastapi import HTTPException
            raise HTTPException(status_code=401, detail="unauthorized")
    return await call_next(request)
import logging
logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.INFO)

import os
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from fastapi.openapi.utils import get_openapi

# importa o router do auth
from app.api.v1.routes import auth as auth_routes




from fastapi import FastAPI

app = FastAPI()

from os import getenv
import hashlib as _hl
try:
    _ms = (getenv('METRICS_SECRET','') or '').strip()
except Exception as _e:
    print('[metrics] warn:', _e)


from os import getenv
print('[ratelimit] RPM=', getenv('RATE_LIMIT_RPM','60'))

import time
from collections import defaultdict, deque
from os import getenv

# --- rate limit leve ---
_RATE_LIMIT = int(getenv("RATE_LIMIT_RPM", "60"))
_WINDOW     = 60
_buckets    = defaultdict(deque)

@app.middleware("http")
async def rate_limit(request, call_next):
    path = request.url.path
    if path.startswith(("/auth", "/transactions", "/metrics")):
        ip = request.client.host if request.client else "unknown"
        now = time.time()
        q = _buckets[ip]
        while q and now - q[0] > _WINDOW:
            q.popleft()
        if len(q) >= _RATE_LIMIT:
            raise HTTPException(status_code=429, detail="too many requests")
        q.append(now)
    return await call_next(request)
# --- fim rate limit ---


from os import getenv
try:
    _ms = (getenv('METRICS_SECRET','') or '').strip()
except Exception as _e:
    print('[metrics] warn:', _e)


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
from fastapi import Request, Header
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
def metrics(x_secret: str | None = Header(None, alias="X-Stats-Secret")):
    
    import os
    secret = os.getenv("METRICS_SECRET")
    if secret and x_secret != secret:
        raise HTTPException(status_code=401, detail="unauthorized")

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



# -- safe import for auth routes --
try:
    from app.api.v1.routes import auth as auth_routes
    app.include_router(auth_routes.router, prefix="/api/v1/auth", tags=["auth"])
except Exception as e:
    import logging
    logging.warning("auth routes disabled: %s", e)
# -- end safe auth --


# -- safe import for transactions routes --
try:
    from app.api.v1.routes import transactions as transactions_routes
    app.include_router(transactions_routes.router, prefix="/api/v1/transactions", tags=["transactions"])
except Exception as e:
    import logging
    logging.warning("transactions routes disabled: %s", e)
# -- end safe transactions --
# redeploy bump sáb 20 set 2025 14:51:41 -03
