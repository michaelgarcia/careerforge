@echo off
cd /d "%~dp0\.."
claude
if %errorlevel% neq 0 (
    echo.
    echo Claude Desktop not found. Install from https://claude.com/download
    pause
)
