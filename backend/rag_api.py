# rag_api.py
import uvicorn
import os
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv  # ⭐️ .env 파일 로드용

# LangChain 관련 임포트
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# ---------------------------------------------------------------
# 1. 환경 변수 및 설정
# ---------------------------------------------------------------
# .env 파일에서 환경 변수를 로드합니다.
load_dotenv()

if "OPENAI_API_KEY" not in os.environ:
    print("⚠️ [경고] OPENAI_API_KEY가 환경 변수에 설정되지 않았습니다.")

# ---------------------------------------------------------------
# 2. FastAPI 앱 초기화
# ---------------------------------------------------------------
app = FastAPI(
    title="Recycle RAG API",
    description="FAISS 벡터 DB 기반의 재활용 가이드 챗봇 API",
    version="1.0.0"
)

# ---------------------------------------------------------------
# 3. 데이터 모델 정의
# ---------------------------------------------------------------
class RagQuery(BaseModel):
    user_input: str | None = None  # 사용자가 입력한 텍스트 (옵션)
    image_class: str | None = None # YOLO가 탐지한 이미지 클래스명 (옵션)

class RagResponse(BaseModel):
    response_text: str

# ---------------------------------------------------------------
# 4. 전역 변수 (모델, 체인)
# ---------------------------------------------------------------
qa_chain = None

# ---------------------------------------------------------------
# 5. 서버 시작 시 모델 로드 (Startup Event)
# ---------------------------------------------------------------
@app.on_event("startup")
def load_models():
    global qa_chain
    print("🚀 [Startup] RAG API 서버를 초기화합니다...")
    
    try:
        # 1) LLM 모델 설정 (gpt-3.5-turbo 또는 gpt-4o-mini 추천)
        # temperature=0 : 창의성을 죽이고 사실(Fact) 위주로 답변하게 함
        llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
        
        # 2) 임베딩 모델
        embeddings = OpenAIEmbeddings()

        # 3) FAISS 벡터 스토어 로드
        vector_db_path = "my_faiss_index" # indexing.py에서 저장한 폴더명
        if not os.path.exists(vector_db_path):
            raise FileNotFoundError(f"'{vector_db_path}' 폴더가 없습니다. indexing.py를 먼저 실행하세요.")

        vector_store = FAISS.load_local(
            folder_path=vector_db_path, 
            embeddings=embeddings, 
            allow_dangerous_deserialization=True
        )
        
        # 4) 리트리버 (검색기) 설정
        # k=3: 가장 관련성 높은 문서 3개를 가져옴
        retriever = vector_store.as_retriever(search_kwargs={"k": 3})

        # 5) ⭐️ 프롬프트 템플릿 (가장 중요한 수정 부분) ⭐️
        # - AI에게 역할을 부여하고, 문맥 외 정보 사용 금지를 명시
        # - 가독성을 위한 포맷팅 지시
        prompt_template = """
        당신은 친절하고 꼼꼼한 '재활용 분리배출 도우미'입니다.
        아래 [제공된 정보(Context)]만을 바탕으로 사용자의 [질문(Question)]에 답변하세요.

        [지침]
        1. **엄격한 사실 기반**: [제공된 정보]에 없는 내용은 절대 지어내지 마세요. 모르는 내용은 "죄송하지만 제공된 자료에는 해당 정보가 나와있지 않아요."라고 솔직하게 말하세요.
        2. **친절한 톤**: 답변은 존댓말로, 부드럽고 격려하는 어조를 사용하세요.
        3. **가독성**: 
           - 답변이 길어지면 줄바꿈을 적절히 사용하세요.
           - 핵심 내용은 **굵게** 표시하세요.
           - 필요하다면 번호 매기기(1., 2.)나 불릿 포인트(-)를 사용해 정리하세요.
           - 적절한 곳에 이모지(🌱, ♻️, 🗑️ 등)를 사용해 답변을 생동감 있게 만드세요.

        [제공된 정보(Context)]
        {context}

        [질문(Question)]
        {question}

        [답변]
        """
        
        PROMPT = PromptTemplate(
            template=prompt_template, 
            input_variables=["context", "question"]
        )

        # 6) RAG 체인 연결 (LCEL)
        qa_chain = (
            {"context": retriever, "question": RunnablePassthrough()}
            | PROMPT
            | llm
            | StrOutputParser()
        )
        
        print("✅ LLM, 임베딩, 벡터스토어 로드 완료.")
        print("✅ RAG 체인 생성 완료.")

    except Exception as e:
        print(f"❌ [치명적 오류] 초기화 실패: {e}")
        qa_chain = None


# ---------------------------------------------------------------
# 6. API 엔드포인트
# ---------------------------------------------------------------
@app.post("/api/rag_query", response_model=RagResponse)
async def process_rag_query(query: RagQuery):
    global qa_chain
    
    # 1. 서버 초기화 실패 시 방어 코드
    if not qa_chain:
        return RagResponse(response_text="죄송합니다. 서버 내부 오류로 답변을 생성할 수 없습니다. (모델 로드 실패)")

    # 2. 질문 조합 로직 (YOLO 클래스 + 사용자 입력)
    input_text = query.user_input.strip() if query.user_input else ""
    detected_class = query.image_class.strip() if query.image_class else ""
    
    final_question = ""

    if detected_class and input_text:
        # 예: 사진은 'pet_bottle'이고 질문은 "뚜껑은 어떻게 해?"
        final_question = f"사진에서 감지된 물체는 '{detected_class}'입니다. 이 물체와 관련하여 사용자가 다음과 같이 질문했습니다: '{input_text}'. 이 물체의 올바른 분리배출 방법을 설명해주세요."
    elif detected_class:
        # 예: 사진만 있고 질문은 없음
        final_question = f"사진에서 '{detected_class}'(이)가 감지되었습니다. 이것의 올바른 분리배출 방법을 자세히 알려주세요."
    elif input_text:
        # 예: 사진 없이 텍스트 질문만 있음
        final_question = input_text
    else:
        return RagResponse(response_text="질문할 내용이나 이미지가 없습니다.")

    # 3. 체인 실행 및 답변 생성
    try:
        result = qa_chain.invoke(final_question)
        return RagResponse(response_text=result)

    except Exception as e:
        print(f"❌ RAG 처리 중 오류: {e}")
        return RagResponse(response_text="답변을 생성하는 도중 문제가 발생했습니다. 잠시 후 다시 시도해주세요.")

# 직접 실행 시 사용 (개발용)
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)