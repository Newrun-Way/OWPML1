"""
Celery Worker 실행 스크립트
Windows 및 Unix 호환
"""

import logging
import platform
from celery_config import celery_app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info(f"Celery Worker 시작 ({platform.system()})...")
    
    if platform.system() == "Windows":
        # Windows에서는 pool type을 solo 또는 threads로 설정
        celery_app.worker_main([
            'worker',
            '--loglevel=info',
            '--pool=threads',
            '--concurrency=2',
            '--queues=celery,document_processing,query_processing',
            '--max-tasks-per-child=1000',
            '--time-limit=600',
            '--soft-time-limit=580'
        ])
    else:
        # Unix/Linux/Mac
        celery_app.worker_main([
            'worker',
            '--loglevel=info',
            '--concurrency=2',
            '--queues=celery,document_processing,query_processing',
            '--max-tasks-per-child=1000',
            '--time-limit=600',
            '--soft-time-limit=580'
        ])

