"""
저장된 RAG 데이터 확인 스크립트
"""
import pickle
from pathlib import Path
import json

metadata_path = Path("data/vector_store/metadata.pkl")

if metadata_path.exists():
    with open(metadata_path, 'rb') as f:
        metadata = pickle.load(f)
    
    print(f"\n저장된 총 청크 수: {len(metadata)}")
    print(f"메타데이터 타입: {type(metadata)}")
    print("\n" + "="*60)
    
    # 구조 확인
    if isinstance(metadata, dict):
        print("\n메타데이터는 딕셔너리입니다:")
        for key, value in metadata.items():
            print(f"  키: {key}, 값 타입: {type(value)}, 길이: {len(value) if hasattr(value, '__len__') else 'N/A'}")
            if isinstance(value, list) and len(value) > 0:
                print(f"    첫 번째 항목: {value[0][:100] if isinstance(value[0], str) else value[0]}")
    elif isinstance(metadata, list):
        print("\n메타데이터는 리스트입니다:")
        for i, item in enumerate(metadata[:3]):  # 처음 3개만
            print(f"\n[항목 {i}]")
            print(f"  타입: {type(item)}")
            if isinstance(item, str):
                print(f"  내용: {item[:150]}...")
            else:
                print(f"  내용: {item}")
else:
    print("메타데이터 파일이 없습니다.")

