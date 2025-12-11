"""
실제 Vector Store의 문서를 기반으로 테스트 케이스 생성
"""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.pipeline import RAGPipeline

def generate_test_cases_from_docs():
    """실제 문서에서 테스트 케이스 생성"""
    
    # RAG 파이프라인 로드
    pipeline = RAGPipeline(load_existing=True)
    
    # Vector Store 정보 확인
    info = pipeline.vector_store.get_collection_info()
    print(f"Vector Store 정보:")
    print(f"  문서 수: {info['count']}개")
    
    # 샘플 문서 조회
    sample_docs = pipeline.vector_store.collection.peek(limit=10)
    
    print(f"\n저장된 문서 샘플:")
    for i, (doc, metadata) in enumerate(zip(sample_docs['documents'], sample_docs['metadatas'])):
        print(f"\n[{i+1}]")
        print(f"  문서명: {metadata.get('doc_name', 'N/A')}")
        print(f"  내용 미리보기: {doc[:100]}...")
    
    # 테스트 케이스 자동 생성 (예시)
    test_cases = []
    
    # 실제 문서 내용을 기반으로 질문 생성
    for i, (doc, metadata) in enumerate(zip(sample_docs['documents'][:5], sample_docs['metadatas'][:5])):
        doc_name = metadata.get('doc_name', 'unknown')
        content_preview = doc[:200]
        
        # 간단한 규칙 기반 질문 생성
        test_cases.append({
            "id": f"auto_gen_{i+1}",
            "question": f"{doc_name}의 주요 내용은 무엇인가요?",
            "ground_truth": content_preview
        })
    
    # 저장
    output_path = Path("tests/test_cases_auto.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(test_cases, f, ensure_ascii=False, indent=2)
    
    print(f"\n\n자동 생성된 테스트 케이스: {output_path}")
    print(f"총 {len(test_cases)}개 생성")
    
    return test_cases


if __name__ == "__main__":
    generate_test_cases_from_docs()


