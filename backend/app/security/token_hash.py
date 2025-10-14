import hashlib
def refresh_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
