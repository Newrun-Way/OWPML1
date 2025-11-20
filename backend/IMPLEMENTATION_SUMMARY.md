
backend/
├── __init__.py                      # 패키지 초기화
├── requirements.txt                 # Python 의존성 
├── api.py                           # FastAPI 메인 앱 
├── models.py                        # Pydantic 데이터 모델 
├── dependencies.py                  # RAG 시스템 의존성 주입
├── celery_config.py                 # Celery 설정
├── tasks.py                         # Celery 비동기 작업
├── utils.py                         # 유틸리티 함수 
├── run_api.py                       # API 서버 실행 스크립트
├── run_worker.py                    # Celery Worker 실행 스크립트
├── README.md                        # 상세 문서
├── QUICKSTART.md                    # 빠른 시작 가이드


 구현 기능


1. 비동기 문서 업로드 API
   POST /api/documents/upload/async
   - 파일 검증 (확장자, 크기)
   - 비동기 Task 등록
   - 즉시 응답 (task_id 반환)
   - 202 Accepted 상태 반환

2. 작업 상태 조회 API
   GET /api/tasks/{task_id}
   - 비동기 작업 상태 확인
   - 진행률 업데이트 (0-100%)
   - 완료 시 결과 반환

3. 질의응답 API
   POST /api/query
   - 동기 처리
   - 메타데이터 필터링
   - 출처 정보 반환

4. 헬스체크 API
   GET /api/health
   - 서버 상태 확인
   - RAG 시스템 상태 확인
   - 벡터 저장소 상태 확인

5. 문서 목록 조회 API
   GET /api/documents
   - 필터링 기능
   - 문서 통계

6. Celery 비동기 작업
   process_document
   - 4단계 진행 상황 업데이트
   - 자동 요약 생성
   - 임베딩 생성
   - ChromaDB 저장


API 요청/응답 흐름


비동기 문서 업로드 흐름:

1. 프론트엔드 → API
   POST /api/documents/upload/async
   - file: HWP/HWPX
   - user_id, dept_id, project_id
   - category, version

2. API 처리 (0.5초)
   ├── 파일 검증
   ├── 파일 저장 (data/uploads/)
   ├── Task 등록 (Redis)
   └── task_id 반환 (202 Accepted)

3. 프론트엔드 ← API
   {
     "status": "processing",
     "task_id": "celery-task-id",
     "message": "문서 처리 중입니다.",
     "estimated_time": 10
   }

4. 백그라운드 처리 (Celery Worker)
   ├── Extract: 파싱 (10%)
   ├── Structure: 구조 분석 (30%)
   ├── Summary: 요약 생성 (40%)
   ├── Chunk: 청킹 (50%)
   ├── Embed: 임베딩 (90%)
   └── Save: ChromaDB 저장 (100%)

5. 상태 조회 (진행 중)
   GET /api/tasks/{task_id}
   {
     "task_id": "celery-task-id",
     "status": "processing",
     "progress": 50,
     "stage": "임베딩 생성 중"
   }

6. 상태 조회 (완료)
   GET /api/tasks/{task_id}
   {
     "task_id": "celery-task-id",
     "status": "completed",
     "progress": 100,
     "result": {
       "doc_id": "doc_인사규정",
       "summary": "...",
       "chunks": 18
     }
   }

질의응답 흐름:

1. 프론트엔드 → API
   POST /api/query
   {
     "question": "연차 휴가는 언제 부여되나?",
     "dept_id": "HR"
   }

2. API 처리 (3-4초)
   ├── 필터 구성
   ├── RAG 질의
   └── 응답 포맷팅

3. 프론트엔드 ← API
   {
     "answer": "연차 휴가는...",
     "sources": [
       {
         "doc_name": "인사규정",
         "hierarchy_path": "제5장 > 제27조",
         "score": 0.9821
       }
     ],
     "processing_time": 3.5
   }


 RAG 시스템 통합


의존성 주입 (dependencies.py):
- get_rag_pipeline() 싱글톤 인스턴스
- 프로젝트 루트 자동 설정
- 에러 처리

작업 정의 (tasks.py):
- process_document: 문서 처리
- process_query: 질의응답 (선택)
- cleanup_old_tasks: 정기 정리

메타데이터 처리 (utils.py):
- build_user_metadata()
- build_query_filters()
- validate_file()
- format_answer_sources()



파일 검증:
 파일 확장자 확인 (.hwp, .hwpx만)
 파일 크기 제한 (10MB 이하)
 빈 파일 거부

API 에러:
 HTTP 400: 잘못된 요청
 HTTP 500: 서버 에러
 에러 코드 및 메시지 제공
 재시도 가능 여부 표시

Celery 작업 에러:
 FAILURE 상태 처리 
 에러 메시지 저장
 작업 로그 기록


 실행 방법

준비:
1. pip install -r backend/requirements.txt
2. Redis 설치 및 실행 (WSL 또는 독립 설치)

3 개의 터미널 열기:

터미널 1 (Redis - WSL):
wsl
redis-server

터미널 2 (API Server):
cd C:\Users\chodo\Desktop\Al Lang
python backend/run_api.py

터미널 3 (Celery Worker):
cd C:\Users\chodo\Desktop\Al Lang
python backend/run_worker.py

테스트:
- Swagger: http://localhost:8000/docs
- API: http://localhost:8000/api/health

========================================
📋 현재 프로젝트와의 호환성
========================================

✅ config.py와 완벽 호환
   - 경로 설정 (UPLOADS_DIR, VECTOR_STORE_DIR 등)
   - 메타데이터 스키마 준수
   - LLM 설정 활용

✅ RAG 모듈과 완벽 호환
   - RAGPipeline 싱글톤 사용
   - add_document_from_extract() 호출
   - query() 호출
   - ChromaDB 통합

✅ 메타데이터 구조 준수
   - DOCUMENT_METADATA_SCHEMA
   - CHUNK_METADATA_SCHEMA
   - 필터링 규칙 준수

 로깅 설정 일관성
   - logs/rag_system.log 활용
   - 동일한 포맷 사용


 Redis 필수
   - 비동기 작업 처리를 위해 필수
   - Windows에서는 WSL 또는 독립 설치 필요

 파일 크기
   - 최대 10MB 제한
   - 대용량 파일은 분할 필요


