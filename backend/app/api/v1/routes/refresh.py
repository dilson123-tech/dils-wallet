from datetime import timedelta
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.api.v1.schemas.auth import RefreshRequest
from app.utils.jwt import create_access_token, verify_refresh_token

router = APIRouter(tags=["auth"])

@router.post("/refresh")
def refresh_token(body: RefreshRequest):
    payload = verify_refresh_token(body.refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="invalid refresh token")
    access = create_access_token({"sub": payload["sub"]}, expires_delta=timedelta(minutes=60))
    return JSONResponse({"access_token": access, "token_type": "bearer"})
