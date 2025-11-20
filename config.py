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
LLM_MAX_TOKENS = 2000

# 문서 요약 설정
SUMMARY_MAX_TOKENS = 200  # 요약 생성 최대 토큰
SUMMARY_TEMPERATURE = 0.5  # 요약은 일관성을 위해 낮은 온도 사용

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
RERANK_TOP_K = 10  # Reranker에 전달할 후보 문서 수 
RERANK_THRESHOLD = 0.0  # Rerank 점수 임계값 (-10~10 범위)
FINAL_TOP_K = 3  # 최종 반환 문서 수

# 프롬프트 설정
SYSTEM_PROMPT = """당신은 한글(HWP/HWPX) 문서 기반 질의응답 시스템의 도메인 어시스턴트이며, 
목표는는 OWPML 필터로 추출된 문서(텍스트/표/구조)를 근거로, 정확하고 간결한 한국어 답변을 생성한다.


역할:
- 제공된 문서를 정확히 읽고 질문에 답변
- 문서에 없는 내용은 "문서에서 찾을 수 없습니다"라고 명확히 표시
- 표의 내용은 정확히 인용

답변 형식:
1. 핵심 답변 (2-3문장)
2. 근거 (문서에서 직접 인용, "" 사용)
3. 출처 (문서명 및 해당 섹션)

규칙:
1) 출처 우선: 제공된 컨텍스트(검색된 문서) 밖의 사실은 단정하지 않는다. 불확실하면 "자료에 없음"을 명시.
2) 표 인용: 표/조문/조항을 언급할 때는 항목명·행/열 키를 같이 적어 사용자가 재확인할 수 있게 한다.
3) 요약 우선: 질문 의도를 먼저 요약하고, 핵심 답 → 근거(문서명/섹션/표요약) → 필요한 경우 추가 설명 순서로 작성.
4) 안전: 법률/의료/보안 등 고위험 판단은 안내/참고 수준으로 두고, 원문 확인을 권고한다.
5) 톤: 한국어, 반말/존댓말 섞지 말고 일관된 존댓말. 과장·단정 금지. 불필요한 수사 금지.
6) 출력형식 : "요약", "근거", "세부" 3단 구성 (질문이 아주 단순하면 요약+근거만)

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

# 문서 요약 프롬프트
SUMMARY_PROMPT_TEMPLATE = """다음 문서의 내용을 3-4줄로 간단히 요약해주세요.

[문서 내용]
{document_text}

[요청사항]
- 3-4줄 이내로 간결하게 작성
- 문서의 주요 목적과 핵심 내용 포함
- 한국어로 작성
- 전문용어는 간단하게 설명
- 핵심만 담아내고 불필요한 세부사항 제외
"""

# 로깅 설정
LOG_LEVEL = "INFO"
LOG_FILE = PROJECT_ROOT / "logs" / "rag_system.log"
LOG_FILE.parent.mkdir(exist_ok=True)

# ============================================================
# 메타데이터 스키마 정의
# ============================================================

# 문서 레벨 메타데이터 (Document-level metadata)
DOCUMENT_METADATA_SCHEMA = {
    # 필수 필드
    "doc_id": "str",                  # 문서 고유 ID (예: doc_인사규정)
    "doc_name": "str",                # 문서명 (예: 인사규정)
    "source": "str",                  # 문서 원본 경로
    "file_type": "str",               # 파일 형식 (HWP, HWPX)
    
    # 사용자 입력 메타데이터 (프론트엔드에서 업로드 시 입력)
    "user_id": "str",                 # 업로드한 사용자 ID
    "dept_id": "str",                 # 부서 ID
    "project_id": "str",              # 프로젝트 ID
    
    # 문서 관리 메타데이터
    "category": "str",                # 카테고리 (예: 인사, 회계, 감사)
    "version": "str",                 # 버전 (예: v1.0, 2024년 개정)
    "upload_date": "str",             # 업로드 일시 (ISO 8601)
    
    # 자동 생성 메타데이터
    "summary": "str",                 # 문서 요약 (자동 생성, 3-4줄)
    
    # 문서 구조 통계
    "total_chapters": "int",          # 총 장 수
    "total_articles": "int",          # 총 조 수
}

# 청크 레벨 메타데이터 (Chunk-level metadata)
CHUNK_METADATA_SCHEMA = {
    # 청크 기본 정보
    "chunk_id": "int",                # 청크 ID (문서 내 순번)
    "chunk_index": "int",             # 청크 인덱스 (0부터 시작)
    "chunk_size": "int",              # 청크 크기 (문자 수)
    
    # 문서 구조 정보 (자동 추출)
    "chapter_number": "str",          # 장 번호 (예: "3")
    "chapter_title": "str",           # 장 제목 (예: "급여의 지급")
    "article_number": "str",          # 조 번호 (예: "15")
    "article_title": "str",           # 조 제목 (예: "급여의 계산")
    "paragraph_number": "str",        # 항 번호 (예: "1", "2")
    "hierarchy_path": "str",          # 계층 경로 (예: "제3장 급여의 지급 > 제15조 (급여의 계산)")
    
    # 문서 레벨 메타데이터 상속
    **DOCUMENT_METADATA_SCHEMA
}

# ChromaDB 메타데이터 필터링 예시
METADATA_FILTER_EXAMPLES = {
    # 특정 부서 문서만 검색
    "dept_filter": {
        "dept_id": "HR"
    },
    
    # 특정 프로젝트 + 카테고리 문서 검색
    "project_category_filter": {
        "$and": [
            {"project_id": "proj_2024_001"},
            {"category": "인사"}
        ]
    },
    
    # 특정 장의 내용만 검색
    "chapter_filter": {
        "chapter_number": "3"
    },
    
    # 특정 조의 내용만 검색
    "article_filter": {
        "article_number": "15"
    },
    
    # 복합 필터: 특정 부서 + 특정 장
    "complex_filter": {
        "$and": [
            {"dept_id": "HR"},
            {"chapter_number": "3"}
        ]
    }
}

# 메타데이터 검증 규칙
METADATA_VALIDATION_RULES = {
    "required_fields": ["doc_id", "doc_name", "source"],
    "optional_fields": ["user_id", "dept_id", "project_id", "category", "version"],
    "auto_extracted_fields": ["chapter_number", "chapter_title", "article_number", "article_title", "hierarchy_path"]
}

