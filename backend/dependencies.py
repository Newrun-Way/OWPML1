"""
의존성 주입
RAG 시스템 인스턴스 관리
"""

import sys
import logging
from pathlib import Path
from typing import Optional

# 프로젝트 루트 경로 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from rag.pipeline import RAGPipeline
import config

logger = logging.getLogger(__name__)

# RAG 파이프라인 싱글톤 인스턴스
_rag_instance: Optional[RAGPipeline] = None


def get_rag_pipeline() -> RAGPipeline:
    """
    RAG 파이프라인 인스턴스 반환 
    
    Returns:
        RAGPipeline: RAG 파이프라인 인스턴스
        
    Raises:
        RuntimeError: RAG 시스템 초기화 실패 시
    """
    global _rag_instance
    
    if _rag_instance is None:
        try:
            logger.info("RAG 파이프라인 초기화 중...")
            _rag_instance = RAGPipeline(load_existing=True)
            logger.info("RAG 파이프라인 초기화 완료")
        except Exception as e:
            logger.error(f"RAG 파이프라인 초기화 실패: {e}")
            raise RuntimeError(f"RAG 시스템 초기화 실패: {str(e)}")
    
    return _rag_instance


def reset_rag_pipeline():
    """RAG 파이프라인 인스턴스 리셋 (테스트/디버깅용)"""
    global _rag_instance
    _rag_instance = None
    logger.info("RAG 파이프라인 인스턴스 리셋됨")


def get_project_root() -> Path:
    """프로젝트 루트 경로 반환"""
    return PROJECT_ROOT


def get_config():
    """설정 객체 반환"""
    return config

