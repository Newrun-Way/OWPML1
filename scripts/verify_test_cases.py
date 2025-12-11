"""
테스트 케이스 검증 스크립트
실제 문서에서 답변을 찾을 수 있는지 확인
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.pipeline import RAGPipeline

def verify_test_cases(test_cases_path: str = "tests/test_cases_real.json"):
    """테스트 케이스가 실제 문서와 매치되는지 확인"""
    
    # 테스트 케이스 로드
    with open(test_cases_path, 'r', encoding='utf-8') as f:
        test_cases = json.load(f)
    
    print(f"=== 테스트 케이스 검증 ===")
    print(f"총 {len(test_cases)}개 케이스\n")
    
    # RAG 파이프라인 로드
    pipeline = RAGPipeline(load_existing=True)
    
    # 각 질문에 대해 검증
    valid_count = 0
    
    for i, case in enumerate(test_cases[:5]):  # 처음 5개만 샘플 체크
        question = case["question"]
        
        print(f"\n[{i+1}] {case['id']}")
        print(f"질문: {question}")
        
        # 질의 실행
        result = pipeline.query(question, top_k=3)
        
        print(f"답변: {result['answer'][:150]}...")
        
        # 관련 문서 확인
        if result['sources']:
            doc_name = result['sources'][0]['metadata'].get('doc_name', 'N/A')
            score = result['sources'][0].get('score', 0)
            print(f"출처: {doc_name}")
            print(f"관련도: {1 - score:.3f}")  # L2 거리를 관련도로 변환
            
            # 간단한 유효성 체크
            if (1 - score) > 0.5:  # 관련도 50% 이상
                valid_count += 1
                print("✅ 관련 문서 찾음")
            else:
                print("⚠️ 관련도 낮음")
        else:
            print("❌ 관련 문서 없음")
    
    print(f"\n\n=== 검증 결과 ===")
    print(f"유효한 케이스: {valid_count}/5")
    
    if valid_count >= 3:
        print("✅ 테스트 케이스가 실제 문서와 잘 매치됩니다!")
        print("\nRAGAS 평가를 실행하세요:")
        print(f"  python tests/test_ragas_evaluation.py --mode simple --test-cases {test_cases_path}")
    else:
        print("⚠️ 테스트 케이스를 조정해야 합니다.")
        print("실제 문서 내용을 확인하고 테스트 케이스를 수정하세요.")


if __name__ == "__main__":
    verify_test_cases()


