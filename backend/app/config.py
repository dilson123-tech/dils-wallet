import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-override-me")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# demo = modo atual/lab, sem dinheiro real
# partner = futuro modo com parceiro financeiro/PSP/BaaS
_wallet_mode_raw = os.getenv("WALLET_MODE", "demo").strip().lower()
WALLET_MODE = _wallet_mode_raw if _wallet_mode_raw in {"demo", "partner"} else "demo"
IS_DEMO_WALLET = WALLET_MODE == "demo"
IS_PARTNER_WALLET = WALLET_MODE == "partner"

