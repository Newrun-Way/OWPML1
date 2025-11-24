# Docker 서비스 테스트 스크립트 (PowerShell)

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Docker 서비스 테스트" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# 1. 서비스 상태 확인
Write-Host ""
Write-Host "1️⃣ 서비스 상태 확인" -ForegroundColor Yellow
docker-compose ps

# 2. Redis 테스트
Write-Host ""
Write-Host "2️⃣ Redis 연결 테스트" -ForegroundColor Yellow
try {
    $redis_result = docker exec rag-redis redis-cli ping 2>$null
    if ($redis_result -like "*PONG*") {
        Write-Host "✅ Redis 정상" -ForegroundColor Green
    } else {
        Write-Host "❌ Redis 연결 실패" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Redis 연결 실패: $_" -ForegroundColor Red
    exit 1
}

# 3. API 헬스체크
Write-Host ""
Write-Host "3️⃣ API 서버 헬스체크" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -TimeoutSec 5 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ API 서버 정상" -ForegroundColor Green
        Write-Host "   응답: $($response.Content)" -ForegroundColor White
    }
} catch {
    Write-Host "❌ API 서버 응답 없음" -ForegroundColor Red
    Write-Host "   로그 확인: docker-compose logs api" -ForegroundColor Yellow
    exit 1
}

# 4. Worker 확인
Write-Host ""
Write-Host "4️⃣ Celery Worker 확인" -ForegroundColor Yellow
$ps_output = docker-compose ps worker
$worker_count = ($ps_output | Select-String "Up" | Measure-Object).Count
if ($worker_count -ge 1) {
    Write-Host "✅ Worker $worker_count 개 실행 중" -ForegroundColor Green
} else {
    Write-Host "❌ Worker 실행 안됨" -ForegroundColor Red
    exit 1
}

# 5. Flower 확인 (선택사항)
Write-Host ""
Write-Host "5️⃣ Flower 모니터링 확인" -ForegroundColor Yellow
try {
    $flower = Invoke-WebRequest -Uri "http://localhost:5555" -TimeoutSec 3 -ErrorAction SilentlyContinue
    Write-Host "✅ Flower 접속 가능 (http://localhost:5555)" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Flower 접속 불가 (선택사항)" -ForegroundColor Yellow
}

# 6. 컨테이너 리소스 확인
Write-Host ""
Write-Host "6️⃣ 컨테이너 리소스 사용량" -ForegroundColor Yellow
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>$null

# 7. 네트워크 확인
Write-Host ""
Write-Host "7️⃣ 네트워크 확인" -ForegroundColor Yellow
$networks = docker network ls | Select-String "rag-network"
if ($networks) {
    Write-Host "✅ rag-network 존재" -ForegroundColor Green
} else {
    Write-Host "❌ rag-network 없음" -ForegroundColor Red
}

# 8. 볼륨 확인
Write-Host ""
Write-Host "8️⃣ 볼륨 확인" -ForegroundColor Yellow
$volumes = docker volume ls | Select-String "redis_data"
if ($volumes) {
    Write-Host "✅ redis_data 볼륨 존재" -ForegroundColor Green
} else {
    Write-Host "❌ redis_data 볼륨 없음" -ForegroundColor Red
}

# 9. API 문서 확인
Write-Host ""
Write-Host "9️⃣ API 문서 확인" -ForegroundColor Yellow
try {
    $docs = Invoke-WebRequest -Uri "http://localhost:8000/docs" -TimeoutSec 3 -ErrorAction SilentlyContinue
    Write-Host "✅ Swagger UI 접속 가능 (http://localhost:8000/docs)" -ForegroundColor Green
} catch {
    Write-Host "❌ Swagger UI 접속 불가" -ForegroundColor Red
}

# 완료
Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "✨ 테스트 완료!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📍 서비스 접속 정보:" -ForegroundColor Cyan
Write-Host "  - API 문서:    http://localhost:8000/docs" -ForegroundColor White
Write-Host "  - 헬스체크:    http://localhost:8000/api/health" -ForegroundColor White
Write-Host "  - Flower UI:   http://localhost:5555" -ForegroundColor White
Write-Host ""
Write-Host "🧪 수동 테스트 명령어:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  파일 업로드 테스트:" -ForegroundColor Yellow
Write-Host "  `curl -X POST http://localhost:8000/api/documents/upload/async \\" -ForegroundColor White
Write-Host "    -F 'file=@test.hwp' \\" -ForegroundColor White
Write-Host "    -F 'user_id=test_user' \\" -ForegroundColor White
Write-Host "    -F 'dept_id=HR' \\" -ForegroundColor White
Write-Host "    -F 'project_id=test_project'`" -ForegroundColor White
Write-Host ""
Write-Host "  작업 상태 조회:" -ForegroundColor Yellow
Write-Host "  `curl http://localhost:8000/api/tasks/{task_id}`" -ForegroundColor White
Write-Host ""
Write-Host "  질의응답 테스트:" -ForegroundColor Yellow
Write-Host "  `curl -X POST http://localhost:8000/api/query \\" -ForegroundColor White
Write-Host "    -H 'Content-Type: application/json' \\" -ForegroundColor White
Write-Host "    -d '{``query``: ``테스트 질문``, ``user_id``: ``test_user``}'`" -ForegroundColor White


