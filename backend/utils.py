"""
유틸리티 함수
파일 관리, 검증, 메타데이터 처리 등
"""

import logging
import os
import uuid
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import aiofiles

import config

logger = logging.getLogger(__name__)


# ========================================
# 파일 관리
# ========================================

def generate_doc_id(doc_name: str) -> str:
    """
    문서 고유 ID 생성
    
    Args:
        doc_name: 문서명
        
    Returns:
        생성된 문서 ID (예: doc_인사규정)
    """
    # 파일명에서 확장자 제거
    name_without_ext = Path(doc_name).stem
    return f"doc_{name_without_ext}"


def generate_upload_path(dept_id: str, filename: str) -> Path:
    """
    업로드 파일 경로 생성
    
    Args:
        dept_id: 부서 ID
        filename: 파일명
        
    Returns:
        업로드할 파일 경로
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    upload_path = config.UPLOADS_DIR / dept_id / f"{timestamp}_{filename}"
    upload_path.parent.mkdir(parents=True, exist_ok=True)
    return upload_path


async def save_upload_file(file_content: bytes, upload_path: Path) -> Path:
    """
    업로드된 파일 저장
    
    Args:
        file_content: 파일 내용
        upload_path: 저장할 경로
        
    Returns:
        저장된 파일 경로
        
    Raises:
        IOError: 파일 저장 실패 시
    """
    try:
        upload_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(upload_path, 'wb') as f:
            await f.write(file_content)
        logger.info(f"파일 저장 완료: {upload_path}")
        return upload_path
    except IOError as e:
        logger.error(f"파일 저장 실패: {e}")
        raise IOError(f"파일 저장 실패: {str(e)}")


def validate_file(filename: str, file_size: int, max_size_mb: int = 10) -> tuple[bool, str]:
    """
    파일 검증
    
    Args:
        filename: 파일명
        file_size: 파일 크기 (바이트)
        max_size_mb: 최대 파일 크기 (MB)
        
    Returns:
        (유효 여부, 메시지)
    """
    # 파일 확장자 확인
    allowed_extensions = {'.hwp', '.hwpx'}
    file_ext = Path(filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        return False, f"지원하지 않는 파일 형식입니다. (지원: {', '.join(allowed_extensions)})"
    
    # 파일 크기 확인
    max_size_bytes = max_size_mb * 1024 * 1024
    if file_size > max_size_bytes:
        return False, f"파일 크기가 {max_size_mb}MB를 초과합니다."
    
    if file_size == 0:
        return False, "빈 파일입니다."
    
    return True, "유효한 파일입니다."


# ========================================
# 메타데이터 관리
# ========================================

def build_user_metadata(
    user_id: str,
    dept_id: str,
    project_id: str,
    category: str = "기타"
) -> Dict[str, Any]:
    """
    사용자 메타데이터 구성
    
    Args:
        user_id: 사용자 ID
        dept_id: 부서 ID
        project_id: 프로젝트 ID
        category: 카테고리
        
    Returns:
        메타데이터 딕셔너리
    """
    return {
        "user_id": user_id,
        "dept_id": dept_id,
        "project_id": project_id,
        "category": category,
        "upload_date": datetime.utcnow().isoformat() + "Z"
    }


def build_query_filters(
    dept_id: Optional[str] = None,
    project_id: Optional[str] = None,
    category: Optional[str] = None,
    chapter_number: Optional[str] = None,
    article_number: Optional[str] = None
) -> Dict[str, Any]:
    """
    ChromaDB 쿼리 필터 구성
    
    Args:
        dept_id: 부서 필터
        project_id: 프로젝트 필터
        category: 카테고리 필터
        chapter_number: 장 번호 필터
        article_number: 조 번호 필터
        
    Returns:
        필터 딕셔너리
    """
    filters = {}
    
    # 단일 필터
    if dept_id:
        filters["dept_id"] = dept_id
    if project_id:
        filters["project_id"] = project_id
    if category:
        filters["category"] = category
    if chapter_number:
        filters["chapter_number"] = chapter_number
    if article_number:
        filters["article_number"] = article_number
    
    return filters


# ========================================
# 에러 처리
# ========================================

def create_error_response(
    code: str,
    message: str,
    details: Optional[str] = None,
    stage: Optional[str] = None,
    retry_possible: bool = False
) -> Dict[str, Any]:
    """
    에러 응답 생성
    
    Args:
        code: 에러 코드
        message: 에러 메시지
        details: 상세 정보
        stage: 발생 단계
        retry_possible: 재시도 가능 여부
        
    Returns:
        에러 응답 딕셔너리
    """
    return {
        "code": code,
        "message": message,
        "details": details,
        "stage": stage,
        "retry_possible": retry_possible
    }


# ========================================
# 요청 ID 생성
# ========================================

def generate_request_id() -> str:
    """
    요청 추적용 고유 ID 생성
    
    Returns:
        생성된 요청 ID
    """
    return str(uuid.uuid4())


# ========================================
# 응답 포맷팅
# ========================================

def format_answer_sources(sources: list) -> list:
    """
    검색 결과를 응답 형식으로 변환
    
    Args:
        sources: 검색된 소스 리스트
        
    Returns:
        포맷팅된 소스 리스트
    """
    formatted_sources = []
    
    for idx, source in enumerate(sources, 1):
        formatted_source = {
            "index": idx,
            "doc_name": source.get("metadata", {}).get("doc_name", "Unknown"),
            "chapter_number": source.get("metadata", {}).get("chapter_number"),
            "chapter_title": source.get("metadata", {}).get("chapter_title"),
            "article_number": source.get("metadata", {}).get("article_number"),
            "article_title": source.get("metadata", {}).get("article_title"),
            "hierarchy_path": source.get("metadata", {}).get("hierarchy_path"),
            "score": source.get("score", 0.0)
        }
        formatted_sources.append(formatted_source)
    
    return formatted_sources

