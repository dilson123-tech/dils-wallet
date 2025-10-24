# Compatibilidade retroativa para código legado que fazia:
# from app.security.jwt_core import SECRET_KEY (ou ALGORITHM)
try:
    from .jwt_core import SECRET_KEY  # variável usada pelo jwt_core
except Exception:  # fallback seguro para dev
    SECRET_KEY = "dev-secret-change-me"

# Alguns trechos legados podem esperar "ALGORITHM" (nome antigo).
# No jwt_core, usamos ALGO. Reexportamos com ambos os nomes.
try:
    from .jwt_core import ALGO as ALGORITHM
except Exception:
    ALGORITHM = "HS256"
