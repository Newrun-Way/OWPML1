# RAG 시스템 테스트 가이드

이 디렉토리에는 RAG 시스템의 성능을 평가하는 테스트가 포함되어 있습니다.

## 📋 테스트 파일

### 1. `test_ragas_evaluation.py`
RAGAS 프레임워크를 사용한 종합 평가 테스트

**실행 방법:**
```bash
# 간단 모드 (3개 질문만 테스트)
pytest tests/test_ragas_evaluation.py::TestRAGASEvaluation::test_simple_mode -v -s

# 전체 평가 (모든 테스트 케이스)
pytest tests/test_ragas_evaluation.py::TestRAGASEvaluation::test_full_evaluation -v -s

# 비교 모드 (구조 청킹 vs 일반 청킹)
pytest tests/test_ragas_evaluation.py::TestRAGASEvaluation::test_compare_modes -v -s

# 전체 테스트 실행
pytest tests/test_ragas_evaluation.py -v -s
```

### 2. `test_cases_real.json`
실제 문서 기반 테스트 케이스

**형식:**
```json
[
  {
    "question": "질문 내용",
    "ground_truth": "정답 (선택사항)"
  }
]
```

## 📊 평가 지표

### RAGAS 메트릭

1. **Faithfulness (신뢰성)**
   - 답변이 검색된 문서(contexts)에 얼마나 충실한지 측정
   - 0.8 이상: 우수
   - 0.6~0.8: 보통
   - 0.6 미만: 개선 필요

2. **Answer Relevancy (관련성)**
   - 답변이 질문과 얼마나 관련있는지 측정
   - 0.8 이상: 우수
   - 0.6~0.8: 보통
   - 0.6 미만: 개선 필요

3. **Response Time (응답 속도)**
   - 질문에 대한 답변 생성 시간
   - 3초 이내: 우수
   - 3~5초: 보통
   - 5초 초과: 개선 필요

## 🎯 테스트 모드

### Simple Mode (간단 모드)
- 3개의 샘플 질문으로 빠른 테스트
- Faithfulness, Answer Relevancy, Response Time 평가
- 개발 중 빠른 검증용

### Full Evaluation (전체 평가)
- 모든 테스트 케이스로 종합 평가
- 결과를 `ragas_results.json`에 저장
- 최종 성능 검증용

### Compare Mode (비교 모드)
- 구조 청킹 vs 일반 청킹 비교
- 두 방식의 성능 차이 측정
- 알고리즘 개선 효과 검증용

## 📝 결과 해석

### 예시 출력
```
faithfulness            : 0.890  ✅ 우수
answer_relevancy        : 0.860  ✅ 우수
평균 응답 시간          : 1.75초
```

### 목표 지표
- Faithfulness: ≥ 0.80
- Answer Relevancy: ≥ 0.75
- Response Time: < 3.0초

## 🔧 문제 해결

### RAGAS 평가 실패
```bash
# OpenAI API 키 확인
echo $OPENAI_API_KEY

# 의존성 재설치
pip install -r requirements.txt
```

### 테스트 케이스 없음
```bash
# test_cases_real.json 생성 확인
ls -l tests/test_cases_real.json

# 내용 확인
cat tests/test_cases_real.json
```

### GPU 메모리 부족
- Reranker가 자동으로 CPU로 전환됨
- 성능 영향: 약 0.3초 증가 (문제없음)

## 📈 지속적 개선

1. **새로운 테스트 케이스 추가**
   - `test_cases_real.json`에 실제 사용 사례 추가
   - 다양한 질문 유형 포함

2. **목표 지표 상향 조정**
   - 현재: Faithfulness ≥ 0.80
   - 목표: Faithfulness ≥ 0.85

3. **정기 평가**
   - 주 1회 전체 평가 실행
   - 결과 추이 모니터링
   - 성능 저하 시 원인 분석

## 🚀 CI/CD 통합

```yaml
# .github/workflows/test.yml
- name: Run RAGAS Evaluation
  run: |
    pytest tests/test_ragas_evaluation.py::TestRAGASEvaluation::test_simple_mode -v
```

## 📚 참고 자료

- [RAGAS 공식 문서](https://docs.ragas.io/)
- [프로젝트 내 평가 가이드](../docs/RAG_성능_평가_가이드.md)

