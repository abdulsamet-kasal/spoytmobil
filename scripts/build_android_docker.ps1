$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$buildozerSource = "C:\Users\abdul\Desktop\kivy-buildozer-b4ae422"

if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker was not found. Install Docker Desktop first, then rerun this script."
}

if (!(Test-Path $buildozerSource)) {
    throw "Buildozer source folder was not found: $buildozerSource"
}

Push-Location $buildozerSource
try {
    docker build --tag=kivy/buildozer .
} finally {
    Pop-Location
}

$buildozerCache = Join-Path $env:USERPROFILE ".buildozer"
New-Item -ItemType Directory -Force -Path $buildozerCache | Out-Null

Push-Location $projectRoot
try {
    docker run --interactive --tty --rm `
        --volume "${buildozerCache}:/home/user/.buildozer" `
        --volume "${projectRoot}:/home/user/hostcwd" `
        kivy/buildozer android debug
} finally {
    Pop-Location
}
