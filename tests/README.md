# 테스트 가이드

## RAGAS 평가

### 설치

```bash
pip install ragas datasets
```

### 빠른 시작 (권장)

```bash
# 간단한 평가: 신뢰성 + 관련성 + 응답 속도
python tests/test_ragas_evaluation.py --mode simple
```

### 다양한 평가 모드

```bash
# 1. 간단한 평가 (신뢰성 + 관련성 + 응답 속도) - 권장
python tests/test_ragas_evaluation.py --mode simple

# 2. 관련성만 (가장 빠르고 저렴)
python tests/test_ragas_evaluation.py --metrics answer_relevancy

# 3. 특정 지표만 선택
python tests/test_ragas_evaluation.py --metrics faithfulness answer_relevancy

# 4. 전체 평가 (5가지 지표)
python tests/test_ragas_evaluation.py --mode evaluate

# 5. 청킹 전략 비교
python tests/test_ragas_evaluation.py --mode compare
```

### 테스트 케이스 수정

`tests/test_cases.json` 파일을 수정하여 평가할 질문과 정답을 추가할 수 있습니다.

```json
{
  "id": "custom_001",
  "question": "당신의 질문",
  "ground_truth": "기대하는 정답"
}
```

### 지표 선택 옵션

```bash
# 사용 가능한 지표
--metrics faithfulness           # 신뢰성 (환각 방지)
--metrics answer_relevancy       # 답변 관련성
--metrics context_precision      # 검색 정밀도
--metrics context_recall         # 검색 재현율
--metrics answer_correctness     # 답변 정확도

# 여러 지표 조합
--metrics answer_relevancy answer_correctness
```

### 응답 시간 측정

```bash
# 응답 시간 포함 (기본값)
python tests/test_ragas_evaluation.py --mode simple

# 응답 시간 제외
python tests/test_ragas_evaluation.py --mode simple --no-response-time
```

### 결과 확인

- **콘솔**: 실시간 결과 출력 (응답 속도 통계 포함)
- **JSON**: `tests/ragas_evaluation_results.json` 또는 `tests/chunking_comparison.json`

### 지표 해석

| 지표 | 목표 | 의미 |
|------|------|------|
| **Faithfulness** | 0.80+ | 환각 없이 문서에 충실 (가장 중요!) |
| **Answer Relevancy** | 0.75+ | 답변이 질문과 관련있는가? |
| **평균 응답 시간** | < 2초 | 실시간 대화 가능 |
| Answer Correctness | 0.80+ | 정답과 일치 |

### 비용 및 시간

| 모드 | 소요 시간 | API 비용 |
|------|----------|----------|
| `--mode simple` | 30-40초 | $0.10-0.15 |
| `--metrics answer_relevancy` | 20-30초 | $0.05-0.10 |
| `--metrics faithfulness answer_relevancy` | 30-40초 | $0.10-0.15 |
| `--mode evaluate` | 60-90초 | $0.30-0.50 |
| `--mode compare` | 120-180초 | $0.60-1.00 |

---

자세한 내용은 `docs/RAG_성능_평가_가이드.md`를 참조하세요.

