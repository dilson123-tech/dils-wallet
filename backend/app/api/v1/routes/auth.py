from fastapi import APIRouter, Request

router = APIRouter()

@router.get("/_version")
def _version():
    return {"marker": "AUTH_OK", "file": __file__}

@router.post("/register", status_code=200)
async def register(req: Request):
    try:
        body = await req.json()
    except Exception as e:
        body = {"_parse_error": str(e)}
    return {"marker": "CANARY_OK", "echo": body}
