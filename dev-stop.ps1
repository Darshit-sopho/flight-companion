# Stops the Postgres container started by dev-start.ps1. The backend/frontend run in their own
# visible terminal windows (not hidden background processes) - close those windows or Ctrl+C in
# each to stop them.

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "Stopping Postgres..." -ForegroundColor Cyan
docker compose stop db
Write-Host "Done. Close the backend/frontend terminal windows (Ctrl+C) if they're still open." -ForegroundColor Green
