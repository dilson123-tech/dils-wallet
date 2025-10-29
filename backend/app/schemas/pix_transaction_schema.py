from pydantic import BaseModel

class PixItem(BaseModel):
    tipo: str            # "entrada" | "saida"
    descricao: str
    valor: str           # string pra não dar imprecisão float no front
    timestamp: str | None

class PixHistoryResponse(BaseModel):
    conta: dict
    saldo_pix: str
    historico: list[PixItem]
