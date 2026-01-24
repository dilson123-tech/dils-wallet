import sys
from fastapi import FastAPI

try:
    # sempre aponta pro app real
    from app.main import app as app  # noqa: F401
    if not isinstance(app, FastAPI):
        raise TypeError(f"app.main.app is not FastAPI: {type(app)}")
    print(f"[ENTRYPOINT] using app.main:app ({type(app)})", file=sys.stderr)
except Exception as e:
    print(f"[ENTRYPOINT] fallback: failed to import app.main:app ({e!r})", file=sys.stderr)
    app = FastAPI(title="Aurea Fallback")

    @app.get("/healthz")
    def healthz():
        return {"ok": True, "service": "dils-wallet", "fallback": True}

    @app.get("/")
    def root():
        return {"ok": True, "root": True, "fallback": True}
