"""
대화형 RAGAS 평가 스크립트
사용자가 직접 질문을 입력하고 실시간으로 RAG 시스템을 평가합니다.
"""

import os
import sys
import time
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rag.pipeline import RAGPipeline
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
)

# 환경 변수 로드
from dotenv import load_dotenv
load_dotenv()


def print_separator(char="=", length=80):
    """구분선 출력"""
    print(char * length)


def print_header(text):
    """헤더 출력"""
    print_separator()
    print(f"  {text}")
    print_separator()


def interactive_ragas_evaluation():
    """대화형 RAGAS 평가"""
    
    print_header("🤖 대화형 RAGAS 평가 시스템")
    print("\n이 스크립트는 사용자가 직접 질문을 입력하고")
    print("RAG 시스템의 답변을 RAGAS로 평가합니다.\n")
    
    # RAG 파이프라인 초기화
    print("📦 RAG 파이프라인 초기화 중...")
    try:
        pipeline = RAGPipeline()
        print("✅ 파이프라인 로드 완료\n")
    except Exception as e:
        print(f"❌ 파이프라인 로드 실패: {e}")
        return
    
    # OpenAI API 키 확인
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  경고: OPENAI_API_KEY가 설정되지 않았습니다.")
        print("RAGAS 평가를 위해 OpenAI API 키가 필요합니다.\n")
    
    while True:
        print_separator("-")
        print("\n💬 질문을 입력하세요 (종료: 'quit' 또는 'exit')")
        question = input("질문: ").strip()
        
        if question.lower() in ['quit', 'exit', 'q']:
            print("\n👋 평가를 종료합니다.")
            break
        
        if not question:
            print("⚠️  질문을 입력해주세요.\n")
            continue
        
        # Ground Truth 입력 (선택사항)
        print("\n📝 Ground Truth (정답)를 입력하세요 (선택사항, 엔터로 건너뛰기)")
        ground_truth = input("Ground Truth: ").strip()
        
        if not ground_truth:
            ground_truth = None
            print("ℹ️  Ground Truth 없이 평가합니다 (일부 지표 제외)\n")
        
        # RAG 시스템으로 답변 생성
        print("\n🔍 RAG 시스템 처리 중...")
        start_time = time.time()
        
        try:
            result = pipeline.query(question, top_k=5)
            elapsed_time = time.time() - start_time
            
            answer = result.get('answer', '')
            contexts = [doc.page_content for doc in result.get('source_documents', [])]
            
            print(f"✅ 답변 생성 완료 (소요 시간: {elapsed_time:.2f}초)\n")
            
        except Exception as e:
            print(f"❌ 답변 생성 실패: {e}\n")
            continue
        
        # 결과 출력
        print_header("📋 RAG 시스템 답변")
        print(f"\n{answer}\n")
        
        print_header("📚 참조 문서 (Contexts)")
        for i, context in enumerate(contexts[:3], 1):
            print(f"\n[문서 {i}]")
            print(context[:200] + "..." if len(context) > 200 else context)
        
        # RAGAS 평가
        print("\n" + "="*80)
        print("⚖️  RAGAS 평가 중...")
        print("="*80 + "\n")
        
        try:
            # 데이터셋 생성
            data = {
                "question": [question],
                "answer": [answer],
                "contexts": [contexts],
            }
            
            if ground_truth:
                data["ground_truth"] = [ground_truth]
            
            dataset = Dataset.from_dict(data)
            
            # 평가 지표 선택
            metrics = [faithfulness, answer_relevancy]
            
            # 평가 실행
            results = evaluate(dataset, metrics=metrics)
            
            # 결과 출력
            print_header("📊 RAGAS 평가 결과")
            print()
            
            for metric_name, score in results.items():
                if metric_name.startswith('_'):
                    continue
                    
                # 이모지 추가
                if score >= 0.8:
                    emoji = "✅"
                    status = "우수"
                elif score >= 0.6:
                    emoji = "⚠️"
                    status = "보통"
                else:
                    emoji = "❌"
                    status = "개선 필요"
                
                print(f"{metric_name:25s}: {score:.3f}  {emoji} {status}")
            
            print(f"\n응답 시간                   : {elapsed_time:.2f}초")
            
            # 종합 평점
            avg_score = sum(score for name, score in results.items() 
                          if not name.startswith('_')) / len(metrics)
            print(f"\n{'='*60}")
            print(f"종합 평점: {avg_score:.3f}")
            print(f"{'='*60}\n")
            
        except Exception as e:
            print(f"❌ RAGAS 평가 실패: {e}")
            print(f"   오류 상세: {type(e).__name__}\n")
            continue
        
        # 다음 질문으로 이동
        print("\n" + "="*80)
        input("엔터를 눌러 다음 질문으로 이동하세요...")
        print("\n")


if __name__ == "__main__":
    try:
        interactive_ragas_evaluation()
    except KeyboardInterrupt:
        print("\n\n👋 사용자가 평가를 중단했습니다.")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류 발생: {e}")
        import traceback
        traceback.print_exc()

