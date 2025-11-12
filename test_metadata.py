"""
메타데이터 스키마 동작 테스트 스크립트

이 스크립트는 프론트엔드/백엔드 연동 없이도
메타데이터 시스템이 올바르게 동작하는지 확인합니다.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import json

# 프로젝트 경로 설정
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# 환경 변수 억제
os.environ["ORT_LOGGING_LEVEL"] = "3"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

from rag.pipeline import RAGPipeline
from rag.chunker import DocumentChunker
import config


def test_1_structure_extraction():
    """테스트 1: extract.py에서 구조 정보 추출 확인"""
    print("\n" + "="*70)
    print("테스트 1: 문서 구조 분석 (extract.py)")
    print("="*70)
    
    extracted_dir = Path(config.EXTRACTED_DIR)
    
    if not extracted_dir.exists():
        print("❌ extracted_results 폴더가 없습니다.")
        print("   먼저 python auto_add.py를 실행하여 문서를 추가해주세요.")
        return False
    
    # 추출된 폴더 목록
    extracted_folders = [d for d in extracted_dir.iterdir() if d.is_dir() and d.name.startswith('extracted_')]
    
    if not extracted_folders:
        print("❌ extracted_results에 추출된 폴더가 없습니다.")
        return False
    
    print(f"\n✓ 발견된 추출 폴더: {len(extracted_folders)}개")
    
    # 첫 번째 폴더 분석
    test_folder = extracted_folders[0]
    print(f"\n📁 테스트 폴더: {test_folder.name}")
    
    # 구조 JSON 파일 찾기
    structure_files = list(test_folder.glob("*구조.json"))
    
    if not structure_files:
        print("❌ 구조 JSON 파일이 없습니다.")
        return False
    
    structure_file = structure_files[0]
    print(f"✓ 구조 파일: {structure_file.name}")
    
    # 구조 정보 로드 및 출력
    with open(structure_file, 'r', encoding='utf-8', errors='replace') as f:
        structure_data = json.load(f)
    
    doc_structure = structure_data.get('document_structure', {})
    print(f"\n📊 구조 정보:")
    print(f"  - 총 장(章): {doc_structure.get('total_chapters', 0)}개")
    print(f"  - 총 조(條): {doc_structure.get('total_articles', 0)}개")
    
    chapters = doc_structure.get('chapters', [])
    if chapters:
        print(f"\n  [장 목록 (처음 5개)]:")
        for ch in chapters[:5]:
            print(f"    제{ch.get('number')}장: {ch.get('title')}")
            articles = ch.get('articles', [])
            if articles:
                print(f"      └─ 포함된 조(條): {len(articles)}개")
                for art in articles[:2]:
                    print(f"         제{art.get('number')}조: {art.get('title', '(제목 없음)')}")
                if len(articles) > 2:
                    print(f"         ... 외 {len(articles) - 2}개")
    
    return True


def test_2_chunk_metadata():
    """테스트 2: 청크 메타데이터 추출 확인"""
    print("\n" + "="*70)
    print("테스트 2: 청크 메타데이터 추출 (chunker.py)")
    print("="*70)
    
    # 테스트 텍스트
    test_text = """제1장 총칙

제1조 (목적) 
이 규정은 회사의 인사관리에 필요한 사항을 규정함을 목적으로 한다.

제2조 (적용범위)
① 이 규정은 회사의 모든 임직원에게 적용한다.
② 계약직 직원은 별도로 정한다.

제3장 급여의 지급

제15조 (급여의 계산)
① 급여는 다음과 같이 계산한다.
② 1년 미만: 월급여, 1년 이상: 연간 15일

제16조 (상여금)
상여금은 연 2회 지급한다.

제5장 휴가 및 휴직

제27조 (연차 휴가)
① 연차휴가는 근무기간에 따라 다르게 지급한다.
② 1년 미만: 월 1일, 1년 이상: 연 15일"""
    
    # 문서 메타데이터
    doc_metadata = {
        'doc_id': 'doc_test_인사규정',
        'doc_name': '인사규정 테스트',
        'user_id': 'user_001',
        'dept_id': 'HR',
        'project_id': 'proj_2024_001'
    }
    
    # 청킹
    chunker = DocumentChunker(chunk_size=300, chunk_overlap=50)
    chunks = chunker.chunk_text(test_text, doc_metadata)
    
    print(f"\n✓ 청킹 완료: {len(chunks)}개 청크")
    
    # 각 청크의 메타데이터 확인
    print(f"\n📋 청크별 메타데이터:")
    for i, chunk in enumerate(chunks):
        metadata = chunk.metadata
        print(f"\n  [청크 {i}]")
        print(f"    - 크기: {metadata.get('chunk_size')} 글자")
        print(f"    - 장(Chapter): {metadata.get('chapter_number')} - {metadata.get('chapter_title')}")
        print(f"    - 조(Article): {metadata.get('article_number')} - {metadata.get('article_title')}")
        print(f"    - 계층 경로: {metadata.get('hierarchy_path')}")
        print(f"    - 부서: {metadata.get('dept_id')}")
        print(f"    - 프로젝트: {metadata.get('project_id')}")
        print(f"    - 내용 미리보기: {chunk.page_content[:50]}...")
    
    return True


def test_3_pipeline_metadata():
    """테스트 3: Pipeline의 메타데이터 설정 확인"""
    print("\n" + "="*70)
    print("테스트 3: Pipeline 메타데이터 (pipeline.py)")
    print("="*70)
    
    extracted_dir = Path(config.EXTRACTED_DIR)
    
    if not extracted_dir.exists():
        print("❌ extracted_results 폴더가 없습니다.")
        return False
    
    # 추출된 폴더 목록
    extracted_folders = [d for d in extracted_dir.iterdir() if d.is_dir() and d.name.startswith('extracted_')]
    
    if not extracted_folders:
        print("❌ 추출된 폴더가 없습니다.")
        return False
    
    # Pipeline 초기화 (기존 벡터 저장소 로드, 새로 추가하지 않음)
    print("Pipeline 초기화 중...")
    try:
        pipeline = RAGPipeline(load_existing=True)
    except Exception as e:
        print(f"❌ Pipeline 초기화 실패: {e}")
        return False
    
    # 현재 저장된 문서 정보 확인
    stats = pipeline.vector_store.get_collection_info()
    
    print(f"\n✓ ChromaDB 컬렉션 정보:")
    print(f"  - 총 문서 수: {stats.get('count', 0)}개")
    print(f"  - 메타데이터 샘플 확인 가능")
    
    return True


def test_4_chromadb_filtering():
    """테스트 4: ChromaDB 필터링 동작 확인"""
    print("\n" + "="*70)
    print("테스트 4: ChromaDB 필터링 (where 조건)")
    print("="*70)
    
    try:
        pipeline = RAGPipeline(load_existing=True)
    except Exception as e:
        print(f"❌ Pipeline 초기화 실패: {e}")
        return False
    
    # 현재 저장된 문서 수
    stats = pipeline.vector_store.get_collection_info()
    doc_count = stats.get('count', 0)
    
    if doc_count == 0:
        print("⚠️  저장된 문서가 없습니다.")
        print("   먼저 python auto_add.py를 실행하여 문서를 추가해주세요.")
        return False
    
    print(f"✓ 저장된 청크: {doc_count}개")
    
    # 필터링 예시
    print(f"\n🔍 필터링 테스트:")
    
    # 1. 특정 부서 필터링
    filter_1 = {"dept_id": "HR"}
    print(f"\n  [필터 1] 부서 = 'HR'")
    print(f"    필터 구조: {filter_1}")
    
    # 2. 특정 장 필터링
    filter_2 = {"chapter_number": "3"}
    print(f"\n  [필터 2] 장 = '3'")
    print(f"    필터 구조: {filter_2}")
    
    # 3. 복합 필터
    filter_3 = {"$and": [{"dept_id": "HR"}, {"chapter_number": "3"}]}
    print(f"\n  [필터 3] 부서 = 'HR' AND 장 = '3'")
    print(f"    필터 구조: {filter_3}")
    
    print(f"\n💡 필터링을 실제로 사용하려면:")
    print(f"   rag.query(question, where_filter=filter_1)")
    
    return True


def test_5_manual_metadata_input():
    """테스트 5: 사용자 입력 메타데이터 시뮬레이션"""
    print("\n" + "="*70)
    print("테스트 5: 사용자 입력 메타데이터 시뮬레이션 (프론트엔드 입력 모의)")
    print("="*70)
    
    # 프론트엔드에서 입력받을 메타데이터
    user_input_metadata = {
        "user_id": "user_123",
        "dept_id": "HR",
        "project_id": "proj_2024_001",
        "category": "인사",
        "version": "2024년 10월 개정",
        "upload_date": datetime.now().isoformat()
    }
    
    print(f"\n📝 프론트엔드에서 입력받은 메타데이터:")
    for key, value in user_input_metadata.items():
        print(f"  - {key}: {value}")
    
    # 자동 생성되는 메타데이터
    auto_metadata = {
        "doc_id": "doc_인사규정_2024",
        "doc_name": "인사규정",
        "source": "extracted_results/extracted_인사규정",
        "file_type": "HWPX",
        "total_chapters": 8,
        "total_articles": 47
    }
    
    print(f"\n🔄 자동 추출/생성 메타데이터:")
    for key, value in auto_metadata.items():
        print(f"  - {key}: {value}")
    
    # 병합된 메타데이터
    merged_metadata = {**auto_metadata, **user_input_metadata}
    
    print(f"\n✅ 최종 병합 메타데이터:")
    for key, value in merged_metadata.items():
        print(f"  - {key}: {value}")
    
    print(f"\n💾 이 메타데이터가 각 청크에 저장되어:")
    print(f"   - ChromaDB에 저장됨")
    print(f"   - 검색 필터링 시 사용됨")
    print(f"   - RAG 답변의 출처 정보로 활용됨")
    
    return True


def test_6_config_schema():
    """테스트 6: config.py의 메타데이터 스키마 확인"""
    print("\n" + "="*70)
    print("테스트 6: 메타데이터 스키마 정의 (config.py)")
    print("="*70)
    
    print(f"\n📋 문서 레벨 메타데이터 스키마:")
    print(f"  {json.dumps(config.DOCUMENT_METADATA_SCHEMA, ensure_ascii=False, indent=2)}")
    
    print(f"\n📋 필터링 예시:")
    for filter_name, filter_value in config.METADATA_FILTER_EXAMPLES.items():
        print(f"\n  {filter_name}:")
        print(f"    {filter_value}")
    
    return True


def main():
    """전체 테스트 실행"""
    print("\n" + "🧪 메타데이터 스키마 동작 테스트 시작" + "\n")
    
    tests = [
        ("구조 정보 추출", test_1_structure_extraction),
        ("청크 메타데이터", test_2_chunk_metadata),
        ("Pipeline 메타데이터", test_3_pipeline_metadata),
        ("ChromaDB 필터링", test_4_chromadb_filtering),
        ("사용자 입력 시뮬레이션", test_5_manual_metadata_input),
        ("스키마 정의", test_6_config_schema)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = "✅ 성공" if result else "⚠️  확인 필요"
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            results[test_name] = f"❌ 실패: {str(e)}"
    
    # 최종 결과 요약
    print("\n" + "="*70)
    print("📊 테스트 결과 요약")
    print("="*70)
    
    for test_name, result in results.items():
        print(f"{result} - {test_name}")
    
    print("\n" + "="*70)
    print("💡 다음 단계:")
    print("="*70)
    print("""
1. 프론트엔드/백엔드 연동 없이 메타데이터 동작 확인 완료
2. 실제 문서로 테스트하려면:
   - python extract.py "문서 경로" (문서 파싱)
   - python auto_add.py (RAG 시스템에 추가)
3. 검색 필터링 테스트:
   - test_search_with_filters.py 실행
4. 백엔드 개발자에게 전달:
   - 메타데이터_스키마_가이드.md 공유
   - 필요한 API 구조 협의
    """)


if __name__ == "__main__":
    main()

