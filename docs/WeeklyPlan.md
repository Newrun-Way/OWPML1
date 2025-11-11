# OWPML 필터를 활용한 한글 문서 기반 질의응답 서비스 개발

## AI/RAG 담당자를 위한 8주 프로젝트 로드맵

### **1주차: 기술 조사 및 아키텍처 설계**

#### 주요 업무
1. **RAG 시스템 아키텍처 설계**
   - Google NotebookLM의 작동 원리 분석 (문서 업로드 → 임베딩 → 벡터 저장 → 검색 → 생성)
   - 한글 문서 처리 파이프라인 설계: OWPML 파싱 → 청킹 → 임베딩 → 벡터DB

2. **기술 스택 선정 및 제안**
   - **임베딩 모델**: `text-embedding-3-small` (OpenAI) 또는 'bge-m3` (한국어 지원)
   - **벡터 DB**: FAISS (로컬 개발) 또는 Pinecone/Weaviate (프로덕션)
   - **LLM**: GPT-4 또는 GPT-3.5-turbo (비용 고려)
   - **프레임워크**: LangChain 또는 LlamaIndex

3. **데이터 플로우 문서화**
   ```
   HWP/HWPX → OWPML 변환 → 텍스트 추출 → 
   청킹(Chunking) → 임베딩 → 벡터DB 저장 → 
   질의 → 유사도 검색 → 컨텍스트 구성 → GPT 응답
   ```

#### 산출물
- RAG 시스템 아키텍처 다이어그램
- 기술 스택 제안서
- 데이터 처리 파이프라인 명세서

---

### **2주차: 문서 처리 파이프라인 구축**

#### 주요 업무
1. **OWPML 텍스트 추출 로직 구현**
   - `python-hwpxlib` 또는 `hwpxlib` 통합 테스트
   - XML 파싱하여 본문 텍스트만 추출 (표, 각주 제외 로직)
   - 문서 메타데이터 보존 (제목, 섹션 정보)

2. **텍스트 전처리 파이프라인**
   ```python
   # 예시 파이프라인
   def preprocess_text(owpml_text):
       # 특수문자 정리
       # 불필요한 공백 제거
       # 문단 구분 유지
       return cleaned_text
   ```

3. **청킹 전략 설계**
   - **고정 크기 청킹**: 500-1000 토큰 단위 (오버랩 100토큰)
   - **의미 단위 청킹**: 문단/섹션 기반 분할 (추천)
   - **재귀적 청킹**: LangChain의 RecursiveCharacterTextSplitter 활용

#### 산출물
- OWPML → 텍스트 변환 스크립트
- 청킹 로직 구현 코드
- 샘플 문서 처리 결과 (JSON 포맷)

#### 팀 협업
- 백엔드 팀과 OWPML 변환 API 인터페이스 협의
- 추출된 텍스트 품질 검증 (팀 리뷰)

---

### **3주차: 임베딩 & 벡터 DB 구축**

#### 주요 업무
1. **임베딩 파이프라인 구현**
   ```python
   from openai import OpenAI
   
   def create_embeddings(chunks):
       embeddings = []
       for chunk in chunks:
           response = openai.Embedding.create(
               model="text-embedding-3-small",
               input=chunk['text']
           )
           embeddings.append(response['data'][0]['embedding'])
       return embeddings
   ```

2. **벡터 DB 구축**
   - **FAISS 기반 로컬 벡터 저장소 구현**
   - 문서 ID, 청크 ID, 메타데이터 매핑 구조 설계
   - 인덱싱 최적화 (IVF, PQ 등)

3. **검색 시스템 구현**
   - 유사도 검색 (코사인 유사도)
   - Top-K 검색 결과 반환 (K=3~5)
   - 하이브리드 검색 (키워드 + 의미 검색) 검토

#### 산출물
- 임베딩 생성 코드
- FAISS 벡터 DB 구축 스크립트
- 검색 API 프로토타입

#### 팀 협업
- S3/클라우드 스토리지에 벡터 인덱스 저장 방안 논의

---

### **4주차: RAG 파이프라인 통합 & GPT 연동**

#### 주요 업무
1. **RAG 파이프라인 구현**
   ```python
   def rag_query(question, vector_db, k=3):
       # 1. 질문 임베딩
       query_embedding = create_embedding(question)
       
       # 2. 유사 문서 검색
       relevant_chunks = vector_db.search(query_embedding, k=k)
       
       # 3. 컨텍스트 구성
       context = "\n\n".join([chunk['text'] for chunk in relevant_chunks])
       
       # 4. GPT 프롬프트 생성
       prompt = f"""다음 문서를 참고하여 질문에 답변해주세요.
       
       문서:
       {context}
       
       질문: {question}
       
       답변:"""
       
       # 5. GPT 호출
       response = openai.ChatCompletion.create(
           model="gpt-4",
           messages=[{"role": "user", "content": prompt}]
       )
       
       return response
   ```

2. **프롬프트 엔지니어링**
   - 한국어 질의응답에 최적화된 프롬프트 설계
   - Few-shot 예시 추가
   - 답변 형식 가이드라인 포함

3. **응답 품질 평가**
   - 테스트 질문 10-20개 작성
   - 정확도, 관련성, 완성도 평가
   - 검색 실패 케이스 분석

#### 산출물
- 완성된 RAG 파이프라인 코드
- 프롬프트 템플릿 라이브러리
- 초기 성능 평가 보고서

---

### **5주차: FastAPI 서버 개발 & 최적화**

#### 주요 업무
1. **FastAPI 엔드포인트 구현**
   ```python
   from fastapi import FastAPI, UploadFile
   
   app = FastAPI()
   
   @app.post("/upload")
   async def upload_document(file: UploadFile):
       # 1. OWPML 변환
       # 2. 청킹 + 임베딩
       # 3. 벡터 DB 저장
       return {"doc_id": doc_id}
   
   @app.post("/query")
   async def query_document(doc_id: str, question: str):
       # RAG 파이프라인 실행
       answer = rag_query(question, vector_db)
       return {"answer": answer, "sources": sources}
   ```

2. **성능 최적화**
   - **캐싱**: 자주 묻는 질문 캐싱 (Redis)
   - **비동기 처리**: 임베딩 생성 비동기화
   - **배치 처리**: 여러 청크 동시 임베딩
   - **레이턴시 목표**: 응답 시간 < 3초

3. **에러 핸들링**
   - 문서 처리 실패 시 롤백
   - GPT API 오류 처리
   - Rate limiting

#### 산출물
- FastAPI 서버 코드
- API 명세서 (OpenAPI/Swagger)
- 성능 테스트 결과 (Postman/k6)

#### 팀 협업
- 프론트엔드 팀과 API 인터페이스 협의
- 백엔드 팀과 문서 저장소 통합

---

### **6주차: 고급 기능 구현 & 통합 테스트**

#### 주요 업무
1. **추천 질문 생성 기능**
   ```python
   def generate_suggested_questions(document_summary):
       prompt = f"""다음 문서에 대해 사용자가 물어볼 만한 질문 5개를 생성해주세요.
       
       문서 요약: {document_summary}
       
       질문 목록:"""
       
       questions = gpt_call(prompt)
       return questions
   ```

2. **대화 이력 관리**
   - 세션 기반 대화 컨텍스트 유지
   - 이전 질문-답변을 고려한 후속 질문 처리

3. **멀티 문서 검색**
   - 여러 문서를 동시에 검색하는 기능
   - 문서별 가중치 적용

4. **통합 테스트**
   - 전체 파이프라인 E2E 테스트
   - 다양한 문서 유형 테스트 (보고서, 계약서 등)
   - 엣지 케이스 처리 (빈 문서, 대용량 문서)

#### 산출물
- 고급 기능 구현 코드
- 통합 테스트 스크립트
- 버그 리포트 및 해결 로그

---

### **7주차: 배포 준비 & 모니터링 구축**

#### 주요 업무
1. **배포 환경 설정**
   - AWS EC2에 FastAPI 서버 배포
   - S3에 벡터 인덱스 저장
   - 환경 변수 관리 (API 키, DB 연결 정보)

2. **모니터링 시스템**
   - **로깅**: 질의, 응답, 에러 로그 수집
   - **메트릭**: 응답 시간, 검색 정확도, API 사용량
   - **알림**: 에러율 임계값 초과 시 알림

3. **비용 최적화**
   - GPT API 호출 최소화 (캐싱 강화)
   - 임베딩 배치 처리
   - 벡터 DB 크기 최적화

4. **보안**
   - API 키 보안 관리
   - Rate limiting 설정
   - CORS 설정

#### 산출물
- 배포 스크립트 (Docker, CI/CD)
- 모니터링 대시보드
- 운영 매뉴얼

#### 팀 협업
- DevOps 팀과 배포 파이프라인 협의
- 프론트엔드 팀과 최종 통합 테스트

---

### **8주차: 성능 평가 & 발표 준비**

#### 주요 업무
1. **정량적 평가**
   - **검색 정확도**: Precision@K, Recall@K, MRR
   - **응답 품질**: BLEU, ROUGE, BERTScore (ground truth 있을 경우)
   - **사용자 만족도**: 베타 테스터 설문 (5점 척도)

2. **정성적 평가**
   - 다양한 질문 유형별 성능 분석
   - 실패 케이스 분석 및 개선 방향 제시

3. **발표 자료 준비**
   - RAG 시스템 아키텍처 설명
   - 기술적 챌린지 및 해결 방안
   - 데모 시나리오 준비
   - 향후 개선 계획

4. **기술 문서 작성**
   - API 사용 가이드
   - 모델 재학습 매뉴얼
   - 트러블슈팅 가이드

#### 산출물
- 성능 평가 보고서
- 발표 자료 (PPT)
- 기술 문서
- 회고록

---

## 핵심 성공 요소

### 1. **효과적인 청킹 전략**
- 문서 구조를 고려한 의미 단위 분할이 성능의 핵심
- 너무 작으면 컨텍스트 부족, 너무 크면 검색 정확도 저하

### 2. **한국어 최적화**
- 한국어 임베딩 모델 선택 중요
- GPT 프롬프트에 한국어 지시사항 명확히 작성

### 3. **반복적 개선**
- 초기 버전은 단순하게, 점진적으로 기능 추가
- 사용자 피드백 기반 지속적 개선

### 4. **팀 커뮤니케이션**
- 주 2회 이상 백엔드/프론트엔드 팀과 동기화
- API 인터페이스 변경 사항 즉시 공유

---

## 추천 학습 자료

### 1. **RAG 기초**
- LangChain 공식 문서: RAG 튜토리얼
- "Building RAG-based LLM Applications" (Pinecone)

### 2. **한국어 NLP**
- KoNLPy 라이브러리
- multilingual 임베딩 모델 비교 논문

### 3. **실전 예제**
- GitHub: `langchain-ai/rag-from-scratch`
- Google Colab: FAISS + OpenAI 통합 예제

---

## 프로젝트 진행 팁

이 계획을 따라가면서 **매주 스프린트 리뷰**를 통해 진행 상황을 점검하고, 필요시 우선순위를 조정하세요. RAG 구현은 반복적인 실험과 개선이 핵심입니다!

---

## 프로젝트 개요

### 프로젝트명
OWPML 필터를 활용한 한글 문서 기반 질의응답 서비스 개발

### 프로젝트 목표
- HWP 형식을 OWPML 필터로 구조화하여 문서 기반 질의응답 시스템 구축
- Google NotebookLM과 유사한 한글 문서 QA 서비스 구현
- AI 기반 질의응답 고객지원 챗봇 제작

### 주요 기술 스택
- **AI/ML**: OpenAI GPT API, LangChain, FAISS
- **백엔드**: FastAPI, Python
- **프론트엔드**: React.js, TailwindCSS
- **인프라**: AWS EC2/S3, Vercel
- **문서 처리**: OWPML, python-hwpxlib

### 프로젝트 기간
총 8주

### 담당 역할
AI 모델링 및 RAG(Retrieval-Augmented Generation) 구현

