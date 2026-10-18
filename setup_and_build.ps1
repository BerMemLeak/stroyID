# StroyID Setup and Build Script
# This script sets up the development environment and builds the application

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "StroyID Setup and Build Script" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Check Python installation
Write-Host "[1/5] Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8 or later from https://www.python.org/" -ForegroundColor Red
    exit 1
}

# Check Python version (require 3.8+)
$versionMatch = $pythonVersion -match "Python (\d+)\.(\d+)"
if ($versionMatch) {
    $major = [int]$Matches[1]
    $minor = [int]$Matches[2]
    if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 8)) {
        Write-Host "ERROR: Python 3.8 or later is required" -ForegroundColor Red
        exit 1
    }
}

# Create virtual environment
Write-Host ""
Write-Host "[2/5] Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path ".venv") {
    Write-Host "Virtual environment already exists, skipping creation" -ForegroundColor Gray
} else {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
    Write-Host "Virtual environment created successfully" -ForegroundColor Green
}

# Activate virtual environment
Write-Host ""
Write-Host "[3/5] Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to activate virtual environment" -ForegroundColor Red
    exit 1
}
Write-Host "Virtual environment activated" -ForegroundColor Green

# Install dependencies
Write-Host ""
Write-Host "[4/5] Installing dependencies..." -ForegroundColor Yellow
Write-Host "Installing runtime dependencies..." -ForegroundColor Gray
python -m pip install --upgrade pip
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install runtime dependencies" -ForegroundColor Red
    exit 1
}

Write-Host "Installing build dependencies..." -ForegroundColor Gray
pip install -r requirements-build.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install build dependencies" -ForegroundColor Red
    exit 1
}
Write-Host "All dependencies installed successfully" -ForegroundColor Green

# Create necessary directories
Write-Host ""
Write-Host "Creating necessary directories..." -ForegroundColor Gray
New-Item -ItemType Directory -Force -Path "logs" | Out-Null
New-Item -ItemType Directory -Force -Path "tmp" | Out-Null
New-Item -ItemType Directory -Force -Path "release" | Out-Null

# Build application
Write-Host ""
Write-Host "[5/5] Building application..." -ForegroundColor Yellow
& .\build_windows.ps1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Build failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Setup and build completed successfully!" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "The application has been built to: release\StroyID.exe" -ForegroundColor White
Write-Host ""
Write-Host "To run the application from source:" -ForegroundColor White
Write-Host "  .\run_windows.bat" -ForegroundColor Cyan
Write-Host ""
