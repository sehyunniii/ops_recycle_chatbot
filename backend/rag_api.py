# rag_api.py
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS  # Chroma 대신 FAISS 사용 (로그 기준)
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import os

# 1. 환경 변수 확인
if "OPENAI_API_KEY" not in os.environ:
    print("경고: OPENAI_API_KEY 환경 변수가 없습니다.")
    # (실행은 계속하되, API 호출 시 실패할 수 있음)

# 2. ⭐️ FastAPI 앱 초기화 (가장 중요) ⭐️
#    APIRouter가 아니라 app 객체를 직접 생성합니다.
app = FastAPI()

# 3. Pydantic 모델 정의
class RagQuery(BaseModel):
    user_input: str
    image_class: str

class RagResponse(BaseModel):
    response_text: str

# 4. LangChain 컴포넌트 전역 변수로 초기화
llm = None
retriever = None
qa_chain = None

# 5. ⭐️ FastAPI 'startup' 이벤트 ⭐️
#    서버가 켜질 때 단 1번만 모델을 로드합니다.
@app.on_event("startup")
def load_models():
    global llm, retriever, qa_chain
    print("RAG API 서버를 초기화합니다...")
    
    try:
        # LLM 모델
        llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
        
        # 임베딩 모델
        embeddings = OpenAIEmbeddings()

        # ⭐️ FAISS 벡터 스토어 로드 (로그 기준) ⭐️
        # indexing.py 에서 생성된 "my_faiss_index" 폴더를 사용합니다.
        vector_store = FAISS.load_local(
            folder_path="my_faiss_index", 
            embeddings=embeddings, 
            allow_dangerous_deserialization=True # FAISS 로드 시 필요
        )
        
        # 리트리버 생성
        retriever = vector_store.as_retriever(search_kwargs={"k": 3})

        # 프롬프트 템플릿
        prompt_template = """
        당신은 분리수거 전문가 챗봇입니다. 제공된 정보를 바탕으로 사용자의 질문에 친절하고 명확하게 답변해주세요.
        정보에 없는 내용은 답변할 수 없다고 솔직하게 말하세요.

        [제공된 정보]
        {context}

        [사용자 질문]
        {question}

        [답변]
        """
        PROMPT = PromptTemplate(
            template=prompt_template, input_variables=["context", "question"]
        )

        # RAG 체인 (LCEL 방식)
        qa_chain = (
            {"context": retriever, "question": RunnablePassthrough()}
            | PROMPT
            | llm
            | StrOutputParser()
        )
        
        print("  > LLM, 임베딩, 벡터스토어 로드 완료.")
        print("  > RAG 체인 생성 완료 (LCEL 방식).")

    except Exception as e:
        print(f"[치명적 오류] 모델 또는 벡터 스토어 로드에 실패했습니다: {e}")
        # (예: my_faiss_index 폴더가 없는 경우)
        qa_chain = None


# 6. ⭐️ API 엔드포인트 정의 (가장 중요) ⭐️
#    app 객체에 직접 POST 경로를 등록합니다.
@app.post("/api/rag_query", response_model=RagResponse)
async def process_rag_query(query: RagQuery):
    global qa_chain
    if not qa_chain:
        # startup에서 로딩 실패 시
        return RagResponse(response_text="RAG 서버가 초기화에 실패했습니다. (모델/DB 로드 오류)")

    # 입력(이미지 클래스, 텍스트)을 하나의 질문으로 조합
    final_question = ""
    if query.image_class and query.user_input:
        final_question = f"'{query.image_class}' 사진에 대한 추가 질문입니다: '{query.user_input}'"
    elif query.image_class:
        final_question = f"'{query.image_class}'는 어떻게 분리배출해야 하나요?"
    elif query.user_input:
        final_question = query.user_input
    else:
        return RagResponse(response_text="질문 내용이 없습니다.")

    try:
        # RAG 체인을 통해 답변 생성
        result = qa_chain.invoke(final_question)
        return RagResponse(response_text=result)

    except Exception as e:
        print(f"RAG 처리 중 오류: {e}")
        # (예: OpenAI API 키가 잘못된 경우 401 오류 발생)
        return RagResponse(response_text=f"답변 생성 중 오류가 발생했습니다: {e}")

# 서버 실행 (uvicorn으로 실행되므로 이 부분은 직접 실행 시에만 사용됨)
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)