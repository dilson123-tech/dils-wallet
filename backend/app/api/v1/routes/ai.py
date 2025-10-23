from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from backend.app.services.ai_service import generate_ai_response

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])

class PromptRequest(BaseModel):
    prompt: str
    user_id: str | None = None

class PromptResponse(BaseModel):
    response: str

@router.post("/process", response_model=PromptResponse)
async def process_ai(req: PromptRequest):
    if not req.prompt or not req.prompt.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="prompt vazio")
    text = await generate_ai_response(req.prompt, req.user_id)
    return PromptResponse(response=text)
