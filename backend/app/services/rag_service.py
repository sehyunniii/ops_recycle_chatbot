# backend/app/services/rag_service.py
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import os
import asyncio 
from typing import AsyncGenerator 

class RAGService:
    def __init__(self, db_path="my_faiss_index"): 
        if "OPENAI_API_KEY" not in os.environ:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")
        
        print("RAG Service를 초기화합니다...")
        try:
            llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
            embeddings = OpenAIEmbeddings()
            
            vector_store = FAISS.load_local(
                folder_path=db_path, 
                embeddings=embeddings, 
                allow_dangerous_deserialization=True
            )
            retriever = vector_store.as_retriever(search_kwargs={"k": 3})

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

            self.chain = (
                {"context": retriever, "question": RunnablePassthrough()}
                | PROMPT
                | llm
                | StrOutputParser()
            )
            print("  > RAG 체인 생성 완료.")
        except Exception as e:
            print(f"[치명적 오류] RAG 모델 로드 실패: {e}")
            self.chain = None

    # (기존 get_response: /api/predict에서 사용 - 변경 없음)
    def get_response(self, user_input: str, image_class: str) -> str:
        if not self.chain:
            return "RAG 서버가 초기화에 실패했습니다."
        
        final_question = ""
        if image_class and user_input:
            final_question = f"'{image_class}' 사진에 대한 추가 질문입니다: '{user_input}'"
        elif image_class:
            final_question = f"'{image_class}'는 어떻게 분리배출해야 하나요?"
        elif user_input:
            final_question = user_input
        else:
            return "질문 내용이 없습니다."

        try:
            result = self.chain.invoke(final_question)
            return result
        except Exception as e:
            print(f"RAG 처리 중 오류: {e}")
            return f"답변 생성 중 오류가 발생했습니다: {e}"

    # ⭐️ (수정) /api/chat을 위한 스트리밍 메서드 (if 순서 변경) ⭐️
    async def stream_response(self, user_input: str, image_class: str) -> AsyncGenerator[str, None]:
        if not self.chain:
            yield "RAG 서버가 초기화에 실패했습니다."
            return

        final_question = ""
        # ⭐️ (수정) 1순위: 이미지 + 텍스트
        if image_class and user_input:
            final_question = f"'{image_class}' 사진에 대한 추가 질문입니다: '{user_input}'"
        # ⭐️ (수정) 2순위: 텍스트만 (이것이 누락되었음)
        elif user_input:
            final_question = user_input 
        # ⭐️ (수정) 3순위: 이미지 문맥만 (예: "이건 어떻게 버려?")
        elif image_class: 
            final_question = f"'{image_class}'는 어떻게 분리배출해야 하나요?"
        # 4. 둘 다 없는 경우
        else:
            yield "질문 내용이 없습니다."
            return

        try:
            # .astream() (비동기 스트림) 사용
            async for chunk in self.chain.astream(final_question):
                yield chunk 
                await asyncio.sleep(0.01) 
        except Exception as e:
            print(f"RAG 스트리밍 중 오류: {e}")
            yield f"답변 생성 중 오류가 발생했습니다: {e}"