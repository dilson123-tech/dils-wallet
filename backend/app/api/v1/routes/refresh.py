from datetime import timedelta
from fastapi import APIRouter, HTTPException
from .api.v1.schemas.auth import RefreshRequest
from .utils.jwt import verify_refresh_token
from ....security import create_access_token
from .... import config

router = APIRouter()

@router.post("/refresh")
def refresh(body: RefreshRequest):
    data = verify_refresh_token(body.refresh_token)
    if not data or data.get("sub") is None:
        raise HTTPException(status_code=401, detail="invalid refresh token")
    access = create_access_token(
        data={"sub": data["sub"]},
        expires_delta=timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access, "token_type": "bearer"}
