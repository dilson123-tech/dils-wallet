from __future__ import annotations

import os
import logging
from typing import Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.utils.security import SECRET_KEY, ALGORITHM

logger = logging.getLogger("authz")
security = HTTPBearer(auto_error=False)

# ⚠️ Produção: fallback DEV deve ser OFF por padrão.
AUREA_ALLOW_DEV_FALLBACK = os.getenv("AUREA_ALLOW_DEV_FALLBACK", "0") == "1"


def _dev_fallback_user(db: Session) -> Optional[User]:
    if not AUREA_ALLOW_DEV_FALLBACK:
        return None
    return db.query(User).filter(User.id == 1).first()


def get_current_user(
    request: Request,
    creds: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Lê Authorization: Bearer <token>, valida JWT e carrega o usuário do banco.
    Em produção, token é obrigatório. Sem fallback por header/email.
    """

    # LAB DEBUG (não vaza token inteiro)
    if os.getenv("AUREA_DEBUG", "").strip().lower() in ("1","true","yes","on"):
        ah = request.headers.get("authorization")
        logger.warning("[AUTHZ][DEBUG] %s %s | authorization=%s",
                       request.method, request.url.path,
                       (ah[:40] + "..." if ah and len(ah) > 40 else ah) or "<none>")
    # Token obrigatório
    if creds is None or creds.scheme.lower() != "bearer":
        fb = _dev_fallback_user(db)
        if fb:
            logger.warning("[AUTHZ] Fallback DEV ativo: usando user id=1 por ausência de token.")
            return fb
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token ausente.",
        )

        # --- LAB DEBUG (sem vazar token) ---
    if os.getenv("AUREA_DEBUG", "").strip().lower() in ("1", "true", "yes", "on"):
        try:
            tok_len = len(creds.credentials) if creds else 0
            scheme = (creds.scheme if creds else None)
            head = (creds.credentials[:12] + "...") if (creds and creds.credentials) else None
            logger.warning("[AUTHZ DEBUG] has_creds=%s scheme=%s tok_len=%s tok_head=%s", bool(creds), scheme, tok_len, head)
        except Exception as _e:
            logger.warning("[AUTHZ DEBUG] log fail: %s", _e)

    token = creds.credentials.strip()

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub: Optional[str] = payload.get("sub")
        if not sub:
            raise JWTError("payload sem 'sub'")
    except JWTError as e:
        fb = _dev_fallback_user(db)
        if fb:
            logger.warning("[AUTHZ] Fallback DEV ativo após erro no JWT: %s", e)
            return fb
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
        )

    # Aceita sub como username OU email, mas sempre vindo do JWT validado.
    user = (
        db.query(User)
        .filter(or_(User.username == sub, User.email == sub))
        .first()
    )
    if not user:
        fb = _dev_fallback_user(db)
        if fb:
            logger.warning("[AUTHZ] Fallback DEV ativo: sub '%s' não encontrado, usando id=1.", sub)
            return fb
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado.",
        )

    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito ao administrador.",
        )
    return current_user


def require_customer(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ("customer", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado ao cliente.",
        )
    return current_user
