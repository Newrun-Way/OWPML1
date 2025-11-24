# Docker Compose로 서비스 시작 스크립트 (PowerShell)

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "RAG 시스템 Docker 서비스 시작" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# 1. 환경 변수 확인
if (-not (Test-Path ".env")) {
    Write-Host "❌ .env 파일이 없습니다!" -ForegroundColor Red
    Write-Host "   .env.example을 참고하여 .env 파일을 생성하세요." -ForegroundColor Yellow
    exit 1
}

# 2. Docker 및 Docker Compose 확인
$docker = Get-Command docker -ErrorAction SilentlyContinue
if (-not $docker) {
    Write-Host "❌ Docker가 설치되어 있지 않습니다!" -ForegroundColor Red
    exit 1
}

$dockerCompose = Get-Command docker-compose -ErrorAction SilentlyContinue
if (-not $dockerCompose) {
    Write-Host "❌ Docker Compose가 설치되어 있지 않습니다!" -ForegroundColor Red
    exit 1
}

# 3. 기존 Dockerfile 백업 (첫 실행시만)
if ((Test-Path "Dockerfile") -and -not (Test-Path "Dockerfile.old")) {
    Write-Host "📦 기존 Dockerfile 백업 중..." -ForegroundColor Yellow
    Move-Item -Path "Dockerfile" -Destination "Dockerfile.old"
    Move-Item -Path "Dockerfile.new" -Destination "Dockerfile"
    Write-Host "✅ Dockerfile 교체 완료" -ForegroundColor Green
}

# 4. 빌드
Write-Host ""
Write-Host "🔨 Docker 이미지 빌드 중..." -ForegroundColor Yellow
docker-compose build

# 5. 서비스 시작
Write-Host ""
Write-Host "🚀 서비스 시작 중..." -ForegroundColor Yellow
docker-compose up -d

# 6. 상태 확인
Write-Host ""
Write-Host "⏳ 서비스 초기화 대기 중 (10초)..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host ""
Write-Host "📊 서비스 상태:" -ForegroundColor Cyan
docker-compose ps

# 7. 헬스체크
Write-Host ""
Write-Host "🏥 헬스체크 중..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -TimeoutSec 5 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ API 서버 정상" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ API 서버 응답 없음" -ForegroundColor Red
    Write-Host "   로그 확인: docker-compose logs api" -ForegroundColor Yellow
}

# 8. 접속 정보
Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "✨ 서비스 시작 완료!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📍 접속 정보:" -ForegroundColor Cyan
Write-Host "  - API 서버:    http://localhost:8000" -ForegroundColor White
Write-Host "  - API 문서:    http://localhost:8000/docs" -ForegroundColor White
Write-Host "  - 헬스체크:    http://localhost:8000/api/health" -ForegroundColor White
Write-Host "  - Flower UI:   http://localhost:5555" -ForegroundColor White
Write-Host "  - Nginx:       http://localhost:80" -ForegroundColor White
Write-Host ""
Write-Host "📋 유용한 명령어:" -ForegroundColor Cyan
Write-Host "  - 로그 확인:   docker-compose logs -f" -ForegroundColor White
Write-Host "  - 상태 확인:   docker-compose ps" -ForegroundColor White
Write-Host "  - 재시작:      docker-compose restart" -ForegroundColor White
Write-Host "  - 중지:        docker-compose down" -ForegroundColor White
Write-Host ""
Write-Host "🎉 준비 완료! API를 사용할 수 있습니다." -ForegroundColor Green


