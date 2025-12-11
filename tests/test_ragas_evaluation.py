"""
RAGAS 기반 RAG 시스템 평가 테스트
"""

import os
import sys
import json
import time
import pytest
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


class TestRAGASEvaluation:
    """RAGAS 평가 테스트 클래스"""
    
    @pytest.fixture(scope="class")
    def pipeline(self):
        """RAG 파이프라인 fixture"""
        return RAGPipeline()
    
    @pytest.fixture
    def test_cases(self):
        """테스트 케이스 로드"""
        test_cases_file = project_root / "tests" / "test_cases_real.json"
        
        if not test_cases_file.exists():
            pytest.skip("테스트 케이스 파일이 없습니다.")
        
        with open(test_cases_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def test_simple_mode(self, pipeline, test_cases):
        """
        간단 모드: Faithfulness, Answer Relevancy, Response Time만 평가
        """
        print("\n" + "="*80)
        print("  📊 RAGAS 평가 - 간단 모드")
        print("="*80)
        
        # 첫 3개 질문만 테스트
        sample_cases = test_cases[:3]
        
        results_data = {
            "question": [],
            "answer": [],
            "contexts": [],
            "ground_truth": [],
        }
        
        response_times = []
        
        for item in sample_cases:
            question = item['question']
            ground_truth = item.get('ground_truth', '')
            
            print(f"\n질문: {question}")
            
            start_time = time.time()
            result = pipeline.query(question, top_k=5)
            elapsed_time = time.time() - start_time
            response_times.append(elapsed_time)
            
            answer = result.get('answer', '')
            contexts = [doc.page_content for doc in result.get('source_documents', [])]
            
            results_data['question'].append(question)
            results_data['answer'].append(answer)
            results_data['contexts'].append(contexts)
            results_data['ground_truth'].append(ground_truth)
            
            print(f"답변: {answer[:100]}...")
            print(f"응답 시간: {elapsed_time:.2f}초")
        
        # RAGAS 평가
        dataset = Dataset.from_dict(results_data)
        metrics = [faithfulness, answer_relevancy]
        
        evaluation_results = evaluate(dataset, metrics=metrics)
        
        # 결과 출력
        print("\n" + "="*80)
        print("  평가 결과")
        print("="*80)
        
        for metric_name, score in evaluation_results.items():
            if not metric_name.startswith('_'):
                print(f"{metric_name:25s}: {score:.3f}")
        
        avg_response_time = sum(response_times) / len(response_times)
        print(f"{'평균 응답 시간':25s}: {avg_response_time:.2f}초")
        
        # Assertion
        assert evaluation_results['faithfulness'] > 0.5, "Faithfulness가 너무 낮습니다"
        assert evaluation_results['answer_relevancy'] > 0.5, "Answer Relevancy가 너무 낮습니다"
        assert avg_response_time < 5.0, "응답 시간이 너무 깁니다"
    
    def test_full_evaluation(self, pipeline, test_cases):
        """
        전체 평가: 모든 테스트 케이스에 대해 평가
        """
        print("\n" + "="*80)
        print("  📊 RAGAS 평가 - 전체 모드")
        print("="*80)
        
        results_data = {
            "question": [],
            "answer": [],
            "contexts": [],
            "ground_truth": [],
        }
        
        response_times = []
        
        for i, item in enumerate(test_cases, 1):
            question = item['question']
            ground_truth = item.get('ground_truth', '')
            
            print(f"\n[{i}/{len(test_cases)}] {question}")
            
            try:
                start_time = time.time()
                result = pipeline.query(question, top_k=5)
                elapsed_time = time.time() - start_time
                response_times.append(elapsed_time)
                
                answer = result.get('answer', '')
                contexts = [doc.page_content for doc in result.get('source_documents', [])]
                
                results_data['question'].append(question)
                results_data['answer'].append(answer)
                results_data['contexts'].append(contexts)
                results_data['ground_truth'].append(ground_truth)
                
                print(f"  ✅ 완료 ({elapsed_time:.2f}초)")
                
            except Exception as e:
                print(f"  ❌ 실패: {e}")
                results_data['question'].append(question)
                results_data['answer'].append("")
                results_data['contexts'].append([])
                results_data['ground_truth'].append(ground_truth)
        
        # RAGAS 평가
        dataset = Dataset.from_dict(results_data)
        metrics = [faithfulness, answer_relevancy]
        
        evaluation_results = evaluate(dataset, metrics=metrics)
        
        # 결과 출력
        print("\n" + "="*80)
        print("  전체 평가 결과")
        print("="*80)
        
        for metric_name, score in evaluation_results.items():
            if not metric_name.startswith('_'):
                emoji = "✅" if score >= 0.7 else "⚠️" if score >= 0.5 else "❌"
                print(f"{metric_name:25s}: {score:.3f}  {emoji}")
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            print(f"{'평균 응답 시간':25s}: {avg_response_time:.2f}초")
        
        # 결과 저장
        output_file = project_root / "tests" / "ragas_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "evaluation_results": dict(evaluation_results),
                "avg_response_time": avg_response_time if response_times else None,
                "total_questions": len(test_cases),
                "successful_queries": len(response_times)
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 결과 저장: {output_file}")
        
        # Assertion
        assert evaluation_results['faithfulness'] > 0.6, "전체 Faithfulness가 낮습니다"
        assert evaluation_results['answer_relevancy'] > 0.6, "전체 Answer Relevancy가 낮습니다"
    
    def test_compare_modes(self, pipeline):
        """
        비교 모드: 구조 청킹 vs 일반 청킹 비교
        """
        print("\n" + "="*80)
        print("  📊 RAGAS 평가 - 비교 모드")
        print("="*80)
        
        # 샘플 질문
        sample_questions = [
            {
                "question": "감사는 누구에게 보고하나요?",
                "ground_truth": "감사는 대표이사 또는 이사회에 직접 보고합니다."
            },
            {
                "question": "계약 체결 시 전결권자는 누구인가요?",
                "ground_truth": "계약 금액과 유형에 따라 위임전결규칙에서 정한 직급의 담당자가 전결권자입니다."
            }
        ]
        
        # 구조 청킹으로 평가
        print("\n--- 구조 청킹 평가 ---")
        structure_results = self._evaluate_with_mode(pipeline, sample_questions, use_structure=True)
        
        # 일반 청킹으로 평가 (비교를 위해 파이프라인 재생성)
        print("\n--- 일반 청킹 평가 ---")
        pipeline_general = RAGPipeline(use_structure_chunking=False)
        general_results = self._evaluate_with_mode(pipeline_general, sample_questions, use_structure=False)
        
        # 비교 출력
        print("\n" + "="*80)
        print("  비교 결과")
        print("="*80)
        print(f"{'지표':25s} | {'구조 청킹':>12s} | {'일반 청킹':>12s} | {'차이':>10s}")
        print("-" * 80)
        
        for metric in ['faithfulness', 'answer_relevancy']:
            if metric in structure_results and metric in general_results:
                struct_score = structure_results[metric]
                general_score = general_results[metric]
                diff = struct_score - general_score
                diff_str = f"+{diff:.3f}" if diff > 0 else f"{diff:.3f}"
                
                print(f"{metric:25s} | {struct_score:12.3f} | {general_score:12.3f} | {diff_str:>10s}")
        
        # Assertion
        assert structure_results['faithfulness'] >= general_results['faithfulness'], \
            "구조 청킹이 일반 청킹보다 Faithfulness가 낮습니다"
    
    def _evaluate_with_mode(self, pipeline, questions, use_structure=True):
        """특정 모드로 평가 실행"""
        results_data = {
            "question": [],
            "answer": [],
            "contexts": [],
            "ground_truth": [],
        }
        
        for item in questions:
            question = item['question']
            ground_truth = item.get('ground_truth', '')
            
            result = pipeline.query(question, top_k=5)
            answer = result.get('answer', '')
            contexts = [doc.page_content for doc in result.get('source_documents', [])]
            
            results_data['question'].append(question)
            results_data['answer'].append(answer)
            results_data['contexts'].append(contexts)
            results_data['ground_truth'].append(ground_truth)
        
        dataset = Dataset.from_dict(results_data)
        metrics = [faithfulness, answer_relevancy]
        
        return evaluate(dataset, metrics=metrics)


def test_ragas_metrics_available():
    """RAGAS 메트릭이 제대로 로드되는지 확인"""
    assert faithfulness is not None
    assert answer_relevancy is not None
    print("\n✅ RAGAS 메트릭이 정상적으로 로드되었습니다.")


if __name__ == "__main__":
    # pytest 실행
    pytest.main([__file__, "-v", "-s"])

