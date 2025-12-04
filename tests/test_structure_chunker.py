"""
StructureAwareChunker 테스트
"""

import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rag.structure_chunker import StructureAwareChunker


def test_structure_chunker():
    """StructureAwareChunker 통합 테스트"""
    
    print("\n" + "=" * 60)
    print("StructureAwareChunker 테스트 시작")
    print("=" * 60)
    
    # 테스트 텍스트
    test_text = """제3장 급여 및 수당

제15조 (급여의 계산) ① 직원의 월 급여는 기본급과 각종 수당을 합산하여 지급한다. ② 기본급은 직급별로 다음 표와 같이 정한다.

[표: 직급별 기본급 및 수당]
직급 | 기본급 | 직책수당 | 합계
과장 | 3,500,000원 | 300,000원 | 3,800,000원
차장 | 4,200,000원 | 500,000원 | 4,700,000원
부장 | 5,000,000원 | 700,000원 | 5,700,000원

③ 기본급은 매년 1월 1일 기준으로 조정할 수 있다. ④ 조정 비율은 전년도 물가상승률과 경영실적을 고려하여 이사회에서 결정한다.

제16조 (수당의 종류) ① 직원에게 지급하는 수당의 종류는 다음 각 호와 같다.
1. 직책수당: 과장급 이상 직원에게 지급
2. 야간근무수당: 22시 이후 근무 시 시간당 15,000원
3. 주말근무수당: 토요일 또는 일요일 근무 시 시간당 20,000원
4. 자격수당: 업무 관련 국가자격증 소지자에게 월 50,000원

② 수당은 매월 급여일에 기본급과 함께 지급한다. ③ 수당의 종류와 금액은 경영상황에 따라 조정할 수 있다.

제17조 (급여의 지급일) ① 급여는 매월 25일에 지급한다. ② 지급일이 토요일 또는 공휴일인 경우 그 전일에 지급한다.

제18조 (급여의 공제) ① 급여에서 다음 각 호의 금액을 공제한다.
1. 소득세
2. 지방소득세
3. 국민연금
4. 건강보험료
5. 고용보험료

② 회사는 법령에서 정한 바에 따라 원천징수 의무를 이행한다."""
    
    # 1. 초기화
    print("\n1. StructureAwareChunker 초기화")
    chunker = StructureAwareChunker(
        max_chunk_size=800,
        min_chunk_size=200,
        overlap_size=100
    )
    print(f"   [OK] 초기화 완료")
    print(f"     - max_chunk_size: 800")
    print(f"     - min_chunk_size: 200")
    print(f"     - overlap_size: 100")
    
    # 2. 문서 구조 파싱 테스트
    print("\n2. 문서 구조 파싱 테스트")
    sections = chunker.parse_document_structure(test_text)
    print(f"   파싱된 섹션 수: {len(sections)}개")
    
    article_sections = [s for s in sections if s['type'] == 'article']
    print(f"   조(Article) 수: {len(article_sections)}개")
    
    for section in article_sections:
        print(f"     - 제{section['number']}조 ({section['title']}): {len(section['text'])} 글자")
    
    # 3. 구조 기반 청킹 테스트
    print("\n3. 구조 기반 청킹 테스트")
    metadata = {
        'doc_name': '급여규정',
        'user_id': 'test_user'
    }
    chunks = chunker.chunk_by_structure(test_text, metadata)
    
    print(f"   생성된 청크 수: {len(chunks)}개")
    
    total_length = 0
    for i, chunk in enumerate(chunks):
        chunk_len = len(chunk.page_content)
        total_length += chunk_len
        
        print(f"\n   [청크 {i+1}]")
        print(f"     - 크기: {chunk_len} 글자")
        print(f"     - hierarchy_path: {chunk.metadata.get('hierarchy_path', 'N/A')}")
        print(f"     - article_number: {chunk.metadata.get('article_number', 'N/A')}")
        print(f"     - article_title: {chunk.metadata.get('article_title', 'N/A')}")
        print(f"     - 미리보기: {chunk.page_content[:100]}...")
    
    print(f"\n   통계:")
    print(f"     - 원본 텍스트 길이: {len(test_text)} 글자")
    print(f"     - 청크 평균 크기: {total_length // len(chunks)} 글자")
    
    # 4. 실제 문서 테스트
    print("\n4. 실제 문서 테스트")
    
    extracted_dir = Path("extracted_results")
    if extracted_dir.exists():
        doc_dirs = list(extracted_dir.glob("extracted_*"))
        
        if doc_dirs:
            # 첫 번째 문서 테스트
            doc_dir = doc_dirs[0]
            doc_name = doc_dir.stem.replace("extracted_", "")
            
            # 전체텍스트 파일 찾기
            text_file = None
            for file in doc_dir.glob("*전체텍스트*"):
                text_file = file
                break
            
            if text_file:
                print(f"   문서: {doc_name}")
                
                # 텍스트 로드
                with open(text_file, 'r', encoding='utf-8', errors='replace') as f:
                    doc_text = f.read()
                
                print(f"     - 텍스트 길이: {len(doc_text)} 글자")
                
                # 구조 기반 청킹
                metadata = {'doc_name': doc_name}
                doc_chunks = chunker.chunk_by_structure(doc_text, metadata)
                
                print(f"     - 생성된 청크 수: {len(doc_chunks)}개")
                
                # 구조별 통계
                chapters = set()
                articles = set()
                for chunk in doc_chunks:
                    ch_num = chunk.metadata.get('chapter_number')
                    ar_num = chunk.metadata.get('article_number')
                    if ch_num:
                        chapters.add(ch_num)
                    if ar_num:
                        articles.add(ar_num)
                
                print(f"     - 장(Chapter) 수: {len(chapters)}개")
                print(f"     - 조(Article) 수: {len(articles)}개")
            else:
                print(f"   [ERROR] 텍스트 파일을 찾을 수 없습니다.")
        else:
            print(f"   [ERROR] 추출된 문서가 없습니다.")
    else:
        print(f"   [ERROR] {extracted_dir} 디렉토리가 없습니다.")
    
    print("\n" + "=" * 60)
    print("테스트 완료!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    test_structure_chunker()

