from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict

# ===== Conteúdo migrado de backend/app/schemas.py (mantém compatibilidade) =====
class UserCreate(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    password: str
    model_config = ConfigDict(from_attributes=True)

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str
    model_config = ConfigDict(from_attributes=True)

# ===== Expor novos schemas do pacote =====
from .pix_transaction_schema import PixItem, PixHistoryResponse  # noqa: F401
