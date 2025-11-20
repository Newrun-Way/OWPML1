백엔드 API 구현

이 폴더는 RAG 시스템과 통합된 FastAPI 기반 백엔드입니다.

========================================
프로젝트 구조
========================================

backend/
├── __init__.py              # 패키지 초기화
├── requirements.txt         # Python 의존성
├── api.py                   # FastAPI 메인 앱
├── models.py                # Pydantic 데이터 모델
├── dependencies.py          # RAG 시스템 의존성
├── celery_config.py         # Celery 설정
├── tasks.py                 # 비동기 작업 정의
├── utils.py                 # 유틸리티 함수
├── run_api.py               # FastAPI 서버 실행
├── run_worker.py            # Celery Worker 실행
├── .env.example             # 환경 변수 템플릿
└── README.md                # 이 파일

========================================
설치 및 실행
========================================

1단계: 의존성 설치

pip install -r backend/requirements.txt

2단계: 환경 변수 설정

.env 파일 (루트 폴더에 이미 있음)에 OPENAI_API_KEY 확인

3단계: Redis 설치 및 시작 (Windows)

중요: 비동기 작업 처리를 위해 Redis 필수!

Option A: Redis Desktop 설치 (GUI)
- https://github.com/luchador-labs/RedisDesktopManager/releases
- 다운로드 후 설치, localhost:6379로 접속

Option B: Redis Subsystem for Windows 설치
- PowerShell (관리자 권한)에서:
  wsl --install
  wsl
  sudo apt-get install redis-server
  redis-server

4단계: FastAPI 서버 실행

python backend/run_api.py

서버는 http://localhost:8000에서 실행됨
API 문서: http://localhost:8000/docs

5단계: Celery Worker 실행 (새로운 터미널)

python backend/run_worker.py

========================================
API 엔드포인트
========================================

1. 헬스체크
GET /api/health
- 서버 및 RAG 시스템 상태 확인

2. 비동기 문서 업로드
POST /api/documents/upload/async
- 파일: HWP/HWPX 파일
- user_id: 사용자 ID
- dept_id: 부서 ID
- project_id: 프로젝트 ID
- category: 문서 카테고리 (기본값: 기타)

응답:
{
    "status": "processing",
    "task_id": "celery-task-id",
    "message": "문서 처리 중입니다.",
    "estimated_time": 10
}

3. 작업 상태 조회
GET /api/tasks/{task_id}

응답:
{
    "task_id": "celery-task-id",
    "status": "processing",
    "progress": 50,
    "stage": "임베딩 생성 중",
    "message": "벡터 임베딩을 생성하고 있습니다..."
}

상태값:
- pending: 대기 중
- processing: 처리 중
- completed: 완료
- failed: 실패

4. 질의응답
POST /api/query

요청:
{
    "question": "연차 휴가는 언제 부여되나?",
    "dept_id": "HR",
    "project_id": "proj_2025",
    "category": "인사",
    "top_k": 5
}

응답:
{
    "answer": "연차 휴가는 재직 기간에 따라 부여됩니다...",
    "sources": [
        {
            "index": 1,
            "doc_name": "인사규정",
            "chapter_number": "5",
            "chapter_title": "휴가 및 휴직",
            "article_number": "27",
            "article_title": "연차 휴가",
            "hierarchy_path": "제5장 휴가 및 휴직 > 제27조",
            "score": 0.9821
        }
    ],
    "processing_time": 3.5,
    "metadata": {...}
}

5. 문서 목록 조회
GET /api/documents?dept_id=HR&project_id=proj_2025

응답:
{
    "documents": [...],
    "total": 42
}

========================================
비동기 처리 흐름
========================================

사용자 흐름:

1. 파일 업로드
   사용자 → POST /api/documents/upload/async → task_id 반환 (즉시)

2. 진행 상황 확인
   사용자 → GET /api/tasks/{task_id} → 진행 상황 (매 2초마다 poll)

3. 완료 확인
   status = "completed" → result에 doc_id, summary, chunks 반환

내부 흐름:

1. FastAPI가 파일 저장
   POST /api/documents/upload/async
   ├── 파일 검증
   ├── 파일 저장 (uploads/{dept_id}/{timestamp}_{filename})
   └── Celery Task 등록 → task_id 반환 (202 Accepted)

2. Celery Worker가 백그라운드 처리
   process_document.delay(file_path, user_metadata)
   ├── Extract.py로 문서 파싱 (progress: 10%)
   ├── 구조 분석 (progress: 30%)
   ├── 요약 생성 (progress: 40%)
   ├── 청킹 (progress: 50%)
   ├── 임베딩 생성 (progress: 90%)
   └── ChromaDB 저장 (progress: 100%)

3. 프론트엔드가 진행 상황 조회
   GET /api/tasks/{task_id}
   ├── status: "processing", progress: 50
   ├── stage: "임베딩 생성 중"
   └── message: "벡터 임베딩을 생성하고 있습니다..."

4. 완료
   status: "completed", result: {...doc_id, summary, chunks...}

========================================
환경 변수 설정
========================================

루트 폴더의 .env 파일에 다음을 포함해야 합니다:

OPENAI_API_KEY=sk-... (이미 있음)

Redis 설정 (선택사항, 기본값 사용):
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_RESULT_DB=1

========================================
주요 기능
========================================

1. 파일 검증
- 파일 확장자 확인 (.hwp, .hwpx만)
- 파일 크기 제한 (최대 10MB)
- 빈 파일 거부

2. 메타데이터 관리
- 자동 doc_id 생성
- 업로드 일시 자동 기록
- 부서/프로젝트/카테고리 필터링

3. 에러 처리
- 각 단계별 에러 로그
- 사용자 친화적 에러 메시지
- 재시도 가능 여부 표시

4. 비동기 처리
- 즉시 응답 (사용자 대기 0.5초)
- 진행 상황 실시간 업데이트
- 여러 파일 동시 처리 가능

========================================
문제 해결
========================================

문제 1: Redis 연결 불가 ("ConnectionRefusedError")

해결:
1. Redis 서버가 실행 중인지 확인
2. localhost:6379에서 실행 중인지 확인
3. Redis Desktop Manager로 접속 확인

문제 2: "ModuleNotFoundError: No module named 'rag'"

해결:
- backend/dependencies.py의 sys.path.insert가 PROJECT_ROOT를 올바르게 설정하는지 확인
- 터미널에서 프로젝트 루트에서 실행: python -m backend.run_api

문제 3: Task가 PENDING 상태에서 진행되지 않음

해결:
1. Celery Worker가 실행 중인지 확인
2. Worker 터미널에서 에러 메시지 확인
3. Redis 연결 상태 확인

문제 4: ChromaDB "doc_id not found" 에러

해결:
- 로컬에서는 벡터 저장소가 비어있습니다
- 서버에서 이미 임베딩된 데이터가 있습니다
- 로컬에서 테스트할 때는 먼저 문서를 업로드하세요

========================================
개발 팁
========================================

1. API 테스트
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- cURL: curl -X GET "http://localhost:8000/api/health"

2. 로그 확인
- api.py 로그: FastAPI 서버 터미널
- tasks.py 로그: Celery Worker 터미널
- rag/ 모듈 로그: logs/rag_system.log

3. 디버깅
- tasks.py에서 self.update_state()로 진행 상황 확인
- utils.generate_request_id()로 요청 추적
- api.py의 logger.info()로 흐름 확인

========================================
다음 단계
========================================

1. 프론트엔드와 통합
   - 업로드 폼에서 /api/documents/upload/async 호출
   - /api/tasks/{task_id}로 진행 상황 폴링
   - 완료 후 결과 표시

2. 인증 추가 (선택사항)
   - JWT 토큰 기반 인증
   - 사용자별 접근 제어

3. 데이터베이스 추가
   - 문서 메타데이터 영구 저장
   - 질의 히스토리 추적

4. 모니터링
   - Celery Flower: 작업 모니터링
   - Prometheus: 메트릭 수집
   - ELK Stack: 로그 분석

