from fastapi import APIRouter, Depends, Request, Response, HTTPException, status, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.security.jwt_core import decode_access_token, issue_refresh_token
import os
from jose import jwt, JWTError

router = APIRouter(tags=["Auth"])

@router.post("/auth/link-refresh-body")
def link_refresh_body(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    access_token: str = Body(embed=True)
):
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing_access_token")

    from app.security.jwt_core import decode_access_token, issue_refresh_token, SECRET_KEY, ALGO

    # 1) tenta decode verificado
    payload = decode_access_token(access_token)
    user_id = payload.get("sub") if payload else None

    # 2) fallback DEV: extrai claims sem verificar assinatura
    if not user_id:
        try:
            claims = jwt.get_unverified_claims(access_token)
            user_id = claims.get("sub")
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"invalid_access_token: {e}")

    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_access_token")

    refresh_raw, _ = issue_refresh_token(db, str(user_id), request)
    secure = os.getenv('ENV','dev') != 'dev'
    response.set_cookie(
        key="aurea_refresh", value=refresh_raw,
        httponly=True, secure=secure,
        samesite='None' if secure else 'Lax',
        max_age=60*60*24*int(os.getenv('JWT_REFRESH_EXPIRE_DAYS','7')),
        path="/api/v1/auth"
    )
    return {"ok": True}
