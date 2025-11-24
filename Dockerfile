# ========================================
# Multi-stage Dockerfile
# 기본 이미지는 동일하지만 실행 명령만 다름
# ========================================

FROM python:3.10-slim AS base

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    default-jdk \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 복사 및 설치
COPY requirements.txt .
COPY backend/requirements.txt backend_requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r backend_requirements.txt

# 프로젝트 파일 복사
COPY . .

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# ========================================
# API 서버 스테이지
# ========================================
FROM base AS api

EXPOSE 8000

# API 서버 실행
CMD ["python", "backend/run_api.py"]


# ========================================
# Celery Worker 스테이지
# ========================================
FROM base AS worker

# Celery Worker 실행
CMD ["python", "backend/run_worker.py"]


# ========================================
# Flower 모니터링 스테이지
# ========================================
FROM base AS flower

EXPOSE 5555

# Flower 실행
CMD ["celery", "-A", "backend.celery_config", "flower", "--port=5555"]


# ========================================
# 기본 스테이지 (호환성)
# ========================================
FROM base AS default

EXPOSE 8000

# 기본 명령어 (레거시)
CMD ["python", "main.py"]

