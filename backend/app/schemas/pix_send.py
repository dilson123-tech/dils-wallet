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
