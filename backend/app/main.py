# backend/app/main.py
import os
import torch
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
# ⭐️ 1. dotenv 라이브러리 추가
from dotenv import load_dotenv 

from .api.endpoints import chat
from .api.endpoints import yolo_api
from .services.classification_service import ModelWrapper
from .services.rag_service import RAGService

# ⭐️ 2. 앱 시작 전 .env 파일 로드 (가장 먼저 실행)
# 이 코드가 있어야 RAGService가 OPENAI_API_KEY를 인식합니다.
load_dotenv()

app = FastAPI()

@app.on_event("startup")
def startup_event():
    # 1. 분류 모델 로드
    model_path = os.path.join(os.path.dirname(__file__), "models", "weights", "recycle_best.pt")
    device = "cuda" if torch.cuda.is_available() else "cpu"

    try:
        app.state.classifier = ModelWrapper(model_path=model_path, device=device)
        print("✅ Classification Model loaded.")
    except Exception as e:
        print(f"❌ 분류 모델 로드 실패: {e}")
        app.state.classifier = None

    # 2. RAG 서비스 로드
    try:
        # DB 경로: backend/app/main.py -> backend/app -> backend -> my_faiss_index
        base_dir = os.path.dirname(os.path.dirname(__file__)) 
        db_path = os.path.join(base_dir, "my_faiss_index")
        
        # 여기서 내부적으로 OPENAI_API_KEY를 사용하므로, 위에서 load_dotenv()가 필수입니다.
        app.state.rag = RAGService(db_path=db_path)
        print("✅ RAG Service loaded.")
    except Exception as e:
        print(f"❌ RAG 서비스 로드 실패: {e}")
        # 키 에러인지 확인하기 위해 구체적인 메시지 출력
        if "OPENAI_API_KEY" in str(e):
            print("💡 힌트: .env 파일에 OPENAI_API_KEY가 올바르게 들어있는지 확인하세요.")
        app.state.rag = None

# CORS 설정
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://172.25.1.156", # (필요시 수정)
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 포함
app.include_router(chat.router, prefix="/api", tags=["API"])
app.include_router(yolo_api.router, prefix="/api", tags=["YOLO"])

@app.get("/")
def read_root():
    return {"Hello": "Unified Recycling RAG API"}