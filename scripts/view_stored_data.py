"""
저장된 RAG 데이터 조회 스크립트 (ChromaDB 버전)
"""

import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.vector_store import VectorStore
import config


def main():
    """저장된 벡터 저장소 데이터 조회"""
    
    try:
        # 벡터 저장소 로드
        vs = VectorStore.load(persist_dir=config.VECTOR_STORE_DIR)
        
        print("\n" + "="*70)
        print("ChromaDB 벡터 저장소에 저장된 데이터")
        print("="*70)
        
        # 기본 정보
        stats = vs.get_stats()
        collection_info = vs.get_collection_info()
        
        print(f"\n[시스템 정보]")
        print(f"  벡터 저장소 타입: {stats['vector_store_type']}")
        print(f"  임베딩 차원: {stats['embedding_dim']}")
        print(f"  총 청크 수: {stats['total_documents']}")
        
        print(f"\n[컬렉션 정보]")
        print(f"  컬렉션명: {collection_info['name']}")
        print(f"  문서 수: {collection_info['count']}")
        print(f"  메타데이터: {collection_info['metadata']}")
        
        # 저장된 문서 샘플 조회
        print(f"\n[저장된 문서 샘플 (최대 10개)]")
        
        all_docs = vs.collection.get(limit=10)
        
        if all_docs['documents']:
            for i, doc_text in enumerate(all_docs['documents'], 1):
                metadata = all_docs['metadatas'][i-1] if all_docs['metadatas'] else {}
                
                print(f"\n  {i}. 청크 ID: {all_docs['ids'][i-1]}")
                if metadata:
                    print(f"     메타데이터:")
                    for key, value in metadata.items():
                        print(f"       - {key}: {value}")
                
                # 내용 미리보기 (첫 100자)
                preview = doc_text[:100].replace('\n', ' ')
                print(f"     내용 미리보기: {preview}...")
        else:
            print("  데이터가 없습니다.")
        
        # 저장소 경로 정보
        print(f"\n[저장소 정보]")
        vector_store_path = Path(config.VECTOR_STORE_DIR)
        if vector_store_path.exists():
            import os
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(vector_store_path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    total_size += os.path.getsize(filepath)
            
            print(f"  저장소 위치: {vector_store_path}")
            print(f"  총 크기: {total_size / (1024*1024):.2f} MB")
            print(f"  파일 수: {len([f for f in vector_store_path.rglob('*') if f.is_file()])}")
        
        print("\n" + "="*70)
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        print("\n먼저 'python3 auto_add.py --all'로 문서를 추가하세요.")


if __name__ == "__main__":
    main()
