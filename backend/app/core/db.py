# Shim de compatibilidade: expõe get_db a partir de app.database
from app.database import get_db  # noqa: F401
