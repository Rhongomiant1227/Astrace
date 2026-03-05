$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..\\..")
Set-Location $root

if (-not (Test-Path ".venv\\Scripts\\python.exe")) {
    Write-Error "Virtual env not found. Run .\\scripts\\windows\\setup.ps1 first."
}

& .\.venv\Scripts\python -m astrace.server --self-test
& .\.venv\Scripts\python -m pytest -q

Write-Host "Windows tests passed."

