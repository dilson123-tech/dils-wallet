# Compat shim: expõe símbolos esperados por imports antigos
# Tenta importar dos módulos novos; se não houver, cai pro legado models_base.
try:
    # Se você tiver modules específicos no pacote novo, exponha aqui:
    from .transaction import Transaction  # opcional: só se existir
except Exception:
    pass

# Fallback legado
try:
    from ..models_base import Transaction  # principal usado no projeto
except Exception:
    pass
