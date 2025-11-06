import os
from sqlalchemy import create_engine

db_url = os.getenv("DATABASE_URL") or os.getenv("DATABASE_PUBLIC_URL")
if not db_url:
    raise RuntimeError("DATABASE_URL/DATABASE_PUBLIC_URL não configurado")

# Normaliza prefixo para o SQLAlchemy
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(db_url, pool_pre_ping=True, pool_recycle=1000)
