@echo off
cd /d "%~dp0"
claude
if %errorlevel% neq 0 (
    echo.
    echo Claude Code not found. Install from https://claude.ai/code
    pause
)
