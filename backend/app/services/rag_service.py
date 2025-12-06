# backend/app/services/rag_service.py
import os
import asyncio
from typing import AsyncGenerator
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# 클래스 초기화 시 환경 변수 로드
load_dotenv()

class RAGService:
    def __init__(self, db_path="my_faiss_index"): 
        if "OPENAI_API_KEY" not in os.environ:
            print("⚠️ [경고] OPENAI_API_KEY가 환경 변수에 없습니다.")
        
        print(f"🚀 RAG Service를 초기화합니다... (DB 경로: {db_path})")
        try:
            # 1. 모델 설정 (Fact Check를 위해 temperature=0)
            llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
            embeddings = OpenAIEmbeddings()
            
            # 2. 벡터 스토어 로드
            if not os.path.exists(db_path):
                # 경로가 틀렸을 경우를 대비해 상위 폴더도 한번 체크
                alt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "my_faiss_index")
                if os.path.exists(alt_path):
                    db_path = alt_path
                else:
                    raise FileNotFoundError(f"벡터 DB 폴더를 찾을 수 없습니다: {db_path}")

            vector_store = FAISS.load_local(
                folder_path=db_path, 
                embeddings=embeddings, 
                allow_dangerous_deserialization=True
            )
            retriever = vector_store.as_retriever(search_kwargs={"k": 3})

            # 3. ⭐️ 개선된 프롬프트 (가독성 + 팩트체크 강화)
            prompt_template = """
            당신은 친절하고 꼼꼼한 '재활용 분리배출 도우미'입니다.
            아래 [제공된 정보(Context)]만을 바탕으로 사용자의 [질문(Question)]에 답변하세요.

            [지침]
            1. **엄격한 사실 기반**: [제공된 정보]에 없는 내용은 절대 지어내지 마세요. 모르는 내용은 "죄송하지만 제공된 자료에는 해당 정보가 나와있지 않아요."라고 솔직하게 말하세요.
            2. **친절한 톤**: 답변은 존댓말로, 부드럽고 격려하는 어조를 사용하세요.
            3. **가독성**: 
               - 답변이 길어지면 줄바꿈을 적절히 사용하세요.
               - 핵심 내용은 **굵게** 표시하세요.
               - 번호 매기기(1., 2.)나 글머리 기호(-)를 사용해 정리하세요.
               - 적절한 곳에 이모지(🌱, ♻️, 🗑️ 등)를 사용해 답변을 생동감 있게 만드세요.

            [제공된 정보(Context)]
            {context}

            [질문(Question)]
            {question}

            [답변]
            """
            
            PROMPT = PromptTemplate(
                template=prompt_template, input_variables=["context", "question"]
            )

            # 4. 체인 생성
            self.chain = (
                {"context": retriever, "question": RunnablePassthrough()}
                | PROMPT
                | llm
                | StrOutputParser()
            )
            print("  > ✅ RAG 체인 생성 완료.")
            
        except Exception as e:
            print(f"❌ [치명적 오류] RAG 모델 로드 실패: {e}")
            self.chain = None

    # ---------------------------------------------------------
    # 공통 질문 생성 로직 (중복 제거를 위해 분리)
    # ---------------------------------------------------------
    def _create_final_question(self, user_input: str, image_class: str) -> str:
        if image_class and user_input:
             return f"사진에서 감지된 물체는 '{image_class}'입니다. 이 물체와 관련하여 사용자가 다음과 같이 질문했습니다: '{user_input}'. 이 물체의 올바른 분리배출 방법을 설명해주세요."
        elif user_input:
            return user_input
        elif image_class:
            return f"사진에서 '{image_class}'(이)가 감지되었습니다. 이것의 올바른 분리배출 방법을 자세히 알려주세요."
        return ""

    # ---------------------------------------------------------
    # 1. 일반 응답 (동기 방식 - YOLO API 등에서 사용)
    # ---------------------------------------------------------
    def get_response(self, user_input: str, image_class: str) -> str:
        if not self.chain:
            return "죄송합니다. RAG 서버가 초기화되지 않았습니다."
        
        final_question = self._create_final_question(user_input, image_class)
        if not final_question:
            return "질문할 내용이 없습니다."

        try:
            return self.chain.invoke(final_question)
        except Exception as e:
            print(f"RAG 처리 중 오류: {e}")
            return "답변 생성 중 오류가 발생했습니다."

    # ---------------------------------------------------------
    # 2. 스트리밍 응답 (비동기 방식 - 채팅 API에서 사용)
    # ---------------------------------------------------------
    async def stream_response(self, user_input: str, image_class: str) -> AsyncGenerator[str, None]:
        if not self.chain:
            yield "죄송합니다. RAG 서버가 초기화되지 않았습니다."
            return

        final_question = self._create_final_question(user_input, image_class)
        if not final_question:
            yield "질문할 내용이 없습니다."
            return

        try:
            # LangChain의 astream을 사용하여 토큰 단위로 스트리밍
            async for chunk in self.chain.astream(final_question):
                yield chunk 
                await asyncio.sleep(0.01) # 너무 빠른 전송 방지
        except Exception as e:
            print(f"RAG 스트리밍 중 오류: {e}")
            yield f"답변 생성 중 오류가 발생했습니다: {e}"