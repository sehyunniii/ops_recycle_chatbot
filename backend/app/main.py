# backend/app/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from .api.endpoints import chat
from .services.classification_service import ModelWrapper
from .services.rag_service import RAGService
import os
import torch

app = FastAPI()

@app.on_event("startup")
def startup_event():
    # 1. 분류 모델 로드
    model_path = os.path.join(os.path.dirname(__file__), "models", "weights", "best_model.pth")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    try:
        app.state.classifier = ModelWrapper(model_path=model_path, device=device)
        print("✅ Classification Model loaded.")
    except Exception as e:
        print(f"❌ 분류 모델 로드 실패: {e}")
        app.state.classifier = None

    # 2. RAG 서비스 로드
    try:
        # ⭐️ (수정) 'vector_db' -> 'my_faiss_index'
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "my_faiss_index")
        
        app.state.rag = RAGService(db_path=db_path)
        print("✅ RAG Service loaded.")
    except Exception as e:
        print(f"❌ RAG 서비스 로드 실패: {e}")
        app.state.rag = None

# CORS 설정
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://172.25.1.156", # (IP 주소는 실제 값으로 변경)
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

@app.get("/")
def read_root():
    return {"Hello": "Unified Recycling RAG API"}