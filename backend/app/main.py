from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# imports corrigidos: agora tudo começa em app., não backend.app.
from app.api.livez import router as livez_router
# se você tiver rotas de API v1 agrupadas num router central, deixa isso:
try:
    from app.api.v1.routes.router import router as api_v1_router
except ImportError:
    api_v1_router = None  # fallback pra não quebrar boot se ainda não existe


app = FastAPI(
    title="dils-wallet2",
    version="1.0.0",
)

# CORS provisório (tá aberto geral; depois a gente fecha)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # TODO: travar pra frontend prod depois
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# health/livez
app.include_router(livez_router, prefix="", tags=["livez/health"])

# rotas de negócio
if api_v1_router:
    app.include_router(api_v1_router, prefix="/api/v1", tags=["api v1"])
