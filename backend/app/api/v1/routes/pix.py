from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Literal, List, Dict, Any
from datetime import datetime, timezone
from threading import Lock

router = APIRouter(tags=["PIX"])

class TransferReq(BaseModel):
    amount: float = Field(..., gt=0)
    type: Literal["in", "out"]
    description: str = "Transação teste"

_state = {
    "balance": 0.0,
    "history": []  # List[Dict[str, Any]]
}
_lock = Lock()

@router.get("/balance")
def get_balance() -> Dict[str, float]:
    with _lock:
        return {"balance": round(_state["balance"], 2)}

@router.get("/history")
def get_history(limit: int = 10) -> List[Dict[str, Any]]:
    with _lock:
        return list(reversed(_state["history"]))[:limit]

@router.post("/transfer")
def post_transfer(req: TransferReq) -> Dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    with _lock:
        delta = req.amount if req.type == "in" else -req.amount
        _state["balance"] = round(_state["balance"] + delta, 2)
        tx = {
            "id": f"mock-{len(_state['history'])+1}",
            "type": req.type,
            "amount": round(req.amount, 2),
            "description": req.description,
            "when": now,
        }
        _state["history"].append(tx)
        return {"balance": _state["balance"], "tx": tx}
