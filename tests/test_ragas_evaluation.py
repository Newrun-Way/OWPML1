"""
RAGAS 기반 RAG 시스템 평가
"""

import json
import time
from pathlib import Path
from typing import List, Dict
import numpy as np
from loguru import logger

# 프로젝트 경로 추가
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.pipeline import RAGPipeline

# RAGAS 관련 임포트
try:
    from ragas import evaluate
    from ragas.metrics import (
        faithfulness,          # 답변이 문서에 충실한가? (환각 방지)
        answer_relevancy,      # 답변이 질문과 관련있는가?
        context_precision,     # 검색된 문서 순위가 정확한가?
        context_recall,        # 필요한 정보를 모두 검색했는가?
        answer_correctness,    # 답변이 정답과 일치하는가?
    )
    from datasets import Dataset
    RAGAS_AVAILABLE = True
except ImportError:
    RAGAS_AVAILABLE = False
    logger.warning("RAGAS가 설치되지 않았습니다. pip install ragas datasets 실행 필요")


class RAGASEvaluator:
    """RAGAS 기반 RAG 평가 클래스"""
    
    def __init__(self, test_cases_path: str = "tests/test_cases.json"):
        """
        Args:
            test_cases_path: 테스트 케이스 JSON 파일 경로
        """
        if not RAGAS_AVAILABLE:
            raise ImportError("RAGAS를 설치해주세요: pip install ragas datasets")
        
        self.test_cases = self._load_test_cases(test_cases_path)
        self.pipeline = RAGPipeline(use_structure_chunking=True)
        
        logger.info(f"RAGAS 평가 초기화: {len(self.test_cases)}개 테스트 케이스")
    
    def _load_test_cases(self, path: str) -> List[Dict]:
        """테스트 케이스 로드"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"테스트 케이스 파일 없음: {path}, 기본 케이스 사용")
            return self._get_default_test_cases()
    
    def _get_default_test_cases(self) -> List[Dict]:
        """기본 테스트 케이스"""
        return [
            {
                "id": "test_001",
                "question": "급여는 언제 지급되나요?",
                "ground_truth": "급여는 매월 25일에 지급하며, 지급일이 토요일 또는 공휴일인 경우 그 전일에 지급한다."
            },
            {
                "id": "test_002",
                "question": "과장의 기본급은 얼마인가요?",
                "ground_truth": "과장의 기본급은 3,500,000원이다."
            },
            {
                "id": "test_003",
                "question": "제3장에서 다루는 내용은 무엇인가요?",
                "ground_truth": "제3장에서는 급여 및 수당에 관한 내용을 다룬다."
            },
            {
                "id": "test_004",
                "question": "직책수당은 누구에게 지급되나요?",
                "ground_truth": "직책수당은 과장급 이상 직원에게 지급된다."
            },
            {
                "id": "test_005",
                "question": "야간근무수당은 시간당 얼마인가요?",
                "ground_truth": "야간근무수당은 22시 이후 근무 시 시간당 15,000원이다."
            }
        ]
    
    def prepare_ragas_dataset(self, measure_response_time: bool = True) -> Dict:
        """
        RAGAS 평가를 위한 데이터셋 준비
        
        Returns:
            {
                "question": [...],
                "contexts": [[...], ...],
                "answer": [...],
                "ground_truths": [[...], ...]
            }
        """
        logger.info("RAGAS 데이터셋 준비 중...")
        
        questions = []
        contexts_list = []
        answers = []
        ground_truths = []
        response_times = []
        
        for i, case in enumerate(self.test_cases):
            logger.info(f"  [{i+1}/{len(self.test_cases)}] {case['question']}")
            
            # RAG 파이프라인 질의 (응답 시간 측정)
            if measure_response_time:
                start_time = time.time()
                result = self.pipeline.query(case["question"], top_k=5)
                elapsed = time.time() - start_time
                response_times.append(elapsed)
            else:
                result = self.pipeline.query(case["question"], top_k=5)
            
            # 데이터 수집
            questions.append(case["question"])
            answers.append(result.get("answer", ""))
            ground_truths.append([case.get("ground_truth", "")])
            
            # 검색된 문서들 (contexts)
            contexts = []
            for source in result.get("sources", []):
                content = source.get("content", "")
                if content:
                    contexts.append(content)
            contexts_list.append(contexts if contexts else ["정보 없음"])
        
        logger.info("데이터셋 준비 완료")
        
        result = {
            "question": questions,
            "contexts": contexts_list,
            "answer": answers,
            "ground_truths": ground_truths
        }
        
        if measure_response_time:
            result["response_times"] = response_times
        
        return result
    
    def evaluate(
        self,
        metrics: List = None,
        save_results: bool = True,
        include_response_time: bool = True
    ) -> Dict:
        """
        RAGAS 평가 실행
        
        Args:
            metrics: 평가 지표 리스트 (None이면 answer_relevancy만 사용)
            save_results: 결과 저장 여부
            include_response_time: 응답 속도 측정 포함 여부
        
        Returns:
            평가 결과
        """
        # 기본 지표 설정 (신뢰성 + 관련성)
        if metrics is None:
            metrics = [
                faithfulness,      # 신뢰성 (환각 방지)
                answer_relevancy,  # 답변 관련성
            ]
        
        self.include_response_time = include_response_time
        
        logger.info("=== RAGAS 평가 시작 ===")
        logger.info(f"평가 지표: {[m.name for m in metrics]}")
        
        # 데이터셋 준비
        data = self.prepare_ragas_dataset(measure_response_time=include_response_time)
        
        # 응답 시간 저장 (RAGAS 데이터셋에서 제외)
        response_times = data.pop("response_times", None)
        
        dataset = Dataset.from_dict(data)
        
        # RAGAS 평가 실행
        logger.info("\nRAGAS 평가 실행 중... (시간이 걸릴 수 있습니다)")
        start_time = time.time()
        
        try:
            result = evaluate(dataset, metrics=metrics)
            evaluation_time = time.time() - start_time
            
            logger.info(f"평가 완료 (소요 시간: {evaluation_time:.1f}초)")
            
            # 결과 정리
            scores = {
                "evaluation_time": evaluation_time,
                "test_count": len(self.test_cases),
                "metrics": {}
            }
            
            # 지표별 점수 추출
            for metric in metrics:
                metric_name = metric.name
                if metric_name in result:
                    scores["metrics"][metric_name] = float(result[metric_name])
            
            # 응답 시간 통계 추가
            if response_times:
                scores["response_time"] = {
                    "average": float(np.mean(response_times)),
                    "min": float(np.min(response_times)),
                    "max": float(np.max(response_times)),
                    "median": float(np.median(response_times)),
                    "per_query": response_times
                }
            
            # 평균 점수 계산
            if scores["metrics"]:
                scores["average_score"] = np.mean(list(scores["metrics"].values()))
            
            # 결과 출력
            self._print_results(scores)
            
            # 결과 저장
            if save_results:
                self._save_results(scores, data)
            
            return scores
            
        except Exception as e:
            logger.error(f"RAGAS 평가 실패: {e}")
            raise
    
    def _print_results(self, scores: Dict):
        """결과 출력"""
        print("\n" + "="*70)
        print("RAGAS 평가 결과")
        print("="*70)
        print(f"\n총 테스트: {scores['test_count']}개")
        print(f"평가 시간: {scores['evaluation_time']:.1f}초")
        
        # 응답 시간 출력
        if "response_time" in scores:
            rt = scores["response_time"]
            print(f"\n응답 속도:")
            print("-"*70)
            print(f"  {'평균 응답 시간':25s}: {rt['average']:.2f}초")
            print(f"  {'최소 응답 시간':25s}: {rt['min']:.2f}초")
            print(f"  {'최대 응답 시간':25s}: {rt['max']:.2f}초")
            print(f"  {'중앙값':25s}: {rt['median']:.2f}초")
            
            # 응답 시간 판정
            avg_time = rt['average']
            if avg_time < 2.0:
                time_status = "✅ 우수"
            elif avg_time < 3.0:
                time_status = "⚠️ 보통"
            else:
                time_status = "❌ 개선 필요"
            print(f"  {'판정':25s}: {time_status}")
        
        print(f"\n평가 지표:")
        print("-"*70)
        
        for metric_name, score in scores["metrics"].items():
            # 지표별 판정
            if score >= 0.85:
                status = "✅ 우수"
            elif score >= 0.70:
                status = "⚠️ 보통"
            else:
                status = "❌ 개선 필요"
            
            print(f"  {metric_name:25s}: {score:.3f}  {status}")
        
        if "average_score" in scores:
            print("-"*70)
            print(f"  {'평균 점수':25s}: {scores['average_score']:.3f}")
        
        print("="*70)
        
        # 해석 가이드
        print("\n[지표 해석 가이드]")
        print("  • Faithfulness (신뢰성):      답변이 문서에 충실한가? (환각 방지)")
        print("  • Answer Relevancy (관련성):  답변이 질문과 관련있는가?")
        print("  • Context Precision (정밀도): 검색된 문서의 순위가 정확한가?")
        print("  • Context Recall (재현율):    필요한 모든 정보를 검색했는가?")
        print("  • Answer Correctness (정확도): 답변이 정답과 일치하는가?")
        
        print("\n[판정 기준]")
        print("  ✅ 우수 (0.85+):    프로덕션 준비 완료")
        print("  ⚠️ 보통 (0.70-0.85): 파라미터 튜닝 권장")
        print("  ❌ 개선 필요 (<0.70): 시스템 개선 필요")
    
    def _save_results(self, scores: Dict, raw_data: Dict):
        """결과 저장"""
        output_path = Path("tests/ragas_evaluation_results.json")
        
        results = {
            "summary": scores,
            "raw_data": {
                "questions": raw_data["question"],
                "answers": raw_data["answer"],
                "ground_truths": raw_data["ground_truths"],
                "contexts_count": [len(ctx) for ctx in raw_data["contexts"]]
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n결과 저장: {output_path}")
    
    def compare_chunking_strategies(self) -> Dict:
        """
        구조 청킹 vs 일반 청킹 비교
        
        Returns:
            비교 결과
        """
        logger.info("\n=== 청킹 전략 비교 평가 ===")
        
        results = {}
        
        # 1. 구조 우선 청킹
        logger.info("\n[1/2] 구조 우선 청킹 평가")
        self.pipeline = RAGPipeline(use_structure_chunking=True)
        results["structure_chunking"] = self.evaluate(save_results=False)
        
        # 2. 일반 청킹
        logger.info("\n[2/2] 일반 청킹 평가")
        self.pipeline = RAGPipeline(use_structure_chunking=False)
        results["general_chunking"] = self.evaluate(save_results=False)
        
        # 비교 출력
        self._print_comparison(results)
        
        # 비교 결과 저장
        output_path = Path("tests/chunking_comparison.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logger.info(f"\n비교 결과 저장: {output_path}")
        
        return results
    
    def _print_comparison(self, results: Dict):
        """비교 결과 출력"""
        print("\n" + "="*70)
        print("청킹 전략 비교 결과")
        print("="*70)
        
        structure = results["structure_chunking"]["metrics"]
        general = results["general_chunking"]["metrics"]
        
        print(f"\n{'지표':25s} {'구조 청킹':>12s} {'일반 청킹':>12s} {'차이':>12s}")
        print("-"*70)
        
        for metric in structure.keys():
            s_score = structure[metric]
            g_score = general[metric]
            diff = s_score - g_score
            
            diff_str = f"+{diff:.3f}" if diff > 0 else f"{diff:.3f}"
            winner = "🏆" if diff > 0 else ""
            
            print(f"{metric:25s} {s_score:>12.3f} {g_score:>12.3f} {diff_str:>12s} {winner}")
        
        print("-"*70)
        
        s_avg = results["structure_chunking"].get("average_score", 0)
        g_avg = results["general_chunking"].get("average_score", 0)
        avg_diff = s_avg - g_avg
        
        print(f"{'평균':25s} {s_avg:>12.3f} {g_avg:>12.3f} {avg_diff:+12.3f}")
        print("="*70)
        
        # 결론
        print("\n[결론]")
        if avg_diff > 0.05:
            print(f"✅ 구조 우선 청킹이 {avg_diff:.3f}점 더 우수합니다!")
        elif avg_diff < -0.05:
            print(f"⚠️ 일반 청킹이 {abs(avg_diff):.3f}점 더 우수합니다.")
        else:
            print("두 전략의 성능이 비슷합니다.")


def main():
    """메인 실행"""
    import argparse
    
    parser = argparse.ArgumentParser(description="RAGAS RAG 평가")
    parser.add_argument(
        "--mode",
        choices=["evaluate", "compare", "simple"],
        default="evaluate",
        help="평가 모드: evaluate (전체 평가), compare (청킹 비교), simple (관련성+속도만)"
    )
    parser.add_argument(
        "--test-cases",
        default="tests/test_cases.json",
        help="테스트 케이스 JSON 파일 경로"
    )
    parser.add_argument(
        "--metrics",
        nargs="+",
        choices=["faithfulness", "answer_relevancy", "context_precision", "context_recall", "answer_correctness"],
        help="평가할 지표 선택 (미지정 시 answer_relevancy만)"
    )
    parser.add_argument(
        "--no-response-time",
        action="store_true",
        help="응답 시간 측정 제외"
    )
    
    args = parser.parse_args()
    
    try:
        evaluator = RAGASEvaluator(test_cases_path=args.test_cases)
        
        # 지표 선택
        selected_metrics = None
        if args.metrics:
            metric_map = {
                "faithfulness": faithfulness,
                "answer_relevancy": answer_relevancy,
                "context_precision": context_precision,
                "context_recall": context_recall,
                "answer_correctness": answer_correctness
            }
            selected_metrics = [metric_map[m] for m in args.metrics]
        
        if args.mode == "simple":
            # 간단한 평가 (신뢰성 + 관련성 + 응답 속도)
            print("\n[간단한 평가 모드: 신뢰성 + 관련성 + 응답 속도]\n")
            evaluator.evaluate(
                metrics=[faithfulness, answer_relevancy],
                include_response_time=True
            )
        elif args.mode == "evaluate":
            # 기본 평가
            evaluator.evaluate(
                metrics=selected_metrics,
                include_response_time=not args.no_response_time
            )
        else:
            # 청킹 전략 비교
            evaluator.compare_chunking_strategies()
            
    except ImportError as e:
        print(f"\n❌ 오류: {e}")
        print("\n설치 명령어:")
        print("  pip install ragas datasets")
        return 1
    except Exception as e:
        print(f"\n❌ 평가 실패: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

