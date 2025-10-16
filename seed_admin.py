import os
from sqlalchemy import create_engine, text

# tenta bcrypt; senão cai pra sha256 (suficiente p/ muitos templates)
try:
    from passlib.hash import bcrypt
    def hash_pw(p: str) -> str: return bcrypt.hash(p)
    print("⚙️ usando bcrypt")
except Exception:
    import hashlib
    def hash_pw(p: str) -> str: return hashlib.sha256(p.encode()).hexdigest()
    print("⚠️ sem passlib/bcrypt; usando sha256")

DB_URL = os.getenv("DATABASE_URL") or os.getenv("DB_URL") or "sqlite:///./app.db"
EMAIL  = os.getenv("SEED_EMAIL", "admin@example.com")
PASS   = os.getenv("SEED_PASS",  "admin")

print("DB_URL:", DB_URL)

engine = create_engine(DB_URL, future=True)

with engine.begin() as cx:
    cx.execute(text("""
    CREATE TABLE IF NOT EXISTS users (
      id SERIAL PRIMARY KEY,
      email TEXT UNIQUE NOT NULL,
      password_hash TEXT,
      hashed_password TEXT,
      is_active BOOLEAN DEFAULT TRUE
    )
    """))

    row = cx.execute(text("SELECT id FROM users WHERE email=:e"), {"e": EMAIL}).first()
    if row is None:
        cx.execute(text("""
            INSERT INTO users (email, password_hash, hashed_password, is_active)
            VALUES (:e, :ph, :ph, TRUE)
        """), {"e": EMAIL, "ph": hash_pw(PASS)})
        print("✅ criado:", EMAIL)
    else:
        cx.execute(text("""
            UPDATE users
               SET password_hash=:ph,
                   hashed_password=:ph
             WHERE email=:e
        """), {"e": EMAIL, "ph": hash_pw(PASS)})
        print("�� senha atualizada para:", EMAIL)
