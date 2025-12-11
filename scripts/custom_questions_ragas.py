"""
커스텀 질문 리스트로 RAGAS 평가
사용자가 직접 작성한 질문 파일로 평가
"""

import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.pipeline import RAGPipeline
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy
from datasets import Dataset
import time

def evaluate_custom_questions(questions_file: str = None):
    """
    커스텀 질문 파일로 평가
    
    질문 파일 형식:
    [
        {"question": "감사규칙의 목적은?", "ground_truth": "감사 업무를 규정함"},
        {"question": "계약서에 뭐가 필요해?", "ground_truth": "계약 당사자, 금액 등"}
    ]
    """
    
    # 질문 파일 입력
    if not questions_file:
        questions_file = input("질문 파일 경로를 입력하세요 (예: my_questions.json): ").strip()
    
    questions_file = Path(questions_file)
    
    if not questions_file.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {questions_file}")
        print("\n질문 파일 생성 예시:")
        print("""
[
  {
    "question": "감사규칙의 목적은 무엇인가요?",
    "ground_truth": "감사 업무를 규정하고 독립성을 확보하기 위함"
  },
  {
    "question": "계약서에 필수로 포함되어야 할 항목은?",
    "ground_truth": "계약 당사자, 목적, 금액, 기간 등"
  }
]
        """)
        return
    
    # 질문 로드
    try:
        with open(questions_file, 'r', encoding='utf-8') as f:
            custom_questions = json.load(f)
    except Exception as e:
        print(f"❌ 파일 읽기 실패: {e}")
        return
    
    print(f"\n✅ {len(custom_questions)}개 질문 로드 완료")
    
    # RAG 파이프라인 초기화
    print("\nRAG 파이프라인 초기화 중...")
    pipeline = RAGPipeline(load_existing=True)
    print("✅ 준비 완료\n")
    
    # 질의 및 평가 데이터 수집
    questions = []
    answers = []
    contexts_list = []
    ground_truths = []
    response_times = []
    
    print("="*70)
    print("질의 실행 중...")
    print("="*70)
    
    for i, item in enumerate(custom_questions, 1):
        question = item.get("question", "")
        ground_truth = item.get("ground_truth", "정답 미제공")
        
        print(f"\n[{i}/{len(custom_questions)}] {question}")
        
        # RAG 질의
        start_time = time.time()
        result = pipeline.query(question, top_k=5)
        elapsed = time.time() - start_time
        
        answer = result.get("answer", "")
        sources = result.get("sources", [])
        
        print(f"  답변: {answer[:100]}...")
        print(f"  응답 시간: {elapsed:.2f}초")
        
        # 데이터 저장
        questions.append(question)
        answers.append(answer)
        ground_truths.append([ground_truth])
        response_times.append(elapsed)
        
        contexts = [src['content'] for src in sources if src.get('content')]
        contexts_list.append(contexts if contexts else ["정보 없음"])
    
    # RAGAS 평가
    print("\n\n" + "="*70)
    print("RAGAS 평가 실행 중...")
    print("="*70)
    
    data = {
        "question": questions,
        "contexts": contexts_list,
        "answer": answers,
        "ground_truths": ground_truths
    }
    dataset = Dataset.from_dict(data)
    
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
        
        # 응답 시간
        avg_time = sum(response_times) / len(response_times)
        print(f"\n응답 속도:")
        print(f"  평균: {avg_time:.2f}초")
        print(f"  최소: {min(response_times):.2f}초")
        print(f"  최대: {max(response_times):.2f}초")
        
        # RAGAS 지표
        print(f"\nRAGAS 지표:")
        faithfulness_score = result.get('faithfulness', 0)
        relevancy_score = result.get('answer_relevancy', 0)
        
        print(f"  Faithfulness (신뢰성):     {faithfulness_score:.3f}")
        print(f"  Answer Relevancy (관련성): {relevancy_score:.3f}")
        
        avg_score = (faithfulness_score + relevancy_score) / 2
        print(f"  평균 점수:                  {avg_score:.3f}")
        
        # 판정
        print("\n판정:")
        if avg_score >= 0.85:
            print("  ✅ 우수 - 프로덕션 준비 완료")
        elif avg_score >= 0.70:
            print("  ⚠️ 보통 - 개선 권장")
        else:
            print("  ❌ 개선 필요 - 시스템 점검 필요")
        
        # 결과 저장
        output_file = questions_file.parent / f"{questions_file.stem}_result.json"
        result_data = {
            "evaluation_time": sum(response_times),
            "avg_response_time": avg_time,
            "faithfulness": faithfulness_score,
            "answer_relevancy": relevancy_score,
            "average_score": avg_score,
            "details": [
                {
                    "question": q,
                    "answer": a,
                    "ground_truth": gt[0],
                    "response_time": rt
                }
                for q, a, gt, rt in zip(questions, answers, ground_truths, response_times)
            ]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n결과 저장: {output_file}")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ RAGAS 평가 실패: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="커스텀 질문으로 RAGAS 평가")
    parser.add_argument("--file", help="질문 파일 경로 (JSON)")
    
    args = parser.parse_args()
    evaluate_custom_questions(args.file)


