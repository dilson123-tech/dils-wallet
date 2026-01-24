import importlib
import pkgutil

from app import database as db

def main():
    engine = db.engine
    Base = getattr(db, "Base", None)
    if not Base:
        raise RuntimeError("app.database.Base não existe")

    # importa models para registrar tabelas no Base.metadata
    import app.models as models_pkg
    for m in pkgutil.walk_packages(models_pkg.__path__, models_pkg.__name__ + "."):
        importlib.import_module(m.name)

    Base.metadata.create_all(bind=engine)
    print("✅ init_db ok. tables:", sorted(Base.metadata.tables.keys()))

if __name__ == "__main__":
    main()
