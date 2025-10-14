import sqlite3, os

DB_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
assert DB_URL.startswith("sqlite:///"), "Script preparado p/ SQLite"
path = DB_URL.replace("sqlite:///", "")

con = sqlite3.connect(path)
cur = con.cursor()

# Descobre schema atual
cur.execute("PRAGMA table_info(refresh_tokens);")
cols = cur.fetchall()
colnames = [c[1] for c in cols]

# Só reconstrói se a coluna 'id' não for PK autoincrement
need_rebuild = True
try:
    cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='refresh_tokens';")
    row = cur.fetchone()
    if row and row[0] and "PRIMARY KEY" in row[0].upper():
        # ainda pode ser PK sem AUTOINCREMENT, mas isso já resolve o NOT NULL na prática;
        # para garantir, forçamos rebuild sempre que a definição não tenha 'AUTOINCREMENT'
        need_rebuild = ("AUTOINCREMENT" not in row[0].upper())
except Exception:
    pass

# Se nem tabela existe, só cria com schema certo
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='refresh_tokens';")
exists = cur.fetchone() is not None

if not exists or need_rebuild:
    print("↻ Rebuild tabela refresh_tokens (schema correto).")
    # Renomeia a antiga (se existir)
    if exists:
        cur.execute("ALTER TABLE refresh_tokens RENAME TO refresh_tokens_old;")
    # Cria nova com schema correto
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
    # Migra dados básicos se havia tabela antiga
    if exists:
        # Copia só colunas que existirem
        src_cols = []
        for c in ["user_id","jti","token_hash","ip","user_agent","created_at","expires_at","revoked_at","active"]:
            if c in colnames:
                src_cols.append(c)
        if src_cols:
            cols_csv = ",".join(src_cols)
            placeholders = ",".join(["?"]*len(src_cols))
            # lê todos e re-insere (id novo é autogerado)
            cur.execute(f"SELECT {cols_csv} FROM refresh_tokens_old;")
            rows = cur.fetchall()
            if rows:
                cur.executemany(
                    f"INSERT INTO refresh_tokens ({cols_csv}) VALUES ({placeholders})",
                    rows
                )
        cur.execute("DROP TABLE refresh_tokens_old;")
    con.commit()
else:
    print("✓ Schema já OK, sem rebuild.")

con.close()
print("✅ refresh_tokens pronto.")
