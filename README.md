# ♻️ 분리수거 RAG 챗봇

이미지 분류와 RAG 챗봇이 결합된 분리수거 안내 웹 앱입니다.

## 🛠️ 기술 스택

* **Frontend:** React (Vite), Vite Proxy
* **Backend:** FastAPI, PyTorch, LangChain, FAISS, OpenAI

## 🚀 실행 방법

### 1. (최초 1회) Backend 설정

1.  프로젝트 루트(`/web 복사본`)에서 가상환경을 생성하고 활성화합니다.
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
2.  `backend` 폴더로 이동하여 모든 Python 라이브러리를 설치합니다.
    ```bash
    cd backend
    pip install -r requirements.txt
    ```
3.  **`.env` 파일 생성 (중요)**
    `backend` 폴더에 `.env` 파일을 생성하고, **OpenAI API 키**와 **CORS 허용 주소**를 입력합니다.
    ```.env
    # backend/.env
    OPENAI_API_KEY="sk-..."
    CORS_ORIGINS="http://localhost:5173,[http://127.0.0.1:5173](http://127.0.0.1:5173),http://[내-IP-주소]:5173"
    ```
4.  **RAG 데이터베이스**를 생성합니다 (최초 1회).
    ```bash
    # (backend 폴더에서 실행)
    python indexing.py
    ```
    > `vector_db` 또는 `my_faiss_index` 폴더가 생성되는지 확인하세요.

### 2. (최초 1회) Frontend 설정

1.  **새 터미널**을 열고 `frontend` 폴더로 이동합니다.
    ```bash
    cd /path/to/your/web 복사본/frontend
    ```
2.  **Node.js 라이브러리**를 설치합니다.
    ```bash
    npm install
    ```

---

## 💨 애플리케이션 실행

**총 2개의 터미널**만 필요합니다.

* **🐍 터미널 1: Backend (통합 서버)**
    ```bash
    # (backend 폴더에서 venv 활성화)
    cd /path/to/your/web 복사본/backend
    source ../venv/bin/activate
    
    # (OMP 오류 방지)
    export KMP_DUPLICATE_LIB_OK=TRUE
    
    # 서버 실행 (API 키는 .env에서 자동 로드됨)
    uvicorn app.main:app --reload --port 8000 --host 0.0.0.0
    ```

* **🖥️ 터미널 2: Frontend (React)**
    ```bash
    # (frontend 폴더에서)
    cd /path/to/your/web 복사본/frontend
    
    # 서버 실행 (Vite 프록시가 /api 요청을 8000번으로 넘김)
    npm run dev -- --host
    ```

### 🔗 접속

* **PC (Mac):** `http://localhost:5173`
* **모바일 (같은 WiFi):** `http://[현재의-IP-주소]:5173`