"""
대화형 RAGAS 평가
사용자가 직접 질문하고 답변에 대해 즉시 평가
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.pipeline import RAGPipeline
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy
from datasets import Dataset
import time

def interactive_ragas_evaluation():
    """대화형 RAGAS 평가"""
    
    print("="*70)
    print("대화형 RAGAS 평가")
    print("="*70)
    print("\n질문을 입력하면 RAG 시스템이 답변하고, RAGAS로 평가합니다.")
    print("종료하려면 'quit' 또는 'exit'를 입력하세요.\n")
    
    # RAG 파이프라인 초기화
    print("RAG 파이프라인 초기화 중...")
    pipeline = RAGPipeline(load_existing=True)
    print("✅ 준비 완료\n")
    
    # 평가 데이터 수집
    questions = []
    answers = []
    contexts_list = []
    ground_truths = []
    response_times = []
    
    while True:
        print("-"*70)
        question = input("\n질문: ").strip()
        
        if question.lower() in ['quit', 'exit', 'q']:
            break
        
        if not question:
            print("질문을 입력해주세요.")
            continue
        
        # 정답(Ground Truth) 입력
        print("\n[정답 입력]")
        print("(평가를 위해 기대하는 답변을 입력하세요. 모르면 Enter)")
        ground_truth = input("정답: ").strip()
        
        if not ground_truth:
            ground_truth = "정답 미제공"
        
        # RAG 질의 실행
        print("\n답변 생성 중...")
        start_time = time.time()
        result = pipeline.query(question, top_k=5)
        elapsed = time.time() - start_time
        
        answer = result.get("answer", "")
        sources = result.get("sources", [])
        
        # 결과 출력
        print("\n" + "="*70)
        print("📝 답변:")
        print("="*70)
        print(answer)
        print(f"\n⏱️ 응답 시간: {elapsed:.2f}초")
        
        print(f"\n📚 출처: ({len(sources)}개)")
        for i, src in enumerate(sources[:3], 1):
            doc_name = src['metadata'].get('doc_name', 'N/A')
            hierarchy = src['metadata'].get('hierarchy_path', '')
            print(f"  [{i}] {doc_name}")
            if hierarchy:
                print(f"      위치: {hierarchy}")
            print(f"      내용: {src['content'][:100]}...")
        
        # 평가 데이터 저장
        questions.append(question)
        answers.append(answer)
        ground_truths.append([ground_truth])
        response_times.append(elapsed)
        
        # 검색된 문서들
        contexts = [src['content'] for src in sources if src.get('content')]
        contexts_list.append(contexts if contexts else ["정보 없음"])
        
        # 계속 여부 확인
        print("\n" + "-"*70)
        continue_choice = input("\n다른 질문을 하시겠습니까? (y/n): ").strip().lower()
        if continue_choice == 'n':
            break
    
    # 평가 실행
    if not questions:
        print("\n평가할 질문이 없습니다.")
        return
    
    print("\n\n" + "="*70)
    print("RAGAS 평가 시작")
    print("="*70)
    print(f"총 {len(questions)}개 질문 평가 중...\n")
    
    # Dataset 생성
    data = {
        "question": questions,
        "contexts": contexts_list,
        "answer": answers,
        "ground_truths": ground_truths
    }
    dataset = Dataset.from_dict(data)
    
    # RAGAS 평가
    try:
        result = evaluate(
            dataset,
            metrics=[faithfulness, answer_relevancy]
        )
        
        # 결과 출력
        print("\n" + "="*70)
        print("RAGAS 평가 결과")
        print("="*70)
        
        print(f"\n총 질문: {len(questions)}개")
        
        # 응답 시간 통계
        avg_time = sum(response_times) / len(response_times)
        print(f"\n응답 속도:")
        print(f"  평균: {avg_time:.2f}초")
        print(f"  최소: {min(response_times):.2f}초")
        print(f"  최대: {max(response_times):.2f}초")
        
        # RAGAS 지표
        print(f"\nRAGAS 지표:")
        print(f"  Faithfulness (신뢰성):     {result['faithfulness']:.3f}")
        print(f"  Answer Relevancy (관련성): {result['answer_relevancy']:.3f}")
        
        # 평균
        avg_score = (result['faithfulness'] + result['answer_relevancy']) / 2
        print(f"  평균 점수:                  {avg_score:.3f}")
        
        # 판정
        print("\n판정:")
        if avg_score >= 0.85:
            print("  ✅ 우수 - 프로덕션 준비 완료")
        elif avg_score >= 0.70:
            print("  ⚠️ 보통 - 개선 권장")
        else:
            print("  ❌ 개선 필요 - 시스템 점검 필요")
        
        # 질문별 상세 결과
        print("\n" + "="*70)
        print("질문별 상세 결과")
        print("="*70)
        for i, (q, a) in enumerate(zip(questions, answers), 1):
            print(f"\n[{i}] {q}")
            print(f"    답변: {a[:100]}...")
            print(f"    응답 시간: {response_times[i-1]:.2f}초")
        
        print("\n" + "="*70)
        
    except Exception as e:
        print(f"\n❌ RAGAS 평가 실패: {e}")
        print("\n입력한 질문과 답변:")
        for i, (q, a) in enumerate(zip(questions, answers), 1):
            print(f"\n[{i}] Q: {q}")
            print(f"    A: {a[:150]}...")


if __name__ == "__main__":
    interactive_ragas_evaluation()


