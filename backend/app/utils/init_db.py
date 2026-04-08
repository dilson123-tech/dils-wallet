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

    # --- schema drift fix: users.email / users.full_name (Railway PG estava defasado) ---
    from sqlalchemy import inspect, text

    insp = inspect(engine)

    if "users" in insp.get_table_names():
        cols = {c["name"] for c in insp.get_columns("users")}

        with engine.begin() as conn:
            if "email" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN email VARCHAR(320)"))
                print("[BOOT] migrated: users.email added ✅")

            if "full_name" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN full_name VARCHAR(255)"))
                print("[BOOT] migrated: users.full_name added ✅")

            cols_after = {c["name"] for c in inspect(engine).get_columns("users")}

            if "username" in cols_after and "email" in cols_after:
                conn.execute(
                    text(
                        """
                        UPDATE users
                           SET email = username
                         WHERE (email IS NULL OR email = '')
                           AND username IS NOT NULL
                           AND username LIKE '%@%'
                        """
                    )
                )

            if "username" in cols_after and "full_name" in cols_after:
                conn.execute(
                    text(
                        """
                        UPDATE users
                           SET full_name = username
                         WHERE (full_name IS NULL OR full_name = '')
                           AND username IS NOT NULL
                           AND username <> ''
                        """
                    )
                )

        print("[BOOT] schema drift fix: users.email/full_name checked/backfilled ✅")
    # --- end schema drift fix ---

    print("✅ init_db ok. tables:", sorted(Base.metadata.tables.keys()))


if __name__ == "__main__":
    main()
