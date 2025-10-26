# eCertificate Windows Setup Script
# This script sets up the development environment for eCertificate on Windows

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "eCertificate - Windows Setup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
Write-Host "[1/5] Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found! Please install Python 3.8 or higher." -ForegroundColor Red
    Write-Host "Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Check Python version
$versionString = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
$version = [version]$versionString
if ($version -lt [version]"3.8") {
    Write-Host "✗ Python 3.8 or higher is required. Found: $versionString" -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host ""
Write-Host "[2/5] Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path ".venv") {
    Write-Host "✓ Virtual environment already exists at .venv" -ForegroundColor Green
} else {
    python -m venv .venv
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Virtual environment created at .venv" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
}

# Activate virtual environment and upgrade pip
Write-Host ""
Write-Host "[3/5] Upgrading pip..." -ForegroundColor Yellow
& ".venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ pip upgraded successfully" -ForegroundColor Green
} else {
    Write-Host "⚠ pip upgrade failed, but continuing..." -ForegroundColor Yellow
}

# Install dependencies
Write-Host ""
Write-Host "[4/5] Installing dependencies..." -ForegroundColor Yellow
if (Test-Path "requirements.txt") {
    & ".venv\Scripts\pip.exe" install -r requirements.txt --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Dependencies installed from requirements.txt" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to install some dependencies" -ForegroundColor Red
        Write-Host "  Run manually: .\.venv\Scripts\pip.exe install -r requirements.txt" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠ requirements.txt not found" -ForegroundColor Yellow
    Write-Host "  Please create requirements.txt with your dependencies" -ForegroundColor Yellow
}

# Setup .env file
Write-Host ""
Write-Host "[5/5] Setting up environment file..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "✓ .env file already exists" -ForegroundColor Green
} else {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "✓ Created .env from .env.example" -ForegroundColor Green
        Write-Host "  ⚠ Please edit .env with your configuration" -ForegroundColor Yellow
    } elseif (Test-Path ".env.sample") {
        Copy-Item ".env.sample" ".env"
        Write-Host "✓ Created .env from .env.sample" -ForegroundColor Green
        Write-Host "  ⚠ Please edit .env with your configuration" -ForegroundColor Yellow
    } else {
        Write-Host "⚠ No .env.example or .env.sample found" -ForegroundColor Yellow
        Write-Host "  Please create a .env file manually" -ForegroundColor Yellow
    }
}

# Success message
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup completed successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Edit .env file with your configuration" -ForegroundColor White
Write-Host "2. Run the application:" -ForegroundColor White
Write-Host "   .\scripts\windows\run.ps1" -ForegroundColor Yellow
Write-Host ""
Write-Host "For Docker:" -ForegroundColor White
Write-Host "   .\scripts\windows\run-docker.ps1" -ForegroundColor Yellow
Write-Host ""
Write-Host "For more information, see README-WINDOWS.md" -ForegroundColor White
Write-Host ""
