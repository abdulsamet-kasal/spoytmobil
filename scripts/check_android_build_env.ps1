Write-Host "Spoyt Android build environment check" -ForegroundColor Cyan

$buildozerSource = "C:\Users\abdul\Desktop\kivy-buildozer-b4ae422"
$projectRoot = Split-Path -Parent $PSScriptRoot

Write-Host ""
Write-Host "Project: $projectRoot"
Write-Host "Buildozer source: $buildozerSource"

if (Test-Path $buildozerSource) {
    Write-Host "OK: local Buildozer source exists"
} else {
    Write-Host "MISSING: local Buildozer source was not found" -ForegroundColor Yellow
}

if (Get-Command wsl -ErrorAction SilentlyContinue) {
    $wslStatus = & wsl --status 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "OK: WSL is available"
    } else {
        Write-Host "WSL command exists, but WSL is not installed/configured:" -ForegroundColor Yellow
        Write-Host $wslStatus
    }
} else {
    Write-Host "MISSING: wsl.exe was not found" -ForegroundColor Yellow
}

if (Get-Command docker -ErrorAction SilentlyContinue) {
    & docker --version
} else {
    Write-Host "MISSING: Docker was not found" -ForegroundColor Yellow
}

if (Get-Command winget -ErrorAction SilentlyContinue) {
    Write-Host "OK: winget is available"
    Write-Host "You can install Docker Desktop with:"
    Write-Host "  winget install Docker.DockerDesktop"
} else {
    Write-Host "MISSING: winget was not found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Native Windows Buildozer cannot build Android APKs."
Write-Host "Use one of these once WSL or Docker is installed:"
Write-Host "  powershell -ExecutionPolicy Bypass -File scripts\build_android_docker.ps1"
Write-Host "  bash scripts/build_android_wsl.sh"
