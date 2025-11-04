import os, time
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

def wait_and_create_all(Base, tries=60, delay=2.0):
    """
    Tenta se conectar ao banco repetidamente e criar as tabelas.
    Evita erro 'connection refused' no boot quando o Postgres demora pra subir.
    """
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL não encontrado.")
    print(f"[AUREA DB] conectando em {url}")
    last = None
    for i in range(1, tries + 1):
        try:
            eng = create_engine(url, pool_pre_ping=True)
            with eng.connect():
                pass
            Base.metadata.create_all(bind=eng)
            print("[AUREA DB] create_all(Base) OK ✅")
            return
        except OperationalError as e:
            last = e
            print(f"[AUREA DB] DB não pronto ({i}/{tries}): {e}")
            time.sleep(delay)
    raise RuntimeError(f"[AUREA DB] DB não ficou pronto: {last}")
