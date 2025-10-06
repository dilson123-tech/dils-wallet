from pydantic import BaseModel
from datetime import datetime

class PixTransactionBase(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: float

class PixTransactionResponse(PixTransactionBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
