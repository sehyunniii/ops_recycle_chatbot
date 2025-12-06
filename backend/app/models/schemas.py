# backend/app/models/schemas.py
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    image_context: str | None = None

class ChatResponse(BaseModel):
    response: str

class PredictResponse(BaseModel):
    main_class: str
    sub_class: str
    confidence: float  # ⭐️ [추가] 확률 값을 위한 필드 (float 타입)
    rag_info: str