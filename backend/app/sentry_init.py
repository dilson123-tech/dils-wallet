import os


def setup_sentry() -> None:
    """
    Inicializa o Sentry SOMENTE se SENTRY_DSN estiver presente e válido.
    Fail-safe em duas camadas independentes:
      - ausência/incompatibilidade do pacote sentry-sdk nunca derruba o app
        (import feito aqui dentro, protegido por seu próprio try/except);
      - qualquer erro em sentry_sdk.init(...) também nunca derruba o app.
    """
    dsn = os.getenv("SENTRY_DSN", "").strip()
    # validação mínima: precisa parecer um DSN real
    if not dsn or not (dsn.startswith(("http://", "https://")) and "@" in dsn):
        return  # DSN ausente/placeholder → não inicializa

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
    except Exception:
        # sentry-sdk ausente ou incompatível no ambiente: não inicializa,
        # e sobretudo não derruba o startup do app.
        return

    try:
        # GIT_SHA já é usado em /healthz; reaproveitado como release só se
        # presente — não torna nenhuma configuração nova obrigatória.
        release = os.getenv("GIT_SHA", "").strip() or None
        sentry_sdk.init(
            dsn=dsn,
            integrations=[FastApiIntegration()],
            traces_sample_rate=float(os.getenv("SENTRY_TRACES", "0.1")),     # 10% tracing
            profiles_sample_rate=float(os.getenv("SENTRY_PROFILES", "0.1")), # 10% profiling
            send_default_pii=False,
            max_request_body_size="never",  # nunca captura corpo da requisição (payloads PIX, credenciais, etc.)
            environment=os.getenv("SENTRY_ENV", "dev"),
            release=release,
        )
    except Exception:
        # falha ao inicializar Sentry não deve derrubar o app
        pass
