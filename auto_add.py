"""
팀원이 전달한 추출 데이터를 자동으로 RAG 시스템에 추가하는 스크립트

사용법:
    python auto_add.py                      # 새 문서만 추가 (기본)
    python auto_add.py --all                # 모든 문서 재추가
    python auto_add.py all                  # 모든 문서 재추가 (위와 동일)
    python auto_add.py --folder 문서명      # 특정 문서만 추가
    python auto_add.py 문서명               # 특정 문서만 추가 (위와 동일)
    python auto_add.py --source 경로        # 커스텀 소스 폴더 지정
"""

import argparse
from pathlib import Path
from rag.pipeline import RAGPipeline
import json
import time
import os

# ONNX Runtime GPU 경고 비활성화 (선택사항)
os.environ["ORT_LOGGING_LEVEL"] = "3"  # 경고 수준 줄이기

# 처리 기록 파일
PROCESSED_LOG = Path("data/.processed_documents.json")

def load_processed_log():
    """이미 처리한 문서 목록 로드"""
    if PROCESSED_LOG.exists():
        with open(PROCESSED_LOG, 'r', encoding='utf-8', errors='replace') as f:
            return json.load(f)
    return {"processed": [], "last_update": None}

def save_processed_log(log):
    """처리한 문서 목록 저장"""
    log["last_update"] = time.strftime("%Y-%m-%d %H:%M:%S")
    PROCESSED_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(PROCESSED_LOG, 'w', encoding='utf-8') as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

def get_extracted_folders(base_dir):
    """추출된 문서 폴더 목록 가져오기"""
    base_path = Path(base_dir)
    if not base_path.exists():
        return []
    
    folders = []
    for item in base_path.iterdir():
        if item.is_dir() and item.name.startswith("extracted_"):
            folders.append(item)
    
    return sorted(folders)

def add_document_to_rag(pipeline, folder_path):
    """문서를 RAG 시스템에 추가"""
    try:
        doc_name = folder_path.name.replace("extracted_", "")
        print(f"\n처리 중: {doc_name}")
        print("-" * 60)
        
        result = pipeline.add_document_from_extract(folder_path)
        
        print(f"✓ 추가 완료: {result['chunks_added']}개 청크")
        return True, result
        
    except Exception as e:
        print(f"✗ 오류 발생: {e}")
        return False, None

def main():
    parser = argparse.ArgumentParser(description="추출된 문서를 RAG 시스템에 자동 추가")
    # 위치 인자 (호환성: all 또는 --all 모두 지원)
    parser.add_argument("action", nargs='?', default=None, 
                       help="작업: 'all' (모든 문서 재추가), '폴더명' (특정 폴더)")
    parser.add_argument("--all", action="store_true", help="모든 문서 재추가")
    parser.add_argument("--folder", type=str, help="특정 폴더만 추가")
    parser.add_argument("--source", type=str, default="extracted_results", 
                       help="문서가 있는 폴더 경로 (기본: extracted_results)")
    args = parser.parse_args()
    
    # 호환성 처리: positional argument 'all' → args.all으로 변환
    if args.action == "all":
        args.all = True
    elif args.action and not args.folder:
        args.folder = args.action
    
    print("\n" + "="*70)
    print("RAG 자동 추가 시스템")
    print("="*70)
    
    # 소스 폴더 확인
    source_path = Path(args.source)
    if not source_path.exists():
        print(f"\n⚠ 소스 폴더가 없습니다: {source_path}")
        print(f"\n사용 방법:")
        print(f"  python3 auto_add.py --source extracted_results  # extract.py 결과물")
        print(f"  python3 auto_add.py --source data/extracted     # 팀원이 전달한 데이터")
        return
    
    # 추출된 문서 폴더 목록
    folders = get_extracted_folders(source_path)
    if not folders:
        print(f"\n⚠ {source_path}/ 폴더에 추출된 문서가 없습니다.")
        print("\n팀원에게 다음 형식으로 폴더를 받아주세요:")
        print("  extracted_문서명/")
        print("    ├── 전체텍스트.txt")
        print("    ├── structure.json")
        print("    └── images/ (선택)")
        return
    
    print(f"\n발견된 문서 폴더: {len(folders)}개")
    for folder in folders:
        print(f"  - {folder.name}")
    
    # 처리 기록 로드
    log = load_processed_log()
    
    # 처리할 문서 결정
    if args.folder:
        # 특정 폴더만
        target_name = f"extracted_{args.folder}" if not args.folder.startswith("extracted_") else args.folder
        folders_to_process = [f for f in folders if f.name == target_name]
        if not folders_to_process:
            print(f"\n✗ 폴더를 찾을 수 없습니다: {target_name}")
            return
    elif args.all:
        # 모든 문서
        folders_to_process = folders
        log["processed"] = []  # 기록 초기화
    else:
        # 새 문서만
        folders_to_process = [f for f in folders if str(f) not in log["processed"]]
        if not folders_to_process:
            print("\n✓ 모든 문서가 이미 추가되었습니다.")
            print(f"  마지막 업데이트: {log.get('last_update', 'N/A')}")
            print("\n옵션:")
            print("  --all           모든 문서 재추가")
            print("  --folder 문서명  특정 문서 추가")
            return
    
    print(f"\n처리할 문서: {len(folders_to_process)}개")
    
    # RAG 파이프라인 초기화
    print("\nRAG 파이프라인 초기화 중...")
    pipeline = RAGPipeline(load_existing=True)
    
    # 문서 추가
    print("\n" + "="*70)
    print("문서 추가 시작")
    print("="*70)
    
    success_count = 0
    fail_count = 0
    total_chunks = 0
    
    for i, folder in enumerate(folders_to_process, 1):
        print(f"\n[{i}/{len(folders_to_process)}]")
        success, result = add_document_to_rag(pipeline, folder)
        
        if success:
            success_count += 1
            total_chunks += result['chunks_added']
            log["processed"].append(str(folder))
        else:
            fail_count += 1
    
    # 처리 기록 저장
    save_processed_log(log)
    
    # 최종 통계
    stats = pipeline.get_stats()
    
    print("\n" + "="*70)
    print("처리 완료")
    print("="*70)
    print(f"\n[이번 작업]")
    print(f"  성공: {success_count}개")
    print(f"  실패: {fail_count}개")
    print(f"  추가된 청크: {total_chunks}개")
    
    print(f"\n[전체 시스템]")
    print(f"  총 문서: {len(log['processed'])}개")
    print(f"  총 청크: {stats['vector_store']['total_documents']}개")
    print(f"  임베딩 모델: {stats['embedding_model']}")
    print(f"  LLM 모델: {stats['llm_model']}")
    
    print("\n다음 단계:")
    print("  1. 질의응답 테스트: python main.py query")
    print("  2. 저장된 데이터 확인: python view_stored_data.py")
    print("  3. 새 문서 추가: 팀원 데이터를 data/extracted/에 넣고 다시 실행")
    print("\n" + "="*70)

if __name__ == "__main__":
    main()
