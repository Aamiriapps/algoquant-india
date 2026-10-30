@echo off
setlocal enabledelayedexpansion
title AlgoQuant India - CLI Scanner

cd /d "%~dp0"

set "PYTHON_EXE="
if exist "C:\Users\Mohammed Ali\AppData\Local\Programs\Python\Python312\python.exe" (
    set "PYTHON_EXE=C:\Users\Mohammed Ali\AppData\Local\Programs\Python\Python312\python.exe"
    goto :found_python
)

for /f "tokens=*" %%i in ('where python 2^>nul') do (
    set "PYTHON_EXE=%%i"
    goto :found_python
)

for /f "tokens=*" %%i in ('where py 2^>nul') do (
    set "PYTHON_EXE=%%i"
    goto :found_python
)

:found_python
if "%PYTHON_EXE%"=="" (
    echo [ERROR] Python not found on your system!
    pause
    exit /b 1
)

"%PYTHON_EXE%" algo_scanner_cli.py %*
pause

