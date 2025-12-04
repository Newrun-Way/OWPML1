"""
TableProcessor 테스트
"""

import json
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rag.table_processor import TableProcessor


def test_table_processor():
    """TableProcessor 통합 테스트"""
    
    print("\n" + "=" * 60)
    print("TableProcessor 테스트 시작")
    print("=" * 60)
    
    # 1. 초기화
    print("\n1. TableProcessor 초기화")
    processor = TableProcessor(extracted_dir=Path("extracted_results"))
    print(f"   [OK] 초기화 완료")
    
    # 2. 실제 문서에서 표 데이터 로드 테스트
    print("\n2. 표 데이터 로드 테스트")
    
    # extracted_results 디렉토리의 문서들 확인
    extracted_dir = Path("extracted_results")
    if not extracted_dir.exists():
        print(f"   [ERROR] {extracted_dir} 디렉토리가 없습니다.")
        return
    
    doc_dirs = list(extracted_dir.glob("extracted_*"))
    if not doc_dirs:
        print(f"   [ERROR] 추출된 문서가 없습니다.")
        return
    
    print(f"   발견된 문서: {len(doc_dirs)}개")
    
    for doc_dir in doc_dirs[:3]:  # 처음 3개만 테스트
        doc_name = doc_dir.stem.replace("extracted_", "")
        print(f"\n   문서: {doc_name}")
        
        # 표 데이터 로드
        tables = processor.load_tables_from_doc(doc_name)
        print(f"     - 표 개수: {len(tables)}개")
        
        if tables:
            # 첫 번째 표 테스트
            table_id = list(tables.keys())[0]
            table_data = tables[table_id]
            
            print(f"     - 첫 번째 표 ID: {table_id}")
            print(f"     - 행 개수: {len(table_data.get('rows', []))}개")
            
            # HTML 변환 테스트
            html = processor.table_to_html(table_data)
            print(f"     - HTML 길이: {len(html)} 글자")
            
            # Markdown 변환 테스트
            markdown = processor.table_to_markdown(table_data)
            print(f"     - Markdown 길이: {len(markdown)} 글자")
    
    # 3. 컨텍스트 처리 테스트
    print("\n3. 컨텍스트 처리 테스트")
    
    if doc_dirs:
        doc_name = doc_dirs[0].stem.replace("extracted_", "")
        tables = processor.load_tables_from_doc(doc_name)
        
        if tables:
            table_id = list(tables.keys())[0]
            
            # 테스트 컨텍스트
            test_contexts = [
                {
                    "content": "이것은 테스트 컨텍스트입니다.",
                    "metadata": {
                        "doc_name": doc_name,
                        "table_id": table_id,
                        "hierarchy_path": "제1장 > 제1조"
                    }
                }
            ]
            
            # 표 추출
            extracted_tables = processor.extract_tables_from_contexts(
                test_contexts, 
                format='both'
            )
            
            print(f"   추출된 표 수: {len(extracted_tables)}개")
            if extracted_tables:
                print(f"   첫 번째 표:")
                print(f"     - table_id: {extracted_tables[0]['table_id']}")
                print(f"     - doc_name: {extracted_tables[0]['doc_name']}")
                print(f"     - location: {extracted_tables[0]['location']}")
                print(f"     - HTML 포함: {'예' if extracted_tables[0]['html'] else '아니오'}")
                print(f"     - Markdown 포함: {'예' if extracted_tables[0]['markdown'] else '아니오'}")
    
    print("\n" + "=" * 60)
    print("테스트 완료!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    test_table_processor()

