from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import os

from app.database import Base, engine

# Routers principais / legados
from app.api.v1.routes import assist as assist_router_v1         # módulo com .router
from app.routers import admin_dbfix                              # módulo com .router
from app.routers.pix_send import router as pix_send_router       # já é APIRouter
from app.api.v1.routes.ai import router as ai_router_v1          # já é APIRouter

# PIX Super2 (nossas rotas novas)
from app.api.v1.routes import pix_balance_get                    # módulo com .router
from app.api.v1.routes import pix_history_get                    # módulo com .router
from app.api.v1.routes import pix_7d
from app.api.v1.routes import pix_forecast_get                             # módulo com .router

app = FastAPI(title="Dils Wallet API", version="0.3.0")

# --- Routers base ---
app.include_router(assist_router_v1.router)
app.include_router(pix_send_router)
app.include_router(ai_router_v1)
app.include_router(admin_dbfix.router, prefix="/admin")

from app.api.v1.ai import chat_lab_router
app.include_router(chat_lab_router, prefix="/api/v1/ai")
# --- CORS ---
_default_dev = [
    "http://localhost:5173", "http://127.0.0.1:5173",
    "http://localhost:5174", "http://127.0.0.1:5174",
    "http://localhost:8080", "http://127.0.0.1:8080",
]
origins = [o for o in os.getenv("CORS_ORIGINS", "").split(",") if o] or _default_dev

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# --- Healthcheck ---
@app.get("/healthz")
def healthz():
    return {"ok": True, "service": "dils-wallet"}

# --- OPTIONS global (CORS preflight) ---
@app.options("/{full_path:path}")
def options_any(full_path: str, request: Request):
    return Response(status_code=204)

# --- AUREA GOLD – PIX SUPER2 ---
from app.api.v1.routes import pix_balance_super2
app.include_router(pix_balance_super2.router)
app.include_router(pix_balance_get.router)
app.include_router(pix_history_get.router)
app.include_router(pix_7d.router)
app.include_router(pix_forecast_get.router)

# --- Execução local ---
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)

# --- AUREA GOLD: IA 3.0 cliente (/api/v1/ai/chat) ---
from app.api.v1.routes import ai_chat
app.include_router(ai_chat.router)

# --- Aurea Gold • Painel Receitas & Reservas LAB ---
from app.api.v1.routes import reservas_lab as reservas_lab_router

app.include_router(reservas_lab_router.router, prefix="/api/v1")

# Painel Receitas & Reservas - endpoint oficial
# from app.api.v1.routes import reservas as reservas_router  # desativado (arquivo removido)

# app.include_router(reservas_router.router, prefix="/api/v1")


# --- IA 3.0 – HEADLINE LAB (endpoint raiz para testes do Painel 3) ---
from pydantic import BaseModel
from fastapi import Header
from app.api.v1.ai.headline import IAHeadlineResponse


class IAHeadlineLabPayload(BaseModel):
    message: str


@app.post("/api/v1/ai/headline-lab", response_model=IAHeadlineResponse)
async def ia_headline_lab_root(payload: IAHeadlineLabPayload, x_user_email: str = Header(None)):
    """Endpoint LAB para o Painel 3 da IA 3.0.

    Por enquanto só devolve uma resposta fixa, confirmando que o POST
    em /api/v1/ai/headline-lab está funcionando.
    """
    return IAHeadlineResponse(
        nivel="ok",
        headline="Aurea Gold – Headline LAB funcionando",
        subheadline=f"Mensagem recebida: {payload.message}",
        resumo="Endpoint /api/v1/ai/headline-lab respondeu com sucesso em ambiente LAB.",
        destaques=[
            "Status do Painel 3 operacional (LAB)",
            "Integração backend → IA 3.0 ok",
            "Pronto para ligar com dados reais depois",
        ],
        recomendacao="Agora é só conectar o Painel 3 e depois evoluir a lógica da IA."
    )
