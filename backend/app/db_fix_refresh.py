import sqlite3, os, sys
from datetime import datetime, timedelta

DB_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
if DB_URL.startswith("sqlite:///"):
    path = DB_URL.replace("sqlite:///", "")
else:
    print("Este fixer está preparado pra SQLite. Ajuste se usar outro DB.")
    sys.exit(0)

conn = sqlite3.connect(path)
cur = conn.cursor()

# cria tabela se não existir
cur.execute("""
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    jti TEXT NOT NULL UNIQUE,
    token_hash TEXT NOT NULL UNIQUE,
    ip TEXT NULL,
    user_agent TEXT NULL,
    created_at DATETIME NOT NULL,
    expires_at DATETIME NOT NULL,
    revoked_at DATETIME NULL,
    active BOOLEAN NOT NULL DEFAULT 1
);
""")

# checa colunas existentes
cur.execute("PRAGMA table_info(refresh_tokens);")
cols = {row[1]: row for row in cur.fetchall()}

def addcol(name, ddl):
    if name not in cols:
        cur.execute(f"ALTER TABLE refresh_tokens ADD COLUMN {name} {ddl};")

# garante campos e nullability
addcol("ip", "TEXT NULL")
addcol("user_agent", "TEXT NULL")
addcol("revoked_at", "DATETIME NULL")
# created_at/expires_at/active podem existir sem default → atualiza where null
cur.execute("UPDATE refresh_tokens SET created_at = ? WHERE created_at IS NULL;", (datetime.utcnow().isoformat(),))
cur.execute("UPDATE refresh_tokens SET active = 1 WHERE active IS NULL;")

conn.commit()
conn.close()
print("✅ refresh_tokens schema OK/ajustado.")
