@echo off
setlocal

title Project Setup

:menu
cls
echo =====================================
echo    Project Installation Menu
echo =====================================
echo.
echo  This script will guide you through the
echo  installation process.
echo.
echo =====================================
echo.
echo  1. Start Full Installation
echo  0. Exit
echo.
echo =====================================
echo.
set /p choice="Select an option (0-1): "

if "%choice%"=="0" exit /b 0
if "%choice%"=="1" (
    goto start_install
)

echo Invalid option. Please try again.
timeout /t 2 >nul
goto menu

:start_install
cls
echo Starting installation...
echo This may take a while. Please be patient.
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0easy-installation\run-setup.ps1"
if errorlevel 1 (
    echo.
    echo ==========================================================
    echo  An error occurred during installation.
    echo  Please check the messages above for more details.
    echo ==========================================================
    echo.
    pause
    goto menu
)

echo.
echo ==========================================================
echo  Installation completed successfully!
echo ==========================================================
echo.
pause
exit /b 0

endlocal