# CareerForge Setup — Windows
# Run with: powershell -ExecutionPolicy Bypass -File scripts\setup_windows.ps1
#
# What this script installs:
#   1. Git          — for cloning repositories
#   2. Python 3.11+ — all scripting (docx generation, LinkedIn scanning, scoring)
#   3. Python packages — python-docx, httpx, pydantic, pyyaml, beautifulsoup4, markdown, weasyprint
#   4. Claude Desktop — checked but not auto-installed (manual step)
#
# Requires: Windows 10 21H2+ or Windows 11 (winget is built-in)
# If winget is unavailable, manual download links are shown for each step.

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "============================================================"
Write-Host "  CareerForge Setup"
Write-Host "============================================================"
Write-Host "  This script will check and install:"
Write-Host "    [1] Git"
Write-Host "    [2] Python 3.11+"
Write-Host "    [3] Python packages (python-docx, httpx, pydantic, ...)"
Write-Host "    [4] Claude Desktop (check only)"
Write-Host "------------------------------------------------------------"
Write-Host ""

$allOk = $true

# ── Helper ──────────────────────────────────────────────────────────────────

function Print-Status($step, $label, $status, $detail = "") {
    $pad = 32 - $label.Length
    if ($pad -lt 1) { $pad = 1 }
    $dots = "." * $pad
    if ($status -eq "OK")        { Write-Host "  [$step] $label $dots [OK] $detail" -ForegroundColor Green }
    elseif ($status -eq "INST")  { Write-Host "  [$step] $label $dots [INSTALLED] $detail" -ForegroundColor Cyan }
    elseif ($status -eq "SKIP")  { Write-Host "  [$step] $label $dots [SKIPPED] $detail" -ForegroundColor Yellow }
    elseif ($status -eq "WARN")  { Write-Host "  [$step] $label $dots [NOT FOUND] $detail" -ForegroundColor Yellow }
    elseif ($status -eq "FAIL")  { Write-Host "  [$step] $label $dots [FAILED] $detail" -ForegroundColor Red }
}

function Check-Winget {
    try {
        $null = Get-Command winget -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

# ── Step 1: Git ─────────────────────────────────────────────────────────────

$gitCmd = Get-Command git -ErrorAction SilentlyContinue
if ($gitCmd) {
    $gitVer = (git --version 2>$null) -replace "git version ", ""
    Print-Status "1/4" "Git" "OK" $gitVer
} else {
    if (Check-Winget) {
        Write-Host "  [1/4] Git ................................ [INSTALLING...]" -ForegroundColor Yellow
        winget install --id Git.Git -e --accept-source-agreements --accept-package-agreements 2>&1 | Out-Null
        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        $gitCmd = Get-Command git -ErrorAction SilentlyContinue
        if ($gitCmd) {
            $gitVer = (git --version 2>$null) -replace "git version ", ""
            Print-Status "1/4" "Git" "INST" $gitVer
        } else {
            Print-Status "1/4" "Git" "FAIL"
            Write-Host "       Manual install: https://git-scm.com/downloads" -ForegroundColor Red
            Write-Host "       After installing, re-run this script." -ForegroundColor Red
            $allOk = $false
        }
    } else {
        Print-Status "1/4" "Git" "WARN"
        Write-Host "       winget not available. Manual install: https://git-scm.com/downloads" -ForegroundColor Yellow
        Write-Host "       After installing, re-run this script." -ForegroundColor Yellow
        $allOk = $false
    }
}

# ── Step 2: Python 3.11+ ────────────────────────────────────────────────────

$pythonCmd = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "Python (\d+)\.(\d+)") {
            $maj = [int]$matches[1]; $min = [int]$matches[2]
            if ($maj -gt 3 -or ($maj -eq 3 -and $min -ge 11)) {
                $pythonCmd = $cmd
                $pythonVer = "$maj.$min"
                break
            }
        }
    } catch {}
}

if ($pythonCmd) {
    Print-Status "2/4" "Python 3.11+" "OK" $pythonVer
} else {
    if (Check-Winget) {
        Write-Host "  [2/4] Python 3.11+ ...................... [INSTALLING...]" -ForegroundColor Yellow
        winget install --id Python.Python.3.11 -e --accept-source-agreements --accept-package-agreements 2>&1 | Out-Null
        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        foreach ($cmd in @("python", "python3", "py")) {
            try {
                $ver = & $cmd --version 2>&1
                if ($ver -match "Python (\d+)\.(\d+)") {
                    $maj = [int]$matches[1]; $min = [int]$matches[2]
                    if ($maj -gt 3 -or ($maj -eq 3 -and $min -ge 11)) {
                        $pythonCmd = $cmd
                        $pythonVer = "$maj.$min"
                        break
                    }
                }
            } catch {}
        }
        if ($pythonCmd) {
            Print-Status "2/4" "Python 3.11+" "INST" $pythonVer
        } else {
            Print-Status "2/4" "Python 3.11+" "FAIL"
            Write-Host "       Manual install: https://www.python.org/downloads" -ForegroundColor Red
            Write-Host "       Choose Python 3.11 or newer. Check 'Add to PATH' during install." -ForegroundColor Red
            Write-Host "       After installing, re-run this script." -ForegroundColor Red
            $allOk = $false
        }
    } else {
        Print-Status "2/4" "Python 3.11+" "WARN"
        Write-Host "       winget not available. Manual install: https://www.python.org/downloads" -ForegroundColor Yellow
        Write-Host "       Choose Python 3.11+. Check 'Add to PATH' during install." -ForegroundColor Yellow
        Write-Host "       After installing, re-run this script." -ForegroundColor Yellow
        $allOk = $false
    }
}

# ── Step 3: Python packages ──────────────────────────────────────────────────

if ($pythonCmd) {
    Write-Host "  [3/4] Python packages ................... [INSTALLING...]" -ForegroundColor Yellow
    $packages = "python-docx httpx pydantic pyyaml beautifulsoup4 markdown weasyprint"
    $result = & $pythonCmd -m pip install --quiet $packages.Split() 2>&1
    if ($LASTEXITCODE -eq 0) {
        Print-Status "3/4" "Python packages" "OK" "python-docx, httpx, pydantic, pyyaml, bs4, markdown, weasyprint"
    } else {
        Print-Status "3/4" "Python packages" "FAIL"
        Write-Host "       Error output:" -ForegroundColor Red
        Write-Host "       $result" -ForegroundColor Red
        Write-Host "       Try manually: $pythonCmd -m pip install python-docx httpx pydantic pyyaml beautifulsoup4 markdown weasyprint" -ForegroundColor Red
        $allOk = $false
    }
} else {
    Print-Status "3/4" "Python packages" "SKIP" "(Python not available)"
    $allOk = $false
}

# ── Step 4: Claude Desktop ───────────────────────────────────────────────────

$claudeCmd = Get-Command claude -ErrorAction SilentlyContinue
if ($claudeCmd) {
    $claudeVer = (claude --version 2>$null) | Select-Object -First 1
    Print-Status "4/4" "Claude Desktop" "OK" $claudeVer
} else {
    Print-Status "4/4" "Claude Desktop" "WARN"
    Write-Host "       Download and install from: https://claude.com/download" -ForegroundColor Yellow
    Write-Host "       After installing, re-run this script or proceed to launch." -ForegroundColor Yellow
}

# ── Summary ──────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "============================================================"
if ($allOk) {
    Write-Host "  Setup complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "  To start CareerForge:"
    Write-Host "    Double-click: scripts\launch_windows.bat"
    Write-Host "    Or run:       .\scripts\launch_windows.bat"
} else {
    Write-Host "  Setup finished with issues (see [FAILED] steps above)." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Fix the failed steps manually using the links shown above,"
    Write-Host "  then re-run this script to confirm everything is ready."
}
Write-Host "============================================================"
Write-Host ""
Read-Host "Press Enter to close"
