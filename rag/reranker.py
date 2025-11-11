"""
Reranker 모듈
검색된 문서를 재정렬하여 정확도 향상
"""

from typing import List, Tuple
from sentence_transformers import CrossEncoder
import numpy as np
from langchain_core.documents import Document
import config
from loguru import logger


class DocumentReranker:
    """BGE Reranker를 사용한 문서 재정렬"""
    
    def __init__(
        self,
        model_name: str = config.RERANKER_MODEL,
        device: str = None
    ):
        """
        Args:
            model_name: Reranker 모델 이름
            device: 실행 장치 ('cuda', 'cpu' 또는 None=자동)
        """
        self.model_name = model_name
        
        logger.info(f"Reranker 모델 로딩 중: {model_name}")
        
        try:
            # CrossEncoder 초기화
            if device:
                self.model = CrossEncoder(model_name, device=device)
            else:
                self.model = CrossEncoder(model_name)
            
            logger.info(f"Reranker 로드 완료: {model_name}")
            
        except Exception as e:
            logger.error(f"Reranker 로딩 실패: {e}")
            raise
    
    def rerank(
        self,
        query: str,
        documents: List[Tuple[Document, float]],
        top_k: int = None
    ) -> List[Tuple[Document, float]]:
        """
        질문과 문서 쌍을 재정렬
        
        Args:
            query: 질문 텍스트
            documents: (Document, score) 튜플 리스트
            top_k: 반환할 상위 문서 수 (None이면 전체)
        
        Returns:
            재정렬된 (Document, rerank_score) 튜플 리스트
        """
        if not documents:
            logger.warning("재정렬할 문서가 없습니다")
            return []
        
        # 질문-문서 쌍 생성
        pairs = []
        for doc, _ in documents:
            pairs.append([query, doc.page_content])
        
        logger.info(f"Reranking 중: {len(pairs)}개 문서")
        
        # Reranker로 점수 계산
        scores = self.model.predict(pairs)
        
        # 점수와 문서 매핑
        reranked = []
        for i, (doc, _) in enumerate(documents):
            reranked.append((doc, float(scores[i])))
        
        # 점수 기준 내림차순 정렬 (높을수록 관련성 높음)
        reranked.sort(key=lambda x: x[1], reverse=True)
        
        # top_k 적용
        if top_k:
            reranked = reranked[:top_k]
        
        logger.info(f"Reranking 완료: {len(reranked)}개 문서 반환")
        
        # 점수 범위 로깅
        if reranked:
            scores_range = [score for _, score in reranked]
            logger.info(
                f"Rerank 점수 범위: "
                f"최고={max(scores_range):.4f}, "
                f"최저={min(scores_range):.4f}"
            )
        
        return reranked
    
    def rerank_with_threshold(
        self,
        query: str,
        documents: List[Tuple[Document, float]],
        threshold: float = config.RERANK_THRESHOLD,
        top_k: int = None
    ) -> List[Tuple[Document, float]]:
        """
        임계값 기반 재정렬
        
        Args:
            query: 질문 텍스트
            documents: (Document, score) 튜플 리스트
            threshold: 최소 점수 임계값
            top_k: 반환할 상위 문서 수
        
        Returns:
            임계값 이상의 재정렬된 문서 리스트
        """
        # 재정렬
        reranked = self.rerank(query, documents, top_k=None)
        
        # 임계값 필터링
        filtered = [
            (doc, score) for doc, score in reranked 
            if score >= threshold
        ]
        
        logger.info(
            f"임계값 필터링: {len(reranked)}개 → {len(filtered)}개 "
            f"(threshold={threshold})"
        )
        
        # top_k 적용
        if top_k:
            filtered = filtered[:top_k]
        
        return filtered
    
    def compare_scores(
        self,
        query: str,
        documents: List[Tuple[Document, float]]
    ) -> List[dict]:
        """
        원본 검색 점수와 Rerank 점수 비교
        
        Args:
            query: 질문 텍스트
            documents: (Document, original_score) 튜플 리스트
        
        Returns:
            비교 결과 리스트
        """
        if not documents:
            return []
        
        # Rerank 수행
        reranked = self.rerank(query, documents, top_k=None)
        
        # 원본 순위 맵 생성
        original_rank = {
            id(doc): (i, score) 
            for i, (doc, score) in enumerate(documents)
        }
        
        # 비교 결과 생성
        comparison = []
        for new_rank, (doc, rerank_score) in enumerate(reranked):
            old_rank, old_score = original_rank[id(doc)]
            
            comparison.append({
                'doc_name': doc.metadata.get('doc_name', 'Unknown'),
                'chunk_id': doc.metadata.get('chunk_id', -1),
                'original_rank': old_rank + 1,
                'original_score': old_score,
                'rerank_rank': new_rank + 1,
                'rerank_score': rerank_score,
                'rank_change': old_rank - new_rank,
                'content_preview': doc.page_content[:100] + "..."
            })
        
        return comparison


def test_reranker():
    """Reranker 테스트"""
    from langchain_core.documents import Document
    
    # 테스트 데이터
    query = "강남구 자동차 등록대수는?"
    
    docs = [
        (Document(
            page_content="2024년 강남구의 자동차 등록대수는 270,479대입니다.",
            metadata={'doc_name': 'test1', 'chunk_id': 0}
        ), 0.5),
        (Document(
            page_content="서울시 전체 인구는 약 1000만명입니다.",
            metadata={'doc_name': 'test2', 'chunk_id': 1}
        ), 0.4),
        (Document(
            page_content="강남구는 서울특별시 남동부에 위치한 자치구입니다.",
            metadata={'doc_name': 'test3', 'chunk_id': 2}
        ), 0.6),
    ]
    
    # Reranker 초기화
    reranker = DocumentReranker()
    
    # 재정렬
    print("\n=== 원본 순서 (벡터 검색) ===")
    for i, (doc, score) in enumerate(docs, 1):
        print(f"{i}. (score={score:.3f}) {doc.page_content[:50]}...")
    
    reranked = reranker.rerank(query, docs)
    
    print("\n=== Rerank 후 ===")
    for i, (doc, score) in enumerate(reranked, 1):
        print(f"{i}. (score={score:.3f}) {doc.page_content[:50]}...")
    
    # 비교
    comparison = reranker.compare_scores(query, docs)
    print("\n=== 순위 변화 ===")
    for item in comparison:
        print(
            f"{item['original_rank']} → {item['rerank_rank']} "
            f"(change: {item['rank_change']:+d}) - {item['doc_name']}"
        )


if __name__ == "__main__":
    test_reranker()


