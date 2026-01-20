from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool

from app.database import Base, engine as app_engine
import app.models  # garante que todos os models sejam importados

# Configuração do Alembic (arquivo .ini)
config = context.config

# Logging padrão do Alembic
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata alvo para autogenerate (todos os models do projeto)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Executa migrations em modo 'offline'.

    Usa apenas a URL do engine, sem abrir conexão real.
    """
    url = str(app_engine.url)

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Executa migrations em modo 'online'.

    Usa o mesmo engine do app (app.database.engine),
    garantindo que o Alembic e a aplicação enxergam o mesmo banco.
    """
    connectable = app_engine

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
