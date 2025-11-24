"""
FastAPI 메인 애플리케이션
비동기 RAG 시스템 API
"""

import logging
import time
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from celery.result import AsyncResult
from models import (
    DocumentMetadata, AsyncUploadResponse, TaskStatusResponse,
    QueryRequest, QueryResponse, DocumentListResponse, DocumentDeleteResponse,
    DocumentInfo, HealthResponse, ErrorResponse
)
from dependencies import get_rag_pipeline, get_project_root
from celery_config import celery_app
from tasks import process_document
import utils
import logging as logging_module

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ========================================
# 라이프사이클 이벤트
# ========================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 라이프사이클 관리
    """
    # 시작 시
    logger.info("FastAPI 애플리케이션 시작")
    try:
        rag = get_rag_pipeline()
        logger.info("RAG 시스템 초기화 완료")
    except Exception as e:
        logger.error(f"RAG 시스템 초기화 실패: {e}")
    
    yield
    
    # 종료 시
    logger.info("FastAPI 애플리케이션 종료")


# ========================================
# FastAPI 앱 생성
# ========================================

app = FastAPI(
    title="RAG System API",
    description="HWP/HWPX 문서 기반 질의응답 시스템",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========================================
# 헬스체크
# ========================================

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """
    서버 및 RAG 시스템 상태 확인
    """
    try:
        rag = get_rag_pipeline()
        rag_status = "ok"
    except Exception as e:
        logger.error(f"RAG 시스템 상태 확인 실패: {e}")
        rag_status = "error"
    
    # 벡터 저장소 상태 확인
    try:
        rag = get_rag_pipeline()
        vector_store_count = rag.vector_store.collection.count()
        vector_store_status = "ok" if vector_store_count >= 0 else "error"
    except Exception as e:
        logger.error(f"벡터 저장소 상태 확인 실패: {e}")
        vector_store_status = "error"
    
    return HealthResponse(
        status="ok" if rag_status == "ok" and vector_store_status == "ok" else "error",
        rag_system=rag_status,
        vector_store=vector_store_status
    )


# ========================================
# 문서 업로드 API (비동기)
# ========================================

@app.post("/api/documents/upload/async", response_model=AsyncUploadResponse)
async def upload_document_async(
    file: UploadFile = File(..., description="HWP/HWPX 파일"),
    user_id: str = None,
    dept_id: str = None,
    project_id: str = None,
    category: str = "기타"
):
    """
    비동기 문서 업로드
    파일을 저장하고 Task를 등록 후 즉시 응답
    
    Args:
        file: 업로드할 파일
        user_id: 사용자 ID
        dept_id: 부서 ID
        project_id: 프로젝트 ID
        category: 문서 카테고리
        
    Returns:
        비동기 업로드 응답 (task_id 포함)
    """
    request_id = utils.generate_request_id()
    logger.info(f"[{request_id}] 비동기 문서 업로드 시작: {file.filename}")
    
    try:
        # 1. 파일 검증
        content = await file.read()
        is_valid, validation_msg = utils.validate_file(file.filename, len(content))
        
        if not is_valid:
            logger.warning(f"[{request_id}] 파일 검증 실패: {validation_msg}")
            raise HTTPException(status_code=400, detail=validation_msg)
        
        # 2. 파일 저장
        upload_path = utils.generate_upload_path(dept_id, file.filename)
        saved_path = await utils.save_upload_file(content, upload_path)
        logger.info(f"[{request_id}] 파일 저장 완료: {saved_path}")
        
        # 3. 사용자 메타데이터 구성
        user_metadata = utils.build_user_metadata(
            user_id=user_id or "anonymous",
            dept_id=dept_id or "unknown",
            project_id=project_id or "default",
            category=category
        )
        
        # 4. 비동기 작업 등록 (Celery Task)
        task = process_document.delay(
            file_path=str(saved_path),
            user_metadata=user_metadata
        )
        logger.info(f"[{request_id}] Celery Task 등록: {task.id}")
        
        return AsyncUploadResponse(
            status="processing",
            task_id=task.id,
            message=f"문서 '{file.filename}' 처리가 시작되었습니다. 진행 상황을 확인하세요.",
            estimated_time=10
        )
        
    except HTTPException as he:
        logger.error(f"[{request_id}] HTTP 예외: {he.detail}")
        raise
    except Exception as e:
        logger.error(f"[{request_id}] 문서 업로드 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"문서 업로드 중 오류가 발생했습니다: {str(e)}"
        )


# ========================================
# 작업 상태 조회 API
# ========================================

@app.get("/api/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
 
    logger.info(f"작업 상태 조회: {task_id}")
    
    try:
        task = AsyncResult(task_id, app=celery_app)
        
        if task.state == 'PENDING':
            return TaskStatusResponse(
                task_id=task_id,
                status="pending",
                progress=0,
                message="작업 대기 중입니다."
            )
        
        elif task.state == 'PROGRESS':
            meta = task.info
            return TaskStatusResponse(
                task_id=task_id,
                status="processing",
                progress=meta.get('progress', 0),
                stage=meta.get('stage', ''),
                message=meta.get('message', '처리 중입니다.')
            )
        
        elif task.state == 'SUCCESS':
            result = task.result
            return TaskStatusResponse(
                task_id=task_id,
                status="completed",
                progress=100,
                stage="완료",
                message="문서 처리가 완료되었습니다.",
                result=result
            )
        
        else:  # FAILURE, REVOKED 등
            error_info = task.info
            return TaskStatusResponse(
                task_id=task_id,
                status="failed",
                progress=0,
                message="작업 처리 중 오류가 발생했습니다.",
                error=str(error_info) if error_info else "Unknown error"
            )
            
    except Exception as e:
        logger.error(f"작업 상태 조회 실패 ({task_id}): {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# 질의응답 API (동기)
# ========================================

@app.post("/api/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    질의응답 처리
    
    Args:
        request: 질의 요청
        
    Returns:
        답변 및 출처 정보
    """
    request_id = utils.generate_request_id()
    logger.info(f"[{request_id}] 질의응답 시작: {request.question}")
    
    start_time = time.time()
    
    try:
        # 1. 필터 구성
        filters = utils.build_query_filters(
            dept_id=request.dept_id,
            project_id=request.project_id,
            category=request.category
        )
        logger.info(f"[{request_id}] 필터: {filters}")
        
        # 2. RAG 시스템에 질의
        rag = get_rag_pipeline()
        result = rag.query(
            question=request.question,
            filters=filters,
            top_k=request.top_k
        )
        
        processing_time = time.time() - start_time
        logger.info(f"[{request_id}] 질의응답 완료 ({processing_time:.2f}초)")
        
        # 3. 응답 포맷팅
        sources = utils.format_answer_sources(result.get('sources', []))
        
        return QueryResponse(
            answer=result.get('answer', '답변을 생성할 수 없습니다.'),
            sources=sources,
            processing_time=processing_time,
            metadata={
                "question": request.question,
                "filters": filters,
                "source_count": len(sources)
            }
        )
        
    except Exception as e:
        logger.error(f"[{request_id}] 질의응답 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"질의응답 처리 중 오류가 발생했습니다: {str(e)}"
        )


# ========================================
# 문서 목록 조회 API
# ========================================

@app.get("/api/documents", response_model=DocumentListResponse)
async def list_documents(
    dept_id: Optional[str] = None,
    project_id: Optional[str] = None,
    category: Optional[str] = None
):
    """
    문서 목록 조회
    
    Args:
        dept_id: 부서 필터
        project_id: 프로젝트 필터
        category: 카테고리 필터
        
    Returns:
        문서 목록
    """
    logger.info("문서 목록 조회")
    
    try:
        rag = get_rag_pipeline()
        
        # 필터 구성
        filters = utils.build_query_filters(
            dept_id=dept_id,
            project_id=project_id,
            category=category
        )
        
        # 메타데이터 조회
        # Note: ChromaDB는 직접 메타데이터만 조회하는 API가 없으므로
        # 전체 컬렉션 통계를 반환
        collection_count = rag.vector_store.collection.count()
        
        # 간단한 문서 정보 반환 (실제 구현은 별도 메타데이터 저장소 필요)
        documents = []
        
        return DocumentListResponse(
            documents=documents,
            total=collection_count
        )
        
    except Exception as e:
        logger.error(f"문서 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# 에러 핸들러
# ========================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP 예외 처리"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "failed",
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """일반 예외 처리"""
    logger.error(f"예상치 못한 오류: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "failed",
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "서버 내부 오류가 발생했습니다."
            }
        }
    )


# ========================================
# 루트 엔드포인트
# ========================================

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "RAG System API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/health",
            "upload_async": "/api/documents/upload/async",
            "task_status": "/api/tasks/{task_id}",
            "query": "/api/query",
            "docs": "/docs"
        }
    }


@app.get("/docs", redirect_slashes=True)
async def get_docs():
    """API 문서"""
    return {
        "message": "Swagger UI로 이동",
        "url": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

