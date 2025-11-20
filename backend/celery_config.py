"""
Celery 설정
비동기 작업 처리 구성
"""

from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

# Redis 설정
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
RESULT_DB = int(os.getenv("REDIS_RESULT_DB", 1))

BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
RESULT_BACKEND = f"redis://{REDIS_HOST}:{REDIS_PORT}/{RESULT_DB}"

# Celery 앱 생성
celery_app = Celery(
    'rag_tasks',
    broker=BROKER_URL,
    backend=RESULT_BACKEND
)

# Celery 설정
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Seoul',
    enable_utc=True,
    task_track_started=True,
    result_expires=3600,  # 1시간 후 결과 삭제
    task_time_limit=600,  # 작업 최대 실행 시간 600초
    task_soft_time_limit=580,  # 소프트 타임 리밋 580초
    worker_prefetch_multiplier=1,  # 워커가 동시에 처리할 작업 수
    task_acks_late=True,  # 작업 완료 후 확인
)

# 작업별 라우팅 (선택사항)
celery_app.conf.task_routes = {
    'backend.tasks.process_document': {'queue': 'document_processing'},
    'backend.tasks.process_query': {'queue': 'query_processing'},
}

