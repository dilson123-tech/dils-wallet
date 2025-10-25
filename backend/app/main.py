import time
from fastapi import Response, FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import get_db, engine
from app.models import Base

# garante tabelas no banco ao subir
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Dils Wallet API",
    version="0.3.0",
)

# servir /ui se existir
app.mount("/ui", StaticFiles(directory="ui", html=True), name="ui")

@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)

# -------------------------------------------------
# CORS
# depois que o front estiver no Railway, troque
# "http://localhost:5173" pelo domínio público do front,
# ex: "https://aurea-gold-client.up.railway.app"
# -------------------------------------------------
ALLOWED_ORIGINS = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/healthz")
def healthz():
    return {"status": "ok", "ts": int(time.time())}

@app.get("/users/test-db")
def test_db(db: Session = Depends(get_db)):
    return {"msg": "DB conectado!"}

# ==== Routers ====

from app.api.v1.routes import auth as _auth
app.include_router(
    _auth.router,
    prefix="/api/v1/auth",
    tags=["auth"],
)

from app.api.v1.routes import refresh as _refresh
app.include_router(
    _refresh.router,
    prefix="/api/v1/auth",
    tags=["auth"],
)

from app.api.v1.routes import users as _users
app.include_router(
    _users.router,
    tags=["users"],
)

from app.api.v1.routes import wallet as _wallet
app.include_router(
    _wallet.router,
    tags=["wallet"],
)
