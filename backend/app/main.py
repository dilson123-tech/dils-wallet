from fastapi import FastAPI
from app.api.v1.routes import auth, transactions
from app.routers.health import router as health_router

# logging estruturado (registramos já já)
from app.logging_setup import configure_logging
configure_logging()

app = FastAPI(title="Dils Wallet API")

# routers
app.include_router(health_router)
app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(transactions.router, prefix="/api/v1/transactions")

# opcional: raiz amigável
@app.get("/")
def root():
    return {"name": "dils-wallet", "status": "ok"}
