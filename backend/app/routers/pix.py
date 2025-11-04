from decimal import Decimal
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.pix_transaction import PixTransaction
from datetime import datetime

router = APIRouter()

# helper seguro pra montar dict de transação
def tx_to_dict(t: PixTransaction):
       return JSONResponse(content=jsonable_encoder({
        "id": t.id,
        "tipo": t.tipo,
        "valor": float(t.valor),
        "descricao": str(t.descricao) if t.descricao else "",
        "timestamp": (
            t.timestamp.isoformat() if getattr(t, "timestamp", None) else None
        ),
    }, custom_encoder={Decimal: float}))

def calcular_saldo(db: Session, user_id: int):
    entradas = (
        db.query(PixTransaction)
        .filter(PixTransaction.user_id == user_id, PixTransaction.tipo == "entrada")
        .all()
    )
    saidas = (
        db.query(PixTransaction)
        .filter(PixTransaction.user_id == user_id, PixTransaction.tipo == "saida")
        .all()
    )
    total_in = sum(t.valor for t in entradas)
    total_out = sum(t.valor for t in saidas)
    return round(total_in - total_out, 2)

@router.get("/balance")
def get_balance(db: Session = Depends(get_db)):
    user_id = 1  # TODO auth real depois
    saldo_pix = calcular_saldo(db, user_id)
    return JSONResponse(content=jsonable_encoder({"saldo_pix": saldo_pix}, custom_encoder={Decimal: float}))
@router.get("/history")
def get_history(db: Session = Depends(get_db)):
    user_id = 1  # TODO auth real depois
    rows = (
        db.query(PixTransaction)
        .filter(PixTransaction.user_id == user_id)
        .order_by(PixTransaction.id.desc())
        .all()
    )

    history = [tx_to_dict(t) for t in rows]
    recebidos = [tx_to_dict(t) for t in rows if t.tipo == "entrada"]
    enviados = [tx_to_dict(t) for t in rows if t.tipo == "saida"]

    return JSONResponse(content=jsonable_encoder({
        "history": history,
        "recebidos": recebidos,
        "enviados": enviados,
    }, custom_encoder={Decimal: float}))
@router.post("/send")
def send_pix(payload: dict, db: Session = Depends(get_db)):
    user_id = 1  # TODO auth real depois

    chave = payload.get("chave")
    valor = payload.get("valor")
    descricao = payload.get("descricao")

    if not chave or not descricao:
        raise HTTPException(status_code=400, detail="Chave e descrição são obrigatórias.")

    try:
        valor_num = float(valor)
    except Exception:
        raise HTTPException(status_code=400, detail="Valor inválido.")

    if valor_num <= 0:
        raise HTTPException(status_code=400, detail="Valor deve ser > 0.")

    nova = PixTransaction(
        user_id=user_id,
        tipo="saida",
        valor=valor_num,
        descricao=descricao if descricao else f"PIX para {chave}",
    )
    db.add(nova)
    db.commit()
    db.refresh(nova)

    saldo_pix = calcular_saldo(db, user_id)

    return JSONResponse(content=jsonable_encoder({
        "ok": True,
        "pix_id": nova.id,
        "saldo_pix": saldo_pix,
        "registro": tx_to_dict(nova),
    }, custom_encoder={Decimal: float}))

    except Exception as e:
        print("[AUREA PIX] fallback:", e)
        # saldo
        if isinstance(locals().get("saldo_pix", None), (int,float)) or "balance" in (locals().get("__name__", "")):
            return JSONResponse(content=jsonable_encoder({"saldo_pix": 0.0}, custom_encoder={Decimal: float}))
        # history
        return JSONResponse(content=jsonable_encoder({"history": []}, custom_encoder={Decimal: float}))
