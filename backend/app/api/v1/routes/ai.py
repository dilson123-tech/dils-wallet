from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.ai_service import get_ai_text

router = APIRouter(tags=["AI 2.0"])

class PromptIn(BaseModel):
    prompt: str

@router.get("/ping")
def ping():
    try:
        return {"ok": True, "message": "AI 2.0 up"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI ping error: {e}")

@router.post("/process")
def process(body: PromptIn):
    try:
        return {"response": get_ai_text(body.prompt)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI error: {e}")
