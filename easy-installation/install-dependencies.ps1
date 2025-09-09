[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
Write-Host "=== Running Pre-installation Checks ===" -ForegroundColor Cyan

# --- Configuration ---
$config = @{
    PythonUrl             = 'https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe'
    PythonInstaller       = Join-Path $env:TEMP 'python-3.10.11-amd64.exe'
    RequiredPythonVersion = '3.10'
    GitInstallerUrl       = 'https://github.com/git-for-windows/git/releases/download/v2.42.0.windows.2/Git-2.42.0.2-64-bit.exe'
    GitInstaller          = Join-Path $env:TEMP 'Git-2.42.0.2-64-bit.exe'
}

# --- Helper Functions ---
function Find-Python310Executable {
    try {
        $pythonPaths = Get-Command python -All -ErrorAction SilentlyContinue | 
            Where-Object { $_.CommandType -eq 'Application' -and $_.Source -notlike "*WindowsApps*" } | 
            Select-Object -Unique -ExpandProperty Source
        if ($pythonPaths) {
            foreach ($path in $pythonPaths) {
                $versionOutput = & $path -c "import sys; print('.'.join(map(str, sys.version_info[:2])))" 2>$null
                if ($versionOutput -eq $config.RequiredPythonVersion) {
                    Write-Host "Found compatible Python 3.10 at: $path" -ForegroundColor Green
                    return $path
                }
            }
        }
    } catch { }
    return $null
}

function Test-GitInstallation {
    return [bool](Get-Command git -ErrorAction SilentlyContinue)
}

# --- Main Logic ---
try {
    # 1. Find or Install Python 3.10
    $pythonExePath = Find-Python310Executable
    if (-not $pythonExePath) {
        Write-Host "Python $($config.RequiredPythonVersion) not found. Downloading..." -ForegroundColor Yellow
        if (-not (Test-Path $config.PythonInstaller)) {
            Import-Module BitsTransfer
            Start-BitsTransfer -Source $config.PythonUrl -Destination $config.PythonInstaller -Description "Downloading Python Installer"
        }

        Write-Host "Installing Python silently... This may take a moment." -ForegroundColor Yellow
        $pythonArgs = @('/quiet', 'InstallAllUsers=1', 'PrependPath=1', 'Include_pip=1')
        Start-Process -FilePath $config.PythonInstaller -ArgumentList $pythonArgs -Wait -NoNewWindow
        
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        
        $pythonExePath = Find-Python310Executable
        if (-not $pythonExePath) {
            throw "Python 3.10 installation failed. Please restart your terminal and try again."
        }
    }

    # 2. Check and Install Git
    if (-not (Test-GitInstallation)) {
        Write-Host "Git is not installed. Downloading..." -ForegroundColor Yellow
        if (-not (Test-Path $config.GitInstaller)) {
            Import-Module BitsTransfer
            Start-BitsTransfer -Source $config.GitInstallerUrl -Destination $config.GitInstaller -Description "Downloading Git Installer"
        }

        Write-Host "Installing Git silently..." -ForegroundColor Yellow
        $gitArgs = @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/NOCANCEL', '/COMPONENTS=assoc,assoc_sh')
        Start-Process -FilePath $config.GitInstaller -ArgumentList $gitArgs -Wait -NoNewWindow
        
        $env:Path = "$($env:Path);$(Join-Path ${env:ProgramFiles} 'Git\cmd')"
        
        if (-not (Test-GitInstallation)) {
            throw "Git installation failed. Please restart your terminal and try again."
        }
        Write-Host "Git installed successfully." -ForegroundColor Green
    } else {
        Write-Host "Git is already installed." -ForegroundColor Green
    }
    
    Write-Host "=== Pre-installation checks completed successfully! ===" -ForegroundColor Cyan
    
    return $pythonExePath

} catch {
    Write-Host "`nError during dependency installation: $_" -ForegroundColor Red
    throw "Script encountered an error."
}
