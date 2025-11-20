빠른 시작 가이드 (Quick Start)

========================================
1단계: 환경 준비 
========================================

1. 루트 폴더의 .env 파일 확인
   - OPENAI_API_KEY 이미 설정되어 있어야 함

2. 의존성 설치
   pip install -r backend/requirements.txt

========================================
2단계: Redis 설치- Windows
========================================

Redis는 비동기 작업 큐(메시지 브로커)입니다.
꼭 필요합니다!

옵션 1: Windows Subsystem for Linux (WSL) 사용 (추천)

1. PowerShell (관리자 권한)에서 실행:
   wsl --install

2. Ubuntu 터미널 열기:
   wsl
   
3. Redis 설치 및 시작:
   sudo apt-get update
   sudo apt-get install redis-server
   redis-server

Ubuntu 터미널은 열어둡니다!

옵션 2: Redis 독립 설치 (Windows)

https://github.com/microsoftarchive/redis/releases/latest
redis-server.exe 다운로드 및 실행

========================================
3단계: FastAPI 서버 실행 (새 터미널)
========================================

터미널 1 (API 서버):

cd C:\Users\chodo\Desktop\Al Lang
python backend/run_api.py

출력:
INFO:     Started server process [1234]
INFO:     Uvicorn running on http://0.0.0.0:8000

 완료! API 서버 실행 중

========================================
4단계: Celery Worker 실행 (새 터미널)
========================================

터미널 2 (Celery Worker):

cd C:\Users\chodo\Desktop\Al Lang
python backend/run_worker.py

출력:
[INFO/MainProcess] celery@DESKTOP-... ready.
[INFO/MainProcess] Celery worker is ready.

✅ 완료! Worker 실행 중

========================================
5단계: 테스트 (선택사항)
========================================

API 문서 접속:
http://localhost:8000/docs

또는 터미널 3에서 테스트:

# 헬스체크
curl -X GET "http://localhost:8000/api/health"

# 문서 업로드 (비동기)
curl -X POST "http://localhost:8000/api/documents/upload/async" \
  -F "file=@path/to/document.hwpx" \
  -F "user_id=user1" \
  -F "dept_id=HR" \
  -F "project_id=proj_2025"

응답:
{
  "status": "processing",
  "task_id": "abc123...",
  "message": "문서 처리 중입니다.",
  "estimated_time": 10
}

task_id를 복사한 후, 아래를 실행:

# 작업 상태 조회
curl -X GET "http://localhost:8000/api/tasks/abc123..."

응답:
{
  "task_id": "abc123...",
  "status": "processing",
  "progress": 50,
  "stage": "임베딩 생성 중"
}

status가 "completed"가 될 때까지 반복 실행!

========================================
프로세스 종료
========================================

모든 작업 완료 후:

터미널 2 (Worker): Ctrl + C
터미널 1 (API): Ctrl + C
WSL (Redis): Ctrl + C (또는 exit)

========================================
문제 해결
========================================

Q: "ConnectionRefusedError: [Errno 111] Connection refused"
A: Redis가 실행 중이 아닙니다.
   WSL에서 "redis-server" 실행 확인

Q: "ModuleNotFoundError: No module named 'rag'"
A: 프로젝트 루트에서 실행하세요
   cd C:\Users\chodo\Desktop\Al Lang

Q: "Task stuck in PENDING"
A: 
   1. Worker가 실행 중인지 확인
   2. Redis가 실행 중인지 확인
   3. 터미널 2의 에러 메시지 확인

Q: "Port 8000 already in use"
A: 다른 프로세스가 포트 8000을 사용 중
   python backend/run_api.py --port 8001

========================================
구조 다시 정리
========================================

프로세스 1 (Redis - WSL):
redis-server
↓
메시지 브로커 역할

프로세스 2 (API Server):
python backend/run_api.py
↓
FastAPI 서버 (포트 8000)
사용자 요청 처리

프로세스 3 (Celery Worker):
python backend/run_worker.py
↓
백그라운드 작업 처리
(파싱, 임베딩, 저장)

프로세스 흐름:
1. 사용자가 /api/documents/upload/async 호출
2. API가 파일 저장 + Task 등록 (즉시 반환)
3. Worker가 Task를 Redis에서 가져와 처리
4. 사용자가 /api/tasks/{task_id}로 진행 상황 확인

========================================
다음 스텝
========================================

현재 상태:
- FastAPI 비동기 API 구현됨
- Celery 백그라운드 작업 구현됨
- 문서 업로드 + 질의응답 API 구현됨

