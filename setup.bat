@echo off
echo === CareerForge Setup ===
echo.

where node >nul 2>&1
if %errorlevel% neq 0 (
    echo Node.js not found. Install from https://nodejs.org ^(v18+^) then re-run.
    pause
    exit /b 1
)
for /f "tokens=1 delims=." %%v in ('node --version') do set NODE_MAJ=%%v
set NODE_MAJ=%NODE_MAJ:v=%
if %NODE_MAJ% lss 18 (
    echo Node.js v18+ required. Update at https://nodejs.org
    pause
    exit /b 1
)
echo OK  Node.js

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found. Install Python 3.11+ from https://www.python.org then re-run.
    pause
    exit /b 1
)
echo OK  Python

echo.
echo Installing Node.js dependencies...
call npm install

echo Installing Python dependencies...
python -m pip install -r requirements.txt --quiet

where claude >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo Claude Code not found. Install from: https://claude.ai/code
    echo Then double-click launch.bat in this folder.
) else (
    echo OK  Claude Code
)

echo.
echo === Setup complete ===
echo.
echo To start CareerForge: double-click launch.bat
pause
