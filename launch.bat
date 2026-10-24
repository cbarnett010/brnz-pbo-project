@echo off
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found. Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add python.exe to PATH" during installation.
    pause
    exit /b 1
)
python "%~dp0pbo_tool.py"
