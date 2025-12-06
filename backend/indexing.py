# backend/indexing.py
import os
import time
# ⭐️ .env 파일을 읽기 위한 라이브러리 추가
from dotenv import load_dotenv 

from langchain_community.document_loaders import DirectoryLoader, UnstructuredMarkdownLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# ---------------------------------------------------------------
# 0. 환경 변수 로드 (.env 파일 읽기)
# ---------------------------------------------------------------
# 이 함수가 호출되면 같은 폴더의 .env 파일 내용을 os.environ에 로드합니다.
load_dotenv()

# ---------------------------------------------------------------
# 설정값
# ---------------------------------------------------------------
DATA_SOURCE_PATH = "documents" 
VECTOR_DB_PATH = "my_faiss_index"
# ---------------------------------------------------------------

def main():
    print(f"1. '{DATA_SOURCE_PATH}' 폴더에서 .md 파일 로드를 시작합니다...")
    loader = DirectoryLoader(
        DATA_SOURCE_PATH,  
        glob="**/*.md",
        loader_cls=UnstructuredMarkdownLoader,
        show_progress=True,
        use_multithreading=True
    )

    try:
        docs = loader.load()
        if not docs:
            print(f"[오류] '{DATA_SOURCE_PATH}' 폴더에 파일이 없거나 .md 파일을 읽을 수 없습니다.")
            print("backend/documents 폴더에 .md 파일이 있는지 확인하세요.")
            return
        print(f"  > 총 {len(docs)}개의 문서를 성공적으로 로드했습니다.")

    except Exception as e:
        print(f"[오류] 문서 로드 중 예외가 발생했습니다: {e}")
        print("unstructured, unstructured-markdown 라이브러리가 올바르게 설치되었는지 확인하세요.")
        return

    print("2. 문서 크기 분석 결과, 청킹(분할)을 생략합니다. (문서 1개 = 1 청크)")
    split_docs = docs

    print("3. OpenAI 임베딩 모델로 문서를 벡터화합니다. (API 호출 발생)")
    start_time = time.time()
    try:
        # .env에서 로드된 API 키가 자동으로 사용됩니다.
        embeddings = OpenAIEmbeddings()
        vector_store = FAISS.from_documents(split_docs, embeddings)

    except Exception as e:
        print(f"[오류] 임베딩 또는 FAISS 생성 중 오류가 발생했습니다: {e}")
        print("API 키가 올바른지, OpenAI 사용량 한도가 남았는지 확인하세요.")
        return

    end_time = time.time()
    print(f"  > 벡터화 완료. (소요 시간: {end_time - start_time:.2f}초)")

    print(f"4. 벡터 스토어를 '{VECTOR_DB_PATH}' 폴더에 저장합니다.")
    vector_store.save_local(VECTOR_DB_PATH)

    print(f"\n[성공] '{VECTOR_DB_PATH}' 생성이 완료되었습니다.")

if __name__ == "__main__":
    # load_dotenv()가 위에서 실행되었으므로 os.environ에서 키 확인 가능
    if "OPENAI_API_KEY" not in os.environ:
        print("[오류] OPENAI_API_KEY를 찾을 수 없습니다.")
        print("1. .env 파일이 존재하는지 확인하세요.")
        print("2. .env 파일 안에 'OPENAI_API_KEY=sk-...' 형식이 맞는지 확인하세요.")
    else:
        main()