"""
HWP/HWPX 통합 추출 스크립트 (이미지 파일명 개선 버전)
- HWPX: 텍스트 + 표 + 이미지 완벽 추출 (이미지에 의미 있는 이름 부여)
- HWP: 텍스트 추출

사용법:
    python extract_v2.py <파일경로>
"""

import zipfile
import xml.etree.ElementTree as ET
import json
import os
import sys
import jpype
import io
import re
from pathlib import Path
from collections import defaultdict

# Windows에서 UTF-8 출력을 위한 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def sanitize_filename(text, max_length=50):
    """텍스트를 안전한 파일명으로 변환"""
    if not text:
        return "image"
    
    # 불필요한 공백/특수문자 제거
    text = text.strip()
    text = re.sub(r'[\\/:*?"<>|]', '', text)  # Windows 금지 문자
    text = re.sub(r'\s+', '_', text)  # 공백을 언더스코어로
    text = text.replace('\n', '_').replace('\r', '')
    
    # 길이 제한
    if len(text) > max_length:
        text = text[:max_length]
    
    return text or "image"


def extract_image_context(root, ns, img_bindata_id):
    """이미지의 문맥 정보 추출"""
    context = {
        "caption": "",
        "surrounding_text": "",
        "parent_type": "",
        "table_title": ""
    }
    
    # 해당 이미지를 참조하는 요소 찾기
    # HWPX에서 이미지는 <hp:img> 또는 <hp:pic> 태그로 참조됨
    for img_elem in root.findall('.//hp:img', ns):
        binary_id = img_elem.get('BinaryItemRef')
        if binary_id == img_bindata_id:
            # 부모 요소 확인
            parent = img_elem
            for _ in range(5):  # 최대 5단계 위로
                parent = parent.find('..')
                if parent is None:
                    break
                
                # 캡션 찾기
                caption = parent.find('.//hp:caption', ns)
                if caption is not None:
                    context["caption"] = ''.join(caption.itertext()).strip()
                    break
    
    # 그림 객체 (hp:pic) 찾기
    for pic_elem in root.findall('.//hp:pic', ns):
        # 이미지 참조 확인
        img_ref = pic_elem.find('.//hp:img[@BinaryItemRef="{0}"]'.format(img_bindata_id), ns)
        if img_ref is not None:
            # 부모 컨테이너 확인
            parent = pic_elem.find('..')
            if parent is not None:
                # 주변 텍스트 수집
                surrounding = []
                for sibling in parent:
                    text = ''.join(sibling.itertext()).strip()
                    if text and len(text) < 100:
                        surrounding.append(text)
                context["surrounding_text"] = " ".join(surrounding[:3])  # 최대 3개 요소
    
    # 표 안의 이미지인지 확인
    for table_elem in root.findall('.//hp:tbl', ns):
        imgs_in_table = table_elem.findall('.//hp:img', ns)
        for img in imgs_in_table:
            if img.get('BinaryItemRef') == img_bindata_id:
                context["parent_type"] = "table"
                # 표 첫 행의 첫 번째 셀을 표 제목으로 사용
                first_cell = table_elem.find('.//hp:tr[1]//hp:tc[1]', ns)
                if first_cell is not None:
                    context["table_title"] = ''.join(first_cell.itertext()).strip()
                break
    
    return context


def generate_image_filename(context, doc_name, img_index, original_ext):
    """문맥 정보를 바탕으로 이미지 파일명 생성"""
    parts = []
    
    # 1. 문서명 추가
    parts.append(sanitize_filename(doc_name, max_length=20))
    
    # 2. 캡션 우선 사용
    if context["caption"]:
        parts.append(sanitize_filename(context["caption"], max_length=30))
    # 3. 표 제목 사용
    elif context["table_title"]:
        parts.append("표")
        parts.append(sanitize_filename(context["table_title"], max_length=25))
    # 4. 주변 텍스트 사용
    elif context["surrounding_text"]:
        parts.append(sanitize_filename(context["surrounding_text"], max_length=30))
    
    # 5. 이미지 번호 추가 (중복 방지)
    parts.append(f"img{img_index:02d}")
    
    # 파일명 조합
    filename = "_".join(parts)
    
    # 확장자 추가
    return f"{filename}{original_ext}"


def extract_hwpx_with_structure(hwpx_path, output_dir="extracted_data"):
    """HWPX 파일에서 구조화된 데이터 추출 (이미지 파일명 개선)"""
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 문서명 추출
    doc_name = Path(hwpx_path).stem
    
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
        
        # 네임스페이스 정의
        ns = {
            'hp': 'http://www.hancom.co.kr/hwpml/2011/paragraph',
            'hc': 'http://www.hancom.co.kr/hwpml/2011/core'
        }
        
        # 이미지 ID와 파일 매핑 수집
        image_id_map = {}
        image_files = [f for f in z.namelist() if f.startswith('BinData/') and 
                      any(f.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif'])]
        
        # Section 파일들 처리하여 이미지 문맥 수집
        section_files = [f for f in z.namelist() if f.startswith('Contents/section') and f.endswith('.xml')]
        all_section_roots = []
        
        for section_file in section_files:
            section_xml = z.read(section_file).decode('utf-8')
            root = ET.fromstring(section_xml)
            all_section_roots.append(root)
            
            # 텍스트 추출 (단락별)
            paragraphs = root.findall('.//hp:p', ns)
            for i, para in enumerate(paragraphs):
                para_text = ''.join(para.itertext()).strip()
                if para_text:
                    result["paragraphs"].append({
                        "id": len(result["paragraphs"]),
                        "text": para_text,
                        "type": "paragraph"
                    })
                    result["text_content"].append(para_text)
            
            # 표(Table) 추출
            tables = root.findall('.//hp:tbl', ns)
            for t_idx, table in enumerate(tables):
                table_data = {
                    "id": len(result["tables"]),
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
                    row_count = len(table_data["rows"])
                    col_count = len(table_data["rows"][0]) if table_data["rows"] else 0
                    table_data["summary"] = f"표 {len(result['tables']) + 1}: {row_count}행 × {col_count}열"
                    result["tables"].append(table_data)
                    
                    # 텍스트 컨텐츠에도 표시
                    result["text_content"].append(f"\n[{table_data['summary']}]\n")
        
        # 이미지 추출 및 파일명 생성
        img_index = 1
        for img_file in image_files:
            img_data = z.read(img_file)
            original_name = os.path.basename(img_file)
            original_ext = os.path.splitext(original_name)[1]
            
            # 이미지 ID 추출 (BinData/image.01 → image.01)
            img_bindata_id = os.path.splitext(original_name)[0]
            
            # 모든 section에서 이미지 문맥 찾기
            context = None
            for root in all_section_roots:
                temp_context = extract_image_context(root, ns, img_bindata_id)
                if temp_context["caption"] or temp_context["surrounding_text"] or temp_context["table_title"]:
                    context = temp_context
                    break
            
            if context is None:
                context = {"caption": "", "surrounding_text": "", "parent_type": "", "table_title": ""}
            
            # 새로운 파일명 생성
            new_filename = generate_image_filename(context, doc_name, img_index, original_ext)
            
            # 이미지 파일 저장
            img_path = os.path.join(output_dir, new_filename)
            with open(img_path, 'wb') as f:
                f.write(img_data)
            
            result["images"].append({
                "filename": new_filename,
                "original_filename": original_name,
                "path": img_path,
                "size": len(img_data),
                "context": {
                    "caption": context["caption"][:100] if context["caption"] else "",
                    "parent_type": context["parent_type"]
                }
            })
            
            img_index += 1
    
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
    
    # jpype 시작
    jpype.startJVM(
        jpype.getDefaultJVMPath(),
        f"-Djava.class.path={hwp_jar_path}",
        convertStrings=True,
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
        "images_info": [
            {
                "filename": img["filename"],
                "original_filename": img.get("original_filename", ""),
                "size": img["size"],
                "context": img.get("context", {})
            } for img in result["images"]
        ],
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
                f.write(f"  - {img['filename']}")
                if img.get("context", {}).get("caption"):
                    f.write(f" (캡션: {img['context']['caption'][:50]}...)")
                f.write(f" ({img['size']:,} bytes)\n")
    
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
        print("사용법: python extract_v2.py <파일경로>")
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
        # HWPX: 표, 이미지 포함 완벽 추출 (이미지 파일명 개선)
        result = extract_hwpx_with_structure(file_path, output_dir)
    else:  # .hwp
        # HWP: 텍스트만 추출
        # JAR 파일 경로
        hwp_jar_path = os.path.join(os.path.dirname(__file__), "..", "python-hwplib", "hwplib-1.1.8.jar")
        if not os.path.exists(hwp_jar_path):
            print(f"[오류] hwplib JAR 파일을 찾을 수 없습니다: {hwp_jar_path}")
            print("python-hwplib 폴더에 hwplib-1.1.8.jar이 있는지 확인하세요.")
            sys.exit(1)
        
        # JAVA_HOME 설정
        os.environ['JAVA_HOME'] = r'C:\Program Files\Java\jdk-21'
        
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
            if img.get('context', {}).get('caption'):
                print(f"       (캡션: {img['context']['caption'][:60]}...)")
    
    if result['file_type'] == 'HWP':
        print("\n" + "=" * 60)
        print("[참고] HWP 파일은 텍스트만 추출됩니다.")
        print("표, 이미지가 필요하면 한글 프로그램에서 HWPX로 저장하세요.")
        print("=" * 60)


if __name__ == "__main__":
    main()

