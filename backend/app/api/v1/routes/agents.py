from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
import hashlib, json

router = APIRouter(prefix="/api/v1/agents", tags=["Agents"])

class ShadowEvent(BaseModel):
    actor: str = Field(..., min_length=3)
    action: str = Field(..., min_length=3)
    target: str = Field(..., min_length=3)
    input: dict
    suggestion: dict
    hash: str = Field(..., min_length=16)

def _mk_hash(payload: dict) -> str:
    raw = f"{payload['actor']}{payload['action']}{payload['target']}" \
          f"{json.dumps(payload['input'],sort_keys=True)}{json.dumps(payload['suggestion'],sort_keys=True)}"
    return hashlib.sha256(raw.encode()).hexdigest()

@router.post("/shadow-event")
def shadow_event(evt: ShadowEvent, idem: str | None = Header(default=None, alias="Idempotency-Key")):
    if _mk_hash(evt.model_dump()) != evt.hash:
        raise HTTPException(status_code=422, detail="hash mismatch")
    print("[SHADOW]", datetime.utcnow().isoformat(), {"idem": idem, **evt.model_dump()})
    return {"ok": True, "at": datetime.utcnow().isoformat(), "idempotency": idem}
