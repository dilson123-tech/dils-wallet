"""
ASGI entrypoint (Railway).
Expose the real FastAPI app so startup events run (DB init, routers, etc).
"""
from app.main import app  # noqa: F401
