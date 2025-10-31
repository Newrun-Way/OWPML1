# OWPML RAG 프로젝트

OWPML 필터를 활용한 한글 문서 기반 질의응답 서비스

## 프로젝트 구조

```
Al Lang/
├── extract.py                  # HWP/HWPX 문서 추출 메인 스크립트
├── auto_add.py                 # RAG 시스템 자동 추가 스크립트
├── main.py                     # RAG CLI 인터페이스
├── config.py                   # 프로젝트 설정
├── jpype_setup.py              # JPype 환경 설정
├── requirements.txt            # Python 의존성
│
├── rag/                        # RAG 시스템 모듈
│   ├── chunker.py             # 문서 청킹
│   ├── embedder.py            # 임베딩 생성
│   ├── vector_store.py        # 벡터 저장소
│   ├── llm.py                 # LLM 인터페이스
│   └── pipeline.py            # RAG 파이프라인
│
├── tests/                      # 테스트 스크립트
│   ├── test_jpype.py          # JPype 환경 테스트
│   └── test_rag.py            # RAG 시스템 테스트
│
├── scripts/                    # 유틸리티 스크립트
│   ├── check_data.py          # 데이터 확인
│   └── view_stored_data.py    # 저장된 데이터 조회
│
├── docs/                       # 프로젝트 문서 (gitignore)
│   ├── README.md
│   ├── extract.py사용법.md
│   ├── RAG_시작가이드.md
│   ├── 빠른시작_가이드.md
│   ├── 팀협업_워크플로우.md
│   └── ...
│
├── data/                       # 데이터 폴더 (gitignore)
│   ├── extracted/             # 팀원이 전달한 추출 결과물
│   ├── vector_store/          # FAISS 벡터 인덱스
│   └── uploads/               # 업로드 파일 (예비)
│
├── extracted_results/          # extract.py 실행 결과 (gitignore)
├── hwp data/                   # 원본 HWP/HWPX 파일
├── 회고록/                     # 프로젝트 회고 (gitignore)
│
├── python-hwplib/              # HWP 파서 라이브러리
├── python-hwpxlib/             # HWPX 파서 라이브러리
└── hwpx-owpml-model/           # OWPML C++ 소스

```

## 빠른 시작

### 1. 환경 설정

```bash
# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정 (.env 파일)
OPENAI_API_KEY=your_api_key_here
```

### 2. 문서 추출

```bash
# HWP/HWPX 파일에서 텍스트, 표, 이미지 추출
python extract.py "hwp data/문서명.hwpx"
```

### 3. RAG 시스템에 추가

```bash
# extracted_results 폴더의 문서를 RAG에 추가
python auto_add.py --source extracted_results

# 또는 data/extracted 폴더의 문서 추가 (팀 협업용)
python auto_add.py
```

### 4. 질의응답

```bash
# 대화형 질의응답
python main.py query

# 단일 질문
python main.py query --question "문서의 주요 내용은?"
```

## 주요 명령어

### 문서 추출
```bash
python extract.py "파일경로.hwpx"
```

### RAG 시스템
```bash
# 새 문서만 추가
python auto_add.py

# 모든 문서 재추가
python auto_add.py --all

# 특정 문서 추가
python auto_add.py --folder 문서명

# 질의응답
python main.py query
```

### 유틸리티
```bash
# 저장된 데이터 확인
python scripts/view_stored_data.py

# JPype 환경 테스트
python tests/test_jpype.py

# RAG 시스템 테스트
python tests/test_rag.py
```

## 팀 협업 워크플로우

### 데이터 가공 담당 (팀원)
1. 원본 HWP/HWPX 파일 수급
2. `python extract.py` 실행
3. `extracted_XXX` 폴더를 공유

### RAG 시스템 담당 (본인)
1. 받은 폴더를 `data/extracted/`에 복사
2. `python auto_add.py` 실행
3. `python main.py query`로 테스트

자세한 내용은 `docs/팀협업_워크플로우.md` 참고

## 기술 스택

- **문서 파싱**: python-hwplib, python-hwpxlib
- **임베딩 모델**: BGE-M3 (BAAI/bge-m3)
- **벡터 저장소**: FAISS
- **LLM**: GPT-4o mini
- **프레임워크**: LangChain, Sentence-Transformers

## 주요 기능

1. **문서 추출**
   - HWP/HWPX 텍스트 추출
   - 표 데이터 구조화
   - 이미지 추출

2. **RAG 시스템**
   - 문서 청킹 (800자 단위)
   - BGE-M3 임베딩 (1024차원)
   - FAISS 벡터 검색
   - GPT-4o mini 응답 생성

3. **자동화**
   - 중복 처리 방지
   - 일괄 문서 추가
   - 처리 기록 관리

## 라이선스

이 프로젝트는 Apache-2.0 라이선스를 따릅니다.

## 참고 문서

- `docs/RAG_시작가이드.md` - RAG 시스템 상세 가이드
- `docs/빠른시작_가이드.md` - 핵심 명령어 모음
- `docs/팀협업_워크플로우.md` - 팀 협업 방법
- `docs/extract.py사용법.md` - 문서 추출 가이드

