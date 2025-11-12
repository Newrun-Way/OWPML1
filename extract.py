"""
HWP/HWPX 통합 추출 스크립트
- HWPX: 텍스트 + 표 + 이미지 완벽 추출
- HWP: 텍스트 추출

사용법:
    단일 파일: python extract.py <파일경로>
    폴더 처리: python extract.py <폴더경로>
    
예시:
    python extract.py "문서.hwpx"
    python extract.py "hwp data/"
"""

import zipfile
import xml.etree.ElementTree as ET
import json
import os
import sys
import io
import re
from pathlib import Path
from jpype_setup import init_jpype

# Windows에서 UTF-8 출력을 위한 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def analyze_document_structure(text_lines):
    """
    문서 텍스트에서 구조 정보 추출 (장/조/항)
    
    Args:
        text_lines: 문서 텍스트 줄 리스트
    
    Returns:
        dict: {
            'chapters': [...],  # 장 정보
            'articles': [...],  # 조 정보
            'structure_map': {...}  # 줄 번호 → 구조 정보 매핑
        }
    """
    structure = {
        'chapters': [],
        'articles': [],
        'structure_map': {}  # line_idx -> structure_info
    }
    
    current_chapter = None
    current_article = None
    
    # 정규식 패턴
    patterns = {
        'chapter': re.compile(r'^제\s*(\d+)\s*장\s+(.+)$'),  # 제1장 총칙
        'article': re.compile(r'^제\s*(\d+)\s*조\s*(?:\((.+?)\))?(.*)$'),  # 제5조 (급여의 계산)
        'paragraph': re.compile(r'^([①②③④⑤⑥⑦⑧⑨⑩]|\d+\))\s*(.*)$'),  # ① 내용, 1) 내용
        'subparagraph': re.compile(r'^([가나다라마바사아자차카타파하])\.\s+(.*)$')  # 가. 내용
    }
    
    for line_idx, line in enumerate(text_lines):
        line = line.strip()
        if not line:
            continue
        
        # 장(Chapter) 감지
        chapter_match = patterns['chapter'].match(line)
        if chapter_match:
            chapter_num = chapter_match.group(1)
            chapter_title = chapter_match.group(2).strip()
            
            current_chapter = {
                'number': chapter_num,
                'title': chapter_title,
                'line_idx': line_idx,
                'articles': []
            }
            structure['chapters'].append(current_chapter)
            structure['structure_map'][line_idx] = {
                'type': 'chapter',
                'number': chapter_num,
                'title': chapter_title
            }
            continue
        
        # 조(Article) 감지
        article_match = patterns['article'].match(line)
        if article_match:
            article_num = article_match.group(1)
            article_title = article_match.group(2).strip() if article_match.group(2) else ''
            
            current_article = {
                'number': article_num,
                'title': article_title,
                'line_idx': line_idx,
                'chapter_num': current_chapter['number'] if current_chapter else None,
                'paragraphs': []
            }
            
            if current_chapter:
                current_chapter['articles'].append(current_article)
            
            structure['articles'].append(current_article)
            structure['structure_map'][line_idx] = {
                'type': 'article',
                'number': article_num,
                'title': article_title,
                'chapter_num': current_chapter['number'] if current_chapter else None
            }
            continue
        
        # 항(Paragraph) 감지
        para_match = patterns['paragraph'].match(line)
        if para_match:
            para_num = para_match.group(1)
            
            # 한글 숫자 변환
            korean_numbers = {'①': '1', '②': '2', '③': '3', '④': '4', '⑤': '5',
                            '⑥': '6', '⑦': '7', '⑧': '8', '⑨': '9', '⑩': '10'}
            para_num_normalized = korean_numbers.get(para_num, para_num.rstrip(')'))
            
            if current_article:
                current_article['paragraphs'].append({
                    'number': para_num_normalized,
                    'line_idx': line_idx
                })
            
            structure['structure_map'][line_idx] = {
                'type': 'paragraph',
                'number': para_num_normalized,
                'article_num': current_article['number'] if current_article else None,
                'chapter_num': current_chapter['number'] if current_chapter else None
            }
            continue
        
        # 호(Subparagraph) 감지
        subpara_match = patterns['subparagraph'].match(line)
        if subpara_match:
            subpara_letter = subpara_match.group(1)
            
            structure['structure_map'][line_idx] = {
                'type': 'subparagraph',
                'letter': subpara_letter,
                'article_num': current_article['number'] if current_article else None,
                'chapter_num': current_chapter['number'] if current_chapter else None
            }
    
    return structure


def build_hierarchy_path(structure_info):
    """
    구조 정보로부터 계층 경로 생성
    예: "제3장 급여의 지급 > 제15조 급여의 계산 > 제1항"
    """
    parts = []
    
    if structure_info.get('chapter_num'):
        if structure_info.get('chapter_title'):
            parts.append(f"제{structure_info['chapter_num']}장 {structure_info['chapter_title']}")
        else:
            parts.append(f"제{structure_info['chapter_num']}장")
    
    if structure_info.get('article_num'):
        if structure_info.get('article_title'):
            parts.append(f"제{structure_info['article_num']}조 {structure_info['article_title']}")
        else:
            parts.append(f"제{structure_info['article_num']}조")
    
    if structure_info.get('paragraph_num'):
        parts.append(f"제{structure_info['paragraph_num']}항")
    
    return " > ".join(parts) if parts else ""


def extract_hwpx_with_structure(hwpx_path, output_dir="extracted_data"):
    """HWPX 파일에서 구조화된 데이터 추출"""
    
    os.makedirs(output_dir, exist_ok=True)
    
    result = {
        "text_content": [],
        "tables": [],
        "images": [],
        "metadata": {},
        "paragraphs": [],
        "file_type": "HWPX"
    }
    
    # HWPX는 ZIP 파일
    with zipfile.ZipFile(hwpx_path, 'r') as z:
        
        # 메타데이터 추출
        try:
            header_xml = z.read('Contents/header.xml').decode('utf-8')
            header_root = ET.fromstring(header_xml)
            result["metadata"]["header"] = "추출됨"
        except:
            pass
        
        # Section 파일들 처리
        section_files = [f for f in z.namelist() if f.startswith('Contents/section') and f.endswith('.xml')]
        
        for section_file in section_files:
            section_xml = z.read(section_file).decode('utf-8')
            root = ET.fromstring(section_xml)
            
            # 네임스페이스 정의
            ns = {
                'hp': 'http://www.hancom.co.kr/hwpml/2011/paragraph',
                'hc': 'http://www.hancom.co.kr/hwpml/2011/core'
            }
            
            # 텍스트 추출 (단락별)
            paragraphs = root.findall('.//hp:p', ns)
            for i, para in enumerate(paragraphs):
                para_text = ''.join(para.itertext()).strip()
                if para_text:
                    result["paragraphs"].append({
                        "id": i,
                        "text": para_text,
                        "type": "paragraph"
                    })
                    result["text_content"].append(para_text)
            
            # 표(Table) 추출
            tables = root.findall('.//hp:tbl', ns)
            for t_idx, table in enumerate(tables):
                table_data = {
                    "id": t_idx,
                    "type": "table",
                    "rows": [],
                    "summary": ""
                }
                
                # 표의 각 행(tr) 처리
                rows = table.findall('.//hp:tr', ns)
                for row in rows:
                    cells = []
                    # 각 셀(tc) 처리
                    for cell in row.findall('.//hp:tc', ns):
                        cell_text = ''.join(cell.itertext()).strip()
                        cells.append(cell_text)
                    if cells:
                        table_data["rows"].append(cells)
                
                if table_data["rows"]:
                    # 표 요약 생성
                    table_data["summary"] = f"표 {t_idx + 1}: {len(table_data['rows'])}행 × {len(table_data['rows'][0])}열"
                    result["tables"].append(table_data)
                    
                    # 텍스트 컨텐츠에도 표시
                    result["text_content"].append(f"\n[{table_data['summary']}]\n")
        
        # 이미지 추출
        image_files = [f for f in z.namelist() if f.startswith('BinData/') and 
                      any(f.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif'])]
        
        for img_file in image_files:
            img_data = z.read(img_file)
            img_name = os.path.basename(img_file)
            
            # 이미지 파일 저장
            img_path = os.path.join(output_dir, img_name)
            with open(img_path, 'wb') as f:
                f.write(img_data)
            
            result["images"].append({
                "filename": img_name,
                "path": img_path,
                "size": len(img_data)
            })
    
    return result


def extract_hwp_text(hwp_jar_path, hwp_path):
    """HWP 파일에서 텍스트 추출"""
    
    result = {
        "text_content": [],
        "tables": [],
        "images": [],
        "metadata": {},
        "paragraphs": [],
        "file_type": "HWP"
    }
    
    try:
        # jpype 초기화 (JAVA_HOME 자동 설정 + JVM 시작)
        jpype = init_jpype(hwp_jar_path)
    except RuntimeError as e:
        # JVM 시작 실패 시 상세 오류 메시지
        raise RuntimeError(
            f"[HWP 추출 실패] JVM 시작 오류:\n"
            f"{str(e)}\n\n"
            f"해결 방법:\n"
            f"1. Java 설치 확인: java -version\n"
            f"2. 환경 설정 테스트: python3 jpype_setup.py\n"
            f"3. 폴더 일괄 처리는 HWP 파일을 각각 다른 프로세스로 처리하세요:\n"
            f"   for f in *.hwp; do python3 extract.py \"$f\"; done"
        )
    
    try:
        # Java 패키지 가져오기
        HWPReader_class = jpype.JPackage('kr.dogfoot.hwplib.reader')
        TextExtrac_class = jpype.JPackage('kr.dogfoot.hwplib.tool.textextractor')
        HWPReader_ = HWPReader_class.HWPReader
        TextExtractMethod_ = TextExtrac_class.TextExtractMethod
        TextExtractor_ = TextExtrac_class.TextExtractor
        
        # HWP 파일 읽기
        hwp_file = HWPReader_.fromFile(hwp_path)
        
        # 전체 텍스트 추출
        full_text = TextExtractor_.extract(hwp_file, TextExtractMethod_.InsertControlTextBetweenParagraphText)
        result["text_content"] = [full_text]
        
        # 메타데이터
        result["metadata"]["note"] = "HWP 파일은 텍스트만 추출됩니다. 표/이미지가 필요하면 HWPX로 저장하세요."
        
    except Exception as e:
        raise RuntimeError(
            f"[HWP 파일 파싱 실패]: {str(e)}\n"
            f"파일: {hwp_path}"
        )
    
    return result


def save_results(result, output_dir="extracted_data"):
    """추출 결과를 파일로 저장"""
    
    # 출력 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)
    
    base_name = Path(output_dir).stem
    
    # 1. 전체 텍스트 저장
    text_file = os.path.join(output_dir, f"{base_name}_전체텍스트.txt")
    with open(text_file, 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(result["text_content"]))
    
    # 2. 표 데이터 저장 (HWPX만)
    table_json = None
    table_txt = None
    if result["tables"]:
        table_json = os.path.join(output_dir, f"{base_name}_표데이터.json")
        with open(table_json, 'w', encoding='utf-8') as f:
            json.dump(result["tables"], f, ensure_ascii=False, indent=2)
        
        # 표 데이터를 읽기 쉬운 텍스트로도 저장
        table_txt = os.path.join(output_dir, f"{base_name}_표목록.txt")
        with open(table_txt, 'w', encoding='utf-8') as f:
            for table in result["tables"]:
                f.write(f"\n{'='*60}\n")
                f.write(f"{table['summary']}\n")
                f.write(f"{'='*60}\n\n")
                for row in table["rows"]:
                    f.write(" | ".join(row) + "\n")
                f.write("\n")
    
    # 3. 문서 구조 분석 및 저장
    # 전체 텍스트를 줄 단위로 분리하여 구조 분석
    full_text = '\n\n'.join(result["text_content"])
    text_lines = full_text.split('\n')
    doc_structure = analyze_document_structure(text_lines)
    
    # 구조 정보 저장
    structure_json = os.path.join(output_dir, f"{base_name}_구조.json")
    save_result = {
        "file_type": result["file_type"],
        "text_paragraphs": result["paragraphs"],
        "tables_count": len(result["tables"]),
        "images_count": len(result["images"]),
        "images_list": [img["filename"] for img in result["images"]],
        "metadata": result["metadata"],
        # 문서 구조 정보 추가
        "document_structure": {
            "chapters": doc_structure['chapters'],
            "articles": doc_structure['articles'],
            "total_chapters": len(doc_structure['chapters']),
            "total_articles": len(doc_structure['articles'])
        }
    }
    with open(structure_json, 'w', encoding='utf-8') as f:
        json.dump(save_result, f, ensure_ascii=False, indent=2)
    
    # 4. 요약 리포트 생성
    report_file = os.path.join(output_dir, f"{base_name}_추출요약.txt")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write(f"{result['file_type']} 파일 추출 요약 리포트\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"파일 형식: {result['file_type']}\n")
        f.write(f"전체 텍스트 길이: {len(''.join(result['text_content']))} 글자\n")
        f.write(f"단락 수: {len(result['paragraphs'])}개\n")
        f.write(f"표 개수: {len(result['tables'])}개\n")
        f.write(f"이미지 개수: {len(result['images'])}개\n\n")
        
        # 문서 구조 정보 추가
        f.write(f"[문서 구조 정보]\n")
        f.write(f"장(Chapter) 수: {len(doc_structure['chapters'])}개\n")
        f.write(f"조(Article) 수: {len(doc_structure['articles'])}개\n")
        
        if doc_structure['chapters']:
            f.write(f"\n[장 목록]\n")
            for ch in doc_structure['chapters']:
                f.write(f"  제{ch['number']}장: {ch['title']}\n")
        
        if doc_structure['articles']:
            f.write(f"\n[조 목록 (일부)]\n")
            for art in doc_structure['articles'][:10]:  # 처음 10개만
                title = f"({art['title']})" if art['title'] else ""
                f.write(f"  제{art['number']}조 {title}\n")
            if len(doc_structure['articles']) > 10:
                f.write(f"  ... 외 {len(doc_structure['articles']) - 10}개\n")
        f.write("\n")
        
        if result["file_type"] == "HWP":
            f.write("[참고] HWP 파일은 텍스트만 추출됩니다.\n")
            f.write("표, 이미지 등이 필요하면 한글 프로그램에서 HWPX로 저장하세요.\n")
        
        if result["tables"]:
            f.write("\n[표 목록]\n")
            for table in result["tables"]:
                f.write(f"  - {table['summary']}\n")
        
        if result["images"]:
            f.write("\n[이미지 목록]\n")
            for img in result["images"]:
                f.write(f"  - {img['filename']} ({img['size']:,} bytes)\n")
    
    return {
        "text_file": text_file,
        "table_json": table_json,
        "table_txt": table_txt,
        "structure_json": structure_json,
        "report_file": report_file,
        "output_dir": output_dir
    }


def process_single_file(file_path):
    """단일 파일 처리"""
    # 파일 확장자 확인
    file_ext = Path(file_path).suffix.lower()
    
    if file_ext not in ['.hwp', '.hwpx']:
        print(f"[건너뜀] 지원하지 않는 형식: {file_path}")
        return None
    
    # 출력 디렉토리 이름 생성
    base_name = Path(file_path).stem
    output_dir = os.path.join("extracted_results", f"extracted_{base_name}")
    
    print(f"[파일] {file_path}")
    print(f"[형식] {file_ext.upper()}")
    print("[추출 중...]\n")
    
    try:
        # 파일 형식에 따라 처리
        if file_ext == '.hwpx':
            # HWPX: 표, 이미지 포함 완벽 추출
            result = extract_hwpx_with_structure(file_path, output_dir)
        else:  # .hwp
            # HWP: 텍스트만 추출
            script_dir = os.path.dirname(os.path.abspath(__file__))
            hwp_jar_path = os.path.join(script_dir, "python-hwplib", "hwplib-1.1.8.jar")
            
            if not os.path.exists(hwp_jar_path):
                print(f"[오류] hwplib JAR 파일을 찾을 수 없습니다: {hwp_jar_path}")
                print("python-hwplib 폴더에 hwplib-1.1.8.jar이 있는지 확인하세요.")
                return None
            
            # HWP 추출 (init_jpype()가 JAVA_HOME 자동 설정)
            result = extract_hwp_text(hwp_jar_path, file_path)
        
        # 결과 저장
        files = save_results(result, output_dir)
        
        # 결과 출력
        print("[추출 완료]\n")
        print("=" * 60)
        print("추출 결과 요약")
        print("=" * 60)
        print(f"파일 형식: {result['file_type']}")
        print(f"단락 수: {len(result['paragraphs'])}개")
        print(f"표 개수: {len(result['tables'])}개")
        print(f"이미지 개수: {len(result['images'])}개")
        print(f"전체 텍스트: {len(''.join(result['text_content']))} 글자\n")
        
        print("=" * 60)
        print("생성된 파일")
        print("=" * 60)
        print(f"출력 폴더: {os.path.abspath(output_dir)}\n")
        print(f"  - {os.path.basename(files['text_file'])}")
        if files['table_json']:
            print(f"  - {os.path.basename(files['table_json'])}")
            print(f"  - {os.path.basename(files['table_txt'])}")
        print(f"  - {os.path.basename(files['structure_json'])}")
        print(f"  - {os.path.basename(files['report_file'])}")
        
        if result['images']:
            print(f"\n  이미지 파일들:")
            for img in result['images']:
                print(f"     - {img['filename']}")
        
        if result['file_type'] == 'HWP':
            print("\n" + "=" * 60)
            print("[참고] HWP 파일은 텍스트만 추출됩니다.")
            print("표, 이미지가 필요하면 한글 프로그램에서 HWPX로 저장하세요.")
            print("=" * 60)
        
        return result
        
    except Exception as e:
        print(f"[오류] 추출 실패: {e}")
        return None


def process_folder(folder_path):
    """폴더 내 모든 HWP/HWPX 파일 일괄 처리"""
    # 폴더 내 모든 HWP/HWPX 파일 검색
    folder = Path(folder_path)
    hwp_files = list(folder.glob("*.hwp"))
    hwpx_files = list(folder.glob("*.hwpx"))
    all_files = hwp_files + hwpx_files
    
    if not all_files:
        print(f"[오류] 폴더에 HWP/HWPX 파일이 없습니다: {folder_path}")
        return
    
    print("=" * 70)
    print(f"폴더 일괄 처리 모드")
    print("=" * 70)
    print(f"폴더: {os.path.abspath(folder_path)}")
    print(f"발견된 파일: {len(all_files)}개")
    print(f"  - HWP: {len(hwp_files)}개")
    print(f"  - HWPX: {len(hwpx_files)}개")
    print("=" * 70 + "\n")
    
    # 각 파일 처리
    results = {
        "success": [],
        "failed": []
    }
    
    # HWPX 파일과 HWP 파일 분리
    hwpx_files = [f for f in all_files if f.suffix.lower() == '.hwpx']
    hwp_files = [f for f in all_files if f.suffix.lower() == '.hwp']
    
    # HWPX 파일 먼저 처리 (같은 프로세스에서 가능)
    print("\n[Phase 1] HWPX 파일 처리 (같은 프로세스)")
    print("=" * 70)
    
    for idx, file_path in enumerate(hwpx_files, 1):
        print(f"\n진행: {idx}/{len(hwpx_files)}")
        result = process_single_file(str(file_path))
        
        if result:
            results["success"].append(file_path.name)
        else:
            results["failed"].append(file_path.name)
    
    # HWP 파일은 각각 새 프로세스에서 처리 (JVM 제약 때문)
    print("\n\n[Phase 2] HWP 파일 처리 (각 파일마다 새 프로세스)")
    print("=" * 70)
    
    import subprocess
    
    # 부모 프로세스에서 먼저 JAVA_HOME 설정
    try:
        from jpype_setup import setup_java_home
        java_home = setup_java_home()
        print(f"\n[JAVA_HOME 설정] {java_home}\n")
    except Exception as e:
        print(f"\n[경고] JAVA_HOME 자동 설정 실패: {e}")
        print("수동으로 설정 필요: export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64\n")
    
    for idx, file_path in enumerate(hwp_files, 1):
        print(f"\n진행: {idx}/{len(hwp_files)}")
        print(f"[파일] {file_path}")
        
        # 새 Python 프로세스에서 HWP 파일 처리
        # 부모 프로세스의 환경변수(JAVA_HOME 포함)를 자식 프로세스로 전달
        script_path = os.path.abspath(__file__)
        env = os.environ.copy()  # 부모 환경변수 복사
        
        result_code = subprocess.call(
            [sys.executable, script_path, str(file_path)],
            env=env  # 환경변수 명시적 전달
        )
        
        if result_code == 0:
            results["success"].append(file_path.name)
            print(f"[완료] {file_path.name}")
        else:
            results["failed"].append(file_path.name)
            print(f"[실패] {file_path.name}")
    
    # 최종 요약
    print("\n" + "=" * 70)
    print("일괄 처리 완료")
    print("=" * 70)
    print(f"총 파일 수: {len(all_files)}개")
    print(f"성공: {len(results['success'])}개")
    print(f"실패: {len(results['failed'])}개")
    
    if results['success']:
        print("\n[성공한 파일]")
        for fname in results['success']:
            print(f"  - {fname}")
    
    if results['failed']:
        print("\n[실패한 파일]")
        for fname in results['failed']:
            print(f"  - {fname}")
    
    print("\n[출력 위치]")
    print(f"  {os.path.abspath('extracted_results/')}")
    print("=" * 70)


def main():
    if len(sys.argv) < 2:
        print("사용법:")
        print("  단일 파일: python extract.py <파일경로>")
        print("  폴더 처리: python extract.py <폴더경로>")
        print("\n지원 형식: HWP, HWPX")
        sys.exit(1)
    
    target_path = sys.argv[1]
    
    if not os.path.exists(target_path):
        print(f"[오류] 경로를 찾을 수 없습니다: {target_path}")
        sys.exit(1)
    
    # 폴더인지 파일인지 확인
    if os.path.isdir(target_path):
        # 폴더 처리
        process_folder(target_path)
    else:
        # 단일 파일 처리
        result = process_single_file(target_path)
        if result is None:
            sys.exit(1)


if __name__ == "__main__":
    main()

