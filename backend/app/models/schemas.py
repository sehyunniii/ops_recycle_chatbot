# backend/app/models/schemas.py
from pydantic import BaseModel

# /api/chat 요청 형식
class ChatRequest(BaseModel):
    message: str
    image_context: str | None = None

# /api/chat 응답 형식
class ChatResponse(BaseModel):
    reply: str

# /api/predict 응답 형식
class PredictResponse(BaseModel):
    main_class: str
    sub_class: str
    # ---------------------------------------------
    # ⭐️ (수정) 이 줄을 삭제하여 500 오류를 해결합니다.
    # confidence: float 
    # ---------------------------------------------
    rag_info: str