from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base
import os

# ------------------------------------------------------------------------------
# CONFIGURAÇÃO DO BANCO
# ------------------------------------------------------------------------------
# prioridade:
# 1. variável de ambiente DATABASE_URL (Railway/Postgres em produção)
# 2. fallback local sqlite (dev local)
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Exemplo esperado Railway:
    # postgres://user:pass@host:port/dbname
    engine = create_engine(DATABASE_URL)
else:
    # ambiente local/dev
    SQLITE_URL = "sqlite:///./app.db"
    engine = create_engine(
        SQLITE_URL,
        connect_args={"check_same_thread": False}  # só pro sqlite
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base declarativa global para os models
Base = declarative_base()

# ------------------------------------------------------------------------------
# DEPENDÊNCIA FASTAPI
# ------------------------------------------------------------------------------
def get_db():
    """
    Dependency de FastAPI:
    abre sessão do banco pro request e fecha no final.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
