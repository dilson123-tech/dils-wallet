from fastapi import FastAPI
from app.api.v1.routes import auth, transactions
from app.routers.health import router as health_router

# logging estruturado (registramos já já)
from app.logging_setup import configure_logging
from app.metrics import MetricsMiddleware, prometheus_asgi_app
configure_logging()

app = FastAPI(title="Dils Wallet API")

# Prometheus metrics middleware
app.add_middleware(MetricsMiddleware)

# routers
app.include_router(health_router)
app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(transactions.router, prefix="/api/v1/transactions")

# opcional: raiz amigável
@app.get("/")
def root():
    return {"name": "dils-wallet", "status": "ok"}


# Expor /metrics para Prometheus (plain WSGI-style)
from starlette.responses import Response
from starlette.routing import Mount
from starlette.applications import Starlette

_metrics_app = Starlette(routes=[])
@_metrics_app.route("/")
async def _metrics(_):
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

# monta em /metrics
app.mount("/metrics", _metrics_app)
