"""
Testes da inicialização fail-safe do Sentry (backend/app/sentry_init.py).

Cobrem, sem nenhuma comunicação real com Sentry ou com a internet:
  1) ausência de SENTRY_DSN -> no-op, sem exceção;
  2) SENTRY_DSN inválido -> no-op, sem exceção;
  3) ausência/import failure do pacote sentry_sdk -> não derruba
     setup_sentry() (simulado via sys.modules, sem desinstalar nada);
  4) configuração válida com SDK mockado -> sentry_sdk.init() recebe
     exatamente os parâmetros de segurança esperados (send_default_pii,
     max_request_body_size, integrations, traces/profiles, environment,
     release).

Nenhum teste aqui chama sentry_sdk.init() real nem abre qualquer socket:
nos casos 1/2/3 a inicialização real nunca é alcançada (retorno antecipado
ou ImportError simulado); no caso 4 o módulo sentry_sdk é substituído por
um dublê em memória antes da chamada.
"""
import sys
import types

import pytest

from app.sentry_init import setup_sentry


@pytest.fixture(autouse=True)
def _clean_sentry_env(monkeypatch):
    # Isola cada teste de qualquer SENTRY_* real que possa estar no ambiente.
    for var in ("SENTRY_DSN", "SENTRY_TRACES", "SENTRY_PROFILES", "SENTRY_ENV", "GIT_SHA"):
        monkeypatch.delenv(var, raising=False)
    yield


def test_no_dsn_is_noop_and_does_not_raise(monkeypatch):
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    setup_sentry()  # não deve lançar nada


@pytest.mark.parametrize(
    "bad_dsn",
    [
        "",
        "not-a-url",
        "ftp://no-at-sign.example/1",
        "https://sem-arroba.example/1",  # sem "@" -> não parece DSN real
    ],
)
def test_invalid_dsn_is_noop_and_does_not_raise(monkeypatch, bad_dsn):
    monkeypatch.setenv("SENTRY_DSN", bad_dsn)
    setup_sentry()  # não deve lançar nada


def test_missing_sentry_sdk_package_does_not_crash(monkeypatch):
    """
    Simula o pacote sentry-sdk ausente/incompatível no ambiente, sem
    desinstalar nada de verdade: registra `None` em sys.modules para o
    nome do pacote, o que faz qualquer `import sentry_sdk` subsequente
    levantar ImportError -- exatamente o cenário que setup_sentry() deve
    absorver sem derrubar o app.
    """
    monkeypatch.setenv("SENTRY_DSN", "https://public@example.ingest.sentry.io/1")
    monkeypatch.setitem(sys.modules, "sentry_sdk", None)
    monkeypatch.setitem(sys.modules, "sentry_sdk.integrations.fastapi", None)

    setup_sentry()  # não deve lançar ImportError nem nenhuma outra exceção


def _install_fake_sentry_sdk(monkeypatch):
    """
    Instala um dublê em memória de sentry_sdk + sentry_sdk.integrations.fastapi
    em sys.modules, capturando os kwargs passados a init(). Nenhuma chamada
    de rede é possível através deste dublê.
    """
    captured = {}

    fake_sentry_sdk = types.ModuleType("sentry_sdk")

    def fake_init(**kwargs):
        captured.update(kwargs)

    fake_sentry_sdk.init = fake_init

    fake_fastapi_integration_module = types.ModuleType("sentry_sdk.integrations.fastapi")

    class FakeFastApiIntegration:
        pass

    fake_fastapi_integration_module.FastApiIntegration = FakeFastApiIntegration

    fake_integrations_pkg = types.ModuleType("sentry_sdk.integrations")
    fake_integrations_pkg.fastapi = fake_fastapi_integration_module

    monkeypatch.setitem(sys.modules, "sentry_sdk", fake_sentry_sdk)
    monkeypatch.setitem(sys.modules, "sentry_sdk.integrations", fake_integrations_pkg)
    monkeypatch.setitem(sys.modules, "sentry_sdk.integrations.fastapi", fake_fastapi_integration_module)

    return captured, FakeFastApiIntegration


def test_valid_config_calls_init_with_expected_safe_kwargs(monkeypatch):
    captured, fake_integration_cls = _install_fake_sentry_sdk(monkeypatch)

    monkeypatch.setenv("SENTRY_DSN", "https://public@example.ingest.sentry.io/1")
    monkeypatch.setenv("SENTRY_TRACES", "0.25")
    monkeypatch.setenv("SENTRY_PROFILES", "0.05")
    monkeypatch.setenv("SENTRY_ENV", "staging")
    monkeypatch.setenv("GIT_SHA", "deadbeef")

    setup_sentry()

    assert captured, "sentry_sdk.init não foi chamado"
    assert captured["dsn"] == "https://public@example.ingest.sentry.io/1"
    assert captured["send_default_pii"] is False
    assert captured["max_request_body_size"] == "never"
    assert captured["traces_sample_rate"] == 0.25
    assert captured["profiles_sample_rate"] == 0.05
    assert captured["environment"] == "staging"
    assert captured["release"] == "deadbeef"

    assert len(captured["integrations"]) == 1
    assert isinstance(captured["integrations"][0], fake_integration_cls)


def test_valid_config_without_git_sha_does_not_require_release(monkeypatch):
    captured, _ = _install_fake_sentry_sdk(monkeypatch)

    monkeypatch.setenv("SENTRY_DSN", "https://public@example.ingest.sentry.io/1")
    monkeypatch.delenv("GIT_SHA", raising=False)

    setup_sentry()  # não deve lançar nada mesmo sem GIT_SHA

    assert captured["release"] is None


def test_init_exception_does_not_propagate(monkeypatch):
    """
    Mesmo com SDK e DSN válidos, se sentry_sdk.init() levantar, o app não
    pode cair.
    """
    fake_sentry_sdk = types.ModuleType("sentry_sdk")

    def failing_init(**kwargs):
        raise RuntimeError("falha simulada de inicialização do Sentry")

    fake_sentry_sdk.init = failing_init

    fake_fastapi_integration_module = types.ModuleType("sentry_sdk.integrations.fastapi")

    class FakeFastApiIntegration:
        pass

    fake_fastapi_integration_module.FastApiIntegration = FakeFastApiIntegration

    monkeypatch.setitem(sys.modules, "sentry_sdk", fake_sentry_sdk)
    monkeypatch.setitem(sys.modules, "sentry_sdk.integrations.fastapi", fake_fastapi_integration_module)

    monkeypatch.setenv("SENTRY_DSN", "https://public@example.ingest.sentry.io/1")

    setup_sentry()  # não deve propagar o RuntimeError
