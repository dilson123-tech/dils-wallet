from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database import get_db
from app.models.pix_transaction import PixTransaction

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])

def safe_dt(value):
    """Converte timestamp em datetime UTC ou retorna None."""
    if not value:
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            return None
    return None

@router.get("/summary")
def resumo_pix(db: Session = Depends(get_db)):
    try:
    txs = db.query(PixTransaction).order_by(PixTransaction.id.desc()).all()
    if not txs:
        return {"mensagem": "Sem transações registradas."}
    except Exception as e:

        print(f"[AUREA AI SUMMARY FALLBACK] {e}")

        return {

            "saldo_atual": 0.0,

            "entradas_total": 0.0,

            "saidas_total": 0.0,

            "ultimas_24h": {"entradas": 0, "saidas": 0, "qtd": 0},

            "status": "degraded"

        }

    saldo = sum(float(t.valor) if t.tipo == "entrada" else -float(t.valor) for t in txs)
    entradas_total = sum(float(t.valor) for t in txs if t.tipo == "entrada")
    saidas_total = sum(float(t.valor) for t in txs if t.tipo == "saida")

    now = datetime.utcnow()
    ult24h, ult7d = [], []

    for t in txs:
        dt = safe_dt(getattr(t, "timestamp", None))
        if dt:
            if now - dt <= timedelta(hours=24):
                ult24h.append(t)
            if now - dt <= timedelta(days=7):
                ult7d.append(t)

    def soma(lista, tipo): return sum(float(t.valor) for t in lista if t.tipo == tipo)
    ult_entradas = soma(ult24h, "entrada")
    ult_saidas   = soma(ult24h, "saida")
    ult7_entradas = soma(ult7d, "entrada")
    ult7_saidas   = soma(ult7d, "saida")

    return {
        "saldo_atual": round(saldo, 2),
        "entradas_total": round(entradas_total, 2),
        "saidas_total": round(saidas_total, 2),
        "ultimas_24h": {"entradas": round(ult_entradas, 2), "saidas": round(ult_saidas, 2), "qtd": len(ult24h)},
        "ultimos_7d": {"entradas": round(ult7_entradas, 2), "saidas": round(ult7_saidas, 2), "qtd": len(ult7d)},
        "qtd_transacoes": len(txs),
        "mensagem": (
            f"Saldo atual R$ {saldo:,.2f}. Entradas totais R$ {entradas_total:,.2f}, saídas totais R$ {saidas_total:,.2f}. "
            f"Últimas 24h: +R$ {ult_entradas:,.2f} / -R$ {ult_saidas:,.2f} ({len(ult24h)} transações). "
            f"Últimos 7d: +R$ {ult7_entradas:,.2f} / -R$ {ult7_saidas:,.2f} ({len(ult7d)} transações)."
        )
    }
