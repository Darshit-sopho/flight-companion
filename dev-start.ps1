# Local development convenience script - NOT used by CI, NOT meant for production deployment.
# Starts Postgres (Docker), the backend (uvicorn --reload), and the frontend (Vite dev server) each
# in their own visible terminal window, waits for both to respond, then opens the app in your
# default browser. Close the two opened windows (or Ctrl+C in each) to stop the dev servers; run
# dev-stop.ps1 to also stop the Postgres container.
#
# Prefer double-clicking dev-start.bat - plain .ps1 files open in a text editor by default on
# Windows rather than running.

$ErrorActionPreference = "Stop"
$repoRoot = $PSScriptRoot
Set-Location $repoRoot

# A raw TCP connect check, not Invoke-WebRequest: repeatedly calling Invoke-WebRequest against a
# port nobody's listening on yet can get its underlying HttpClient/connection state stuck in Windows
# PowerShell, so it keeps failing for minutes even after the server is actually up and answering
# fine to everything else (curl, a fresh Invoke-WebRequest call, a browser). Confirmed by timing:
# the backend itself is ready in ~2s; only the polling-in-a-loop approach was ever slow.
#
# Tries both 127.0.0.1 and ::1 explicitly rather than "localhost": uvicorn binds IPv4-only, Vite
# binds IPv6-only by default here. Each needs a TcpClient constructed for the matching address
# family - the default (parameterless) constructor is IPv4-only, so connecting it to "::1" fails
# with "address incompatible with the requested protocol" even though nothing else is wrong; and
# under Windows PowerShell 5.1 (.NET Framework, used when launched via dev-start.bat), passing an
# IPv6 literal as a bare string to the Connect(string, int) overload fails outright, so the address
# must be parsed to an IPAddress first.
function Wait-Port {
    param([int]$Port, [string]$Name, [int]$TimeoutSeconds = 45)
    Write-Host -NoNewline "Waiting for $Name"
    for ($i = 0; $i -lt $TimeoutSeconds * 2; $i++) {
        foreach ($family in @([System.Net.Sockets.AddressFamily]::InterNetwork, [System.Net.Sockets.AddressFamily]::InterNetworkV6)) {
            $addr = if ($family -eq [System.Net.Sockets.AddressFamily]::InterNetwork) { "127.0.0.1" } else { "::1" }
            $tcp = New-Object System.Net.Sockets.TcpClient($family)
            try {
                $tcp.Connect([System.Net.IPAddress]::Parse($addr), $Port)
                if ($tcp.Connected) { $tcp.Close(); Write-Host " ready." -ForegroundColor Green; return $true }
            } catch {}
            $tcp.Close()
        }
        Write-Host -NoNewline "."
        Start-Sleep -Milliseconds 500
    }
    Write-Host ""
    Write-Host "$Name did not start listening on port $Port (checked 127.0.0.1 and ::1) within ${TimeoutSeconds}s." -ForegroundColor Red
    return $false
}

if (-not (Test-Path "$repoRoot\.env")) {
    Write-Host "No .env found - copy .env.example to .env first (see README Quickstart)." -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path "$repoRoot\backend\.venv\Scripts\python.exe")) {
    Write-Host "No backend/.venv found - run 'pip install -e .[dev]' from backend/ first (see backend/README.md)." -ForegroundColor Yellow
    exit 1
}

Write-Host "Checking Docker..." -ForegroundColor Cyan
docker info *>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker daemon not running - starting Docker Desktop (this can take a minute)..." -ForegroundColor Yellow
    docker desktop start
    $dockerReady = $false
    for ($i = 0; $i -lt 60; $i++) {
        docker info *>$null
        if ($LASTEXITCODE -eq 0) { $dockerReady = $true; break }
        Start-Sleep -Seconds 2
    }
    if (-not $dockerReady) {
        Write-Host "Docker did not become ready in time." -ForegroundColor Red
        exit 1
    }
}

Write-Host "Starting Postgres..." -ForegroundColor Cyan
docker compose up -d db

Write-Host "Waiting for Postgres..." -ForegroundColor Cyan
$pgReady = $false
for ($i = 0; $i -lt 30; $i++) {
    docker exec flight-companion-db pg_isready -U flightcompanion *>$null
    if ($LASTEXITCODE -eq 0) { $pgReady = $true; break }
    Start-Sleep -Seconds 1
}
if (-not $pgReady) {
    Write-Host "Postgres did not become ready in time." -ForegroundColor Red
    exit 1
}
Write-Host "Postgres is ready." -ForegroundColor Green

Write-Host "Starting backend in a new window..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "Set-Location '$repoRoot\backend'; & '.\.venv\Scripts\python.exe' -m uvicorn app.main:app --reload --port 8000"
)

Write-Host "Starting frontend in a new window..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "Set-Location '$repoRoot\frontend'; npm run dev"
)

Write-Host "Waiting for backend and frontend to come up..." -ForegroundColor Cyan
$backendOk = Wait-Port -Port 8000 -Name "Backend"
$frontendOk = Wait-Port -Port 5173 -Name "Frontend"

if ($backendOk -and $frontendOk) {
    Write-Host "Opening http://localhost:5173 ..." -ForegroundColor Green
    Start-Process "http://localhost:5173"
} else {
    Write-Host "One or both services didn't start - check the two opened terminal windows for errors." -ForegroundColor Red
    exit 1
}
