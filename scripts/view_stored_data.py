"""
저장된 RAG 데이터 조회 스크립트
"""
import pickle
from pathlib import Path

metadata_path = Path("data/vector_store/metadata.pkl")

if metadata_path.exists():
    with open(metadata_path, 'rb') as f:
        data = pickle.load(f)
    
    print("\n" + "="*70)
    print("RAG 시스템에 저장된 데이터")
    print("="*70)
    
    print(f"\n[시스템 정보]")
    print(f"  임베딩 차원: {data.get('embedding_dim', 'N/A')}")
    print(f"  인덱스 타입: {data.get('index_type', 'N/A')}")
    print(f"  총 청크 수: {len(data.get('documents', []))}")
    
    documents = data.get('documents', [])
    
    print(f"\n[문서 목록]")
    doc_names = {}
    for doc in documents:
        meta = doc.metadata
        doc_name = meta.get('doc_name', 'Unknown')
        if doc_name not in doc_names:
            doc_names[doc_name] = []
        doc_names[doc_name].append(meta.get('chunk_id', -1))
    
    for i, (doc_name, chunk_ids) in enumerate(doc_names.items(), 1):
        print(f"  {i}. {doc_name}")
        print(f"     - 청크 수: {len(chunk_ids)}개")
        print(f"     - 청크 ID: {sorted(chunk_ids)}")
    
    print(f"\n[청크 상세 정보]")
    for doc in documents:
        meta = doc.metadata
        print(f"\n  청크 {meta.get('chunk_id', '?')}: {meta.get('doc_name', 'Unknown')}")
        print(f"    - 파일 타입: {meta.get('file_type', 'N/A')}")
        print(f"    - 청크 크기: {meta.get('chunk_size', 'N/A')}자")
        print(f"    - 내용 미리보기:")
        content = doc.page_content[:200].replace('\n', ' ')
        print(f"      {content}...")
    
    print("\n" + "="*70)
    
    # 파일 크기 정보
    faiss_path = Path("data/vector_store/faiss_index.bin")
    if faiss_path.exists():
        faiss_size = faiss_path.stat().st_size
        print(f"\n[저장 파일 정보]")
        print(f"  faiss_index.bin: {faiss_size:,} bytes ({faiss_size/1024:.1f} KB)")
        print(f"  metadata.pkl: {metadata_path.stat().st_size:,} bytes ({metadata_path.stat().st_size/1024:.1f} KB)")
        print(f"  총 크기: {(faiss_size + metadata_path.stat().st_size)/1024:.1f} KB")
    
    print("\n" + "="*70)

else:
    print("\n⚠ 저장된 데이터가 없습니다.")
    print("먼저 'python main.py add' 또는 'python test_rag.py'를 실행하세요.")

