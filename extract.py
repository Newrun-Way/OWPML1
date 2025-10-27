"""
HWP/HWPX 통합 추출 스크립트
- HWPX: 텍스트 + 표 + 이미지 완벽 추출
- HWP: 텍스트 추출

사용법:
    python extract.py <파일경로>
"""

import zipfile
import xml.etree.ElementTree as ET
import json
import os
import sys
import io
from pathlib import Path
from jpype_setup import init_jpype

# Windows에서 UTF-8 출력을 위한 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


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
    
    # jpype 초기화 (JAVA_HOME 자동 설정 + JVM 시작)
    jpype = init_jpype(hwp_jar_path)
    
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
        
    finally:
        pass
    
    return result


def save_results(result, output_dir="extracted_data"):
    """추출 결과를 파일로 저장"""
    
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
    
    # 3. 구조화된 데이터 저장 (JSON)
    structure_json = os.path.join(output_dir, f"{base_name}_구조.json")
    save_result = {
        "file_type": result["file_type"],
        "text_paragraphs": result["paragraphs"],
        "tables_count": len(result["tables"]),
        "images_count": len(result["images"]),
        "images_list": [img["filename"] for img in result["images"]],
        "metadata": result["metadata"]
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


def main():
    if len(sys.argv) < 2:
        print("사용법: python extract.py <파일경로>")
        print("지원 형식: HWP, HWPX")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"[오류] 파일을 찾을 수 없습니다: {file_path}")
        sys.exit(1)
    
    # 파일 확장자 확인
    file_ext = Path(file_path).suffix.lower()
    
    if file_ext not in ['.hwp', '.hwpx']:
        print(f"[오류] 지원하지 않는 파일 형식입니다: {file_ext}")
        print("지원 형식: .hwp, .hwpx")
        sys.exit(1)
    
    # 출력 디렉토리 이름 생성
    base_name = Path(file_path).stem
    output_dir = os.path.join("extracted_results", f"extracted_{base_name}")
    
    print(f"[파일] {file_path}")
    print(f"[형식] {file_ext.upper()}")
    print("[추출 중...]\n")
    
    # 파일 형식에 따라 처리
    if file_ext == '.hwpx':
        # HWPX: 표, 이미지 포함 완벽 추출
        result = extract_hwpx_with_structure(file_path, output_dir)
    else:  # .hwp
        # HWP: 텍스트만 추출
        # JAR 파일 경로
        hwp_jar_path = os.path.join(os.path.dirname(__file__), "..", "python-hwplib", "hwplib-1.1.8.jar")
        if not os.path.exists(hwp_jar_path):
            print(f"[오류] hwplib JAR 파일을 찾을 수 없습니다: {hwp_jar_path}")
            print("python-hwplib 폴더에 hwplib-1.1.8.jar이 있는지 확인하세요.")
            sys.exit(1)
        
        # HWP 추출 (init_jpype()가 JAVA_HOME 자동 설정)
        try:
            result = extract_hwp_text(hwp_jar_path, file_path)
        except Exception as e:
            print(f"[오류] HWP 추출 실패: {e}")
            print("       Java 설치 확인: python jpype_setup.py")
            print("       전체 환경 테스트: python test_jpype.py")
            sys.exit(1)
    
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


if __name__ == "__main__":
    main()

