$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..\\..")
Set-Location $root

if (-not (Test-Path ".venv")) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        py -3.12 -m venv .venv
    }
    else {
        python -m venv .venv
    }
}

& .\.venv\Scripts\python -m pip install --upgrade pip
& .\.venv\Scripts\python -m pip install -r requirements.txt

& .\.venv\Scripts\python -m astrace.server --self-test

Write-Host ""
Write-Host "Astrace setup complete."
Write-Host "Start with: .\\scripts\\windows\\start.ps1"

