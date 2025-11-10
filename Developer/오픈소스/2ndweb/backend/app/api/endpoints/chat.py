# backend/app/api/endpoints/chat.py
from fastapi import APIRouter, File, UploadFile, HTTPException, Request
from fastapi.responses import StreamingResponse 
from ...models.schemas import ChatRequest, ChatResponse, PredictResponse

router = APIRouter()

# /api/predict 엔드포인트 (변경 없음)
@router.post("/predict", response_model=PredictResponse)
async def predict(request: Request, file: UploadFile = File(...)):
    classifier = request.app.state.classifier
    if not classifier:
        raise HTTPException(status_code=500, detail="분류 모델이 로드되지 않았습니다.")
    
    rag = request.app.state.rag
    if not rag:
        raise HTTPException(status_code=500, detail="RAG 서비스가 로드되지 않았습니다.")

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다.")
    
    try:
        image_bytes = await file.read()
        main_class, confidence = classifier.predict_image_bytes(image_bytes)
        # ⭐️ (수정) 레이블명만 보내도록 (예: 01_ClearPET -> ClearPET)
        main_class_label = main_class.split('_', 1)[-1] if '_' in main_class else main_class
        sub_class = main_class_label # sub_class도 동일하게

        # ⭐️ (수정) RAG에는 원본 ID(01_ClearPET)를 보냄
        rag_info = rag.get_response(
            user_input="", 
            image_class=main_class # 원본 ID
        )
        
        return PredictResponse(
            main_class=main_class_label, # 깔끔한 이름
            sub_class=sub_class,
            # (신뢰도 제거)
            rag_info=rag_info
        )
    except Exception as e:
        print(f"예측 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=f"서버 오류 발생: {e}")


# ⭐️ /api/chat 엔드포인트 (수정) ⭐️
@router.post("/chat") 
async def chat(request: Request, chat_request: ChatRequest):
    rag = request.app.state.rag
    if not rag:
        raise HTTPException(status_code=500, detail="RAG 서비스가 로드되지 않았습니다.")

    try:
        # ⭐️ (수정) 'image_context=' -> 'image_class='
        response_generator = rag.stream_response(
            user_input=chat_request.message,
            image_class=chat_request.image_context if chat_request.image_context else ""
        )
        return StreamingResponse(response_generator, media_type="text/plain")
    
    except Exception as e:
        print(f"채팅 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=f"서버 오류 발생: {e}")