Docker 컨테이너 분리 가이드

========================================
1. 아키텍처 개요
========================================

분리된 서비스 구조:

1. Redis (메시지 브로커)
   - 포트: 6379
   - 역할: Celery Task Queue, Result Backend
   - 컨테이너: rag-redis

2. FastAPI (API 서버)
   - 포트: 8000
   - 역할: 파일 업로드, Task 등록, 질의응답
   - 컨테이너: rag-api
   - 리소스 제한: CPU 2코어, 메모리 2GB

3. Celery Worker (문서 처리)
   - 역할: 백그라운드 문서 파싱, 임베딩, 저장
   - 컨테이너: rag-worker (2개 복제)
   - 리소스 제한: CPU 4코어, 메모리 8GB, GPU 1개

4. Celery Flower (모니터링, 선택사항)
   - 포트: 5555
   - 역할: Celery 작업 모니터링 UI
   - 컨테이너: rag-flower

5. Nginx (리버스 프록시, 선택사항)
   - 포트: 80
   - 역할: 로드 밸런싱, 라우팅
   - 컨테이너: rag-nginx

========================================
2. 장점
========================================

격리된 리소스:
- API 서버와 Worker가 독립적으로 실행됨
- 한 사용자의 큰 파일 업로드가 다른 사용자의 질의응답에 영향 없음
- Worker가 처리하는 동안 API는 즉시 응답 가능

확장성:
- Worker를 여러 개 복제 가능 (replicas: 2)
- 동시에 여러 파일 처리 가능
- API 서버도 필요시 복제 가능

리소스 최적화:
- API 서버: 가벼운 리소스 (2GB)
- Worker: 무거운 리소스 (8GB, GPU)
- 각 서비스에 맞는 리소스 할당

독립적 재시작:
- Worker 재시작해도 API는 영향 없음
- API 업데이트해도 Worker는 계속 작업 가능

모니터링:
- Flower로 Worker 상태 실시간 확인
- 각 컨테이너의 헬스체크

========================================
3. 실행 방법
========================================

3.1 준비

1. Dockerfile 교체
   
   기존 Dockerfile 백업:
   mv Dockerfile Dockerfile.old
   
   새 Dockerfile 사용:
   mv Dockerfile.new Dockerfile

2. .env 파일 확인
   
   루트 폴더의 .env 파일에 OPENAI_API_KEY 있는지 확인

3.2 빌드 및 실행

전체 서비스 시작:
docker-compose up -d

특정 서비스만 시작:
docker-compose up -d api
docker-compose up -d worker

로그 확인:
docker-compose logs -f api
docker-compose logs -f worker

3.3 상태 확인

모든 서비스 상태:
docker-compose ps

API 헬스체크:
curl http://localhost:8000/api/health

Flower 모니터링:
http://localhost:5555

3.4 종료

전체 서비스 종료:
docker-compose down

볼륨까지 삭제:
docker-compose down -v

========================================
4. 서비스별 설명
========================================

4.1 Redis

역할:
- Celery의 메시지 브로커
- Task Queue 관리
- Result Backend

설정:
- appendonly yes: 데이터 영구 저장
- 볼륨 마운트: redis_data

헬스체크:
redis-cli ping

4.2 API 서버

역할:
- 파일 업로드 받기
- Task 등록 후 즉시 응답 (0.5초)
- 질의응답 처리
- 작업 상태 조회

포트:
- 8000 (외부 접근 가능)

볼륨:
- data/: 업로드된 파일
- logs/: 로그 파일
- extracted_results/: 파싱 결과

리소스:
- CPU: 2코어
- 메모리: 2GB

4.3 Celery Worker

역할:
- 백그라운드 문서 처리
- Extract.py 실행
- 임베딩 생성
- ChromaDB 저장

복제:
- replicas: 2 (2개 Worker 동시 실행)

볼륨:
- data/: 업로드된 파일 읽기
- logs/: 로그 기록
- extracted_results/: 파싱 결과 저장
- hwp_data/: HWP 파일 접근

리소스:
- CPU: 4코어
- 메모리: 8GB
- GPU: 1개 (임베딩 가속)

4.4 Flower (선택사항)

역할:
- Celery Worker 모니터링
- Task 진행 상황 시각화
- Worker 상태 확인

포트:
- 5555

접속:
http://localhost:5555

4.5 Nginx (선택사항)

역할:
- API 서버 앞단 리버스 프록시
- 로드 밸런싱
- 최대 업로드 크기 제한 (50MB)

포트:
- 80

설정:
- least_conn: 가장 여유로운 서버로 라우팅
- 타임아웃: 600초
- WebSocket 지원

========================================
5. 스케일링
========================================

5.1 Worker 개수 증가

docker-compose.yml 수정:
deploy:
  replicas: 4  # 2 → 4개로 증가

재시작:
docker-compose up -d --scale worker=4

5.2 API 서버 복제

docker-compose.yml 수정:
deploy:
  replicas: 2

Nginx가 자동으로 로드 밸런싱

5.3 리소스 조정

메모리 증가:
deploy:
  resources:
    limits:
      memory: 16G

GPU 개수 증가:
devices:
  - count: 2

========================================
6. 모니터링
========================================

6.1 Docker 상태

실시간 리소스 사용량:
docker stats

특정 컨테이너:
docker stats rag-api rag-worker

6.2 로그

API 로그:
docker-compose logs -f api

Worker 로그:
docker-compose logs -f worker

Redis 로그:
docker-compose logs -f redis

6.3 Flower 대시보드

접속:
http://localhost:5555

확인 가능 항목:
- 활성 Worker 수
- 진행 중인 Task
- 완료된 Task 통계
- 실패한 Task 목록

========================================
7. 개발 vs 프로덕션
========================================

개발 환경:

docker-compose.yml:
volumes:
  - .:/app  # 코드 실시간 반영

command: python backend/run_api.py --reload

프로덕션 환경:

volumes:
  - ./data:/app/data  # 데이터만 마운트

restart: unless-stopped

deploy:
  resources:
    limits: ...

========================================
8. 트러블슈팅
========================================

8.1 Redis 연결 실패

문제:
ConnectionRefusedError: [Errno 111] Connection refused

해결:
1. Redis 컨테이너 실행 확인
   docker-compose ps redis

2. 네트워크 확인
   docker network ls
   docker network inspect rag-network

3. 환경 변수 확인
   REDIS_HOST=redis (서비스명)

8.2 Worker가 Task를 처리하지 않음

문제:
Task가 PENDING 상태에서 멈춤

해결:
1. Worker 로그 확인
   docker-compose logs worker

2. Worker 재시작
   docker-compose restart worker

3. Redis 상태 확인
   docker exec -it rag-redis redis-cli
   KEYS *

8.3 GPU 인식 안됨

문제:
Worker에서 GPU를 찾을 수 없음

해결:
1. nvidia-docker 설치 확인
   nvidia-smi

2. docker-compose.yml 수정
   runtime: nvidia

8.4 API 서버 접근 불가

문제:
curl http://localhost:8000/api/health
Connection refused

해결:
1. 컨테이너 실행 확인
   docker-compose ps api

2. 포트 매핑 확인
   docker port rag-api

3. 로그 확인
   docker-compose logs api

========================================
9. 마이그레이션 가이드
========================================

기존 → 새 구조 전환:

1단계: 데이터 백업
cp -r data data_backup
cp -r logs logs_backup

2단계: 기존 컨테이너 중지
docker stop $(docker ps -aq)
docker rm $(docker ps -aq)

3단계: 새 구조로 빌드
docker-compose build

4단계: 서비스 시작
docker-compose up -d

5단계: 헬스체크
curl http://localhost:8000/api/health

6단계: 데이터 확인
docker-compose exec api python -c "from rag.vector_store import VectorStore; vs = VectorStore.load(); print(vs.collection.count())"

========================================
10. 베스트 프랙티스
========================================

1. 환경 변수 관리
   - .env 파일 사용
   - 민감 정보는 Docker secrets 사용

2. 볼륨 마운트
   - 데이터만 마운트
   - 코드는 이미지에 포함

3. 헬스체크
   - 모든 서비스에 헬스체크 추가
   - depends_on: condition 사용

4. 로깅
   - 각 서비스의 로그를 외부 볼륨에 저장
   - 로그 로테이션 설정

5. 리소스 제한
   - CPU, 메모리 제한 설정
   - OOM killer 방지

6. 네트워크
   - 서비스별 네트워크 분리
   - 외부 노출 최소화

========================================
요약
========================================

기존 구조:
하나의 컨테이너에서 모든 기능 실행
→ 큰 파일 업로드 시 전체 서비스 블로킹

새 구조:
- API 서버: 즉시 응답 (경량)
- Worker: 백그라운드 처리 (중량, GPU)
- Redis: 메시지 큐
→ 서로 독립적, 동시 처리 가능

실행 명령:
docker-compose up -d

확인:
- API: http://localhost:8000/api/health
- Flower: http://localhost:5555
- 로그: docker-compose logs -f

다음 단계:
1. docker-compose.yml 환경에 맞게 조정
2. GPU 설정 확인
3. 프로덕션 배포

