import os

# pega a SECRET_KEY do ambiente (Railway), senão usa fallback de dev
SECRET_KEY = os.getenv("SECRET_KEY", "dev-temp-key")

# algoritmo padrão de assinatura JWT
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# helpers opcionais para outras partes do código poderem consultar
def get_secret_key() -> str:
    return SECRET_KEY

def get_algorithm() -> str:
    return ALGORITHM
