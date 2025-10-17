import os, sys
from sqlalchemy import create_engine, inspect, text

EMAIL = os.getenv("SEED_EMAIL", "admin@example.com")
PASS  = os.getenv("SEED_PASS",  "admin")

try:
    from passlib.hash import bcrypt
    def hash_pw(p): return bcrypt.hash(p)
    print("⚙️ usando bcrypt")
except Exception:
    import hashlib
    def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()
    print("⚠️ sem passlib/bcrypt; usando sha256")

DB_URL = os.getenv("DATABASE_URL") or os.getenv("DB_URL") or "sqlite:///./app.db"
print("DB_URL:", DB_URL)
eng = create_engine(DB_URL, future=True)
insp = inspect(eng)

# candidatos de tabela que muita gente usa p/ usuário
candidates = [
    "users","user","auth_user","accounts","account","app_user","usuario","usuarios"
]

with eng.begin() as cx:
    existing = set(insp.get_table_names())
    targets = [t for t in candidates if t in existing]
    if not targets:
        # fallback: tenta descobrir qualquer tabela com coluna 'email'
        for t in existing:
            cols = {c["name"].lower() for c in insp.get_columns(t)}
            if "email" in cols:
                targets.append(t)
    if not targets:
        print("❌ nenhuma tabela com coluna 'email' encontrada."); sys.exit(0)

    for t in targets:
        cols = {c["name"].lower() for c in insp.get_columns(t)}
        print(f"→ tabelA: {t} | colunas: {sorted(cols)}")

        # campos comuns
        has_email   = "email" in cols
        has_user    = "username" in cols
        has_active  = "is_active" in cols or "active" in cols or "is_enabled" in cols
        # possibilidades de senha
        cand_pw_cols = [c for c in ["password","password_hash","hashed_password","password_digest"] if c in cols]

        if not has_email and not has_user:
            print(f"  - pula {t}: não tem email/username")
            continue
        if not cand_pw_cols:
            print(f"  - {t}: sem colunas de senha; criando se possível")
            # cria coluna password se for SQLite (em PG precisa ALTER TABLE)
            try:
                cx.execute(text(f'ALTER TABLE {t} ADD COLUMN password TEXT'))
                cand_pw_cols.append("password")
            except Exception:
                pass

        # verifica se já existe
        keycol = "email" if has_email else "username"
        row = cx.execute(text(f"SELECT * FROM {t} WHERE {keycol}=:v LIMIT 1"), {"v": EMAIL}).first()

        # valores a setar
        sets = {}
        if has_email: sets["email"] = EMAIL
        if has_user:  sets["username"] = EMAIL
        if has_active: sets[[c for c in ["is_active","active","is_enabled"] if c in cols][0]] = True

        # preenche todas colunas de senha candidatas
        for c in cand_pw_cols:
            if c in ["password"]:     # vários backends guardam plaintext (péssimo, mas existe)
                sets[c] = PASS
            else:
                sets[c] = hash_pw(PASS)

        if row is None:
            cols_list = ", ".join(sets.keys())
            params_list = ", ".join([f":{k}" for k in sets.keys()])
            cx.execute(text(f"INSERT INTO {t} ({cols_list}) VALUES ({params_list})"), sets)
            print(f"  ✅ criado em {t}: {EMAIL}")
        else:
            upd = ", ".join([f"{k}=:{k}" for k in sets.keys()])
            sets[keycol] = EMAIL
            cx.execute(text(f"UPDATE {t} SET {upd} WHERE {keycol}=:email"), sets)
            print(f"  🔁 atualizado em {t}: {EMAIL}")
