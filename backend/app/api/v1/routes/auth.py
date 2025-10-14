from fastapi import Body
import os
from backend.app.security.jwt_core import create_access_token, issue_refresh_token, verify_and_rotate_refresh, revoke_refresh, decode_access_token
from backend.app.database import get_db
from typing import Optional
from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session

from backend.app import database, models
from backend.app.auth import create_access_token
from backend.app.utils import verify_password

router = APIRouter(tags=["auth"])

class LoginRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: str

@router.post("/login", summary="Login")
def login(payload: LoginRequest, db: Session = Depends(database.get_db)):
    # aceita ambos, mas usa email do banco
    login_id = payload.username or payload.email
    if not login_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="username or email required",
        )

    # seu modelo só tem 'email', então procuramos por email
    user = db.query(models.User).filter(models.User.email == login_id).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas.",
        )

    access_token = create_access_token_for_user(user)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/ping", summary="Auth ping")
def ping():
    return {"ok": True}
# --- compat: manter a call-site que usa create_access_token_for_user(user)
def create_access_token_for_user(user):
    username_claim = getattr(user, "username", None) or getattr(user, "email", None) or ""
    return create_access_token({"sub": str(getattr(user, "id", "")), "username": username_claim})

@router.post("/refresh")
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    raw = request.cookies.get("aurea_refresh")
    try:
        access, new_refresh = verify_and_rotate_refresh(db, raw, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"refresh_failed: {e}")
    secure = os.getenv('ENV','dev') != 'dev'
    if new_refresh:
        response.set_cookie(
            key="aurea_refresh", value=new_refresh,
            httponly=True, secure=secure,
            samesite='None' if secure else 'Lax',
            max_age=60*60*24*int(os.getenv('JWT_REFRESH_EXPIRE_DAYS','7')),
            path="/api/v1/auth"
        )
    return {"access_token": access, "token_type": "bearer", "expires_in": int(os.getenv('JWT_ACCESS_EXPIRE_MIN','15'))*60}

@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    raw = request.cookies.get("aurea_refresh")
    if not raw:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="no_refresh_cookie")
    from backend.app.security.token_hash import refresh_hash
    from backend.app.models.refresh_token import RefreshToken
    h = refresh_hash(raw)
    rt = db.query(RefreshToken).filter(RefreshToken.token_hash == h, RefreshToken.active == True).first()
    if not rt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="refresh_not_found")
    revoke_refresh(db, rt.jti)
    secure = os.getenv('ENV','dev') != 'dev'
    response.delete_cookie("aurea_refresh", path="/api/v1/auth", samesite='None' if secure else 'Lax')
    return {"ok": True}


@router.post("/link-refresh")
def link_refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    # pega Authorization: Bearer <access_token>
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing_bearer")
    access = auth.split(" ", 1)[1].strip()
    payload = decode_access_token(access)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_access_token")

    # emite refresh e seta cookie HttpOnly
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


@router.post("/auth/link-refresh-body")
def link_refresh_body(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    access_token: str = Body(embed=True)
):
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing_access_token")
    from backend.app.security.jwt_core import decode_access_token, issue_refresh_token
    payload = decode_access_token(access_token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_access_token")
    import os
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
