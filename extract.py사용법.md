# HWP/HWPX 추출 가이드

---

## 핵심 명령어

```powershell
cd "C:\Users\chodo\Desktop\Al Lang\python-hwpxlib"
python extract.py "파일경로"
```

HWP든 HWPX든 자동으로 처리

---

## 처리 방식

### HWPX 파일
```
입력: 파일.hwpx
출력:
  - 전체텍스트.txt
  - 표데이터.json (99개 표)
  - 표목록.txt
  - 이미지 파일들
  - 구조.json
  - 추출요약.txt
```

### HWP 파일
```
입력: 파일.hwp
출력:
  - 전체텍스트.txt (텍스트만)
  - 구조.json
  - 추출요약.txt
  
[참고] 표/이미지는 추출 안 됨
```

---
## 사용 예시

### 기본 사용
```powershell
# HWPX 파일
python extract.py "..\hwp data\문서.hwpx"

# HWP 파일
python extract.py "..\hwp data\문서.hwp"

# 둘 다 같은 명령어! 자동 감지됨
```

### 여러 파일 한번에
```powershell
# 폴더의 모든 한글 파일 처리
Get-ChildItem "..\hwp data\*.hwp*" | ForEach-Object {
    python extract.py $_.FullName
}
```

---


## 프로젝트에서 권장 워크플로우

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

**작성일**: 2025년 10월 22일

