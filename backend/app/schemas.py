from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

# ==== User Schemas ====
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    type: str = "pf"  # pf = pessoa física, pj = pessoa jurídica

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

# ==== Transaction Schemas ====
class TransactionBase(BaseModel):
    tipo: str
    valor: float
    referencia: Optional[str] = None

class TransactionCreate(TransactionBase):
    pass

class TransactionResponse(TransactionBase):
    id: int
    criado_em: datetime
    user_id: int

    class Config:
        orm_mode = True

# ==== Auth Schemas ====
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None

from pydantic import BaseModel
class BalanceOut(BaseModel):
    saldo: float
# --- Pagination (Dils Wallet) ---
from pydantic import BaseModel
from typing import List

class PageMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool

class TransactionsPage(BaseModel):
    items: List[TransactionResponse]  # usa o schema já definido acima no arquivo
    meta: PageMeta
