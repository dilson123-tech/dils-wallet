from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# SQLite local (padrão)
DB_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")

# Config para SQLite (check_same_thread só para uso local/single-thread)
engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency p/ FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
