"""
Regressão: a revogação por reuse no POST /api/v1/auth/refresh não pode
deixar a família apagada viva no identity map da Session.

O DELETE em massa com synchronize_session=False não tira da Session a
instância `family` carregada no próprio endpoint. Em SQLite o id INTEGER
é reutilizado, então o próximo login na mesma Session grava uma família
nova com o MESMO id: SAWarning "Identity map already had an identity"
e, se o GC recolher a instância velha no meio do flush, AttributeError
no commit do refresh (HTTP 500). Como o identity map guarda referências
fracas, a falha original era intermitente (dependia do momento do GC).
Aqui o teste segura uma referência forte à família e trata SAWarning
como erro, o que torna a reprodução determinística.
"""
import warnings

from sqlalchemy import exc as sa_exc

from app.models.refresh_token import RefreshToken

from test_refresh_reuse_detection import (  # noqa: F401  (fixtures importadas)
    _age_retired,
    _assert_generic_401,
    _family_of,
    _login,
    _refresh,
    _rotate,
    _user,
    client,
    db_session,
)


def test_reuse_revocation_does_not_leave_stale_family_in_session(client, db_session):
    _user(db_session, "im@test.local")
    rt_a = _login(client, "im@test.local")
    fam_id = _family_of(db_session, rt_a)
    _rotate(client, rt_a)
    _age_retired(db_session, rt_a)

    # Mesma instância que o endpoint carrega (Session compartilhada).
    family = db_session.get(RefreshToken, fam_id)
    _assert_generic_401(_refresh(client, rt_a))
    assert family not in db_session

    with warnings.catch_warnings():
        warnings.simplefilter("error", sa_exc.SAWarning)
        rt_new = _login(client, "im@test.local")
        new_family = _family_of(db_session, rt_new)
        # pré-condição do bug: o SQLite reutilizou o id da família revogada
        assert new_family == fam_id
        assert _family_of(db_session, _rotate(client, rt_new)) == new_family
