from fastapi import APIRouter, Header
from pydantic import BaseModel, Field
from datetime import datetime

router = APIRouter(tags=["PIX"])

class TransferRequest(BaseModel):
    to: str = Field(..., min_length=3)
    amount: float = Field(..., gt=0)
    currency: str = "BRL"
    description: str | None = None

class TransferResponse(BaseModel):
    status: str
    transfer_id: str
    new_balance: float
    echoed: dict
    at: datetime

@router.get("/balance")
def get_balance():
    return {"balance": 159.32}

@router.get("/history")
def get_history(limit: int = 10):
    items = [
        {"id": f"mock-{i}", "when": "2025-10-21T19:00:00Z", "type": "IN" if i % 2 == 0 else "OUT", "description": "PIX demo"}
        for i in range(limit)
    ]
    return {"items": items}

@router.post("/transfer", response_model=TransferResponse)
def post_transfer(
    payload: TransferRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    base_balance = 159.32
    transfer_id = f"tr_{(idempotency_key or str(datetime.utcnow().timestamp())).replace('.', '')}"
    new_balance = round(max(0.0, base_balance - float(payload.amount)), 2)
    return TransferResponse(
        status="accepted",
        transfer_id=transfer_id,
        new_balance=new_balance,
        echoed=payload.model_dump(),
        at=datetime.utcnow(),
    )
