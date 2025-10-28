# eCertificate Windows Run Script
# This script runs the eCertificate application on Windows

param(
    [string]$Entrypoint = "app.py",
    [ValidateSet("flask", "fastapi")]
    [string]$Framework = "flask",
    [int]$Port = 5000
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "eCertificate - Starting Application" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path ".venv")) {
    Write-Host "✗ Virtual environment not found!" -ForegroundColor Red
    Write-Host "  Please run setup first: .\scripts\windows\setup.ps1" -ForegroundColor Yellow
    exit 1
}

# Load environment variables from .env file
Write-Host "[1/4] Loading environment variables..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]*)\s*=\s*(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            # Remove quotes if present, but handle empty values
            if ($value -match '^["'']' -and $value -match '["'']$') {
                $value = $value.Substring(1, $value.Length - 2)
            }
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
    Write-Host "[OK] Environment variables loaded from .env" -ForegroundColor Green
} else {
    Write-Host "[WARN] .env file not found, using defaults" -ForegroundColor Yellow
    Write-Host "  Run setup to create .env: .\scripts\windows\setup.ps1" -ForegroundColor Yellow
}

# Check if entrypoint exists
Write-Host ""
Write-Host "[2/4] Checking entrypoint..." -ForegroundColor Yellow
if (-not (Test-Path $Entrypoint)) {
    Write-Host "[FAIL] Entrypoint not found: $Entrypoint" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Entrypoint found: $Entrypoint" -ForegroundColor Green

# Check framework dependencies
Write-Host ""
Write-Host "[3/4] Checking framework dependencies..." -ForegroundColor Yellow

if ($Framework -eq "flask") {
    $flaskInstalled = & ".venv\Scripts\python.exe" -c "import flask" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠ Flask not installed. Installing..." -ForegroundColor Yellow
        & ".venv\Scripts\pip.exe" install flask --quiet
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Flask installed successfully" -ForegroundColor Green
        } else {
            Write-Host "✗ Failed to install Flask" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "✓ Flask is installed" -ForegroundColor Green
    }
} elseif ($Framework -eq "fastapi") {
    $fastapiInstalled = & ".venv\Scripts\python.exe" -c "import fastapi" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠ FastAPI not installed. Installing..." -ForegroundColor Yellow
        & ".venv\Scripts\pip.exe" install fastapi uvicorn --quiet
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ FastAPI and uvicorn installed successfully" -ForegroundColor Green
        } else {
            Write-Host "✗ Failed to install FastAPI" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "✓ FastAPI is installed" -ForegroundColor Green
    }
}

# Start the application
Write-Host ""
Write-Host "[4/4] Starting application..." -ForegroundColor Yellow
Write-Host "Framework: $Framework" -ForegroundColor White
Write-Host "Entrypoint: $Entrypoint" -ForegroundColor White
Write-Host "Port: $Port" -ForegroundColor White
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Application is starting..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Set environment variables for the app
[Environment]::SetEnvironmentVariable("FLASK_APP", $Entrypoint, "Process")
[Environment]::SetEnvironmentVariable("PORT", $Port.ToString(), "Process")

if ($Framework -eq "flask") {
    # Use Flask development server
    [Environment]::SetEnvironmentVariable("FLASK_RUN_PORT", $Port.ToString(), "Process")
    
    # Check if we should use flask run or python directly
    if ($Entrypoint -eq "app.py") {
        # Use python app.py for the default entrypoint
        & ".venv\Scripts\python.exe" $Entrypoint
    } else {
        # Use flask run for other entrypoints
        & ".venv\Scripts\flask.exe" run --host=0.0.0.0 --port=$Port
    }
} elseif ($Framework -eq "fastapi") {
    # Use uvicorn for FastAPI
    $module = $Entrypoint -replace '\.py$', '' -replace '[/\\]', '.'
    & ".venv\Scripts\uvicorn.exe" "${module}:app" --host 0.0.0.0 --port $Port --reload
}

# Cleanup on exit
Write-Host ""
Write-Host "Application stopped." -ForegroundColor Yellow
