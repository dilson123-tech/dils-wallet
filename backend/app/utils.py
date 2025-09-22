from passlib.context import CryptContext

# Aceita pbkdf2_sha256 e bcrypt (qualquer um que estiver no banco)
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256", "bcrypt"],
    deprecated="auto",
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return pwd_context.verify(plain_password, password_hash)
    except Exception:
        # Evita 500 se vier um formato inesperado
        return False
