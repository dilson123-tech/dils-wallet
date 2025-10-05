from pydantic import BaseModel, Field, PositiveFloat

class PixMockIn(BaseModel):
    from_account_id: int = Field(..., gt=0)
    to_account_id:   int = Field(..., gt=0)
    amount:          PositiveFloat
    idempotency_key: str = Field(..., min_length=8, max_length=64)

class PixMockOut(BaseModel):
    status: str
    debit_tx_id: int
    credit_tx_id: int
    balance_from: float
    balance_to: float
