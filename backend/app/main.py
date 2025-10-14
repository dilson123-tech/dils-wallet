from fastapi import FastAPI, Response
from backend.app.api.v1.routes.whoami import router as whoami_router
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.v1.routes import users, auth, refresh, auth_extras
from backend.app.api.v1.routes.pix import router as pix_router

app = FastAPI(title="Dils Wallet", version="1.0.0")
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
app.include_router(pix_router, prefix="/api/v1/pix")

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
