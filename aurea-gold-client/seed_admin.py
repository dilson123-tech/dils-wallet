import os
from sqlalchemy import create_engine, text

# tenta usar bcrypt (padrão FastAPI); se faltar, usa SHA256 (pode não autenticar, mas não quebra)
try:
    from passlib.hash import bcrypt
    def hash_pw(p: str) -> str: return bcrypt.hash(p)
    print("⚙️ usando bcrypt")
except Exception as e:
    import hashlib
    def hash_pw(p: str) -> str: return hashlib.sha256(p.encode()).hexdigest()
    print("⚠️ passlib/bcrypt não disponível; usando sha256")

DB_URL = os.getenv("DATABASE_URL") or os.getenv("DB_URL") or "sqlite:///./app.db"
EMAIL  = os.getenv("SEED_EMAIL", "admin@example.com")
PASS   = os.getenv("SEED_PASS",  "admin")

engine = create_engine(DB_URL, future=True)

with engine.begin() as cx:
    # cria tabela users se não existir (ajuste se seu schema for outro)
    cx.execute(text("""
    CREATE TABLE IF NOT EXISTS users (
      id SERIAL PRIMARY KEY,
      email TEXT UNIQUE NOT NULL,
      password_hash TEXT,
      hashed_password TEXT,
      is_active BOOLEAN DEFAULT TRUE
    )
    """))

    row = cx.execute(text("SELECT id FROM users WHERE email = :e"), {"e": EMAIL}).first()
    if row is None:
        cx.execute(text("""
            INSERT INTO users (email, password_hash, hashed_password, is_active)
            VALUES (:e, :ph, :ph, TRUE)
        """), {"e": EMAIL, "ph": hash_pw(PASS)})
        print(f"✅ criado usuário: {EMAIL}")
    else:
        cx.execute(text("""
            UPDATE users
               SET password_hash = :ph,
                   hashed_password = :ph
             WHERE email = :e
        """), {"e": EMAIL, "ph": hash_pw(PASS)})
        print(f"🔁 senha atualizada para: {EMAIL}")
