"""
Compat layer (LEGADO).
Fonte oficial de senha: app.utils.security

Este arquivo existe só para não quebrar imports antigos como:
- from app.utils import hash_password
- from app.utils import verify_password
"""
from app.utils.security import pwd_context, hash_password, verify_password

__all__ = ["pwd_context", "hash_password", "verify_password"]
