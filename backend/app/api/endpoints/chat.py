# backend/app/api/endpoints/chat.py
from fastapi import APIRouter, File, UploadFile, HTTPException, Request
from fastapi.responses import StreamingResponse 
from ...models.schemas import ChatRequest, PredictResponse # ChatResponse는 안 쓰면 제거 가능

router = APIRouter()

# -------------------------------------------------------------------
# 1. 이미지 예측 엔드포인트 (/api/predict)
# -------------------------------------------------------------------
@router.post("/predict", response_model=PredictResponse)
async def predict(request: Request, file: UploadFile = File(...)):
    # 1. 모델 및 서비스 로드 확인
    classifier = request.app.state.classifier
    rag = request.app.state.rag
    
    if not classifier:
        raise HTTPException(status_code=500, detail="분류 모델이 로드되지 않았습니다.")
    if not rag:
        raise HTTPException(status_code=500, detail="RAG 서비스가 로드되지 않았습니다.")

    # 2. 파일 타입 검증
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다.")
    
    try:
        # 3. 이미지 읽기 및 예측 실행
        image_bytes = await file.read()
        
        # classifier에서 (클래스명, 확률)을 반환받음
        raw_label, confidence_score = classifier.predict_image_bytes(image_bytes)

        # 4. 레이블 정제 (01_ClearPET -> ClearPET)
        # ⭐️ RAG와 프론트엔드 모두에게 '깨끗한 이름'을 주는 것이 정확도에 훨씬 좋습니다.
        clean_label = raw_label
        if raw_label and "_" in raw_label:
            clean_label = raw_label.split("_", 1)[-1] 
        
        # 5. RAG 서비스 호출 (초기 가이드 멘트 생성)
        # ⭐️ 중요: 정제된 clean_label을 넘겨야 챗봇이 자연스럽게 인식합니다.
        rag_info = rag.get_response(
            user_input="", 
            image_class=clean_label 
        )
        
        # 6. 확률(%) 계산 (선택 사항: 0.0~1.0 사이 값 그대로 보내거나 백분율로 변환)
        # 여기서는 0.95 그대로 보내고 프론트에서 %로 바꾸거나, 여기서 *100을 해도 됩니다.
        # 일단 float 그대로 보냅니다.
        
        print(f"📸 예측 성공: {clean_label} ({confidence_score*100:.2f}%)")

        return PredictResponse(
            main_class=clean_label,  # 예: Appliance
            sub_class=clean_label,   # (필요 시 세분화 가능)
            confidence=confidence_score, # ⭐️ [수정] 확률 값 정상 반환
            rag_info=rag_info
        )

    except Exception as e:
        print(f"❌ 예측 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=f"서버 예측 처리 중 오류: {str(e)}")


# -------------------------------------------------------------------
# 2. 채팅 엔드포인트 (/api/chat)
# -------------------------------------------------------------------
@router.post("/chat") 
async def chat(request: Request, chat_request: ChatRequest):
    rag = request.app.state.rag
    if not rag:
        raise HTTPException(status_code=500, detail="RAG 서비스가 로드되지 않았습니다.")

    try:
        # 프론트엔드에서 받은 image_context가 있다면 사용, 없으면 빈 문자열
        context_label = chat_request.image_context if chat_request.image_context else ""

        # ⭐️ 로그를 찍어서 현재 어떤 이미지를 기준으로 대화하는지 확인하세요
        print(f"💬 채팅 요청: '{chat_request.message}' (문맥: {context_label})")

        response_generator = rag.stream_response(
            user_input=chat_request.message,
            image_class=context_label
        )
        
        return StreamingResponse(response_generator, media_type="text/plain")
    
    except Exception as e:
        print(f"❌ 채팅 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=f"서버 채팅 처리 중 오류: {str(e)}")