import hashlib
import json

def stable_hash_payload(payload: dict) -> str:
    ser = json.dumps(payload, sort_keys=True, separators=(",",":")).encode()
    return hashlib.sha256(ser).hexdigest()
