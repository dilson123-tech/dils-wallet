"""
Compat layer para produção.

Este módulo existe porque temos tanto um pacote `app/security/` (este diretório)
quanto um módulo `app/security.py`. Em runtime (Railway), Python prioriza o pacote,
então imports tipo `from app.security import get_current_user`
acabavam pegando este pacote e quebrando.

Aqui nós definimos `get_current_user` inline, sem importar `app.security`
de volta (para evitar import circular).
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
# Se você tem um modelo User e helpers pra decodificar JWT, importa aqui:
# Ajuste esses imports de acordo com o que tem no seu security.py / jwt_core.py
from app.security import jwt_core  # <- isso é seguro: jwt_core é um arquivo separado dentro da pasta security/
from app import models  # ajustar se o User mora em outro lugar

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    Extrai o usuário logado a partir do JWT de Authorization: Bearer <token>.
    Levanta HTTP 401 se inválido.
    """
    try:
        payload = jwt_core.decode_access_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Ajusta conforme seu modelo; normalmente models.User ou similar
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
