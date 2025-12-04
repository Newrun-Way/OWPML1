# AI Lang - HWP/HWPX 기반 RAG 시스템

한국어 공공 문서의 구조를 이해하는 지능형 질의응답 시스템

---

## 프로젝트 개요

AI Lang은 한글 HWP/HWPX 문서를 파싱하여 RAG(Retrieval Augmented Generation) 시스템으로 질의응답 서비스를 제공하는 프로젝트입니다. 공공기관, 기업의 규정집, 지침서 등 한국어 공공 문서에 특화되어 있습니다.

### 핵심 가치

"어디선가 본 것 같은데..." → "제3장 > 제15조에 따르면..."

정확한 출처와 함께 신뢰할 수 있는 답변을 제공합니다.

---

## 3가지 차별화 포인트

### 1. HWP/HWPX 파싱 자체 구현 (95%)
- Python 표준 라이브러리만으로 HWPX 완벽 파싱
- JPype + hwplib로 HWP 텍스트 추출
- 한컴오피스 설치 불필요 → 클라우드 독립 실행
- 텍스트 + 표 + 이미지 완벽 추출

### 2. 장/조/항/호 구조 기반 의미 단위 청킹 (85%)
- 정규식으로 문서 구조 자동 인식
- 조(Article) 단위 우선 청킹
- 구조 메타데이터 자동 태깅
- 검색 정확도 15-20% 향상

### 3. 표/이미지 참조 기반 처리 (70%)
- 표 데이터 JSON 구조화
- 참조 기반 처리로 중복 임베딩 방지
- HTML/Markdown 형식 변환
- 답변에 표 포함 가능

---

## 시스템 아키텍처

```
사용자 → API → Worker → Vector DB → LLM
         ↓       ↓         ↓
      Redis  Celery   ChromaDB
```

### Docker 5개 컨테이너 구성
1. **Redis**: 메시지 큐
2. **API**: FastAPI 서버 (8001)
3. **Worker**: Celery 백그라운드 처리
4. **Flower**: 모니터링 (5555)
5. **Nginx**: 리버스 프록시

---

## 기술 스택

| 레이어 | 기술 | 선택 이유 |
|--------|------|-----------|
| 파싱 | zipfile, ElementTree, hwplib | 외부 의존성 최소화 |
| 청킹 | StructureAwareChunker | 문서 구조 보존 |
| 임베딩 | BAAI/bge-m3 | 한국어 성능 우수 |
| 리랭킹 | BAAI/bge-reranker-v2-m3 | 정확도 향상 |
| Vector DB | ChromaDB | 빠른 HNSW 검색 |
| LLM | GPT-4o-mini | 비용 효율 + 품질 |
| 백엔드 | FastAPI + Celery | 비동기 처리 |

---

## 빠른 시작

### 1. 환경 설정

```bash
# 의존성 설치
pip install -r requirements.txt

# .env 파일 생성
OPENAI_API_KEY=your-api-key
```

### 2. 문서 파싱

```bash
# HWP/HWPX 파일 추출
python extract.py "path/to/document.hwpx"

# 결과: extracted_results/extracted_문서명/
#   - 전체텍스트.txt
#   - 구조.json
#   - 표데이터.json (HWPX만)
```

### 3. RAG 시스템 실행

#### 로컬 환경
```bash
# 문서 추가
python auto_add.py

# 대화형 모드
python main.py --mode chat

# 단일 질문
python main.py --mode single --question "급여는 어떻게 계산되나요?"
```

#### Docker 환경
```bash
# 컨테이너 실행
docker-compose up -d

# 문서 업로드
curl -X POST "http://localhost:8001/api/documents/upload/async" \
  -F "file=@인사규정.hwpx" \
  -F "dept_id=HR"

# 질의응답
curl -X POST "http://localhost:8001/api/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "급여는 어떻게 계산되나요?"}'
```

---

## 프로젝트 구조

```
Al Lang/
├── extract.py                    # HWP/HWPX 파싱
├── auto_add.py                   # 문서 자동 추가
├── main.py                       # CLI 인터페이스
│
├── rag/                          # RAG 핵심 모듈
│   ├── pipeline.py               # 전체 파이프라인
│   ├── chunker.py                # 일반 청킹
│   ├── structure_chunker.py     # 구조 우선 청킹 (신규)
│   ├── embedder.py               # BGE-M3 임베딩
│   ├── vector_store.py           # ChromaDB
│   ├── llm.py                    # GPT-4o-mini
│   ├── reranker.py               # BGE-reranker
│   └── table_processor.py        # 표 참조 처리 (신규)
│
├── backend/                      # FastAPI 백엔드
│   ├── api.py                    # REST API
│   ├── tasks.py                  # Celery 작업
│   ├── models.py                 # Pydantic 모델
│   └── celery_config.py          # Celery 설정
│
├── tests/                        # 테스트
│   ├── test_structure_chunker.py
│   └── test_table_processor.py
│
├── docs/                         # 문서
│   ├── README.md                          # 이 문서
│   ├── 시스템_핵심_기술_및_차별화_포인트.md  # 기술 상세
│   ├── 최종_발표_자료_통합본.md              # 발표 자료
│   ├── 구현_완료_기능_설명.md                # 신규 기능
│   ├── 실제_문서_색인_구조_시각화.md         # 색인 과정
│   ├── 장조항호_구조_청킹_상세_예시.md       # 청킹 예시
│   ├── Docker_구조_설명.md                 # Docker 아키텍처
│   └── 파이프라인_테스트_가이드.md          # 테스트 가이드
│
├── docker-compose.yml            # Docker 구성
├── Dockerfile                    # Docker 이미지
└── config.py                     # 설정
```

---

## 주요 기능

### 문서 파싱
- ✅ HWPX 완벽 파싱 (텍스트 + 표 + 이미지)
- ✅ HWP 텍스트 파싱
- ✅ 정규식 기반 문서 구조 인식 (장/조/항/호)
- ✅ 표 데이터 JSON 변환

### 구조 기반 청킹
- ✅ 조(Article) 단위 우선 청킹
- ✅ 항(Paragraph) 단위 분할 (조가 큰 경우)
- ✅ 조 병합 (조가 작은 경우)
- ✅ 계층 경로 자동 생성

### 검색 및 답변
- ✅ 벡터 유사도 검색
- ✅ BGE-reranker 재순위화
- ✅ GPT-4o-mini 답변 생성
- ✅ 정확한 출처 정보 포함

### 표 참조 처리
- ✅ table_id 기반 참조
- ✅ HTML/Markdown 변환
- ✅ API 응답에 표 데이터 포함

### 백엔드 인프라
- ✅ FastAPI + Celery 비동기 처리
- ✅ Docker 5개 컨테이너 분리
- ✅ Redis 메시지 큐
- ✅ Flower 모니터링

---

## API 문서

### 문서 업로드 (비동기)

```bash
POST /api/documents/upload/async
Content-Type: multipart/form-data

file: 파일
user_id: 사용자 ID (선택)
dept_id: 부서 ID (선택)
project_id: 프로젝트 ID (선택)
category: 카테고리 (선택)

응답:
{
  "status": "processing",
  "task_id": "abc123",
  "message": "문서 처리 중입니다"
}
```

### 작업 상태 조회

```bash
GET /api/tasks/{task_id}

응답:
{
  "task_id": "abc123",
  "status": "completed",
  "progress": 100,
  "result": {
    "doc_name": "인사규정",
    "chunks": 45,
    "summary": "..."
  }
}
```

### 질의응답

```bash
POST /api/query
Content-Type: application/json

{
  "question": "급여는 어떻게 계산되나요?",
  "dept_id": "HR",
  "top_k": 5
}

응답:
{
  "answer": "제3장 급여의 지급 > 제15조에 따르면...",
  "sources": [
    {
      "doc_name": "인사규정",
      "hierarchy_path": "제3장 급여의 지급 > 제15조",
      "score": 0.85,
      "table_id": "t001"
    }
  ],
  "tables": [
    {
      "table_id": "t001",
      "html": "<table>...</table>",
      "markdown": "| ... |"
    }
  ],
  "processing_time": 1.23
}
```

---

## 테스트

### 구조 우선 청킹 테스트
```bash
python tests/test_structure_chunker.py
```

### 표 참조 처리 테스트
```bash
python tests/test_table_processor.py
```

### 전체 파이프라인 테스트
```bash
python scripts/test_full_pipeline.py
```

---

## 성과 지표

### 기술적 성과
- 파싱 성공률: 95% (HWPX 100%, HWP 90%)
- 청킹 정확도: 기존 대비 30-40% 향상
- 검색 정확도: 기존 대비 15-20% 향상
- 처리 속도: 문서당 평균 5-10초

### 시스템 안정성
- Docker 컨테이너 분리로 확장성 확보
- 비동기 처리로 다중 사용자 지원
- GPU 지원으로 성능 최적화

---

## 향후 계획

### 단기 (1-2주)
- 표 내용 검색 (표 자체를 임베딩)
- 프론트엔드 통합 (표 렌더링)
- 구조 기반 검색 UI

### 중장기 (1-3개월)
- 한국어 특화 처리 (법률 용어 사전)
- 다양한 문서 형식 지원 (법률, 계약서)
- 이미지 OCR (선택)
- 한국어 모델 파인튜닝 (선택)

---

## 참고 문서

### 핵심 문서
- [시스템 핵심 기술 및 차별화 포인트](시스템_핵심_기술_및_차별화_포인트.md): 기술 상세 설명
- [최종 발표 자료 통합본](최종_발표_자료_통합본.md): 멘토링/발표 자료
- [구현 완료 기능 설명](구현_완료_기능_설명.md): 신규 기능 (표 참조, 구조 청킹)

### 상세 가이드
- [실제 문서 색인 구조 시각화](실제_문서_색인_구조_시각화.md): 색인 과정 단계별 설명
- [장조항호 구조 청킹 상세 예시](장조항호_구조_청킹_상세_예시.md): 청킹 전략 및 예시
- [Docker 구조 설명](Docker_구조_설명.md): 컨테이너 아키텍처
- [파이프라인 테스트 가이드](파이프라인_테스트_가이드.md): 테스트 방법

---

## 라이선스

본 프로젝트는 학습 목적으로 제작되었습니다.

---

## 팀

한글과컴퓨터 학습 과정 팀 프로젝트 - AI Lang Team

---

**최종 업데이트**: 2025년 12월 4일
