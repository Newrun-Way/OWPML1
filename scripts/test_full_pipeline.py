"""
전체 파이프라인 테스트 스크립트
실제 문서 색인 구조 시각화 문서의 내용을 검증하기 위한 스크립트

사용법:
    로컬: python scripts/test_full_pipeline.py
    Docker: docker exec -it rag-api python scripts/test_full_pipeline.py
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# 프로젝트 루트 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import extract
import config
from rag.chunker import DocumentChunker
from rag.embedder import DocumentEmbedder
from rag.vector_store import VectorStore
from rag.pipeline import RAGPipeline


def print_section(title: str):
    """섹션 구분선 출력"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_step1_parsing(file_path: str):
    """1단계: HWP/HWPX 파싱 테스트"""
    print_section("1단계: HWP/HWPX 파싱 (extract.py)")
    
    file_path_obj = Path(file_path)
    print(f"입력 파일: {file_path_obj.name}")
    print(f"파일 크기: {file_path_obj.stat().st_size / 1024:.1f} KB")
    print(f"확장자: {file_path_obj.suffix.upper()}")
    
    # 파싱 실행
    print("\n[파싱 중...]")
    result = extract.process_single_file(str(file_path_obj))
    
    if result is None:
        print("[오류] 파싱 실패")
        return None
    
    # 출력 디렉토리 확인
    output_dir = Path(result['output_dir'])
    print(f"\n출력 디렉토리: {output_dir}")
    
    # 생성된 파일 목록
    print("\n생성된 파일:")
    for f in output_dir.iterdir():
        size = f.stat().st_size
        print(f"  ├── {f.name} ({size:,} bytes)")
    
    # 구조.json 내용 확인
    structure_file = output_dir / f"extracted_{file_path_obj.stem}_구조.json"
    if structure_file.exists():
        with open(structure_file, 'r', encoding='utf-8') as f:
            structure = json.load(f)
        
        print(f"\n구조 분석 결과:")
        print(f"  - 총 장(Chapter) 수: {len(structure.get('chapters', []))}")
        print(f"  - 총 조(Article) 수: {len(structure.get('articles', []))}")
        print(f"  - structure_map 항목 수: {len(structure.get('structure_map', {}))}")
        
        # 첫 번째 장 정보
        if structure.get('chapters'):
            ch = structure['chapters'][0]
            print(f"\n첫 번째 장 예시:")
            print(f"  - 장 번호: 제{ch.get('number')}장")
            print(f"  - 장 제목: {ch.get('title')}")
            print(f"  - 포함 조 수: {len(ch.get('articles', []))}")
    
    # 표데이터.json 내용 확인
    table_file = output_dir / f"extracted_{file_path_obj.stem}_표데이터.json"
    if table_file.exists():
        with open(table_file, 'r', encoding='utf-8') as f:
            tables = json.load(f)
        
        print(f"\n표 데이터:")
        print(f"  - 총 표 수: {len(tables.get('tables', []))}")
        
        if tables.get('tables'):
            t = tables['tables'][0]
            print(f"\n첫 번째 표 예시:")
            print(f"  - table_id: {t.get('table_id', 'N/A')}")
            print(f"  - 행 수: {len(t.get('rows', []))}")
            if t.get('rows'):
                print(f"  - 첫 행 셀 수: {len(t['rows'][0].get('cells', []))}")
    
    return output_dir


def test_step2_chunking(extracted_dir: Path):
    """2단계: 청킹 테스트"""
    print_section("2단계: 문서 청킹 (DocumentChunker)")
    
    # 텍스트 파일 찾기
    text_file = None
    for f in extracted_dir.glob("*전체텍스트.txt"):
        text_file = f
        break
    
    if not text_file:
        print("[오류] 텍스트 파일을 찾을 수 없습니다")
        return None
    
    # 텍스트 로드
    with open(text_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    print(f"텍스트 길이: {len(text):,} 글자")
    
    # 청커 초기화
    chunker = DocumentChunker()
    print(f"\n청킹 설정:")
    print(f"  - chunk_size: {config.CHUNK_SIZE}")
    print(f"  - chunk_overlap: {config.CHUNK_OVERLAP}")
    
    # 청킹 실행
    doc_name = extracted_dir.stem.replace('extracted_', '')
    chunks = chunker.chunk_document(
        text=text,
        doc_name=doc_name,
        base_metadata={
            'user_id': 'test_user',
            'dept_id': 'test_dept',
            'project_id': 'test_project'
        }
    )
    
    print(f"\n청킹 결과:")
    print(f"  - 생성된 청크 수: {len(chunks)}")
    
    # 청크 예시 출력
    print("\n청크 예시 (첫 3개):")
    for i, chunk in enumerate(chunks[:3]):
        print(f"\n  Chunk {i+1:03d}:")
        print(f"    - 텍스트 길이: {len(chunk.page_content)} 글자")
        print(f"    - hierarchy_path: {chunk.metadata.get('hierarchy_path', 'N/A')}")
        print(f"    - chapter_number: {chunk.metadata.get('chapter_number', 'N/A')}")
        print(f"    - article_number: {chunk.metadata.get('article_number', 'N/A')}")
        print(f"    - 텍스트 미리보기: {chunk.page_content[:100]}...")
    
    return chunks


def test_step3_embedding(chunks):
    """3단계: 임베딩 테스트"""
    print_section("3단계: 임베딩 생성 (DocumentEmbedder)")
    
    # 임베더 초기화
    print("임베딩 모델 로드 중...")
    embedder = DocumentEmbedder()
    
    print(f"\n임베딩 설정:")
    print(f"  - 모델: {config.EMBEDDING_MODEL}")
    print(f"  - 차원: {config.EMBEDDING_DIM}")
    
    # 첫 3개 청크만 임베딩 (테스트용)
    test_chunks = chunks[:3]
    texts = [c.page_content for c in test_chunks]
    
    print(f"\n임베딩 생성 중 ({len(texts)}개 청크)...")
    embeddings = embedder.embed_documents(texts)
    
    print(f"\n임베딩 결과:")
    print(f"  - 임베딩 수: {len(embeddings)}")
    print(f"  - 벡터 차원: {len(embeddings[0])}")
    print(f"  - 첫 벡터 샘플: [{embeddings[0][0]:.4f}, {embeddings[0][1]:.4f}, ..., {embeddings[0][-1]:.4f}]")
    
    return embeddings


def test_step4_vector_store(chunks, embeddings):
    """4단계: 벡터 저장소 테스트"""
    print_section("4단계: 벡터 저장소 (ChromaDB)")
    
    # 테스트용 임시 저장소
    test_dir = config.DATA_DIR / "test_vector_store"
    test_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"테스트 저장소: {test_dir}")
    
    # 벡터 저장소 초기화
    vector_store = VectorStore(persist_dir=test_dir)
    
    # 문서 추가
    test_chunks = chunks[:3]
    print(f"\n문서 추가 중 ({len(test_chunks)}개 청크)...")
    
    for i, (chunk, embedding) in enumerate(zip(test_chunks, embeddings)):
        vector_store.add_document(
            doc_id=f"test_chunk_{i:03d}",
            text=chunk.page_content,
            embedding=embedding,
            metadata=chunk.metadata
        )
    
    print(f"\n저장소 상태:")
    stats = vector_store.get_stats()
    print(f"  - 총 문서 수: {stats['total_documents']}")
    print(f"  - 임베딩 차원: {stats['embedding_dim']}")
    print(f"  - 저장소 타입: {stats['vector_store_type']}")
    
    return vector_store


def test_step5_search(vector_store, embedder):
    """5단계: 검색 테스트"""
    print_section("5단계: 검색 파이프라인")
    
    # 테스트 질문
    question = "급여는 어떻게 계산되나요?"
    print(f"테스트 질문: \"{question}\"")
    
    # 질문 임베딩
    print("\n질문 임베딩 생성 중...")
    query_embedding = embedder.embed_query(question)
    print(f"  - 질문 벡터: [{query_embedding[0]:.4f}, {query_embedding[1]:.4f}, ..., {query_embedding[-1]:.4f}]")
    
    # 검색
    print("\n벡터 유사도 검색 중...")
    results = vector_store.search(
        query_embedding=query_embedding,
        top_k=3
    )
    
    print(f"\n검색 결과 ({len(results)}개):")
    for i, (doc, score) in enumerate(results):
        print(f"\n  결과 {i+1}:")
        print(f"    - 거리(distance): {score:.4f}")
        print(f"    - hierarchy_path: {doc.metadata.get('hierarchy_path', 'N/A')}")
        print(f"    - 텍스트 미리보기: {doc.page_content[:100]}...")
    
    return results


def test_full_pipeline_with_rag(file_path: str):
    """전체 RAG 파이프라인 테스트"""
    print_section("전체 RAG 파이프라인 테스트")
    
    file_path_obj = Path(file_path)
    print(f"테스트 파일: {file_path_obj.name}")
    
    # RAG 파이프라인 초기화
    print("\nRAG 파이프라인 초기화 중...")
    try:
        rag = RAGPipeline(load_existing=True)
        print("  - 기존 벡터 저장소 로드 완료")
    except Exception as e:
        print(f"  - 기존 저장소 없음, 새로 생성: {e}")
        rag = RAGPipeline(load_existing=False)
    
    # 문서 추가
    print("\n문서 추가 중...")
    extracted_dir = config.EXTRACTED_DIR / f"extracted_{file_path_obj.stem}"
    
    if not extracted_dir.exists():
        print(f"  - 추출 디렉토리 없음, 파싱 먼저 실행...")
        extract.process_single_file(str(file_path_obj))
    
    result = rag.add_document_from_extract(
        extracted_dir=extracted_dir,
        user_metadata={
            'user_id': 'test_user',
            'dept_id': 'test_dept',
            'project_id': 'test_project'
        }
    )
    
    print(f"\n문서 추가 결과:")
    print(f"  - doc_id: {result.get('doc_id')}")
    print(f"  - 추가된 청크 수: {result.get('chunks_added')}")
    
    # 질의응답 테스트
    print("\n질의응답 테스트...")
    question = "급여는 어떻게 계산되나요?"
    print(f"질문: \"{question}\"")
    
    answer_result = rag.query(question=question)
    
    print(f"\n답변:")
    print(f"  {answer_result.get('answer', 'N/A')[:500]}...")
    
    print(f"\n출처:")
    for src in answer_result.get('sources', [])[:3]:
        print(f"  - {src.get('hierarchy_path', 'N/A')}")
    
    return result


def main():
    """메인 함수"""
    print("\n" + "=" * 70)
    print("  실제 문서 색인 구조 시각화 - 파이프라인 검증 테스트")
    print("=" * 70)
    print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 테스트 파일 선택
    hwp_data_dir = PROJECT_ROOT / "hwp_data"
    
    # 사용 가능한 파일 목록
    print("\n사용 가능한 테스트 파일:")
    test_files = list(hwp_data_dir.glob("*.hwpx")) + list(hwp_data_dir.glob("*.hwp"))
    
    for i, f in enumerate(test_files[:10]):
        print(f"  {i+1}. {f.name}")
    
    # 첫 번째 HWPX 파일 사용
    hwpx_files = list(hwp_data_dir.glob("*.hwpx"))
    if not hwpx_files:
        print("\n[오류] HWPX 파일을 찾을 수 없습니다")
        return
    
    test_file = hwpx_files[0]
    print(f"\n선택된 테스트 파일: {test_file.name}")
    
    # 단계별 테스트
    try:
        # 1단계: 파싱
        extracted_dir = test_step1_parsing(str(test_file))
        if extracted_dir is None:
            return
        
        # 2단계: 청킹
        chunks = test_step2_chunking(extracted_dir)
        if chunks is None:
            return
        
        # 3단계: 임베딩
        embeddings = test_step3_embedding(chunks)
        
        # 4단계: 벡터 저장소
        vector_store = test_step4_vector_store(chunks, embeddings)
        
        # 5단계: 검색
        embedder = DocumentEmbedder()
        results = test_step5_search(vector_store, embedder)
        
        print_section("테스트 완료")
        print("모든 단계가 성공적으로 완료되었습니다!")
        print("\n이 결과는 '실제_문서_색인_구조_시각화.md' 문서의 내용을 검증합니다.")
        
    except Exception as e:
        print(f"\n[오류] 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

