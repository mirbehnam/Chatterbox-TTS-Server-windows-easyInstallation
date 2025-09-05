[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

# --- Path Configuration ---
$scriptDir = $PSScriptRoot 
$projectRoot = (Split-Path -Parent $scriptDir)

Write-Host "Project Root Directory set to: $projectRoot" -ForegroundColor Cyan

try {
    # Step 1: Run dependency installer and CAPTURE its output (the python path)
    Write-Host "Searching for Python 3.10 and other dependencies..." -ForegroundColor Yellow
    $pythonExePath = & (Join-Path $scriptDir "install-dependencies.ps1")
    
    # Error handling: ensure we got a valid path
    if (-not $pythonExePath -or -not (Test-Path $pythonExePath)) {
        throw "Could not find or install a valid Python 3.10 executable. Aborting."
    }
    Write-Host "Using Python executable: $pythonExePath" -ForegroundColor Green

    # Step 2: Ask user for installation type
    $installType = ''
    while ($installType -notin ('1', '2')) {
        Write-Host "`n=== Choose Installation Type ===" -ForegroundColor Magenta
        Write-Host "1) NVIDIA GPU Version (Recommended for better performance)"
        Write-Host "2) CPU Only Version (Slower, but works on any computer)"
        $installType = Read-Host "Enter your choice (1 or 2)"
    }

    $useNvidia = $false
    if ($installType -eq '1') {
        Write-Host "Checking for NVIDIA GPU..." -ForegroundColor Cyan
        $gpu = Get-WmiObject -Query "SELECT * FROM Win32_VideoController WHERE Name LIKE '%NVIDIA%'"
        if ($gpu) {
            Write-Host "NVIDIA GPU detected: $($gpu.Name)" -ForegroundColor Green
            $useNvidia = $true
        } else {
            Write-Host "No NVIDIA GPU detected on your system." -ForegroundColor Yellow
            Write-Host "Switching to CPU-only installation." -ForegroundColor Yellow
            $useNvidia = $false
        }
    } else {
        Write-Host "CPU-only installation selected." -ForegroundColor Green
        $useNvidia = $false
    }

    # Step 3: Create virtual environment in the project root using the EXACT python path
    $venvPath = Join-Path $projectRoot "venv"
    Write-Host "`nCreating Python virtual environment in '$venvPath'..." -ForegroundColor Yellow
    if (Test-Path $venvPath) {
        Write-Host "Virtual environment folder 'venv' already exists. Reusing it." -ForegroundColor Cyan
    }
    
    # Use the specific python executable we found
    & $pythonExePath -m venv $venvPath

    # Step 4: Activate and install packages
    $venvPip = Join-Path $venvPath "Scripts\pip.exe"

    Write-Host "Upgrading pip..." -ForegroundColor Yellow
    & $venvPip install --upgrade pip

    if ($useNvidia) {
        $requirementsFile = "requirements-nvidia.txt"
        Write-Host "Installing NVIDIA GPU requirements from '$requirementsFile'..." -ForegroundColor Yellow
    } else {
        $requirementsFile = "requirements.txt"
        Write-Host "Installing CPU requirements from '$requirementsFile'..." -ForegroundColor Yellow
    }

    $reqPath = Join-Path $projectRoot $requirementsFile
    if (-not (Test-Path $reqPath)) {
        throw "Requirement file not found: $reqPath"
    }

    & $venvPip install -r $reqPath

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install Python packages from $requirementsFile."
    }

    Write-Host "`nProject setup completed successfully!" -ForegroundColor Green

} catch {
    Write-Host "`nError during setup: $_" -ForegroundColor Red
    throw "Main setup script failed."
}