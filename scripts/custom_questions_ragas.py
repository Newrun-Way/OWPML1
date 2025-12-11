"""
커스텀 질문 리스트를 파일에서 읽어 RAGAS 평가하는 스크립트
"""

import os
import sys
import json
import time
import argparse
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


def load_questions_from_file(file_path: str):
    """
    JSON 파일에서 질문 리스트 로드
    
    파일 형식:
    [
        {
            "question": "질문 내용",
            "ground_truth": "정답 (선택사항)"
        },
        ...
    ]
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        questions = json.load(f)
    
    return questions


def evaluate_custom_questions(questions_file: str, output_file: str = None):
    """커스텀 질문 리스트로 RAGAS 평가"""
    
    print("="*80)
    print("  📋 커스텀 질문 리스트 RAGAS 평가")
    print("="*80)
    print()
    
    # 질문 로드
    print(f"📂 질문 파일 로딩: {questions_file}")
    try:
        questions_data = load_questions_from_file(questions_file)
        print(f"✅ {len(questions_data)}개의 질문을 로드했습니다.\n")
    except FileNotFoundError:
        print(f"❌ 파일을 찾을 수 없습니다: {questions_file}")
        return
    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 오류: {e}")
        return
    
    # RAG 파이프라인 초기화
    print("📦 RAG 파이프라인 초기화 중...")
    try:
        pipeline = RAGPipeline()
        print("✅ 파이프라인 로드 완료\n")
    except Exception as e:
        print(f"❌ 파이프라인 로드 실패: {e}")
        return
    
    # 각 질문에 대해 RAG 시스템 실행
    results_data = {
        "question": [],
        "answer": [],
        "contexts": [],
        "ground_truth": [],
    }
    
    print("="*80)
    print("🔍 RAG 시스템으로 답변 생성 중...")
    print("="*80)
    print()
    
    for i, item in enumerate(questions_data, 1):
        question = item['question']
        ground_truth = item.get('ground_truth', '')
        
        print(f"[{i}/{len(questions_data)}] {question}")
        
        try:
            start_time = time.time()
            result = pipeline.query(question, top_k=5)
            elapsed_time = time.time() - start_time
            
            answer = result.get('answer', '')
            contexts = [doc.page_content for doc in result.get('source_documents', [])]
            
            results_data['question'].append(question)
            results_data['answer'].append(answer)
            results_data['contexts'].append(contexts)
            results_data['ground_truth'].append(ground_truth)
            
            print(f"  ✅ 완료 ({elapsed_time:.2f}초)")
            print(f"  답변: {answer[:100]}...")
            print()
            
        except Exception as e:
            print(f"  ❌ 실패: {e}\n")
            # 실패한 경우 빈 값으로 채우기
            results_data['question'].append(question)
            results_data['answer'].append("")
            results_data['contexts'].append([])
            results_data['ground_truth'].append(ground_truth)
    
    # RAGAS 평가
    print("="*80)
    print("⚖️  RAGAS 평가 실행 중...")
    print("="*80)
    print()
    
    try:
        dataset = Dataset.from_dict(results_data)
        
        # 평가 지표
        metrics = [faithfulness, answer_relevancy]
        
        # 평가 실행
        evaluation_results = evaluate(dataset, metrics=metrics)
        
        # 결과 출력
        print("="*80)
        print("  📊 RAGAS 평가 결과")
        print("="*80)
        print()
        
        for metric_name, score in evaluation_results.items():
            if metric_name.startswith('_'):
                continue
            
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
        
        print()
        print("="*80)
        
        # 결과 저장
        if output_file:
            output_data = {
                "evaluation_results": dict(evaluation_results),
                "details": []
            }
            
            for i in range(len(results_data['question'])):
                output_data['details'].append({
                    "question": results_data['question'][i],
                    "answer": results_data['answer'][i],
                    "ground_truth": results_data['ground_truth'][i],
                    "contexts": results_data['contexts'][i]
                })
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 결과가 저장되었습니다: {output_file}")
        
    except Exception as e:
        print(f"❌ RAGAS 평가 실패: {e}")
        import traceback
        traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(
        description="커스텀 질문 리스트로 RAGAS 평가"
    )
    parser.add_argument(
        "--file",
        type=str,
        default="my_questions.json",
        help="질문이 담긴 JSON 파일 경로"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="평가 결과를 저장할 파일 경로 (선택사항)"
    )
    
    args = parser.parse_args()
    
    evaluate_custom_questions(args.file, args.output)


if __name__ == "__main__":
    main()

