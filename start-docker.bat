@echo off
REM Docker Compose로 서비스 시작 스크립트 (배치 파일)

setlocal enabledelayedexpansion

echo =========================================
echo RAG 시스템 Docker 서비스 시작
echo =========================================

REM 1. 환경 변수 확인
if not exist ".env" (
    echo.
    echo [ERROR] .env 파일이 없습니다!
    echo 프로젝트 루트 폴더에 .env 파일을 생성하세요.
    echo OPENAI_API_KEY=your-key 형식으로.
    pause
    exit /b 1
)

REM 2. Docker 및 Docker Compose 확인
docker --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Docker가 설치되어 있지 않습니다!
    echo https://www.docker.com/products/docker-desktop 에서 설치하세요.
    pause
    exit /b 1
)

REM 3. Dockerfile 교체
echo.
if exist "Dockerfile" (
    if not exist "Dockerfile.old" (
        echo [*] Dockerfile 백업 중...
        ren Dockerfile Dockerfile.old
    )
)

if exist "Dockerfile.new" (
    if not exist "Dockerfile" (
        echo [*] Dockerfile.new를 Dockerfile로 복사 중...
        copy Dockerfile.new Dockerfile
    )
)

REM 4. 빌드
echo.
echo [*] Docker 이미지 빌드 중... (몇 분 걸릴 수 있습니다)
docker-compose build
if errorlevel 1 (
    echo.
    echo [ERROR] 빌드 실패!
    pause
    exit /b 1
)

REM 5. 서비스 시작
echo.
echo [*] 서비스 시작 중...
docker-compose up -d
if errorlevel 1 (
    echo.
    echo [ERROR] 서비스 시작 실패!
    docker-compose logs
    pause
    exit /b 1
)

REM 6. 상태 확인
echo.
echo [*] 서비스 초기화 대기 중 (10초)...
timeout /t 10 /nobreak

echo.
echo ========== 서비스 상태 ==========
docker-compose ps

REM 7. 헬스체크
echo.
echo [*] API 서버 헬스체크 중...
timeout /t 3 /nobreak

for /f "tokens=*" %%i in ('powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:8000/api/health' -TimeoutSec 5 -ErrorAction SilentlyContinue; if($r.StatusCode -eq 200) { Write-Host 'OK' } else { Write-Host 'FAIL' } } catch { Write-Host 'FAIL' }"') do set "HEALTH=%%i"

if "%HEALTH%"=="OK" (
    echo [OK] API 서버 정상
) else (
    echo [WARNING] API 서버 응답 확인 불가 (시작 중일 수 있습니다)
)

REM 8. 완료 메시지
echo.
echo =========================================
echo [SUCCESS] 서비스 시작 완료!
echo =========================================
echo.
echo 접속 정보:
echo   - API 서버:    http://localhost:8000
echo   - API 문서:    http://localhost:8000/docs
echo   - 헬스체크:    http://localhost:8000/api/health
echo   - Flower UI:   http://localhost:5555
echo.
echo 유용한 명령어:
echo   docker-compose ps              ^(상태 확인^)
echo   docker-compose logs -f api     ^(API 로그^)
echo   docker-compose logs -f worker  ^(Worker 로그^)
echo   docker-compose down            ^(종료^)
echo.
echo 준비 완료! 브라우저에서 http://localhost:8000/docs 접속하세요.
echo.
pause


