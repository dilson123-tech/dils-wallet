from pydantic import BaseModel, Field
from decimal import Decimal


class PixSendRequest(BaseModel):
    chave_pix: str = Field(..., min_length=3, max_length=255)
    valor: Decimal = Field(..., gt=0)
    descricao: str | None = Field(default="PIX")


class PixSendResponse(BaseModel):
    id: int
    valor: Decimal
    taxa_percentual: Decimal
    taxa_valor: Decimal
    valor_liquido: Decimal
    status: str


class PixSendIntentRequest(BaseModel):
    chave_pix: str = Field(..., min_length=3, max_length=255)
    valor: Decimal = Field(..., gt=0)
    descricao: str | None = Field(default="PIX")
    force_new: bool = Field(default=False)


class PixSendIntentResponse(BaseModel):
    state: str
    send_key: str | None
    generation: int
    reused: bool
    can_send: bool
    requires_explicit_new: bool
    force_new_rejected: bool = False


class PixSendIntentAckRequest(BaseModel):
    send_key: str = Field(..., min_length=1, max_length=64)


class PixSendIntentAckResponse(BaseModel):
    state: str
    generation: int
    reused: bool
