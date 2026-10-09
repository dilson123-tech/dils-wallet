"""
F8.1 — reuse detection de refresh token (Opção B: tabela de hashes
aposentados, família = refresh_tokens.id).

Contrato do POST /api/v1/auth/refresh:
  1) token inválido/revogado/expirado      -> 401 genérico, sem Retry-After
  2) reapresentação transitória (hash aposentado há <= 15s com família
     viva, ou perdedor do CAS)               -> 401 genérico + Retry-After,
                                               nada é revogado
  3) reuse confirmado (hash aposentado há > 15s com família viva)
                                            -> família revogada + 401 genérico

Estratégia: TestClient real contra app.main.app com get_db em SQLite em
memória (mesmo padrão de test_auth_logout.py). A janela é exercitada
recuando retired_at no banco, sem mexer no relógio.
"""
import hashlib
import logging
import os
import secrets
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

os.environ.setdefault("SECRET_KEY", "auth-reuse-test-secret")
os.environ.setdefault("JWT_SECRET", os.environ["SECRET_KEY"])

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1.routes.auth import REFRESH_REUSE_GRACE_SEC
from app.database import Base, get_db
from app.main import app
from app.models.refresh_token import RefreshToken
from app.models.refresh_token_retired import RefreshTokenRetiredHash
from app.models.user_main import User
from app.utils.security import hash_password

# Reaproveita o harness de corrida real (threads + pausa no SELECT).
from test_refresh_concurrency import (  # noqa: F401  (fixture importada)
    _create_refresh_token_row,
    _create_user,
    _do_refresh,
    _run_concurrent_rotation,
    session_factory,
)

LOGIN = "/api/v1/auth/login"
REFRESH = "/api/v1/auth/refresh"
LOGOUT = "/api/v1/auth/logout"
LOGOUT_ALL = "/api/v1/auth/logout-all"
PW = "pw-reuse"


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def client(db_session, monkeypatch):
    monkeypatch.setenv("LOGIN_RL_ENABLED", "0")
    monkeypatch.setenv("REFRESH_RL_ENABLED", "0")

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db, None)


def _sha(raw):
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _user(db, email):
    u = User(email=email, hashed_password=hash_password(PW), role="customer")
    db.add(u)
    db.commit()
    return u


def _login(client, email):
    r = client.post(LOGIN, json={"username": email, "password": PW})
    assert r.status_code == 200, r.text
    return r.json()["refresh_token"]


def _refresh(client, rt):
    return client.post(REFRESH, json={"refresh_token": rt})


def _rotate(client, rt):
    r = _refresh(client, rt)
    assert r.status_code == 200, r.text
    return r.json()["refresh_token"]


def _family_of(db, rt):
    db.expire_all()
    row = db.query(RefreshToken).filter(RefreshToken.token_hash == _sha(rt)).first()
    return row.id if row else None


def _family_exists(db, family_id):
    db.expire_all()
    return db.query(RefreshToken).filter(RefreshToken.id == family_id).count() == 1


def _age_retired(db, rt, seconds=REFRESH_REUSE_GRACE_SEC + 1):
    """Simula a passagem do tempo: recua retired_at do hash aposentado."""
    db.expire_all()
    row = (
        db.query(RefreshTokenRetiredHash)
        .filter(RefreshTokenRetiredHash.token_hash == _sha(rt))
        .one()
    )
    row.retired_at = datetime.now(timezone.utc) - timedelta(seconds=seconds)
    db.commit()


def _assert_generic_401(r):
    assert r.status_code == 401, r.text
    assert r.json() == {"detail": "Refresh token inválido/expirado"}
    assert "retry-after" not in r.headers


def _assert_transient_401(r):
    assert r.status_code == 401, r.text
    assert r.json() == {"detail": "Refresh token inválido/expirado"}
    assert r.headers.get("retry-after") == "1"


# A) login + refresh legítimo
def test_a_login_and_legit_refresh(client, db_session):
    _user(db_session, "a@test.local")
    rt_a = _login(client, "a@test.local")
    r = _refresh(client, rt_a)
    assert r.status_code == 200
    body = r.json()
    assert body["access_token"] and body["refresh_token"] and body["refresh_token"] != rt_a


# B) rotação mantém a família e aposenta o hash anterior
def test_b_rotation_keeps_family_and_retires_old_hash(client, db_session):
    _user(db_session, "b@test.local")
    rt_a = _login(client, "b@test.local")
    family = _family_of(db_session, rt_a)
    rt_b = _rotate(client, rt_a)

    assert _family_of(db_session, rt_b) == family
    retired = db_session.query(RefreshTokenRetiredHash).all()
    assert [(r.token_hash, r.family_id) for r in retired] == [(_sha(rt_a), family)]
    assert retired[0].retired_at is not None


# C) RT antigo fora da janela -> 401 e família revogada
def test_c_old_token_outside_window_revokes_family(client, db_session, caplog):
    u = _user(db_session, "c@test.local")
    rt_a = _login(client, "c@test.local")
    family = _family_of(db_session, rt_a)
    _rotate(client, rt_a)
    _age_retired(db_session, rt_a)

    with caplog.at_level(logging.WARNING, logger="app.api.v1.routes.auth"):
        r = _refresh(client, rt_a)
    _assert_generic_401(r)
    assert not _family_exists(db_session, family)
    assert db_session.query(RefreshTokenRetiredHash).filter_by(family_id=family).count() == 0
    assert f"refresh_token_reuse_detected family_id={family} user_id={u.id}" in caplog.text


# D) depois de C, o RT atual da família (B) também morre
def test_d_current_token_dies_after_reuse(client, db_session):
    _user(db_session, "d@test.local")
    rt_a = _login(client, "d@test.local")
    rt_b = _rotate(client, rt_a)
    _age_retired(db_session, rt_a)
    _assert_generic_401(_refresh(client, rt_a))

    _assert_generic_401(_refresh(client, rt_b))
    # e o RT antigo segue morto (família não existe mais -> genérico)
    _assert_generic_401(_refresh(client, rt_a))


# E) novo login depois do reuse cria família nova e funcional
def test_e_new_login_after_reuse_creates_working_family(client, db_session):
    _user(db_session, "e@test.local")
    rt_a = _login(client, "e@test.local")
    old_family = _family_of(db_session, rt_a)
    _rotate(client, rt_a)
    _age_retired(db_session, rt_a)
    _assert_generic_401(_refresh(client, rt_a))

    rt_new = _login(client, "e@test.local")
    new_family = _family_of(db_session, rt_new)
    assert new_family is not None
    rt_new2 = _rotate(client, rt_new)
    assert _family_of(db_session, rt_new2) == new_family
    # mesmo que o SQLite reutilize o id, o hash velho não aponta pra família nova
    _assert_generic_401(_refresh(client, rt_a))
    assert _family_exists(db_session, new_family)
    if new_family == old_family:
        assert _rotate(client, rt_new2)


# F) corrida real: um vencedor; perdedor não revoga; token do vencedor vale
def test_f_concurrent_loser_is_transient_and_does_not_revoke(session_factory):
    user_id = _create_user(session_factory, "f@test.local")
    raw_rt = secrets.token_urlsafe(48)
    _create_refresh_token_row(session_factory, user_id=user_id, token_hash=_sha(raw_rt))

    result = _run_concurrent_rotation(session_factory, raw_rt=raw_rt, select_index=1)
    winner = result.get("t1") or result.get("t2")
    loser_err = result.get("t1_error") or result.get("t2_error")
    assert winner is not None and loser_err is not None
    assert loser_err.status_code == 401
    assert (loser_err.headers or {}).get("Retry-After") == "1"

    s = session_factory()
    rows = s.query(RefreshToken).filter(RefreshToken.user_id == user_id).all()
    assert len(rows) == 1  # família intacta
    retired = s.query(RefreshTokenRetiredHash).all()
    assert [(r.token_hash, r.family_id) for r in retired] == [(_sha(raw_rt), rows[0].id)]
    s.close()

    res, err = _do_refresh(
        session_factory, host="198.51.100.40", raw_refresh_token=winner["refresh_token"]
    )
    assert err is None, err
    assert res["refresh_token"]


# G) RT antigo dentro da janela: sem revogação, sem logout indevido
def test_g_old_token_inside_window_is_transient(client, db_session):
    _user(db_session, "g@test.local")
    rt_a = _login(client, "g@test.local")
    family = _family_of(db_session, rt_a)
    rt_b = _rotate(client, rt_a)

    # outra aba / retry reapresenta A logo depois da rotação
    _assert_transient_401(_refresh(client, rt_a))
    assert _family_exists(db_session, family)

    # na borda da janela ainda é transitório
    _age_retired(db_session, rt_a, seconds=REFRESH_REUSE_GRACE_SEC - 1)
    _assert_transient_401(_refresh(client, rt_a))
    assert _family_exists(db_session, family)

    # a sessão legítima (B) segue funcionando
    rt_c = _rotate(client, rt_b)
    assert _family_of(db_session, rt_c) == family


# H) um RT não gera duas rotações válidas
def test_h_one_token_cannot_rotate_twice(client, db_session):
    _user(db_session, "h@test.local")
    rt_a = _login(client, "h@test.local")
    _rotate(client, rt_a)
    for _ in range(3):
        assert _refresh(client, rt_a).status_code == 401
    _age_retired(db_session, rt_a)
    assert _refresh(client, rt_a).status_code == 401
    assert db_session.query(RefreshTokenRetiredHash).filter_by(token_hash=_sha(rt_a)).count() <= 1


# I) logout 204 e o token para de funcionar (sem tombstone)
def test_i_logout_204_and_token_dead(client, db_session):
    _user(db_session, "i@test.local")
    rt_a = _login(client, "i@test.local")
    family = _family_of(db_session, rt_a)
    rt_b = _rotate(client, rt_a)

    r = client.post(LOGOUT, json={"refresh_token": rt_b})
    assert r.status_code == 204 and r.content == b""
    _assert_generic_401(_refresh(client, rt_b))
    # RT antigo da família também morre e sem Retry-After (família não existe)
    _assert_generic_401(_refresh(client, rt_a))
    assert not _family_exists(db_session, family)
    assert db_session.query(RefreshTokenRetiredHash).count() == 0
    # idempotente, não revela existência
    assert client.post(LOGOUT, json={"refresh_token": rt_b}).status_code == 204
    assert client.post(LOGOUT, json={"refresh_token": "nunca-existiu"}).status_code == 204


# J) logout-all derruba todas as famílias do usuário
def test_j_logout_all_kills_every_family(client, db_session):
    _user(db_session, "j@test.local")
    other = _user(db_session, "j-other@test.local")
    rt1 = _rotate(client, _login(client, "j@test.local"))
    rt2 = _login(client, "j@test.local")
    rt_other = _login(client, "j-other@test.local")

    access = _refresh(client, rt2).json()
    rt2 = access["refresh_token"]
    r = client.post(LOGOUT_ALL, headers={"Authorization": f"Bearer {access['access_token']}"})
    assert r.status_code == 204

    _assert_generic_401(_refresh(client, rt1))
    _assert_generic_401(_refresh(client, rt2))
    db_session.expire_all()
    remaining = db_session.query(RefreshTokenRetiredHash.family_id).all()
    other_families = {
        x.id for x in db_session.query(RefreshToken).filter_by(user_id=other.id)
    }
    assert {f for (f,) in remaining} <= other_families
    # outro usuário intacto
    assert _refresh(client, rt_other).status_code == 200


# K) expiração de 7 dias e rotação renova +7d
def test_k_seven_day_expiry_and_rotation_renews(client, db_session):
    _user(db_session, "k@test.local")
    rt_a = _login(client, "k@test.local")

    db_session.expire_all()
    row = db_session.query(RefreshToken).filter_by(token_hash=_sha(rt_a)).one()
    row.expires_at = datetime.now(timezone.utc) + timedelta(days=1)
    db_session.commit()

    before = datetime.now(timezone.utc)
    rt_b = _rotate(client, rt_a)
    db_session.expire_all()
    row = db_session.query(RefreshToken).filter_by(token_hash=_sha(rt_b)).one()
    exp = row.expires_at if row.expires_at.tzinfo else row.expires_at.replace(tzinfo=timezone.utc)
    assert before + timedelta(days=7) - timedelta(minutes=1) <= exp
    assert exp <= datetime.now(timezone.utc) + timedelta(days=7, minutes=1)

    row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db_session.commit()
    _assert_generic_401(_refresh(client, rt_b))


# L) nenhum token cru persistido
def test_l_no_raw_token_persisted(client, db_session):
    _user(db_session, "l@test.local")
    raws = [_login(client, "l@test.local")]
    for _ in range(3):
        raws.append(_rotate(client, raws[-1]))
    _assert_transient_401(_refresh(client, raws[0]))

    conn = db_session.connection()
    dump = []
    for table in ("refresh_tokens", "refresh_token_retired_hashes"):
        for row in conn.execute(sa.text(f"SELECT * FROM {table}")):
            dump.extend(str(v) for v in row)
    blob = "\n".join(dump)
    for raw in raws:
        assert raw not in blob
    retired = {h for (h,) in db_session.query(RefreshTokenRetiredHash.token_hash)}
    assert retired == {_sha(r) for r in raws[:-1]}


# M) nenhum token cru nos logs
def test_m_no_raw_token_in_logs(client, db_session, caplog, capsys):
    _user(db_session, "m@test.local")
    with caplog.at_level(logging.DEBUG):
        rt_a = _login(client, "m@test.local")
        rt_b = _rotate(client, rt_a)
        _refresh(client, rt_a)  # transitório
        _age_retired(db_session, rt_a)
        _refresh(client, rt_a)  # reuse
        _refresh(client, rt_b)
    out = capsys.readouterr()
    text = caplog.text + out.out + out.err
    assert "refresh_token_reuse_detected" in caplog.text
    for raw in (rt_a, rt_b):
        assert raw not in text
        assert _sha(raw) not in text


# N) reuse numa família não derruba outra família do mesmo usuário
def test_n_reuse_in_one_family_spares_other_family(client, db_session):
    _user(db_session, "n@test.local")
    rt_1a = _login(client, "n@test.local")
    rt_2 = _login(client, "n@test.local")
    fam2 = _family_of(db_session, rt_2)
    _rotate(client, rt_1a)
    _age_retired(db_session, rt_1a)
    _assert_generic_401(_refresh(client, rt_1a))

    assert _family_exists(db_session, fam2)
    assert _family_of(db_session, _rotate(client, rt_2)) == fam2


# O) A -> B -> C; usar A fora da janela é reuse
def test_o_older_ancestor_reuse(client, db_session):
    _user(db_session, "o@test.local")
    rt_a = _login(client, "o@test.local")
    family = _family_of(db_session, rt_a)
    rt_b = _rotate(client, rt_a)
    rt_c = _rotate(client, rt_b)
    _age_retired(db_session, rt_a)

    _assert_generic_401(_refresh(client, rt_a))
    assert not _family_exists(db_session, family)
    _assert_generic_401(_refresh(client, rt_c))
    _assert_generic_401(_refresh(client, rt_b))


# Prova da "necessidade técnica" da remoção explícita dos hashes
# aposentados: em SQLite sem PRAGMA foreign_keys o ON DELETE CASCADE não
# dispara e o id INTEGER é reutilizado.
def test_sqlite_cascade_does_not_fire_and_ids_are_reused(db_session):
    u = _user(db_session, "fk@test.local")
    exp = datetime.now(timezone.utc) + timedelta(days=7)
    fam = RefreshToken(user_id=u.id, token_hash="x" * 64, expires_at=exp)
    db_session.add(fam)
    db_session.commit()
    fam_id = fam.id
    db_session.add(
        RefreshTokenRetiredHash(token_hash="y" * 64, family_id=fam_id, retired_at=exp)
    )
    db_session.commit()

    db_session.query(RefreshToken).filter_by(id=fam_id).delete(synchronize_session=False)
    db_session.commit()
    assert db_session.query(RefreshTokenRetiredHash).filter_by(family_id=fam_id).count() == 1

    new = RefreshToken(user_id=u.id, token_hash="z" * 64, expires_at=exp)
    db_session.add(new)
    db_session.commit()
    assert new.id == fam_id  # órfão passaria a apontar para a família nova


# P) migration: upgrade / downgrade / upgrade num SQLite temporário.
# A cadeia completa desde a base não roda em SQLite (migrations antigas usam
# ALTER COLUMN ... SET NOT NULL), então o banco nasce do schema dos models
# SEM a tabela nova, é carimbado na revisão anterior e só esta migration roda.
def test_p_migration_upgrade_and_downgrade(tmp_path):
    backend = Path(__file__).resolve().parents[1]
    db_file = tmp_path / "mig.db"
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{db_file}"}

    def alembic(*args):
        r = subprocess.run(
            [sys.executable, "-m", "alembic", "-c", str(backend / "alembic.ini"), *args],
            cwd=backend, env=env, capture_output=True, text=True,
        )
        assert r.returncode == 0, r.stdout + r.stderr

    def inspect():
        eng = create_engine(f"sqlite:///{db_file}")
        try:
            insp = sa.inspect(eng)
            tables = set(insp.get_table_names())
            idx = (
                {i["name"]: (tuple(i["column_names"]), bool(i["unique"]))
                 for i in insp.get_indexes("refresh_token_retired_hashes")}
                if "refresh_token_retired_hashes" in tables else None
            )
            fks = (
                insp.get_foreign_keys("refresh_token_retired_hashes")
                if "refresh_token_retired_hashes" in tables else None
            )
            return tables, idx, fks
        finally:
            eng.dispose()

    eng = create_engine(f"sqlite:///{db_file}")
    Base.metadata.create_all(
        bind=eng,
        tables=[t for t in Base.metadata.sorted_tables
                if t.name != "refresh_token_retired_hashes"],
    )
    eng.dispose()
    alembic("stamp", "77ac52cd2468")

    alembic("upgrade", "head")
    tables, idx, fks = inspect()
    assert "refresh_token_retired_hashes" in tables
    assert idx["ix_refresh_token_retired_hashes_token_hash"] == (("token_hash",), True)
    assert idx["ix_refresh_token_retired_hashes_family_id"] == (("family_id",), False)
    assert idx["ix_refresh_token_retired_hashes_retired_at"] == (("retired_at",), False)
    assert len(fks) == 1
    assert fks[0]["referred_table"] == "refresh_tokens"
    assert fks[0]["referred_columns"] == ["id"]
    assert (fks[0].get("options") or {}).get("ondelete") == "CASCADE"

    alembic("downgrade", "-1")
    tables, _, _ = inspect()
    assert "refresh_token_retired_hashes" not in tables
    assert "refresh_tokens" in tables

    alembic("upgrade", "head")
    tables, _, _ = inspect()
    assert "refresh_token_retired_hashes" in tables
