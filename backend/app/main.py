from backend.app.api.v1.routes.pix import router as pix_router
from fastapi import FastAPI, Response
from backend.app.api.healthz import router as healthz_router
from starlette.middleware.base import BaseHTTPMiddleware

from starlette.responses import Response



class SecurityHeadersMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request, call_next):

        response: Response = await call_next(request)

        response.headers["Content-Security-Policy"] = (

            "default-src 'self'; "
            "connect-src 'self' https://dils-wallet-production.up.railway.app; "
            "img-src 'self' data: blob:; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "font-src 'self' data:; "
            "frame-ancestors 'self'; "
            "base-uri 'self';"

        )

        return response





from backend.app.api.v1.routes.whoami import router as whoami_router
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.v1.routes import users, auth, refresh, auth_extras

app = FastAPI(title="Dils Wallet", version="1.0.0")
app.include_router(pix_router, prefix="/api/v1/pix")
app.add_middleware(SecurityHeadersMiddleware)
from starlette.middleware.base import BaseHTTPMiddleware

from starlette.responses import Response



class SecurityHeadersMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request, call_next):

        response: Response = await call_next(request)

        response.headers["Content-Security-Policy"] = (

            "default-src 'self'; "
            "connect-src 'self' https://dils-wallet-production.up.railway.app; "
            "img-src 'self' data: blob:; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "font-src 'self' data:; "
            "frame-ancestors 'self'; "
            "base-uri 'self';"

        )

        return response



app.add_middleware(SecurityHeadersMiddleware)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://stunning-magic-production.up.railway.app",
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(whoami_router, prefix='/api/v1')
app.include_router(auth_extras.router, prefix='/api/v1')
# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rotas principais
app.include_router(users.router, prefix="/api/v1/users")
app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(refresh.router, prefix="/api/v1/refresh")

# --- Root e Healthcheck (GET e HEAD) ---
@app.get("/")
def root_ok():
    return {"ok": True}

@app.head("/")
def root_head():
    return Response(status_code=200)

@app.get("/api/v1/health")
def health():
    return {"status": "ok", "service": "dils-wallet"}

@app.head("/api/v1/health")
def health_head():
    return Response(status_code=200)

# --- Root e Healthcheck (GET e HEAD) ---
@app.get("/")
def root_ok():
    return {"ok": True}

@app.head("/")
def root_head():
    from fastapi import Response
    return Response(status_code=200)

@app.get("/api/v1/health")
def health():
    return {"status": "ok", "service": "dils-wallet"}

@app.head("/api/v1/health")
def health_head():
    from fastapi import Response
    return Response(status_code=200)

@app.get('/api/v1/health')
def api_health():
    return {'status':'ok'}

@app.head('/api/v1/health')
def api_health_head():
    return Response(status_code=200)

@app.get('/health')
def health():
    return {'status':'ok'}

@app.head('/health')
def health_head():
    return Response(status_code=200)

@app.get('/')
def root_ok():
    return {'status':'ok','service':'dils-wallet'}

@app.head('/')
def root_head():
    return Response(status_code=200)
