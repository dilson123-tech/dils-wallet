import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base  # Base unificada

# Tenta Postgres primeiro (produção), cai pra SQLite (dev)
POSTGRES_URL = os.getenv("POSTGRES_URL")  # ex: postgres://user:pass@host/db
if POSTGRES_URL:
    SQLALCHEMY_DATABASE_URL = POSTGRES_URL
    connect_args = {}  # Postgres não usa connect_args especial
else:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"
    connect_args = {"check_same_thread": False}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
