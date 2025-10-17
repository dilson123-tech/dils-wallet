import os, sys, json
from sqlalchemy import create_engine, inspect, text

EMAIL = os.getenv("SEED_EMAIL", "admin@example.com")
PASS  = os.getenv("SEED_PASS",  "admin")

# Hash: tenta bcrypt, senão sha256 (melhor do que nada)
try:
    from passlib.hash import bcrypt
    def hash_pw(p): return bcrypt.hash(p)
    HAS_BCRYPT = True
except Exception:
    import hashlib
    def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()
    HAS_BCRYPT = False

DB_URL = os.getenv("DATABASE_URL") or os.getenv("DB_URL") or "sqlite:///./app.db"
print(json.dumps({"step":"init","db_url":DB_URL,"bcrypt":HAS_BCRYPT}, ensure_ascii=False))

eng = create_engine(DB_URL, future=True)
insp = inspect(eng)

def cols_of(table):
    return [c["name"] for c in insp.get_columns(table)]

with eng.begin() as cx:
    tables = insp.get_table_names()
    print(json.dumps({"step":"tables","tables":tables}, ensure_ascii=False))

    # tenta descobrir tables candidatas
    candidates = []
    for t in tables:
        cols = [c.lower() for c in cols_of(t)]
        if "email" in cols or "username" in cols:
            candidates.append(t)
    print(json.dumps({"step":"candidates","candidates":candidates}, ensure_ascii=False))

    found_some = False
    for t in candidates:
        cols = [c.lower() for c in cols_of(t)]
        has_email   = "email" in cols
        has_user    = "username" in cols
        has_active  = any(c in cols for c in ["is_active","active","is_enabled"])
        pw_cols     = [c for c in ["password","password_hash","hashed_password","password_digest"] if c in cols]

        print(json.dumps({"step":"table_info","table":t,"cols":cols}, ensure_ascii=False))

        key = "email" if has_email else ("username" if has_user else None)
        if not key:
            continue

        row = cx.execute(text(f"SELECT * FROM {t} WHERE {key}=:v LIMIT 1"), {"v": EMAIL}).first()
        print(json.dumps({"step":"before","table":t,"exists":bool(row)}, ensure_ascii=False))

        # prepara SET
        sets = {}
        if has_email: sets["email"] = EMAIL
        if has_user:  sets["username"] = EMAIL
        if has_active:
            for k in ["is_active","active","is_enabled"]:
                if k in cols: sets[k] = True

        # cobre todas as colunas de senha:
        # - se for "password" (muitos guardam plaintext), grava plaintext
        # - nas demais, grava hash (bcrypt/sha256)
        for c in pw_cols:
            if c == "password":
                sets[c] = PASS
            else:
                sets[c] = hash_pw(PASS)

        # se não tem coluna de senha nenhuma, tenta criar "password" (só vai em SQLite);
        # se falhar, segue sem quebrar
        if not pw_cols:
            try:
                cx.execute(text(f'ALTER TABLE {t} ADD COLUMN password TEXT'))
                sets["password"] = PASS
                print(json.dumps({"step":"alter_added_password","table":t}, ensure_ascii=False))
            except Exception as e:
                print(json.dumps({"step":"alter_failed","table":t,"err":str(e)}, ensure_ascii=False))

        if row is None:
            if not sets:
                print(json.dumps({"step":"skip_insert_no_sets","table":t}, ensure_ascii=False))
                continue
            cols_list = ", ".join(sets.keys())
            params_list = ", ".join([f":{k}" for k in sets.keys()])
            cx.execute(text(f"INSERT INTO {t} ({cols_list}) VALUES ({params_list})"), sets)
            print(json.dumps({"step":"inserted","table":t,"email":EMAIL}, ensure_ascii=False))
            found_some = True
        else:
            if not sets:
                print(json.dumps({"step":"skip_update_no_sets","table":t}, ensure_ascii=False))
                continue
            upd = ", ".join([f"{k}=:{k}" for k in sets.keys()])
            sets[key] = EMAIL
            cx.execute(text(f"UPDATE {t} SET {upd} WHERE {key}=:email"), sets)
            print(json.dumps({"step":"updated","table":t,"email":EMAIL}, ensure_ascii=False))
            found_some = True

    print(json.dumps({"step":"done","affected":found_some}, ensure_ascii=False))
