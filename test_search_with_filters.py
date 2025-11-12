"""
메타데이터 필터링을 사용한 검색 테스트

ChromaDB의 where 필터링 기능이 제대로 동작하는지 확인합니다.
"""

import os
import sys
from pathlib import Path
import json

# 환경 변수 억제
os.environ["ORT_LOGGING_LEVEL"] = "3"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# 프로젝트 경로 설정
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from rag.pipeline import RAGPipeline
import config
from loguru import logger

# 로깅 설정
logger.remove()
logger.add(lambda msg: print(msg, end=""))


def check_documents_in_system():
    """시스템에 저장된 문서 확인"""
    print("\n" + "="*70)
    print("저장된 문서 현황 확인")
    print("="*70)
    
    try:
        pipeline = RAGPipeline(load_existing=True)
    except Exception as e:
        print(f"❌ Pipeline 초기화 실패: {e}")
        return False
    
    stats = pipeline.vector_store.get_collection_info()
    total_chunks = stats.get('count', 0)
    
    if total_chunks == 0:
        print("⚠️  저장된 청크가 없습니다.")
        print("먼저 다음을 실행하세요:")
        print("  1. python extract.py \"문서경로.hwp\"")
        print("  2. python auto_add.py")
        return False
    
    print(f"✓ 저장된 청크: {total_chunks}개")
    
    # 메타데이터 샘플 확인 (첫 5개)
    print(f"\n📋 메타데이터 샘플 (첫 5개):")
    results = pipeline.vector_store.collection.get(
        limit=5,
        include=['metadatas', 'documents']
    )
    
    for i, metadata in enumerate(results['metadatas']):
        print(f"\n  [{i+1}] 청크 {metadata.get('chunk_id')} - {metadata.get('doc_name')}")
        if metadata.get('hierarchy_path'):
            print(f"      위치: {metadata.get('hierarchy_path')}")
        print(f"      부서: {metadata.get('dept_id', '미설정')}")
        print(f"      프로젝트: {metadata.get('project_id', '미설정')}")
    
    return True


def test_simple_query():
    """기본 쿼리 테스트 (필터 없음)"""
    print("\n" + "="*70)
    print("테스트 1: 기본 쿼리 (필터 없음)")
    print("="*70)
    
    try:
        pipeline = RAGPipeline(load_existing=True)
    except Exception as e:
        print(f"❌ Pipeline 초기화 실패: {e}")
        return False
    
    stats = pipeline.vector_store.get_collection_info()
    if stats.get('count', 0) == 0:
        print("⚠️  저장된 문서가 없습니다.")
        return False
    
    # 테스트 쿼리
    question = "인사 관련 규정이 있나요?"
    print(f"\n🔍 질문: {question}")
    print(f"🎯 필터: 없음 (전체 검색)")
    
    try:
        result = pipeline.query(question, top_k=3, return_sources=True)
        
        print(f"\n✅ 답변:")
        print(f"   {result['answer'][:200]}...")
        
        print(f"\n📚 출처 ({len(result.get('sources', []))}개):")
        for i, source in enumerate(result.get('sources', [])[:3], 1):
            print(f"\n   [{i}] {source.get('doc_name')}")
            if source.get('hierarchy_path'):
                print(f"       위치: {source.get('hierarchy_path')}")
            print(f"       유사도: {source.get('score', 0):.4f}")
            print(f"       내용: {source.get('content_preview', '')[:100]}...")
        
        return True
    except Exception as e:
        print(f"❌ 쿼리 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dept_filter():
    """부서 필터링 테스트"""
    print("\n" + "="*70)
    print("테스트 2: 부서 필터링")
    print("="*70)
    
    try:
        pipeline = RAGPipeline(load_existing=True)
    except Exception as e:
        print(f"❌ Pipeline 초기화 실패: {e}")
        return False
    
    # 현재 저장된 부서 정보 확인
    print("\n📊 저장된 부서 현황:")
    all_results = pipeline.vector_store.collection.get(
        include=['metadatas']
    )
    
    depts = set()
    for metadata in all_results['metadatas']:
        dept = metadata.get('dept_id', '')
        if dept:
            depts.add(dept)
    
    if not depts:
        print("⚠️  부서 정보가 저장되지 않았습니다.")
        print("프론트엔드에서 부서를 입력받고 저장해야 합니다.")
        print("지금은 모든 문서가 dept_id = ''로 저장되어 있습니다.")
        return False
    
    print(f"발견된 부서: {depts}")
    
    # 첫 번째 부서로 필터링 테스트
    test_dept = list(depts)[0]
    
    question = "인사 관련 규정이 있나요?"
    where_filter = {"dept_id": test_dept}
    
    print(f"\n🔍 질문: {question}")
    print(f"🎯 필터: dept_id = '{test_dept}'")
    
    try:
        result = pipeline.query(question, top_k=3, where_filter=where_filter, return_sources=True)
        
        print(f"\n✅ 필터링된 검색 완료")
        print(f"   반환된 결과: {len(result.get('sources', []))}개")
        
        for i, source in enumerate(result.get('sources', [])[:3], 1):
            print(f"\n   [{i}] {source.get('doc_name')}")
            print(f"       부서: {source.get('dept_id')}")
            if source.get('hierarchy_path'):
                print(f"       위치: {source.get('hierarchy_path')}")
        
        return True
    except Exception as e:
        print(f"❌ 필터링 쿼리 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_chapter_filter():
    """장(Chapter) 필터링 테스트"""
    print("\n" + "="*70)
    print("테스트 3: 장(Chapter) 필터링")
    print("="*70)
    
    try:
        pipeline = RAGPipeline(load_existing=True)
    except Exception as e:
        print(f"❌ Pipeline 초기화 실패: {e}")
        return False
    
    # 현재 저장된 장 정보 확인
    print("\n📊 저장된 장 현황:")
    all_results = pipeline.vector_store.collection.get(
        include=['metadatas']
    )
    
    chapters = set()
    for metadata in all_results['metadatas']:
        chapter = metadata.get('chapter_number', '')
        if chapter:
            chapters.add(chapter)
    
    if not chapters:
        print("⚠️  장 정보가 저장되지 않았습니다.")
        print("문서가 제대로 파싱되고 청킹되었는지 확인하세요.")
        return False
    
    chapters_sorted = sorted(chapters, key=lambda x: int(x) if x.isdigit() else 999)
    print(f"발견된 장: {chapters_sorted}")
    
    # 첫 번째 장으로 필터링 테스트
    test_chapter = chapters_sorted[0]
    
    question = "어떤 내용이 있나요?"
    where_filter = {"chapter_number": test_chapter}
    
    print(f"\n🔍 질문: {question}")
    print(f"🎯 필터: chapter_number = '{test_chapter}'")
    
    try:
        result = pipeline.query(question, top_k=3, where_filter=where_filter, return_sources=True)
        
        print(f"\n✅ 필터링된 검색 완료")
        print(f"   반환된 결과: {len(result.get('sources', []))}개")
        
        for i, source in enumerate(result.get('sources', [])[:3], 1):
            print(f"\n   [{i}] {source.get('doc_name')}")
            print(f"       장: {source.get('chapter_number')} - {source.get('chapter_title')}")
            if source.get('article_number'):
                print(f"       조: {source.get('article_number')} - {source.get('article_title')}")
        
        return True
    except Exception as e:
        print(f"❌ 필터링 쿼리 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_complex_filter():
    """복합 필터링 테스트"""
    print("\n" + "="*70)
    print("테스트 4: 복합 필터링 (AND 조건)")
    print("="*70)
    
    try:
        pipeline = RAGPipeline(load_existing=True)
    except Exception as e:
        print(f"❌ Pipeline 초기화 실패: {e}")
        return False
    
    # 부서와 장 정보 확인
    all_results = pipeline.vector_store.collection.get(
        include=['metadatas']
    )
    
    depts = set()
    chapters = set()
    for metadata in all_results['metadatas']:
        dept = metadata.get('dept_id', '')
        chapter = metadata.get('chapter_number', '')
        if dept:
            depts.add(dept)
        if chapter:
            chapters.add(chapter)
    
    if not depts or not chapters:
        print("⚠️  필터링에 필요한 메타데이터가 부족합니다.")
        print(f"  - 부서 정보: {bool(depts)}")
        print(f"  - 장 정보: {bool(chapters)}")
        return False
    
    test_dept = list(depts)[0]
    test_chapter = list(chapters)[0]
    
    question = "규정 내용이 있나요?"
    where_filter = {
        "$and": [
            {"dept_id": test_dept},
            {"chapter_number": test_chapter}
        ]
    }
    
    print(f"\n🔍 질문: {question}")
    print(f"🎯 필터: dept_id = '{test_dept}' AND chapter_number = '{test_chapter}'")
    
    try:
        result = pipeline.query(question, top_k=3, where_filter=where_filter, return_sources=True)
        
        print(f"\n✅ 복합 필터링 검색 완료")
        print(f"   반환된 결과: {len(result.get('sources', []))}개")
        
        for i, source in enumerate(result.get('sources', [])[:3], 1):
            print(f"\n   [{i}] {source.get('doc_name')}")
            print(f"       부서: {source.get('dept_id')}")
            print(f"       장: {source.get('chapter_number')} - {source.get('chapter_title')}")
        
        return True
    except Exception as e:
        print(f"❌ 복합 필터링 쿼리 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """전체 테스트 실행"""
    print("\n" + "🧪 메타데이터 필터링 검색 테스트" + "\n")
    
    # 문서 현황 확인
    if not check_documents_in_system():
        print("\n❌ 테스트 중단: 저장된 문서가 필요합니다.")
        return
    
    # 테스트 실행
    tests = [
        ("기본 쿼리", test_simple_query),
        ("부서 필터링", test_dept_filter),
        ("장 필터링", test_chapter_filter),
        ("복합 필터링", test_complex_filter)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = "✅ 성공" if result else "⚠️  부분 성공"
        except Exception as e:
            print(f"\n❌ 오류: {e}")
            results[test_name] = f"❌ 실패"
    
    # 최종 요약
    print("\n" + "="*70)
    print("📊 테스트 결과 요약")
    print("="*70)
    
    for test_name, result in results.items():
        print(f"{result} - {test_name}")
    
    print("\n" + "="*70)
    print("💡 참고사항")
    print("="*70)
    print("""
1. 부서/프로젝트 필터링:
   - 프론트엔드에서 입력받은 데이터가 필요합니다
   - 현재는 모든 문서가 기본값('')으로 저장되어 있습니다
   - 백엔드 API 구현 시 user_metadata 전달 필요

2. 장/조 필터링:
   - 자동 추출되므로 문서가 잘 파싱되면 동작합니다
   - 구조 정보가 빠진 경우 테스트할 수 없습니다

3. 검색 쿼리 사용 예시:
   
   # 부서 필터링
   result = rag.query(
       question="휴가 규정은?",
       where_filter={"dept_id": "HR"}
   )
   
   # 복합 필터링
   result = rag.query(
       question="휴가 규정은?",
       where_filter={
           "$and": [
               {"dept_id": "HR"},
               {"chapter_number": "5"}
           ]
       }
   )
    """)


if __name__ == "__main__":
    main()

