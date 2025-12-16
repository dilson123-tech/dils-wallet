# compat shim: antigos imports de app.models_base
try:
    from .models import Transaction, User  # noqa: F401
except Exception:
    Transaction = None  # type: ignore
    User = None  # type: ignore
