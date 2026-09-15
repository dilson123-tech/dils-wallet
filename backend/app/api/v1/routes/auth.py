from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timezone

from app.database import get_db
from app.models.user_main import User
from app.models.refresh_token import RefreshToken
from app.utils.security import (
    verify_password,
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
    refresh_token_expiry_dt,
    SECRET_KEY,
    ALGORITHM,
)

from app.utils.rate_limit import rl_check, rl_peek, rl_client_ip

# AUREA_DEBUG: logs sensíveis só com AUREA_DEBUG=1
import os
_AUREA_DEBUG = os.getenv('AUREA_DEBUG', '0') == '1'
def _dbg(*a, **k):
    if _AUREA_DEBUG:
        print(*a, **k)


router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    ident = (payload.username or "").strip()
    # --- Rate limit (anti brute-force) ---
    rl_on = os.getenv('LOGIN_RL_ENABLED', '1').strip().lower() not in ('0','false','no','off')
    ip = rl_client_ip(request)
    win = int(os.getenv('LOGIN_RL_WINDOW_SEC', '60'))
    max_ip = int(os.getenv('LOGIN_RL_MAX_PER_IP', '10'))
    max_ident = int(os.getenv('LOGIN_RL_MAX_PER_IDENT', '5'))
    if rl_on:
        # Pre-check: se já estourou, bloqueia (SEM consumir tentativa)
        ok_ip, ra_ip = rl_peek(f'login:ip:{ip}', max_ip, win)
        ok_id, ra_id = (True, 0)
        if ident:
            ok_id, ra_id = rl_peek(f'login:ident:{ip}:{ident.lower()}', max_ident, win)
        if (not ok_ip) or (not ok_id):
            ra = str(max(ra_ip, ra_id))
            raise HTTPException(status_code=429, detail='Muitas tentativas. Aguarde e tente novamente.', headers={'Retry-After': ra})

    def _rl_fail():
        # Só consome tentativa quando a autenticação falha (401)
        if rl_on:
            ok_ip2, ra_ip2 = rl_check(f'login:ip:{ip}', max_ip, win)
            ok_id2, ra_id2 = (True, 0)
            if ident:
                ok_id2, ra_id2 = rl_check(f'login:ident:{ip}:{ident.lower()}', max_ident, win)
            if (not ok_ip2) or (not ok_id2):
                ra = str(max(ra_ip2, ra_id2))
                raise HTTPException(status_code=429, detail='Muitas tentativas. Aguarde e tente novamente.', headers={'Retry-After': ra})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Credenciais inválidas')
    _dbg('[AUTH LOGIN] ident=', repr(ident), 'pwd_len=', len(payload.password))

    user = None

    # aceita email OU username
    if hasattr(User, "email") and ident:
        user = db.query(User).filter((User.email == ident) | (User.username == ident)).first()

    if not user and hasattr(User, "username") and ident:
        user = db.query(User).filter(User.username == ident).first()

    if not user:
        _rl_fail()

    # hash no campo padrão do projeto
    pwd_hash = getattr(user, "hashed_password", None)
    _dbg('[AUTH LOGIN] user.id=', getattr(user,'id',None), 'username=', getattr(user,'username',None), 'email=', getattr(user,'email',None))

    if (not pwd_hash) or (not verify_password(payload.password, pwd_hash)):
        _rl_fail()

    # sub do token: prioriza username, senão email
    sub = (getattr(user, "username", None) or getattr(user, "email", None) or ident)
    access_token = create_access_token({"sub": sub})

    raw_refresh = generate_refresh_token()
    hashed = hash_refresh_token(raw_refresh)

    token_row = RefreshToken(
        user_id=user.id,
        token_hash=hashed,
        expires_at=refresh_token_expiry_dt(),
        created_at=datetime.now(timezone.utc),
    )
    db.add(token_row)
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        token_type="bearer",
    )


# ---------------------------
# Refresh token (JWT) - Aurea Gold
# ---------------------------
def _jwt_encode(payload: dict, secret: str, algo: str) -> str:
    try:
        from jose import jwt as _j
        return _j.encode(payload, secret, algorithm=algo)
    except Exception:
        import jwt as _j
        tok = _j.encode(payload, secret, algorithm=algo)
        return tok.decode("utf-8") if isinstance(tok, (bytes, bytearray)) else str(tok)

def _jwt_decode(token: str, secret: str, algo: str) -> dict:
    try:
        from jose import jwt as _j
        return _j.decode(token, secret, algorithms=[algo])
    except Exception:
        import jwt as _j
        return _j.decode(token, secret, algorithms=[algo])

def create_refresh_token(subject: str) -> str:
    import os
    from datetime import datetime, timedelta

    secret = SECRET_KEY
    algo = ALGORITHM
    days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    exp = datetime.utcnow() + timedelta(days=days)
    payload = {"sub": subject, "typ": "refresh", "exp": exp}
    return _jwt_encode(payload, secret, algo)

def decode_refresh_token(token: str) -> dict:
    import os
    secret = SECRET_KEY
    algo = ALGORITHM
    payload = _jwt_decode(token, secret, algo)
    if payload.get("typ") != "refresh":
        raise ValueError("token typ != refresh")
    if not payload.get("sub"):
        raise ValueError("missing sub")
    return payload

# endpoint: /api/v1/auth/refresh  (fica no mesmo router do auth.py)
try:
    from pydantic import BaseModel
    from fastapi import HTTPException
except Exception:
    BaseModel = object  # fallback (não deve acontecer)

class RefreshRequest(BaseModel):
    refresh_token: str

# se já existir TokenResponse/Token, a gente não briga: só adiciona o campo no retorno do login
@router.post("/refresh")
def refresh(body: RefreshRequest, request: Request, db: Session = Depends(get_db)):
    rt = (body.refresh_token or "").strip()

    # --- Rate limit (volume/amplificação de DB) ---
    # Roda ANTES de qualquer validação JWT ou consulta ao banco. Cada
    # tentativa que chega aqui consome o bucket por IP, independentemente
    # de terminar em sucesso ou falha (diferente do /login, que só
    # consome em falha) -- o objetivo é limitar volume de chamadas ao
    # endpoint, não só tentativas de autenticação malsucedidas.
    #
    # Somente por IP (rl_client_ip -- ver docstring de rl_client_ip sobre
    # X-Forwarded-For): deliberadamente NÃO existe bucket derivado do
    # refresh token/fingerprint. _BUCKETS nunca remove suas próprias
    # chaves (confirmado por investigação e simulação dedicadas), então
    # uma chave por-token, alimentada por qualquer string arbitrária que
    # o cliente escolha enviar no body, permitiria crescimento permanente
    # e não limitado do dicionário -- inclusive continuando a crescer
    # mesmo depois que o próprio IP já estivesse bloqueado. O bucket por
    # IP sozinho já cumpre o objetivo desta correção (limitar volume
    # antes de qualquer trabalho de banco), sem esse risco.
    rl_on = os.getenv('REFRESH_RL_ENABLED', '1').strip().lower() not in ('0', 'false', 'no', 'off')
    if rl_on:
        ip = rl_client_ip(request)

        win = int(os.getenv('REFRESH_RL_WINDOW_SEC', '60'))
        max_ip = int(os.getenv('REFRESH_RL_MAX_PER_IP', '30'))

        ip_ok, ip_retry = rl_check(f'refresh:ip:{ip}', max_ip, win)

        if not ip_ok:
            raise HTTPException(status_code=429, detail='Muitas tentativas. Aguarde e tente novamente.', headers={'Retry-After': str(ip_retry)})

    if not rt:
        raise HTTPException(status_code=401, detail="Refresh token inválido/expirado")

    # Caso JWT (3 partes) — compat futuro
    if rt.count(".") == 2:
        try:
            payload = decode_refresh_token(rt)
            sub = payload.get("sub") if isinstance(payload, dict) else payload["sub"]
        except Exception:
            raise HTTPException(status_code=401, detail="Refresh token inválido/expirado")

        try:
            new_access = create_access_token({"sub": sub})
        except Exception:
            new_access = create_access_token(sub=sub)  # type: ignore

        new_refresh = create_refresh_token(sub)
        return {"access_token": new_access, "refresh_token": new_refresh, "token_type": "bearer"}

    # Caso OPACO (sem pontos) — DB guarda token_hash (sha256 do token puro)
    from datetime import datetime, timezone, timedelta
    import secrets, hashlib

    try:
        from app.models.refresh_token import RefreshToken
    except Exception:
        raise HTTPException(status_code=500, detail="Modelo RefreshToken não encontrado")

    if not hasattr(RefreshToken, "token_hash"):
        raise HTTPException(status_code=500, detail="RefreshToken sem coluna token_hash")

    rt_hash = hashlib.sha256(rt.encode("utf-8")).hexdigest()

    obj = db.query(RefreshToken).filter(RefreshToken.token_hash == rt_hash).first()
    if not obj:
        # fallback ultra-legacy (se algum dia foi salvo “sem hash”)
        obj = db.query(RefreshToken).filter(RefreshToken.token_hash == rt).first()

    if not obj:
        raise HTTPException(status_code=401, detail="Refresh token inválido/expirado")

    now = datetime.now(timezone.utc)

    exp = getattr(obj, "expires_at", None)
    if exp:
        try:
            if getattr(exp, "tzinfo", None) is None:
                exp = exp.replace(tzinfo=timezone.utc)
            if now >= exp:
                raise HTTPException(status_code=401, detail="Refresh token inválido/expirado")
        except HTTPException:
            raise
        except Exception:
            pass

    # resolve sub via user_id -> User
    sub = None
    uid = getattr(obj, "user_id", None)
    if uid is not None:
        try:
            from app.models.user_main import User
            u = db.query(User).get(uid)
            if u:
                sub = getattr(u, "username", None) or getattr(u, "email", None)
        except Exception:
            sub = None

    if not sub:
        raise HTTPException(status_code=401, detail="Refresh token inválido/expirado")

    # rotaciona: novo token puro -> salva hash
    new_rt = secrets.token_hex(32)
    new_hash = hashlib.sha256(new_rt.encode("utf-8")).hexdigest()

    # CAS (compare-and-swap) contra corrida de rotação concorrente: duas
    # requisições podem chegar aqui com o MESMO obj (mesmo refresh token
    # ainda válido) e cada uma calcular seu próprio new_rt/new_hash. Sem
    # uma condição no WHERE que reconfirme o token_hash lido, um UPDATE
    # incondicional por id permitiria que a segunda a commitar
    # sobrescrevesse silenciosamente a primeira -- fazendo o cliente que
    # "perdeu" a corrida receber HTTP 200 com um refresh_token que já
    # nasce inválido (confirmado empiricamente em SQLite e PostgreSQL
    # real antes desta correção).
    #
    # expected_token_hash é o valor de token_hash EFETIVAMENTE
    # encontrado no SELECT acima -- nunca presumido como rt_hash --
    # porque também protege o fallback ultra-legacy (linha em que
    # token_hash foi historicamente salvo como o token cru, sem hash).
    expected_token_hash = obj.token_hash

    update_values = {"token_hash": new_hash}
    if hasattr(obj, "expires_at"):
        update_values["expires_at"] = now + timedelta(days=30)

    rows_updated = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.id == obj.id,
            RefreshToken.token_hash == expected_token_hash,
        )
        .update(update_values, synchronize_session=False)
    )

    if rows_updated != 1:
        # 0 => outra requisição já rotacionou este token primeiro
        # (perdeu a corrida). >1 nunca deveria ocorrer (id é chave
        # primária) -- tratado fail-closed do mesmo jeito, nunca
        # aceito silenciosamente.
        db.rollback()
        raise HTTPException(status_code=401, detail="Refresh token inválido/expirado")

    try:
        new_access = create_access_token({"sub": sub})
    except Exception:
        new_access = create_access_token(sub=sub)  # type: ignore

    db.commit()

    return {"access_token": new_access, "refresh_token": new_rt, "token_type": "bearer"}

