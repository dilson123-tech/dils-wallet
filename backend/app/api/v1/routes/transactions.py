from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app import models, schemas, database
from app.security import get_current_user

router = APIRouter(tags=["transactions"])
ALLOWED_TYPES = {"deposito", "saque", "transferencia"}

@router.post("", response_model=schemas.TransactionResponse)
def create_transaction(
    payload: schemas.TransactionCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    t = (payload.tipo or "").strip().lower()
    if t not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"tipo inválido. Use: {sorted(ALLOWED_TYPES)}")
    if payload.valor is None or payload.valor <= 0:
        raise HTTPException(status_code=400, detail="valor deve ser > 0")

    tx = models.Transaction(
        user_id=current_user.id,
        tipo=t,
        valor=payload.valor,
        referencia=payload.referencia or "",
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx

@router.get("", response_model=List[schemas.TransactionResponse])
def list_transactions(
    skip: int = 0, limit: int = 50,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    return (db.query(models.Transaction)
              .filter(models.Transaction.user_id == current_user.id)
              .order_by(models.Transaction.id.desc())
.offset(skip).limit(limit).all())

@router.get("/balance", response_model=schemas.BalanceOut)
def get_balance(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    from sqlalchemy import func, case
    q = db.query(
        func.coalesce(func.sum(
            case(
                (models.Transaction.tipo == "deposito", models.Transaction.valor),
                (models.Transaction.tipo == "saque", -models.Transaction.valor),
                (models.Transaction.tipo == "transferencia", -models.Transaction.valor),
                else_=0.0
            )
        ), 0.0)
    ).filter(models.Transaction.user_id == current_user.id)
    saldo = q.scalar() or 0.0
    return schemas.BalanceOut(saldo=saldo)

# --- Transferência entre usuários (gera 2 lançamentos) ---
from pydantic import BaseModel, EmailStr
from typing import Optional
from sqlalchemy import func, case
from app.security import get_current_user

class TransferIn(BaseModel):
    destino_email: EmailStr
    valor: float
    referencia: Optional[str] = None

@router.post("/transfer")
def create_transfer(
    payload: TransferIn,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    # validações básicas
    if payload.valor is None or payload.valor <= 0:
        raise HTTPException(status_code=400, detail="valor deve ser > 0")
    if payload.destino_email.lower() == getattr(current_user, "email", "").lower():
        raise HTTPException(status_code=400, detail="destino não pode ser o próprio usuário")

    # verifica destinatário
    dest = db.query(models.User).filter(models.User.email == payload.destino_email).first()
    if not dest:
        raise HTTPException(status_code=404, detail="destinatário não encontrado")

    # saldo do remetente
    saldo_q = db.query(
        func.coalesce(func.sum(
            case(
                (models.Transaction.tipo == "deposito", models.Transaction.valor),
                (models.Transaction.tipo == "saque", -models.Transaction.valor),
                (models.Transaction.tipo == "transferencia", -models.Transaction.valor),
                else_=0.0
            )
        ), 0.0)
    ).filter(models.Transaction.user_id == current_user.id)
    saldo_atual = float(saldo_q.scalar() or 0.0)
    if saldo_atual < payload.valor:
        raise HTTPException(status_code=400, detail="saldo insuficiente")

    # cria lançamentos: saída do remetente (transferencia) e entrada do destinatário (deposito)
    try:
        tx_out = models.Transaction(
            user_id=current_user.id,
            tipo="transferencia",
            valor=payload.valor,
            referencia=payload.referencia or f"para {payload.destino_email}",
        )
        tx_in = models.Transaction(
            user_id=dest.id,
            tipo="deposito",
            valor=payload.valor,
            referencia=payload.referencia or f"de {current_user.email}",
        )
        db.add(tx_out)
        db.add(tx_in)
        db.commit()
        db.refresh(tx_out)
        db.refresh(tx_in)
    except Exception:
        db.rollback()
        raise

    novo_saldo = saldo_atual - float(payload.valor)
    return {
        "ok": True,
        "valor": float(payload.valor),
        "de": current_user.email,
        "para": payload.destino_email,
        "saida_id": tx_out.id,
        "entrada_id": tx_in.id,
        "saldo_apos": novo_saldo,
    }
# --- fim transferência ---

@router.get("/paged", response_model=schemas.TransactionsPage)
def list_transactions_paged(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Lista paginada das transações do usuário atual.
    Retorna {"items":[TransactionResponse...], "meta":{page,page_size,total,total_pages,has_next,has_prev}}.
    """
    base_q = db.query(models.Transaction).filter(models.Transaction.user_id == current_user.id)

    total = base_q.count()
    items = (
        base_q.order_by(models.Transaction.id.desc())
             .offset((page - 1) * page_size)
             .limit(page_size)
             .all()
    )
    total_pages = (total + page_size - 1) // page_size

    return schemas.TransactionsPage(
        items=[schemas.TransactionResponse(id=t.id, tipo=t.tipo, valor=t.valor, referencia=t.referencia, criado_em=t.criado_em, user_id=t.user_id) for t in items],
        meta=schemas.PageMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            has_next=(page * page_size) < total,
            has_prev=page > 1,
        ),
    )
