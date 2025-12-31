from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field

class ErrorResponse(BaseModel):
    error: str = Field(..., examples=["unauthorized", "internal_error"])
    message: str = Field(..., examples=["Missing or invalid token"])
    detail: Optional[Any] = None
    request_id: Optional[str] = None

# Reuso: força a aparecer 422 no OpenAPI mesmo quando a rota não tem query/body
OPENAPI_422 = {
    "description": "Validation Error",
    "content": {
        "application/json": {
            "schema": {"$ref": "#/components/schemas/HTTPValidationError"}
        }
    },
}
