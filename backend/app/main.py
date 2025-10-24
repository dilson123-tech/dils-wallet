from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# importa os routers de saúde
from app.api.healthz import router as healthz_router
from app.api.livez import router as livez_router

# tenta importar as rotas de negócio (/api/v1/*)
# seu projeto tem várias rotas soltas (auth, pix, etc), não um único router central.
# Então vamos montar um APIRouter agregador e registrar nele.
from fastapi import APIRouter

api_v1_router = APIRouter(prefix="/api/v1")

# vamos importar e anexar tudo que existe em app/api/v1/routes/*
# cada um desses arquivos define `router = APIRouter(...)`
# alguns já vêm com prefix tipo "/pix", outros não. A gente só inclui eles.

from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.transactions import router as transactions_router
from app.api.v1.routes.whoami import router as whoami_router
from app.api.v1.routes.pix_stats import router as pix_stats_router
from app.api.v1.routes.pix_summary import router as pix_summary_router
from app.api.v1.routes.pix_daily import router as pix_daily_router
from app.api.v1.routes.pix_history import router as pix_history_router
from app.api.v1.routes.refresh import router as refresh_router
from app.api.v1.routes.ai import router as ai_router
from app.api.v1.routes.agents import router as agents_router
from app.api.v1.routes.users import router as users_router
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.admin import router as admin_router
from app.api.v1.routes.auth_extras import router as auth_extras_router
from app.api.v1.routes.pix import router as pix_router

# registra cada subrouter dentro de /api/v1
api_v1_router.include_router(auth_router)
api_v1_router.include_router(transactions_router)
api_v1_router.include_router(whoami_router)
api_v1_router.include_router(pix_stats_router)
api_v1_router.include_router(pix_summary_router)
api_v1_router.include_router(pix_daily_router)
api_v1_router.include_router(pix_history_router)
api_v1_router.include_router(refresh_router)
api_v1_router.include_router(ai_router)
api_v1_router.include_router(agents_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(health_router)
api_v1_router.include_router(admin_router)
api_v1_router.include_router(auth_extras_router)
api_v1_router.include_router(pix_router)

# instancia FastAPI
app = FastAPI(
    title="dils-wallet2",
    version="1.0.0",
)

# CORS (depois a gente fecha isso pra origem específica do teu frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# health puro (sem prefixo) -> Railway bate aqui
app.include_router(healthz_router, prefix="", tags=["healthz"])
# livez (diagnóstico interno etc)
app.include_router(livez_router, prefix="", tags=["livez"])

# rotas de negócio autenticadas etc
app.include_router(api_v1_router, prefix="", tags=["api-v1"])
