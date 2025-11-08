from sqlalchemy import create_engine, text
import os

url = os.environ.get("DATABASE_URL") or os.environ.get("DATABASE_PUBLIC_URL")
if not url:
    raise SystemExit("DATABASE_URL não encontrado")
engine = create_engine(url)

with engine.begin() as conn:
    conn.execute(text("""
        INSERT INTO users (username, hashed_password, role)
        VALUES ('admin@aurea.local','!seed-placeholder!','admin')
        ON CONFLICT DO NOTHING
    """))
print("✅ Usuário admin semeado com sucesso")
