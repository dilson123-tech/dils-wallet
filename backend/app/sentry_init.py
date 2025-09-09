import os
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

def setup_sentry():
    dsn = os.getenv("SENTRY_DSN", "").strip()
    # validação mínima: precisa parecer um DSN real
    if not dsn or not (dsn.startswith(("http://", "https://")) and "@" in dsn):
        return  # DSN ausente/placeholder → não inicializa
    try:
        sentry_sdk.init(
            dsn=dsn,
            integrations=[FastApiIntegration()],
            traces_sample_rate=float(os.getenv("SENTRY_TRACES", "0.1")),     # 10% tracing
            profiles_sample_rate=float(os.getenv("SENTRY_PROFILES", "0.1")), # 10% profiling
            send_default_pii=False,
            environment=os.getenv("SENTRY_ENV", "dev"),
        )
    except Exception:
        # falha ao inicializar Sentry não deve derrubar o app
        pass
