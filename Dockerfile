FROM python:3.10

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 (Java 포함)
RUN apt-get update && apt-get install -y \
    default-jdk \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 프로젝트 파일 복사
COPY . .

# 포트 노출 (필요시)
EXPOSE 8000

# 기본 명령어
CMD ["python", "main.py"]