"""
벡터 저장소 모듈
Chroma를 사용한 벡터 인덱싱 및 검색
"""

from typing import List, Tuple, Dict, Optional
import numpy as np
import chromadb
from pathlib import Path
from langchain_core.documents import Document
import config
from loguru import logger


class VectorStore:
    """Chroma 벡터 저장소 클래스"""
    
    def __init__(
        self,
        embedding_dim: int = config.EMBEDDING_DIM,
        persist_dir: Path = config.VECTOR_STORE_DIR
    ):
        """
        Args:
            embedding_dim: 임베딩 차원 (참고용, Chroma가 자동 관리)
            persist_dir: 데이터 저장 디렉토리
        """
        self.embedding_dim = embedding_dim
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        # Chroma 클라이언트 초기화 (새로운 API)
        # PersistentClient: 로컬 저장소를 사용하는 클라이언트
        self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        
        # 컬렉션 초기화 (기존에 있으면 로드, 없으면 생성)
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "l2"}  # L2 거리 사용 (FAISS와 동일)
        )
        
        logger.info(f"Chroma VectorStore 초기화: dir={self.persist_dir}, dim={embedding_dim}")
        logger.info(f"컬렉션 크기: {self.collection.count()}개 문서")
    
    def add_documents(
        self,
        documents: List[Document],
        embeddings: np.ndarray
    ):
        """
        문서와 임베딩을 컬렉션에 추가
        
        Args:
            documents: Document 리스트
            embeddings: 임베딩 벡터 배열 (shape: [n, dim])
        """
        if len(documents) != len(embeddings):
            raise ValueError("문서 수와 임베딩 수가 일치하지 않습니다")
        
        if len(documents) == 0:
            logger.warning("추가할 문서가 없습니다")
            return
        
        # Chroma에 추가할 데이터 준비
        ids = []
        metadatas = []
        documents_text = []
        embeddings_list = []
        
        # 현재 컬렉션 크기를 기반으로 ID 생성
        start_id = self.collection.count()
        
        for i, doc in enumerate(documents):
            doc_id = f"doc_{start_id + i}"
            ids.append(doc_id)
            documents_text.append(doc.page_content)
            metadatas.append(doc.metadata if doc.metadata else {})
            embeddings_list.append(embeddings[i].tolist())  # numpy array → list
        
        # Chroma 컬렉션에 추가
        self.collection.add(
            ids=ids,
            embeddings=embeddings_list,
            documents=documents_text,
            metadatas=metadatas
        )
        
        logger.info(f"문서 추가 완료: {len(documents)}개 (총 {self.collection.count()}개)")
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = config.TOP_K,
        threshold: Optional[float] = None,
        where_filter: Optional[Dict] = None
    ) -> List[Tuple[Document, float]]:
        """
        유사 문서 검색
        
        Args:
            query_embedding: 질문 임베딩 벡터
            top_k: 반환할 문서 수
            threshold: 유사도 임계값 (L2 거리 기준, 선택사항)
            where_filter: 메타데이터 필터 (사전필터링용)
        
        Returns:
            (Document, score) 튜플 리스트
        """
        if self.collection.count() == 0:
            logger.warning("컬렉션이 비어있습니다")
            return []
        
        # 임베딩 변환
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        query_embedding_list = query_embedding[0].tolist()  # numpy array → list
        
        # Chroma 검색 (사전필터링 포함)
        results = self.collection.query(
            query_embeddings=[query_embedding_list],
            n_results=top_k,
            where=where_filter if where_filter else None
        )
        
        # 결과 정리
        output = []
        
        if not results['documents'] or not results['documents'][0]:
            logger.warning("검색 결과 없음")
            return []
        
        for i, doc_text in enumerate(results['documents'][0]):
            metadata = results['metadatas'][0][i] if results['metadatas'] else {}
            distance = results['distances'][0][i]
            
            # 임계값 체크 (선택사항)
            if threshold is not None and distance > threshold:
                continue
            
            # Document 객체 생성
            doc = Document(page_content=doc_text, metadata=metadata)
            output.append((doc, float(distance)))
        
        logger.info(f"검색 완료: {len(output)}개 문서 반환")
        return output
    
    def save(self, save_dir: Optional[Path] = None):
        """
        데이터 저장 (Chroma는 자동 저장, 이 메서드는 명시적 저장용)
        
        Args:
            save_dir: 저장 디렉토리 (생략 시 초기화 시 설정한 디렉토리)
        """
        # Chroma는 자동으로 persist_directory에 저장하므로
        # 명시적 저장은 필요 없음. 로그만 출력
        logger.info(f"Chroma 데이터 저장 (자동 영구 저장): {self.persist_dir}")
    
    @classmethod
    def load(cls, load_dir: Path = config.VECTOR_STORE_DIR):
        """
        저장된 컬렉션과 메타데이터 로드
        
        Args:
            load_dir: 로드 디렉토리
        
        Returns:
            VectorStore 인스턴스
        """
        load_dir = Path(load_dir)
        
        if not load_dir.exists():
            logger.warning(f"벡터 저장소 디렉토리가 없습니다: {load_dir}")
            return cls(persist_dir=load_dir)
        
        logger.info(f"벡터 저장소 로드 중: {load_dir}")
        store = cls(persist_dir=load_dir)
        logger.info(f"벡터 저장소 로드 완료: {store.collection.count()}개 문서")
        
        return store
    
    def get_stats(self) -> Dict:
        """저장소 통계 반환"""
        return {
            'total_documents': self.collection.count(),
            'embedding_dim': self.embedding_dim,
            'vector_store_type': 'chromadb'
        }
    
    def delete_all(self):
        """모든 문서 삭제 (개발/테스트용)"""
        all_docs = self.collection.get()
        if all_docs['ids']:
            self.collection.delete(ids=all_docs['ids'])
            logger.warning(f"모든 문서 삭제 완료: {len(all_docs['ids'])}개")
    
    def get_collection_info(self) -> Dict:
        """컬렉션 상세 정보 반환"""
        return {
            'name': self.collection.name,
            'count': self.collection.count(),
            'metadata': self.collection.metadata if hasattr(self.collection, 'metadata') else {}
        }
    
    def save(self):
        """벡터 저장소 저장 (Chroma는 자동으로 저장됨)"""
        logger.info(f"Chroma 데이터 자동 저장 (persist_dir: {self.persist_dir})")
    
    @classmethod
    def load(cls, persist_dir: Path = config.VECTOR_STORE_DIR):
        """기존 벡터 저장소 로드"""
        logger.info(f"Chroma 벡터 저장소 로드 중: {persist_dir}")
        return cls(persist_dir=persist_dir)


def test_vector_store():
    """벡터 저장소 테스트"""
    from rag.embedder import DocumentEmbedder
    from langchain_core.documents import Document
    
    # 임베더 초기화
    embedder = DocumentEmbedder()
    
    # 테스트 문서
    docs = [
        Document(page_content="디지털정부 발전에 기여한 공무원을 포상합니다.", 
                 metadata={"doc_id": 1, "doc_type": "공지"}),
        Document(page_content="포상 대상은 공무원과 민간인입니다.", 
                 metadata={"doc_id": 2, "doc_type": "공지"}),
        Document(page_content="총 50명 내외를 선발합니다.", 
                 metadata={"doc_id": 3, "doc_type": "공지"}),
    ]
    
    # 임베딩 생성
    embeddings = embedder.embed_documents(docs)
    
    # 벡터 저장소 생성 (테스트용)
    store = VectorStore(embedding_dim=embedder.get_embedding_dim())
    store.add_documents(docs, embeddings)
    
    print(f"\n=== Chroma 벡터 저장소 테스트 ===")
    print(f"저장된 문서 수: {store.collection.count()}")
    print(f"컬렉션 정보: {store.get_collection_info()}")
    
    # 검색 테스트
    query = "포상 대상자는 누구인가요?"
    query_embedding = embedder.embed_query(query)
    results = store.search(query_embedding, top_k=2)
    
    print(f"\n질문: {query}")
    print(f"검색 결과:")
    for i, (doc, score) in enumerate(results):
        print(f"\n{i+1}. (L2 거리: {score:.4f})")
        print(f"   내용: {doc.page_content}")
        print(f"   메타데이터: {doc.metadata}")
    
    # 사전필터링 테스트 (메타데이터 기반)
    print(f"\n\n=== 사전필터링 테스트 ===")
    print(f"필터: doc_type = '공지'")
    filtered_results = store.search(
        query_embedding, 
        top_k=2,
        where_filter={"doc_type": {"$eq": "공지"}}
    )
    print(f"필터링된 검색 결과: {len(filtered_results)}개")
    
    # 저장/로드 테스트
    print(f"\n\n=== 저장/로드 테스트 ===")
    print(f"저장 중...")
    store.save()
    
    print(f"로드 중...")
    loaded_store = VectorStore.load()
    print(f"로드된 문서 수: {loaded_store.collection.count()}")
    print(f"로드 완료!")


if __name__ == "__main__":
    test_vector_store()
