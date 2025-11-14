# OWPML RAG 프로젝트

OWPML 필터를 활용한 한글 문서 기반 질의응답 시스템 (B2B/B2G 서비스)

## 📋 프로젝트 개요

- **목적**: HWP/HWPX 한글 문서를 파싱하여 RAG(Retrieval Augmented Generation) 시스템에 통합
- **주요 기능**: 문서 추출, 임베딩, 벡터 검색, LLM 기반 질의응답
- **인프라**: Docker 컨테이너화, EC2 배포 가능
- **메타데이터**: 사용자/부서/프로젝트 기반 필터링 지원

## 🏗️ 프로젝트 구조

```
OWPML1/
├── extract.py                  # HWP/HWPX 문서 추출 (폴더 일괄 처리 지원)
├── auto_add.py                 # RAG 시스템 자동 추가 스크립트
├── main.py                     # RAG CLI 인터페이스 (대화형/단일 질문)
├── config.py                   # 프로젝트 설정 및 메타데이터 스키마
├── jpype_setup.py              # JPype 환경 설정 (Windows/Linux 크로스플랫폼)
├── requirements.txt            # Python 의존성
├── Dockerfile                  # Docker 컨테이너 설정
│
├── rag/                        # RAG 시스템 모듈
│   ├── __init__.py
│   ├── chunker.py             # 문서 청킹 (RecursiveCharacterTextSplitter)
│   ├── embedder.py            # 임베딩 생성 (BAAI/bge-m3)
│   ├── vector_store.py        # 벡터 저장소 (ChromaDB - PersistentClient)
│   ├── llm.py                 # LLM 인터페이스 (GPT-4o mini)
│   ├── reranker.py            # 검색 결과 재순위화 (BGE Reranker v2-m3)
│   └── pipeline.py            # RAG 파이프라인 통합
│
├── tests/                      # 테스트 스크립트
│   ├── test_jpype.py          # JPype 환경 테스트
│   └── test_rag.py            # RAG 시스템 테스트
│
├── docs/                       # 프로젝트 문서
│   ├── README.md
│   ├── extract.py사용법.md     # 문서 추출 상세 가이드
│   ├── Chroma_마이그레이션_가이드.md
│   ├── 메타데이터_스키마_가이드.md  # 메타데이터 설계 및 필터링
│   ├── 메타데이터_테스트_가이드.md
│   ├── JPype_에러_해결가이드.md
│   └── ...
│
├── data/                       # 데이터 폴더 (.gitignore)
│   ├── extracted/             # 팀원이 전달한 추출 결과물
│   ├── vector_store/          # ChromaDB 벡터 저장소 (persist_dir)
│   └── .processed_documents.json  # 처리 완료 문서 기록
│
├── extracted_results/          # extract.py 실행 결과 (.gitignore)
│   └── extracted_DOCUMENT_NAME/
│       ├── _텍스트.txt
│       ├── _표.json
│       ├── _이미지.json
│       ├── _구조.json           # 문서 구조 정보 (chapters, articles)
│       └── _추출요약.txt
│
├── hwp data/                   # 원본 HWP/HWPX 파일
│
├── python-hwplib/              # HWP 파서 라이브러리
├── python-hwpxlib/             # HWPX 파서 라이브러리
└── hwpx-owpml-model/           # OWPML C++ 소스
```

## 🚀 빠른 시작

### 1️⃣ 환경 설정

```bash
# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정 (.env 파일)
OPENAI_API_KEY=your_api_key_here
```

### 2️⃣ 문서 추출

```bash
# 단일 파일 추출
python extract.py "hwp data/문서명.hwpx"

# 폴더 일괄 추출
python extract.py "hwp data/" --batch

# 결과물
# extracted_results/extracted_문서명/
#   ├── _텍스트.txt
#   ├── _표.json
#   ├── _이미지.json
#   ├── _구조.json (문서 구조: 장, 조, 항)
#   └── _추출요약.txt
```

### 3️⃣ RAG 시스템에 추가

```bash
# 새 문서만 추가 (중복 확인)
python auto_add.py

# 특정 폴더 문서 추가
python auto_add.py --folder extracted_results

# 모든 문서 재추가
python auto_add.py --all
```

### 4️⃣ 질의응답

```bash
# 대화형 모드
python main.py interactive

# 단일 질문
python main.py query "질문 내용"
```

## 📊 주요 명령어

### 문서 추출
```bash
# 단일 파일
python extract.py "파일경로.hwpx"

# 폴더 일괄 처리
python extract.py "폴더경로/" --batch

# 결과: extracted_results/extracted_XXX/
```

### RAG 시스템
```bash
# 새 문서 추가 (중복 제외)
python auto_add.py

# 특정 문서 추가
python auto_add.py --folder 문서명

# 모든 문서 재추가 (벡터 스토어 초기화)
python auto_add.py --all

# 대화형 질의응답
python main.py interactive

# 단일 질문
python main.py query "질문"
```

### 유틸리티
```bash
# 벡터 저장소 정보 확인
python -c "from rag.vector_store import VectorStore; vs = VectorStore.load(); print(vs.get_collection_info())"

# JPype 환경 테스트
python jpype_setup.py
```

## 🛠️ 기술 스택

### 문서 처리
- **파싱**: python-hwplib (HWP), python-hwpxlib (HWPX)
- **구조 분석**: 정규표현식 (장, 조, 항, 단락)
- **텍스트 청킹**: LangChain RecursiveCharacterTextSplitter (800자, 150자 오버랩)

### 임베딩 & 검색
- **임베딩 모델**: BAAI/bge-m3 (1024차원, GPU 가속)
- **벡터 저장소**: ChromaDB (PersistentClient, 사전 필터링 지원)
- **재순위화**: BAAI/bge-reranker-v2-m3

### LLM & API
- **LLM**: GPT-4o mini (OpenAI)
- **프레임워크**: LangChain Core 0.1+

### 배포 & 인프라
- **컨테이너**: Docker (Python 3.11, OpenJDK 17)
- **클라우드**: AWS EC2 (G6 xlarge 권장)
- **일정 관리**: GitHub (commits, issues)

## 📈 주요 기능

### 1. 문서 추출
- HWP/HWPX 파일에서 텍스트, 표, 이미지 추출
- 문서 구조 자동 분석 (장/조/항 분류)
- 메타데이터 자동 생성

### 2. RAG 파이프라인
- 문서 청킹: 800자 단위 (150자 오버랩)
- 임베딩: BGE-M3 (CUDA 기반 GPU 가속)
- 벡터 검색: ChromaDB (사전 필터링 + 유사도 검색)
- 재순위화: BGE Reranker로 정확도 향상
- 응답 생성: GPT-4o mini

### 3. 메타데이터 관리
- **문서 레벨**: doc_id, doc_title, user_id, dept_id, project_id, category, version
- **청크 레벨**: chunk_index, total_chapters, total_articles, hierarchy_path
- **필터링**: ChromaDB where 쿼리로 부서/프로젝트별 검색

### 4. 자동화
- 중복 처리 방지 (.processed_documents.json)
- 일괄 문서 추가/업데이트
- 처리 기록 관리

## 💾 메타데이터 스키마

### 문서 레벨
```json
{
  "doc_id": "doc_감사규칙",
  "doc_title": "감사규칙(2024년도 9월 개정)",
  "doc_name": "감사규칙(2024년도 9월 개정)",
  "user_id": "user_001",
  "dept_id": "audit_dept",
  "project_id": "2024_policy",
  "category": "규정",
  "version": "1.0",
  "upload_date": "2024-11-11",
  "total_chapters": 5,
  "total_articles": 42
}
```

### 청크 레벨
```json
{
  "chunk_id": 0,
  "chunk_index": "0/35",
  "doc_id": "doc_감사규칙",
  "hierarchy_path": "제1장 총칙 > 제1조 (목적)",
  "chapter_number": 1,
  "chapter_title": "총칙",
  "article_number": 1,
  "article_title": "목적",
  "section_title": "",
  "page_number": 1
}
```

## 🔧 설정 & 환경

### 필수 환경변수
```bash
OPENAI_API_KEY=sk-...
```

### 선택 환경변수
```bash
# GPU 경고 억제
export ORT_LOGGING_LEVEL=3
export TF_CPP_MIN_LOG_LEVEL=3
```

### Python 버전
- **로컬**: Python 3.13 (개발)
- **EC2/Docker**: Python 3.11 (호환성)
- **Java**: OpenJDK 17

## 🐳 Docker 사용

### 로컬 빌드 및 실행
```bash
# 이미지 빌드
docker build -t owpml-rag:latest .

# 컨테이너 실행
docker run -it \
  -e OPENAI_API_KEY=sk-... \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/extracted_results:/app/extracted_results \
  owpml-rag:latest bash
```

### EC2 배포
```bash
# EC2에서 이미지 빌드 및 실행
git clone https://github.com/Newrun-Way/OWPML1.git
cd OWPML1
docker build -t owpml-rag .
docker run -d -e OPENAI_API_KEY=sk-... owpml-rag-rag
```

## 📚 참고 문서

| 문서 | 설명 |
|------|------|
| `docs/extract.py사용법.md` | 문서 추출 상세 가이드 |
| `docs/메타데이터_스키마_가이드.md` | 메타데이터 설계 및 필터링 |
| `docs/Chroma_마이그레이션_가이드.md` | FAISS → ChromaDB 마이그레이션 |
| `docs/JPype_에러_해결가이드.md` | JPype 관련 문제 해결 |

## 🤝 팀 협업 가이드

### 역할 분담
- **문서 처리 담당**: HWP/HWPX 파일 수급 및 추출
- **RAG 시스템 담당**: 벡터 저장소 관리 및 질의응답 서비스

### 워크플로우
1. **문서 수급**: 팀원이 HWP/HWPX 파일 제공
2. **추출**: `python extract.py` 실행 → `extracted_XXX` 폴더 생성
3. **통합**: `python auto_add.py --folder` 또는 `--all`
4. **테스트**: `python main.py interactive`로 검증

## ⚡ 성능 최적화

### GPU 가속 활용
- **임베딩**: CUDA 기반 배치 처리 (1024차원)
- **모니터링**: NVIDIA GPU 사용률 확인
  ```bash
  nvidia-smi -l 1  # 1초 단위 업데이트
  ```

### 벡터 저장소 최적화
- ChromaDB PersistentClient (자동 저장)
- where 쿼리로 사전 필터링
- Reranker로 정확도 개선

## 🐛 알려진 이슈

### Windows PowerShell 한글 인코딩
- **해결책**: Git Bash 사용 또는 PowerShell에서 `$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'` 설정

### EC2 ONNX Runtime GPU 감지 실패
- **원인**: NVIDIA 드라이버 환경 차이
- **해결책**: `ORT_LOGGING_LEVEL=3` 설정으로 경고 억제 (실제로는 PyTorch가 GPU 사용 중)

## 📝 라이선스

프로젝트별 내부 정책 참고

## 🎯 다음 단계

- [ ] 프론트엔드 UI 개발 (메타데이터 입력 폼)
- [ ] 백엔드 API 서버화 (Flask/FastAPI)
- [ ] 메타데이터 세분화 최적화
- [ ] 성능 모니터링 대시보드
- [ ] 다국어 지원 (영어, 중국어)
