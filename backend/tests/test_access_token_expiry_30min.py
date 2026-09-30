"""
A15: a expiração oficial do access token é 30 minutos, fixa em
app/utils/security.py. Não existe variável de ambiente para alterá-la
(a config morta ACCESS_TOKEN_EXPIRE_MINUTES de app/config.py foi removida).
"""
import os
from datetime import datetime, timezone

os.environ.setdefault("SECRET_KEY", "access-token-expiry-test-secret")
os.environ.setdefault("JWT_SECRET", os.environ["SECRET_KEY"])

import jwt

from app import config
from app.utils import security


def _lifetime_seconds(token: str) -> float:
    payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
    return payload["exp"] - datetime.now(timezone.utc).timestamp()


def test_access_token_expires_in_30_minutes():
    assert security.ACCESS_TOKEN_EXPIRE_MINUTES == 30

    lifetime = _lifetime_seconds(security.create_access_token({"sub": "a15@example.test"}))

    assert 30 * 60 - 60 < lifetime <= 30 * 60


def test_env_var_does_not_change_access_token_expiry(monkeypatch):
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "5")

    lifetime = _lifetime_seconds(security.create_access_token({"sub": "a15@example.test"}))

    assert 30 * 60 - 60 < lifetime <= 30 * 60


def test_dead_config_removed():
    assert not hasattr(config, "ACCESS_TOKEN_EXPIRE_MINUTES")
