# OWPML 필터를 활용한 한글 문서 추출 프로젝트

HWP/HWPX 파일에서 텍스트, 표, 이미지를 추출하는 통합 솔루션

---

## 핵심 기능

- **자동 파일 형식 감지**: HWP와 HWPX를 자동으로 구분하여 처리
- **HWPX 완벽 추출**: 텍스트, 표 구조, 이미지 모두 추출
- **HWP 텍스트 추출**: 텍스트 추출 지원
- **JSON 출력**: 표 데이터를 JSON 형식으로 저장하여 RAG 시스템에 바로 적용 가능

---

## 빠른 시작

### 설치 요구사항

- Python 3.7+
- Java (JDK 8+)
- JPype1: `pip install JPype1`

### 사용법 (단 1줄)

```powershell
cd python-hwpxlib
python extract.py "파일경로.hwpx"
```

### 예시

```powershell
# HWPX 파일 처리
python extract.py "..\hwp data\문서.hwpx"

# HWP 파일 처리
python extract.py "..\hwp data\문서.hwp"
```

---

## 추출 결과

### HWPX 파일
```
extracted_파일명/
├── 전체텍스트.txt          모든 텍스트
├── 표데이터.json            표 구조 데이터 (RAG용)
├── 표목록.txt              읽기 쉬운 표 목록
├── 구조.json               문서 구조 정보
├── 추출요약.txt            추출 결과 요약
└── image1.jpg, ...         추출된 이미지들
```

### HWP 파일
```
extracted_파일명/
├── 전체텍스트.txt          텍스트만 추출
├── 구조.json
└── 추출요약.txt

[참고] 표/이미지는 추출 안 됨
```

---

## 프로젝트 구조

```
Al Lang/
├── python-hwpxlib/
│   ├── extract.py              [핵심] 통합 추출 스크립트
│   ├── hwpx_loader.py
│   └── hwpxlib-1.0.5.jar
│
├── python-hwplib/
│   ├── hwp_loader.py
│   └── hwplib-1.1.8.jar
│
├── hwp data/                   테스트 문서
│
├── WeeklyPlan.md               프로젝트 계획
└── 프로젝트_구조.md            상세 구조 설명
```

---

## RAG 프로젝트 적용

### 워크플로우

1. HWP 문서를 HWPX로 변환
2. `extract.py`로 처리
3. `표데이터.json` 로드
4. 텍스트 + 표 데이터를 벡터 DB에 저장
5. RAG 질의응답 서비스 구축

### Python 코드 예시

```python
import json
import subprocess

# 1. 추출 실행
subprocess.run([
    'python', 'python-hwpxlib/extract.py',
    'document.hwpx'
])

# 2. 표 데이터 로드
with open('extracted_document/표데이터.json', 'r', encoding='utf-8') as f:
    tables = json.load(f)

# 3. RAG 시스템에 적용
for table in tables:
    print(f"{table['summary']}")
    # 벡터 DB에 저장 등...
```

---

## 기술 스택

- **OWPML**: 한글과컴퓨터 공식 문서 포맷
- **hwpxlib**: HWPX 파일 처리 (Java)
- **hwplib**: HWP 파일 처리 (Java)
- **JPype1**: Python-Java 브릿지
- **Python 3.7+**

---

## 비교표

| 항목 | HWPX | HWP |
|------|------|-----|
| 텍스트 추출 | O | O |
| 표 구조 추출 | O | X |
| 이미지 추출 | O | X |
| 단락 구분 | O | X |
| RAG 적합성 | 강력 추천 | 제한적 |

---

## 참고 자료

- [hwpxlib GitHub](https://github.com/neolord0/hwpxlib)
- [hwplib GitHub](https://github.com/neolord0/hwplib)
- [python-hwpxlib](https://github.com/choijhyeok/python-hwpxlib)
- [python-hwplib](https://github.com/choijhyeok/python-hwplib)

---

## 라이선스

프로젝트별 라이선스 참조

---

## 팀원

한글과컴퓨터 학습 과정 팀 프로젝트

---

**최종 업데이트**: 2025년 10월 22일

