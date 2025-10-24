import os
from fastapi import APIRouter
from backend.app.services.ai_client import chat as ai_chat

router = APIRouter(prefix="/api/v1/ai", tags=["AI"])

@router.get("/ping")
def ai_ping():
    return {
        "ok": True,
        "message": "AI 2.0 up",
        "model": os.getenv("OPENAI_MODEL"),
        "base": os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"),
        "key_hint": "proj" if (os.getenv("OPENAI_API_KEY","").startswith("sk-proj-")) else "std",
    }

@router.post("/process")
def ai_process(payload: dict):
    prompt = (payload or {}).get("prompt", "").strip()
    if not prompt:
        return {"ok": False, "error": "missing_prompt"}
    try:
        out = ai_chat(prompt)
        return {"ok": True, "result": out}
    except Exception as e:
        return {"ok": False, "error": str(e)}
