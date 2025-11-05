"""
RAG 시스템 설정
환경변수 및 모델 파라미터 관리
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 프로젝트 경로
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
VECTOR_STORE_DIR = DATA_DIR / "vector_store"
UPLOADS_DIR = DATA_DIR / "uploads"
EXTRACTED_DIR = PROJECT_ROOT / "extracted_results"  # extract.py 출력 폴더

# 디렉토리 생성
for dir_path in [DATA_DIR, VECTOR_STORE_DIR, UPLOADS_DIR, EXTRACTED_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# API 키
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# 임베딩 모델 설정
EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDING_DIM = 1024
MAX_SEQ_LENGTH = 8192

# LLM 설정
LLM_MODEL = "gpt-4o-mini"
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 1024

# 청킹 설정
CHUNK_SIZE = 800  # 토큰
CHUNK_OVERLAP = 150  # 토큰
SEPARATORS = ["\n\n", "\n", ".", "!", "?", " ", ""]

# 검색 설정
TOP_K = 5  # 검색할 문서 청크 수
SIMILARITY_THRESHOLD = 0.7  # 유사도 임계값

# Reranker 설정
USE_RERANKER = True  # Reranker 사용 여부
RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"  # Reranker 모델
RERANK_TOP_K = 10  # Reranker에 전달할 후보 문서 수 (TOP_K보다 크게)
RERANK_THRESHOLD = 0.0  # Rerank 점수 임계값 (보통 -10~10 범위)
FINAL_TOP_K = 3  # 최종 반환 문서 수

# 프롬프트 설정
SYSTEM_PROMPT = """당신은 한국어 공문서 전문 AI 어시스턴트입니다.

역할:
- 제공된 문서를 정확히 읽고 질문에 답변
- 문서에 없는 내용은 "문서에서 찾을 수 없습니다"라고 명확히 표시
- 표의 내용은 정확히 인용

답변 형식:
1. 핵심 답변 (2-3문장)
2. 근거 (문서에서 직접 인용, "" 사용)
3. 출처 (문서명 및 해당 섹션)

규칙:
- 존댓말 사용
- 명확하게
- 추측하지 말 것
- 표는 마크다운 형식으로 표시
- 문서 내용만 사용, 외부 지식 사용 금지
- 애매하면 "확실하지 않습니다" 표시
- 여러 답변 가능하면 모두 제시
"""

USER_PROMPT_TEMPLATE = """다음 문서를 참고하여 질문에 답해주세요.

[문서 내용]
{context}

[질문]
{question}

[지시사항]
- 문서에 명시된 내용만 사용
- 표가 있다면 정확히 인용
- 출처 문서명 반드시 명시
"""

# 로깅 설정
LOG_LEVEL = "INFO"
LOG_FILE = PROJECT_ROOT / "logs" / "rag_system.log"
LOG_FILE.parent.mkdir(exist_ok=True)

