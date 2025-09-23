from passlib.context import CryptContext

# Exporta as funções de senha para quem faz `from app import utils`
_pwd = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return _pwd.hash(password)

def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return _pwd.verify(plain_password, password_hash)
    except Exception:
        return False
