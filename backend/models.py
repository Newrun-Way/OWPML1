from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ========================================
# 문서 업로드 관련 모델
# ========================================

class DocumentMetadata(BaseModel):
    """문서 업로드 시 필요한 메타데이터"""
    user_id: str = Field(..., description="사용자 ID")
    dept_id: str = Field(..., description="부서 ID (예: HR, Finance)")
    project_id: str = Field(..., description="프로젝트 ID")
    category: str = Field(default="기타", description="문서 카테고리")


class DocumentUploadResponse(BaseModel):
    """문서 업로드 응답"""
    status: str = Field(..., description="completed / processing / failed")
    doc_id: str = Field(..., description="문서 고유 ID")
    doc_name: str = Field(..., description="문서명")
    summary: Optional[str] = Field(None, description="문서 요약 (3-4줄)")
    chunks: int = Field(..., description="생성된 청크 수")
    processing_time: Optional[float] = Field(None, description="처리 시간 (초)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="메타데이터")
    message: Optional[str] = Field(None, description="상태 메시지")


class TaskStatusResponse(BaseModel):
    """비동기 작업 상태 응답"""
    task_id: str = Field(..., description="작업 ID")
    status: str = Field(..., description="pending / processing / completed / failed")
    progress: int = Field(default=0, description="진행 상황 (0-100)")
    stage: Optional[str] = Field(None, description="현재 단계")
    message: Optional[str] = Field(None, description="상태 메시지")
    result: Optional[Dict[str, Any]] = Field(None, description="완료 시 결과")
    error: Optional[str] = Field(None, description="에러 메시지")


class AsyncUploadResponse(BaseModel):
    """비동기 문서 업로드 즉시 응답"""
    status: str = Field(default="processing", description="processing")
    task_id: str = Field(..., description="작업 ID")
    message: str = Field(..., description="상태 메시지")
    estimated_time: int = Field(default=10, description="예상 처리 시간 (초)")


# ========================================
# 질의응답 관련 모델
# ========================================

class QueryRequest(BaseModel):
    """질의응답 요청"""
    question: str = Field(..., description="사용자 질문", min_length=1, max_length=1000)
    dept_id: Optional[str] = Field(None, description="부서 필터")
    project_id: Optional[str] = Field(None, description="프로젝트 필터")
    category: Optional[str] = Field(None, description="카테고리 필터")
    top_k: int = Field(default=5, description="반환할 최대 결과 수", ge=1, le=20)


class AnswerSource(BaseModel):
    """답변의 출처 정보"""
    index: int = Field(..., description="출처 순서")
    doc_name: str = Field(..., description="문서명")
    chapter_number: Optional[str] = Field(None, description="장 번호")
    chapter_title: Optional[str] = Field(None, description="장 제목")
    article_number: Optional[str] = Field(None, description="조 번호")
    article_title: Optional[str] = Field(None, description="조 제목")
    hierarchy_path: Optional[str] = Field(None, description="계층 경로")
    score: float = Field(..., description="유사도 점수 (0-1)")


class QueryResponse(BaseModel):
    """질의응답 응답"""
    answer: str = Field(..., description="생성된 답변")
    sources: List[AnswerSource] = Field(..., description="출처 정보")
    processing_time: float = Field(..., description="처리 시간 (초)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="추가 메타데이터")


# ========================================
# 문서 정보 조회 관련 모델
# ========================================

class DocumentInfo(BaseModel):
    """문서 정보"""
    doc_id: str = Field(..., description="문서 ID")
    doc_name: str = Field(..., description="문서명")
    summary: Optional[str] = Field(None, description="문서 요약")
    user_id: str = Field(..., description="업로드자 ID")
    dept_id: str = Field(..., description="부서 ID")
    project_id: str = Field(..., description="프로젝트 ID")
    category: str = Field(..., description="카테고리")
    upload_date: str = Field(..., description="업로드 일시")
    chunks: int = Field(..., description="청크 수")
    total_chapters: Optional[int] = Field(None, description="총 장 수")
    total_articles: Optional[int] = Field(None, description="총 조 수")


class DocumentListResponse(BaseModel):
    """문서 목록 응답"""
    documents: List[DocumentInfo] = Field(..., description="문서 목록")
    total: int = Field(..., description="총 문서 수")


class DocumentDeleteResponse(BaseModel):
    """문서 삭제 응답"""
    status: str = Field(..., description="success / failed")
    message: str = Field(..., description="상태 메시지")


# ========================================
# 에러 관련 모델
# ========================================

class ErrorDetail(BaseModel):
    """에러 상세 정보"""
    code: str = Field(..., description="에러 코드")
    message: str = Field(..., description="에러 메시지")
    details: Optional[str] = Field(None, description="상세 정보")
    stage: Optional[str] = Field(None, description="발생 단계")
    retry_possible: bool = Field(default=False, description="재시도 가능 여부")


class ErrorResponse(BaseModel):
    """에러 응답"""
    status: str = Field(default="failed", description="failed")
    error: ErrorDetail = Field(..., description="에러 정보")
    request_id: Optional[str] = Field(None, description="요청 ID")


# ========================================
# 헬스체크 모델
# ========================================

class HealthResponse(BaseModel):
    """헬스체크 응답"""
    status: str = Field(..., description="ok / error")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="응답 시간")
    rag_system: str = Field(..., description="RAG 시스템 상태")
    vector_store: str = Field(..., description="벡터 저장소 상태")

