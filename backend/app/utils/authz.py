from __future__ import annotations

from fastapi import Depends, HTTPException, status

from app.security import get_current_user as _get_current_user
from app.models import User


def get_current_user(current_user: User = Depends(_get_current_user)) -> User:
    return current_user


def require_admin(current_user: User = Depends(_get_current_user)) -> User:
    # tenta usar flag, mas mantém fallback pro admin "fixo"
    if bool(getattr(current_user, "is_admin", False)):
        return current_user

    email = (getattr(current_user, "email", "") or "").lower()
    username = (getattr(current_user, "username", "") or "").lower()
    if email == "admin@aurea.local" or username in ("admin@aurea.local", "admin"):
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Acesso negado.",
    )


def require_customer(current_user: User = Depends(_get_current_user)) -> User:
    return current_user
