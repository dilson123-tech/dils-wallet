from typing import Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

def create_pix_tx(db: Session, user_id: int, valor: float, descricao: Optional[str] = None, tipo: str = "envio") -> int:
    v = float(valor or 0)
    if v <= 0:
        raise ValueError("valor_invalido")
    t = tipo or "envio"
    stmt = text("""
        INSERT INTO pix_transactions (user_id, tipo, valor, descricao)
        VALUES (:user_id, :tipo, :valor, :descricao)
        RETURNING id
    """)
    rid = db.execute(stmt, {"user_id": user_id, "tipo": t, "valor": v, "descricao": descricao}).scalar()
    db.commit()
    return int(rid)

from typing import List, Dict, Any
from datetime import datetime, timedelta

def _window_clause(dialect: str) -> str:
    """Retorna cláusula de janela de tempo por dialect (postgres/sqlite)."""
    if dialect.startswith("postgres"):
        return "created_at >= NOW() - INTERVAL ':hours hour'"
    # sqlite / outros
    return "created_at >= DATETIME('now', printf('-%d hours', :hours))"

def _has_created_at(db: Session) -> bool:
    """Tenta checar se a coluna created_at existe; se falhar, assume False."""
    try:
        dname = (db.bind.dialect.name or "").lower()
        if dname.startswith("postgres"):
            q = text("""
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'pix_transactions' AND column_name = 'created_at'
                LIMIT 1
            """)
        else:
            # sqlite
            q = text("PRAGMA table_info(pix_transactions)")
        rows = list(db.execute(q))
        if dname.startswith("postgres"):
            return bool(rows)
        else:
            # sqlite: coluna 'name' fica no índice 1
            return any((r[1] == 'created_at') for r in rows)
    except Exception:
        return False

def get_pix_context(db: Session, hours: int = 24, user_id: int | None = None) -> Dict[str, Any]:
    """
    Produz um resumo rápido das transações PIX:
      - total_envios (saídas)
      - total_recebidos (entradas)
      - últimas transações (até 20)
      - considera janela de 'hours' se houver coluna created_at
    """
    dname = (db.bind.dialect.name or "").lower()
    has_ct = _has_created_at(db)

    where_parts = []
    params = {}
    if user_id is not None:
        where_parts.append("(user_id = :uid)")
        params["uid"] = user_id
    if has_ct:
        if dname.startswith("postgres"):
            where_parts.append("created_at >= NOW() - INTERVAL :hours || ' hour'")
        else:
            where_parts.append("created_at >= DATETIME('now', printf('-%d hours', :hours))")
        params["hours"] = int(hours)

    where = "WHERE " + " AND ".join(where_parts) if where_parts else ""

    # Totais
    stmt_tot = text(f"""
        SELECT
          COALESCE(SUM(CASE WHEN tipo IN ('envio','saida') THEN valor ELSE 0 END), 0) AS total_envios,
          COALESCE(SUM(CASE WHEN tipo IN ('recebido','entrada') THEN valor ELSE 0 END), 0) AS total_recebidos,
          COUNT(*) AS qnt
        FROM pix_transactions
        {where}
    """)
    row = db.execute(stmt_tot, params).first()
    total_envios = float(row[0]) if row and row[0] is not None else 0.0
    total_recebidos = float(row[1]) if row and row[1] is not None else 0.0
    qnt = int(row[2]) if row and row[2] is not None else 0

    # Ultimas transações (máx 20)
    order_col = "created_at DESC, id DESC" if has_ct else "id DESC"
    stmt_tx = text(f"""
        SELECT id, user_id, tipo, valor,
               COALESCE(descricao, '') AS descricao
               {', created_at' if has_ct else ''}
        FROM pix_transactions
        {where}
        ORDER BY {order_col}
        LIMIT 20
    """)
    txs: List[Dict[str, Any]] = []
    for r in db.execute(stmt_tx, params):
        d = {
            "id": int(r[0]),
            "user_id": int(r[1]) if r[1] is not None else None,
            "tipo": r[2],
            "valor": float(r[3]) if r[3] is not None else 0.0,
            "descricao": r[4] or "",
        }
        if has_ct:
            d["created_at"] = str(r[5])
        txs.append(d)

    return {
        "periodo_horas": int(hours) if has_ct else None,
        "janela_aplicada": bool(has_ct),
        "totais": {
            "envios": total_envios,
            "recebidos": total_recebidos,
            "saldo_delta": total_recebidos - total_envios,
            "qtd_transacoes": qnt,
        },
        "transacoes": txs,
        "dialeto": dname,
    }
