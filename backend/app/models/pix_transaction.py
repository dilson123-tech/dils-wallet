"""
Compat layer (PROD):

Vários endpoints legados importam `PixTransaction` a partir de `app.models.pix_transaction`.
Em Postgres, a source-of-truth é a tabela `public.transactions`, mapeada pelo model `Transaction`.

Este módulo expõe `PixTransaction` como alias de `Transaction` para:
- evitar duplicação de tabela no SQLAlchemy MetaData
- manter compatibilidade com imports antigos
- garantir migração suave para o modelo único

⚠️ NÃO crie um segundo model ORM com __tablename__="transactions" aqui.
"""
from app.models.transaction import Transaction as PixTransaction

__all__ = ["PixTransaction"]
