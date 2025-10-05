from fastapi import Depends
from types import SimpleNamespace
from .database import get_db  # reexport

def get_current_user():
    # Stub mínimo para compilar/testar PIX em ambientes sem auth
    # Ajuste depois para sua lógica real de autenticação.
    return SimpleNamespace(id=0)
