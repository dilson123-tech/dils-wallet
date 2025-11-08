from fastapi import APIRouter
from app.utils.ledger_seed import seed_ledger_from_users

router = APIRouter()

@router.post("/admin/seed-ledger")
def run_seed():
    try:
        seed_ledger_from_users()
        return {"ok": True, "msg": "Ledger seed executado com sucesso"}
    except Exception as e:
        return {"ok": False, "erro": str(e)}
