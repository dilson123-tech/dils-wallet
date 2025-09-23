from app.cors import add_cors
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from app.routers import favicon
app = FastAPI()
add_cors(app)
app.include_router(favicon.router)
app.mount("/static", StaticFiles(directory="app/static"), name="static")





from fastapi import Request
import os, hashlib

@app.get("/metrics_diag")
def metrics_diag(request: Request):
    hdr = (request.headers.get("X-Stats-Secret") or request.headers.get("x-stats-secret") or "").strip()
    env = (os.getenv("METRICS_SECRET_V2") or os.getenv("METRICS_SECRET") or "").strip()
    h8  = hashlib.sha256(hdr.encode()).hexdigest()[:8] if hdr else "None"
    e8  = hashlib.sha256(env.encode()).hexdigest()[:8] if env else "None"
    return {"hdr_len": len(hdr), "hdr_sha8": h8, "env_len": len(env), "env_sha8": e8}

from hashlib import sha256
from fastapi import Request, HTTPException

@app.middleware("http")
async def _protect_metrics(request: Request, call_next):
    p = request.url.path or ""
    if p.startswith("/metrics"):
        # header (case-insensitive) + strip
        hdr = (request.headers.get("x-stats-secret") or request.headers.get("X-Stats-Secret") or "").strip()
        # env: V2 -> V1 -> vazio; strip
        from os import getenv
        env = (getenv("METRICS_SECRET_V2") or getenv("METRICS_SECRET") or "").strip()

        # comparação
        if not hdr or not env or hdr != env:
            try:
                h8  = sha256(hdr.encode()).hexdigest()[:8] if hdr else "None"
                e8  = sha256(env.encode()).hexdigest()[:8] if env else "None"
                print(f"[metrics] unauthorized: hdr len={len(hdr)} sha8={h8} | env len={len(env)} sha8={e8}")
            except Exception as e:
                print(f"[metrics] diag error: {e}")
            raise HTTPException(status_code=401, detail="unauthorized")
    return await call_next(request)

from hashlib import sha256
@app.middleware("http")
async def protect_metrics(request, call_next):
    if request.url.path.startswith("/metrics"):
        from os import getenv
        hdr = (request.headers.get("X-Stats-Secret") or request.headers.get("x-stats-secret") or "").strip()
        env = (getenv("METRICS_SECRET_V2") or getenv('METRICS_SECRET_V2') or getenv('METRICS_SECRET') or '' or "").strip()
        print(f"[metrics] hdr_len={len(hdr)} sha8={sha256(hdr.encode()).hexdigest()[:8]} "
              f"env_len={len(env)} env_sha8={sha256(env.encode()).hexdigest()[:8]}")
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
from app.api.v1.routes import refresh as refresh_routes
from fastapi import FastAPI

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")

from os import getenv
import hashlib as _hl
try:
    _ms = (getenv('METRICS_SECRET_V2') or getenv('METRICS_SECRET') or '' or '').strip()
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
    _ms = (getenv('METRICS_SECRET_V2') or getenv('METRICS_SECRET') or '' or '').strip()
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
    secret = os.getenv('METRICS_SECRET_V2') or os.getenv('METRICS_SECRET_V2') or getenv('METRICS_SECRET') or '' or ''
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
    app.include_router(refresh_routes.router, prefix="/api/v1/auth")
except Exception as e:
    import logging
    logging.warning("auth routes disabled: %s", e)
# -- end safe auth --


# -- safe import for transactions routes --
try:
    from app.api.v1.routes import transactions as transactions_routes
    app.include_router(transactions_routes.router, prefix="/api/v1/transactions", tags=["transactions"])
    from app.routers import ui_public as ui_public_router
    app.include_router(ui_public_router.router, tags=["ui"])
except Exception as e:
    import logging
    logging.warning("transactions routes disabled: %s", e)
# -- end safe transactions --
# redeploy bump sáb 20 set 2025 14:51:41 -03
