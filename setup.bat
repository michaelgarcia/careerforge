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
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
for /f "tokens=1,2 delims=." %%a in ("%PY_VER%") do (set PY_MAJ=%%a & set PY_MIN=%%b)
if %PY_MAJ% lss 3 goto py_old
if %PY_MAJ% equ 3 if %PY_MIN% lss 11 goto py_old
echo OK  Python %PY_VER%
goto py_ok
:py_old
echo Python 3.11+ required (found %PY_VER%). Update at https://www.python.org
pause
exit /b 1
:py_ok

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
