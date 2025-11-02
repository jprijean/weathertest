# Setup script for Weather Alert System
# This script creates a virtual environment and installs dependencies

Write-Host "Setting up Python virtual environment..." -ForegroundColor Green

# Try different ways to find Python
$pythonCmd = $null

# Try python
try {
    $version = python --version 2>&1
    if ($LASTEXITCODE -eq 0 -and $version -match "Python \d+\.\d+") {
        $pythonCmd = "python"
        Write-Host "Found Python: $version" -ForegroundColor Green
    }
} catch {}

# Try python3
if (-not $pythonCmd) {
    try {
        $version = python3 --version 2>&1
        if ($LASTEXITCODE -eq 0 -and $version -match "Python \d+\.\d+") {
            $pythonCmd = "python3"
            Write-Host "Found Python3: $version" -ForegroundColor Green
        }
    } catch {}
}

# Try py launcher
if (-not $pythonCmd) {
    try {
        $version = py --version 2>&1
        if ($LASTEXITCODE -eq 0 -and $version -match "Python \d+\.\d+") {
            $pythonCmd = "py"
            Write-Host "Found Python via launcher: $version" -ForegroundColor Green
        }
    } catch {}
}

if (-not $pythonCmd) {
    Write-Host "ERROR: Python not found!" -ForegroundColor Red
    Write-Host "Please install Python from https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Make sure to check 'Add Python to PATH' during installation." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Create virtual environment
Write-Host ""
Write-Host "Creating virtual environment..." -ForegroundColor Cyan
& $pythonCmd -m venv venv

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to create virtual environment" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& .\venv\Scripts\Activate.ps1

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to activate virtual environment" -ForegroundColor Red
    Write-Host "Try running: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Upgrade pip
Write-Host ""
Write-Host "Upgrading pip..." -ForegroundColor Cyan
python -m pip install --upgrade pip

# Install requirements
Write-Host ""
Write-Host "Installing requirements..." -ForegroundColor Cyan
pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Setup complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "To activate the virtual environment in the future, run:" -ForegroundColor Cyan
    Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "ERROR: Failed to install requirements" -ForegroundColor Red
}

Write-Host ""
Read-Host "Press Enter to exit"

