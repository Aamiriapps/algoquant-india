@echo off
setlocal enabledelayedexpansion
title AlgoQuant India - Indian Stock Market Screener

:: Always execute from project directory
cd /d "%~dp0"

echo ====================================================================
echo Starting AlgoQuant India Web Dashboard...
echo ====================================================================

:: Locate Python executable
set "PYTHON_EXE="

:: 1. Check direct path to Python 3.12
if exist "C:\Users\Mohammed Ali\AppData\Local\Programs\Python\Python312\python.exe" (
    set "PYTHON_EXE=C:\Users\Mohammed Ali\AppData\Local\Programs\Python\Python312\python.exe"
    goto :found_python
)

:: 2. Check if python is in PATH
for /f "tokens=*" %%i in ('where python 2^>nul') do (
    set "PYTHON_EXE=%%i"
    goto :found_python
)

:: 3. Check py launcher
for /f "tokens=*" %%i in ('where py 2^>nul') do (
    set "PYTHON_EXE=%%i"
    goto :found_python
)

:found_python
if "%PYTHON_EXE%"=="" (
    echo [ERROR] Python not found on your system!
    echo Please ensure Python 3.10+ is installed.
    pause
    exit /b 1
)

echo [OK] Python found: "%PYTHON_EXE%"
echo [OK] Launching AlgoQuant India Web Server...

:: Launch browser in background after 2 seconds to allow Flask to bind to available port
start "" cmd /c "timeout /t 2 /nobreak >nul & powershell -Command \"try { $info = Get-Content 'cache\server_info.json' | ConvertFrom-Json; Start-Process $info.url } catch { Start-Process 'http://localhost:5000' }\""

:: Start the Python server
"%PYTHON_EXE%" server.py

if errorlevel 1 (
    echo.
    echo [ERROR] Server terminated with an error code.
)
pause

