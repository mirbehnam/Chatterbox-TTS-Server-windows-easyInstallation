[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

# --- Path Configuration ---
$scriptDir   = $PSScriptRoot 
$projectRoot = (Split-Path -Parent $scriptDir)

Write-Host "Project Root Directory set to: $projectRoot" -ForegroundColor Cyan

try {
    # Step 1: Run dependency installer and CAPTURE its output (the python path)
    Write-Host "Searching for Python 3.10 and other dependencies..." -ForegroundColor Yellow
    $pythonExePath = & (Join-Path $scriptDir "install-dependencies.ps1")
    
    if (-not $pythonExePath -or -not (Test-Path $pythonExePath)) {
        throw "Could not find or install a valid Python 3.10 executable. Aborting."
    }
    Write-Host "Using Python executable: $pythonExePath" -ForegroundColor Green

    # Step 2: Ask user for installation type
    $installType = ''
    while ($installType -notin ('1', '2', '3')) {
        Write-Host "`n=== Choose Installation Type ===" -ForegroundColor Magenta
        Write-Host "1) NVIDIA GPU Version (CUDA, recommended for NVIDIA GPUs)"
        Write-Host "2) CPU Only Version (Works everywhere, slower)"
        Write-Host "3) AMD GPU Version (ROCm, RX 6000/7000 series and newer)"
        $installType = Read-Host "Enter your choice (1, 2 or 3)"
    }

    $useNvidia = $false
    $useAmd    = $false

    if ($installType -eq '1') {
        Write-Host "Checking for NVIDIA GPU..." -ForegroundColor Cyan
        $gpu = Get-WmiObject -Query "SELECT * FROM Win32_VideoController WHERE Name LIKE '%NVIDIA%'"
        if ($gpu) {
            Write-Host "NVIDIA GPU detected: $($gpu.Name)" -ForegroundColor Green
            $useNvidia = $true
        } else {
            Write-Host "No NVIDIA GPU detected. Switching to CPU-only." -ForegroundColor Yellow
        }
    } elseif ($installType -eq '2') {
        Write-Host "CPU-only installation selected." -ForegroundColor Green
    } elseif ($installType -eq '3') {
        Write-Host "Checking for AMD GPU..." -ForegroundColor Cyan
        $gpu = Get-WmiObject -Query "SELECT * FROM Win32_VideoController WHERE Name LIKE '%AMD%' OR Name LIKE '%Radeon%'"
        if ($gpu) {
            Write-Host "AMD GPU detected: $($gpu.Name)" -ForegroundColor Green
            $useAmd = $true
        } else {
            Write-Host "No AMD GPU detected. Switching to CPU-only." -ForegroundColor Yellow
        }
    }

    # Step 3: Create virtual environment
    $venvPath = Join-Path $projectRoot "venv"
    Write-Host "`nCreating Python virtual environment in '$venvPath'..." -ForegroundColor Yellow
    if (Test-Path $venvPath) {
        Write-Host "Virtual environment folder 'venv' already exists. Reusing it." -ForegroundColor Cyan
    }

    & $pythonExePath -m venv $venvPath

    # Step 4: Activate and install packages
    $venvPip = Join-Path $venvPath "Scripts\pip.exe"

    Write-Host "Upgrading pip..." -ForegroundColor Yellow
    & $venvPip install --upgrade pip

    if ($useNvidia) {
        $requirementsFile = "requirements-nvidia.txt"
        Write-Host "Installing NVIDIA GPU requirements from '$requirementsFile'..." -ForegroundColor Yellow
    } elseif ($useAmd) {
        $requirementsFile = "requirements-rocm.txt"
        Write-Host "Installing AMD ROCm requirements from '$requirementsFile'..." -ForegroundColor Yellow
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

    Write-Host "`n✅ Project setup completed successfully!" -ForegroundColor Green

} catch {
    Write-Host "`n❌ Error during setup: $_" -ForegroundColor Red
    throw "Main setup script failed."
}
