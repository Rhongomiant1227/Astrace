$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..\\..")
Set-Location $root

if (-not (Test-Path ".venv\\Scripts\\python.exe")) {
    Write-Error "Virtual env not found. Run .\\scripts\\windows\\setup.ps1 first."
}

if (-not $env:MCP_HOST) { $env:MCP_HOST = "0.0.0.0" }
if (-not $env:MCP_PORT) { $env:MCP_PORT = "8788" }
if (-not $env:SEARCH_MAX_RESULTS) { $env:SEARCH_MAX_RESULTS = "8" }
if (-not $env:REQUEST_TIMEOUT) { $env:REQUEST_TIMEOUT = "15" }
if (-not $env:MAX_TEXT_CHARS) { $env:MAX_TEXT_CHARS = "12000" }
if (-not $env:ASTRACE_TASK_WORKERS) { $env:ASTRACE_TASK_WORKERS = "2" }

& .\.venv\Scripts\python -m astrace.server
