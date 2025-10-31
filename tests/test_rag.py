"""
RAG 시스템 간단 테스트
교통안전현황분석 리포트 추가 및 질의응답
"""

from pathlib import Path
from rag.pipeline import RAGPipeline

print("\n" + "="*60)
print("RAG 시스템 테스트 시작")
print("="*60)

# 파이프라인 초기화
print("\n1. RAG 파이프라인 초기화 중...")
pipeline = RAGPipeline(load_existing=False)

# 교통안전현황분석 리포트만 추가
print("\n2. 교통안전현황분석 리포트 추가 중...")
doc_path = Path("extracted_results/extracted_교통안전현황분석 리포트")
try:
    pipeline.add_document_from_extract(doc_path)
    print("✓ 문서 추가 완료")
except Exception as e:
    print(f"✗ 문서 추가 실패: {e}")
    exit(1)

# 통계 출력
stats = pipeline.get_stats()
print(f"\n현재 시스템 상태:")
print(f"  - 총 문서 수: {stats['vector_store']['total_documents']}")
print(f"  - 임베딩 모델: {stats['embedding_model']}")
print(f"  - LLM 모델: {stats['llm_model']}")

# 질의응답 테스트
test_questions = [
    "이 문서의 주요 내용은 무엇인가요?",
    "강남구의 자동차 등록대수는 몇 대인가요?",
    "2024년 강남구 순위는 어떻게 되나요?"
]

print("\n" + "="*60)
print("질의응답 테스트")
print("="*60)

for i, question in enumerate(test_questions, 1):
    print(f"\n[질문 {i}] {question}")
    print("-" * 60)
    
    try:
        result = pipeline.query(question)
        print(f"\n답변:")
        print(result['answer'])
        
        if result.get('sources'):
            print(f"\n출처:")
            for source in result['sources'][:2]:  # 상위 2개만
                print(f"  - {source['doc_name']} (청크 {source['chunk_id']})")
        
        print(f"\n처리 시간: {result['processing_time']:.2f}초")
    
    except Exception as e:
        print(f"✗ 오류 발생: {e}")

print("\n" + "="*60)
print("테스트 완료")
print("="*60)

