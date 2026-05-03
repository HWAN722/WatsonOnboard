# PowerShell script for local development tasks

param(
    [Parameter(Position=0)]
    [ValidateSet('install', 'test', 'lint', 'format', 'run', 'clean', 'help')]
    [string]$Command = 'help'
)

function Show-Help {
    Write-Host "Available commands:" -ForegroundColor Green
    Write-Host "  .\run_local.ps1 install    - Install dependencies"
    Write-Host "  .\run_local.ps1 test       - Run tests"
    Write-Host "  .\run_local.ps1 lint       - Run linters"
    Write-Host "  .\run_local.ps1 format     - Format code"
    Write-Host "  .\run_local.ps1 run        - Run API server"
    Write-Host "  .\run_local.ps1 clean      - Clean cache and build files"
}

function Install-Dependencies {
    Write-Host "Installing dependencies..." -ForegroundColor Green
    python -m pip install --upgrade pip
    pip install -r requirements.txt
}

function Run-Tests {
    Write-Host "Running tests..." -ForegroundColor Green
    pytest
}

function Run-Lint {
    Write-Host "Running linters..." -ForegroundColor Green
    ruff check src tests
    mypy src
}

function Format-Code {
    Write-Host "Formatting code..." -ForegroundColor Green
    black src tests
    ruff check --fix src tests
}

function Start-Server {
    Write-Host "Starting API server..." -ForegroundColor Green
    uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
}

function Clean-Project {
    Write-Host "Cleaning project..." -ForegroundColor Green
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue .cache, .chroma, __pycache__, .pytest_cache, .coverage, htmlcov
    Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
    Get-ChildItem -Recurse -File -Filter "*.pyc" | Remove-Item -Force
}

switch ($Command) {
    'install' { Install-Dependencies }
    'test' { Run-Tests }
    'lint' { Run-Lint }
    'format' { Format-Code }
    'run' { Start-Server }
    'clean' { Clean-Project }
    'help' { Show-Help }
    default { Show-Help }
}

# Made with Bob
