import sqlite3, os
db = os.getenv("DATABASE_URL","sqlite:///./app.db").replace("sqlite:///","")
con = sqlite3.connect(db); cur = con.cursor()

# se existir, renomeia
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='refresh_tokens';")
if cur.fetchone():
    cur.execute("ALTER TABLE refresh_tokens RENAME TO refresh_tokens_old;")

# cria novo schema correto
cur.execute("""
CREATE TABLE refresh_tokens (
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

# migra dados, se houver (sem id)
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='refresh_tokens_old';")
if cur.fetchone():
    cols = [c for c in ["user_id","jti","token_hash","ip","user_agent","created_at","expires_at","revoked_at","active"]]
    cur.execute(f"SELECT {','.join(cols)} FROM refresh_tokens_old;")
    rows = cur.fetchall()
    if rows:
        placeholders = ",".join(["?"]*len(cols))
        cur.executemany(
            f"INSERT INTO refresh_tokens ({','.join(cols)}) VALUES ({placeholders})", rows
        )
    cur.execute("DROP TABLE refresh_tokens_old;")

con.commit(); con.close()
print("✅ rebuild forçado concluído (PK AUTOINCREMENT).")
