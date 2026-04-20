# DocSentry Startup Script
# Run this from the project root: .\start.ps1

$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
$BACKEND = "$ROOT\backend"
$FRONTEND = "$ROOT\frontend"
$PYTHON = "$BACKEND\venv\Scripts\python.exe"

Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "   DocSentry Startup" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# ── Step 1: Kill anything on port 8000 or 8001 ──────────────────────────────
foreach ($port in @(8000, 8001)) {
    $pids = (netstat -ano 2>$null | Select-String ":$port\s.*LISTEN") |
            ForEach-Object { ($_.ToString().Trim() -split '\s+')[-1] } |
            Where-Object { $_ -match '^\d+$' } |
            Select-Object -Unique

    foreach ($p in $pids) {
        try {
            Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
            Write-Host "  Freed port $port (killed PID $p)" -ForegroundColor Yellow
        } catch {}
    }
}

# ── Step 2: Kill any lingering Python uvicorn processes ──────────────────────
Get-Process -Name "python*" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*uvicorn*" } |
    Stop-Process -Force -ErrorAction SilentlyContinue

Start-Sleep -Seconds 1

# ── Step 3: Verify python.exe exists ────────────────────────────────────────
if (-not (Test-Path $PYTHON)) {
    Write-Host ""
    Write-Host "ERROR: venv python not found at:" -ForegroundColor Red
    Write-Host "  $PYTHON" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please recreate the venv:" -ForegroundColor Yellow
    Write-Host "  cd $BACKEND"
    Write-Host "  python -m venv venv"
    Write-Host "  .\venv\Scripts\activate"
    Write-Host "  pip install -r requirements.txt"
    exit 1
}

# ── Step 4: Start backend ────────────────────────────────────────────────────
Write-Host "  Starting backend on http://127.0.0.1:8000 ..." -ForegroundColor Green
$backend_proc = Start-Process -FilePath $PYTHON `
    -ArgumentList "-m", "uvicorn", "app.main:app", "--port", "8000", "--host", "127.0.0.1" `
    -WorkingDirectory $BACKEND `
    -PassThru `
    -WindowStyle Normal

Start-Sleep -Seconds 4

# Check it actually started
$portInUse = netstat -ano 2>$null | Select-String ":8000\s.*LISTEN"
if (-not $portInUse) {
    Write-Host ""
    Write-Host "  Backend failed to start. Running in console for diagnostics..." -ForegroundColor Red
    Set-Location $BACKEND
    & $PYTHON -m uvicorn app.main:app --port 8000 --host 127.0.0.1
    exit 1
}

Write-Host "  Backend running. (PID $($backend_proc.Id))" -ForegroundColor Green

# ── Step 5: Update frontend .env to port 8000 ────────────────────────────────
$envFile = "$FRONTEND\.env"
Set-Content -Path $envFile -Value "VITE_API_URL=http://127.0.0.1:8000"

# ── Step 6: Start frontend ────────────────────────────────────────────────────
Write-Host "  Starting frontend on http://localhost:5173 ..." -ForegroundColor Green
$frontend_proc = Start-Process -FilePath "cmd.exe" `
    -ArgumentList "/c", "npm run dev" `
    -WorkingDirectory $FRONTEND `
    -PassThru `
    -WindowStyle Normal

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "  Both servers are running!" -ForegroundColor Green
Write-Host ""
Write-Host "  Frontend : http://localhost:5173" -ForegroundColor White
Write-Host "  Backend  : http://127.0.0.1:8000" -ForegroundColor White
Write-Host "  API Docs : http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Press CTRL+C to stop the backend." -ForegroundColor Gray
Write-Host "  (Close the frontend window separately)" -ForegroundColor Gray
Write-Host ""

# Keep script alive so backend stays visible in this window
Wait-Process -Id $backend_proc.Id
