"""Provisiona (idempotente) o usuário de smoke test local/CI.

Uso:
    python -m scripts.provision_smoke_user
    # ou
    python scripts/provision_smoke_user.py

Variáveis de ambiente (obrigatórias, sem defaults):
    SMOKE_USER   email do usuário de smoke
    SMOKE_PASS   senha em texto plano a ser hasheada

Este script cria/atualiza SOMENTE o registro na tabela users. Não cria,
credita ou altera nada em pix_ledger, saldo ou qualquer outra tabela de
transação.

Este script NUNCA deve ser executado contra o banco de produção (Railway).
Ele é destinado apenas a ambientes locais/CI com banco local (SQLite/Postgres de teste).
"""

import os
import sys


def _guard_against_production() -> None:
    """Recusa rodar se variáveis típicas de produção estiverem presentes.

    Precisa ser chamado ANTES de qualquer import de app.database, pois esse
    módulo cria o engine (e tenta conectar) no nível de módulo. Checar depois
    do import seria tarde demais.
    """
    db_url = os.environ.get("DATABASE_URL", "")
    if "railway" in db_url.lower() or os.environ.get("RAILWAY_ENVIRONMENT"):
        raise SystemExit(
            "provision_smoke_user.py: recusando executar — ambiente parece ser "
            "produção/Railway (DATABASE_URL/RAILWAY_ENVIRONMENT detectados)."
        )


_guard_against_production()

# Garante que o diretório backend/ esteja no sys.path quando o script é
# chamado diretamente (python scripts/provision_smoke_user.py) e não como
# módulo (python -m scripts.provision_smoke_user).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal  # noqa: E402
from app.models import User  # noqa: E402
from app.utils.security import hash_password  # noqa: E402


def provision_smoke_user(email: str, password: str) -> None:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            user = User(
                email=email,
                full_name="customer",
                hashed_password=hash_password(password),
                role="customer",
            )
            db.add(user)
            db.flush()
        else:
            if user.role != "customer":
                db.rollback()
                raise SystemExit(
                    f"provision_smoke_user.py: recusando executar — usuário "
                    f"'{email}' existe com role diferente de 'customer' "
                    f"(role atual: '{user.role}')."
                )
            user.hashed_password = hash_password(password)

        db.commit()
        print(f"provision_smoke_user: usuário '{email}' provisionado (id={user.id}).")
    finally:
        db.close()


def main() -> None:
    email = os.environ.get("SMOKE_USER")
    password = os.environ.get("SMOKE_PASS")
    if not email or not password:
        raise SystemExit(
            "provision_smoke_user.py: SMOKE_USER e SMOKE_PASS são obrigatórias "
            "e não possuem valor default. Abortando antes de tocar o banco."
        )
    provision_smoke_user(email, password)


if __name__ == "__main__":
    main()
