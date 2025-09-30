from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from sqlalchemy import text
from .database import get_db
from .security import get_current_user  # ajuste se o caminho diferir

router = APIRouter(prefix="/api/v1/transactions", tags=["transactions"])

@router.get("/export.csv")
def export_csv(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # SQL simples pra evitar dependência de modelos
    rows = db.execute(text("""
        SELECT id, tipo, valor, COALESCE(referencia,'' ) AS referencia, criado_em, user_id
        FROM transactions
        WHERE user_id = :uid
        ORDER BY criado_em
    """), {"uid": current_user.id}).mappings().all()

    # monta CSV
    header = "id,criado_em,tipo,valor,referencia,user_id\n"
    lines = [
        f'{r["id"]},{r["criado_em"]},{r["tipo"]},{r["valor"]},"{r["referencia"]}",{r["user_id"]}'
        for r in rows
    ]
    csv_data = header + "\n".join(lines)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="transactions_export.csv"'
        },
    )
