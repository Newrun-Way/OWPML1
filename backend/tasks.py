"""
Celery 비동기 작업 정의
문서 업로드, 임베딩, 저장 등을 백그라운드에서 처리
"""

import logging
import time
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# 프로젝트 루트 추가 (우선)
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import extract
import config

from celery_config import celery_app
from dependencies import get_rag_pipeline

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name='backend.tasks.process_document')
def process_document(
    self,
    file_path: str,
    user_metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    비동기 문서 처리 (파싱 + 임베딩 + 저장)
    
    Args:
        file_path: 업로드된 파일 경로
        user_metadata: 사용자 메타데이터
        
    Returns:
        처리 결과 딕셔너리
    """
    try:
        start_time = time.time()
        
        # 1단계: 문서 파싱
        logger.info(f"[Task {self.request.id}] 문서 파싱 시작: {file_path}")
        self.update_state(
            state='PROGRESS',
            meta={
                'stage': '파싱 중',
                'progress': 10,
                'message': 'HWP/HWPX 문서를 파싱하고 있습니다...'
            }
        )
        
        file_path_obj = Path(file_path)
        extracted_dir = extract.run_extraction(str(file_path_obj))
        logger.info(f"[Task {self.request.id}] 파싱 완료: {extracted_dir}")
        
        # 2단계: 구조 분석 (extract.py 내부에서 수행됨)
        self.update_state(
            state='PROGRESS',
            meta={
                'stage': '구조 분석 중',
                'progress': 30,
                'message': '문서 구조를 분석하고 있습니다...'
            }
        )
        
        # 3단계: 요약 생성
        self.update_state(
            state='PROGRESS',
            meta={
                'stage': '요약 생성 중',
                'progress': 40,
                'message': '문서 요약을 생성하고 있습니다...'
            }
        )
        logger.info(f"[Task {self.request.id}] 요약 생성 중...")
        
        # 4단계: RAG 파이프라인에 추가
        self.update_state(
            state='PROGRESS',
            meta={
                'stage': '임베딩 생성 중',
                'progress': 50,
                'message': '벡터 임베딩을 생성하고 있습니다...'
            }
        )
        logger.info(f"[Task {self.request.id}] RAG 파이프라인 추가 중...")
        
        try:
            rag = get_rag_pipeline()
            result = rag.add_document_from_extract(
                extracted_dir=extracted_dir,
                user_metadata=user_metadata
            )
            
            # 진행 상황 업데이트 (임베딩 진행 중)
            self.update_state(
                state='PROGRESS',
                meta={
                    'stage': '저장 중',
                    'progress': 90,
                    'message': 'ChromaDB에 저장하고 있습니다...'
                }
            )
            
            processing_time = time.time() - start_time
            logger.info(f"[Task {self.request.id}] 문서 처리 완료 ({processing_time:.2f}초)")
            
            # 최종 결과
            final_result = {
                'status': 'completed',
                'doc_id': result.get('doc_id', ''),
                'doc_name': result.get('doc_name', ''),
                'summary': result.get('summary', ''),
                'chunks': result.get('chunks_added', 0),
                'processing_time': processing_time,
                'metadata': result.get('metadata', {}),
                'message': '문서 처리가 완료되었습니다.'
            }
            
            return final_result
            
        except Exception as rag_error:
            logger.error(f"[Task {self.request.id}] RAG 파이프라인 오류: {rag_error}")
            raise
            
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = str(e)
        logger.error(f"[Task {self.request.id}] 문서 처리 실패: {error_msg}")
        
        # 에러 상태 업데이트
        self.update_state(
            state='FAILURE',
            meta={
                'status': 'failed',
                'error': error_msg,
                'processing_time': processing_time,
                'message': '문서 처리 중 오류가 발생했습니다.'
            }
        )
        
        return {
            'status': 'failed',
            'error': error_msg,
            'processing_time': processing_time,
            'message': f'처리 실패: {error_msg}'
        }


@celery_app.task(bind=True, name='backend.tasks.process_query')
def process_query(
    self,
    question: str,
    filters: Optional[Dict[str, Any]] = None,
    top_k: int = 5
) -> Dict[str, Any]:
    """
    비동기 질의응답 처리 (선택사항)
    
    Args:
        question: 사용자 질문
        filters: 메타데이터 필터
        top_k: 반환할 최대 결과 수
        
    Returns:
        답변 결과
    """
    try:
        start_time = time.time()
        
        logger.info(f"[Task {self.request.id}] 질의응답 처리 시작: {question}")
        
        rag = get_rag_pipeline()
        
        # 질의응답 처리
        result = rag.query(
            question=question,
            filters=filters or {},
            top_k=top_k
        )
        
        processing_time = time.time() - start_time
        logger.info(f"[Task {self.request.id}] 질의응답 완료 ({processing_time:.2f}초)")
        
        return {
            'status': 'completed',
            'answer': result.get('answer', ''),
            'sources': result.get('sources', []),
            'processing_time': processing_time,
            'metadata': result.get('metadata', {})
        }
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = str(e)
        logger.error(f"[Task {self.request.id}] 질의응답 실패: {error_msg}")
        
        return {
            'status': 'failed',
            'error': error_msg,
            'processing_time': processing_time
        }


@celery_app.task(bind=True, name='backend.tasks.cleanup_old_tasks')
def cleanup_old_tasks(self):
    """
    오래된 작업 정리 (주기적으로 실행)
    """
    logger.info("오래된 작업 정리 중...")
    # Redis에서 자동으로 TTL 기반 삭제
    return {'status': 'completed', 'message': 'Cleanup completed'}

