# eCertificate Windows Docker Run Script
# This script builds and runs the eCertificate application using Docker

param(
    [string]$ImageName = "ecertificate-app",
    [string]$ContainerName = "ecertificate-container",
    [int]$Port = 5000
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "eCertificate - Docker Run Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is installed
Write-Host "[1/5] Checking Docker installation..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>&1
    Write-Host "✓ Docker found: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker not found! Please install Docker Desktop for Windows." -ForegroundColor Red
    Write-Host "Download from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# Check if Docker is running
Write-Host ""
Write-Host "[2/5] Checking Docker daemon..." -ForegroundColor Yellow
try {
    docker info | Out-Null 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Docker daemon is running" -ForegroundColor Green
    } else {
        Write-Host "✗ Docker daemon is not running. Please start Docker Desktop." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "✗ Docker daemon is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Check if Dockerfile exists
Write-Host ""
Write-Host "[3/5] Checking for Dockerfile..." -ForegroundColor Yellow
if (-not (Test-Path "Dockerfile")) {
    Write-Host "⚠ Dockerfile not found. Creating a basic Dockerfile..." -ForegroundColor Yellow
    
    $dockerfileContent = @"
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create necessary directories
RUN mkdir -p uploads generated_certificates

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
"@
    
    Set-Content -Path "Dockerfile" -Value $dockerfileContent
    Write-Host "✓ Created basic Dockerfile" -ForegroundColor Green
} else {
    Write-Host "✓ Dockerfile found" -ForegroundColor Green
}

# Check if .env file exists
Write-Host ""
Write-Host "[4/5] Checking for .env file..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Write-Host "⚠ .env file not found" -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Write-Host "  Using .env.example for Docker (please create .env for customization)" -ForegroundColor Yellow
        $envFile = ".env.example"
    } elseif (Test-Path ".env.sample") {
        Write-Host "  Using .env.sample for Docker (please create .env for customization)" -ForegroundColor Yellow
        $envFile = ".env.sample"
    } else {
        Write-Host "  No environment file found. Running without env file..." -ForegroundColor Yellow
        $envFile = $null
    }
} else {
    Write-Host "✓ .env file found" -ForegroundColor Green
    $envFile = ".env"
}

# Build Docker image
Write-Host ""
Write-Host "[5/5] Building Docker image..." -ForegroundColor Yellow
Write-Host "Image name: $ImageName" -ForegroundColor White
Write-Host ""

docker build -t $ImageName .
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to build Docker image" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Docker image built successfully" -ForegroundColor Green

# Stop and remove existing container if it exists
Write-Host ""
Write-Host "Checking for existing container..." -ForegroundColor Yellow
$existingContainer = docker ps -a --filter "name=$ContainerName" --format "{{.Names}}" 2>&1
if ($existingContainer -eq $ContainerName) {
    Write-Host "Stopping and removing existing container..." -ForegroundColor Yellow
    docker stop $ContainerName | Out-Null 2>&1
    docker rm $ContainerName | Out-Null 2>&1
    Write-Host "✓ Existing container removed" -ForegroundColor Green
}

# Prepare volume mounts
Write-Host ""
Write-Host "Preparing volume mounts..." -ForegroundColor Yellow
$currentDir = (Get-Location).Path
$volumeMounts = @()

# Mount common directories if they exist
$dirsToMount = @("templates", "static", "output", "uploads", "generated_certificates")
foreach ($dir in $dirsToMount) {
    if (Test-Path $dir) {
        $volumeMounts += "-v"
        $volumeMounts += "${currentDir}\${dir}:/app/${dir}"
        Write-Host "  Mounting: $dir" -ForegroundColor White
    }
}

if ($volumeMounts.Count -eq 0) {
    Write-Host "  No directories to mount" -ForegroundColor White
}

# Run Docker container
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Docker container..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Container name: $ContainerName" -ForegroundColor White
Write-Host "Port mapping: ${Port}:5000" -ForegroundColor White
Write-Host "Access at: http://localhost:$Port" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the container" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Build docker run command
$dockerArgs = @(
    "run"
    "--rm"
    "--name", $ContainerName
    "-p", "${Port}:5000"
)

if ($envFile) {
    $dockerArgs += "--env-file"
    $dockerArgs += $envFile
}

$dockerArgs += $volumeMounts
$dockerArgs += $ImageName

# Run the container
& docker $dockerArgs

# Cleanup message
Write-Host ""
Write-Host "Container stopped." -ForegroundColor Yellow
