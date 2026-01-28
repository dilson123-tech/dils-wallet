import importlib
import pkgutil

from app import database as db

def main():
    engine = db.engine
    try:
        print("ENGINE_URL =", engine.url.render_as_string(hide_password=True))
    except Exception:
        print("ENGINE_URL =", str(engine.url))
    Base = getattr(db, "Base", None)
    if not Base:
        raise RuntimeError("app.database.Base não existe")

    # importa models para registrar tabelas no Base.metadata
    import app.models as models_pkg
    for m in pkgutil.walk_packages(models_pkg.__path__, models_pkg.__name__ + "."):
        importlib.import_module(m.name)

    Base.metadata.create_all(bind=engine)


    # --- schema drift fix: users.email (Railway PG estava sem coluna) ---

    from sqlalchemy import inspect, text

    insp = inspect(engine)

    if "users" in insp.get_table_names():

        cols = {c["name"] for c in insp.get_columns("users")}

        if "email" not in cols:

            with engine.begin() as conn:

                conn.execute(text("ALTER TABLE users ADD COLUMN email VARCHAR(320)"))

                conn.execute(text("UPDATE users SET email = username WHERE email IS NULL AND username LIKE '%@%'"))

            print("[BOOT] migrated: users.email added/backfilled ✅")

    # --- end schema drift fix ---
    print("✅ init_db ok. tables:", sorted(Base.metadata.tables.keys()))

if __name__ == "__main__":
    main()
