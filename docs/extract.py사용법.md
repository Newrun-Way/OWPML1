# HWP/HWPX 추출 가이드

---

## 핵심 명령어

```powershell
# 단일 파일 처리
python extract.py "파일경로"

# 폴더 일괄 처리 (NEW!)
python extract.py "폴더경로"
```

HWP든 HWPX든 자동으로 처리

---

## 처리 방식

### HWPX 파일
```
입력: 파일.hwpx
출력 위치: extracted_results/extracted_파일명/
  - 전체텍스트.txt
  - 표데이터.json (표 있을 경우)
  - 표목록.txt (표 있을 경우)
  - 이미지 파일들 (이미지 있을 경우)
  - 구조.json
  - 추출요약.txt
```

### HWP 파일
```
입력: 파일.hwp
출력 위치: extracted_results/extracted_파일명/
  - 전체텍스트.txt (텍스트만)
  - 구조.json
  - 추출요약.txt
  
[참고] 표/이미지는 추출 안 됨
```

---
## 사용 예시

### 1. 단일 파일 처리
```powershell
# HWPX 파일
python extract.py "hwp data/문서.hwpx"

# HWP 파일
python extract.py "hwp data/문서.hwp"

# 둘 다 같은 명령어! 자동 감지됨
```

### 2. 폴더 일괄 처리 (NEW!)
```powershell
# 폴더 내 모든 HWP/HWPX 파일을 한번에 처리
python extract.py "hwp data/"

# 실행 결과:
# ======================================================================
# 폴더 일괄 처리 모드
# ======================================================================
# 폴더: C:\Users\chodo\Desktop\Al Lang\hwp data
# 발견된 파일: 15개
#   - HWP: 3개
#   - HWPX: 12개
# ======================================================================
# 
# 진행: 1/15
# [파일] hwp data\보고서.hwpx
# [추출 완료]
# ...
# 
# 일괄 처리 완료
# 총 파일 수: 15개
# 성공: 15개
# 실패: 0개
```

### 3. EC2 (Ubuntu)에서 사용
```bash
# 단일 파일
python3 extract.py "hwp_data/문서.hwpx"

# 폴더 일괄 처리
python3 extract.py "hwp_data/"
```

---

워크플로우우

```
1. 모든 HWP 파일을 HWPX로 변환
   (한글 프로그램: 파일 > 다른 이름으로 저장 > HWPX)
   
2. extract.py로 처리
   python extract.py "문서.hwpx"
   
3. 표데이터.json 활용
   - RAG 시스템에 바로 적용
   - 표 구조 유지하며 검색 가능
```

---

## Python 코드에서 사용

```python
import subprocess

# 파일 처리 (HWP/HWPX 자동 감지)
result = subprocess.run([
    'python',
    'python-hwpxlib/extract.py',
    'path/to/file.hwpx'  # 또는 .hwp
], capture_output=True, text=True, encoding='utf-8')

# 추출 결과는 extracted_파일명/ 폴더에 저장됨
```

## 스크립트 위치

```
C:\Users\chodo\Desktop\Al Lang\python-hwpxlib\extract.py
```


