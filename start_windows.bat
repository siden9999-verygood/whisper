@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM AI 智慧工作站 - Windows 一鍵啟動腳本（可自動建立虛擬環境並安裝依賴）
REM 使用方式：雙擊本檔案即可啟動程式；首次執行會自動安裝依賴（需網路）

set "APPDIR=%~dp0"
pushd "%APPDIR%" >nul 2>nul

REM 檢查 whisper_resources 必要檔
if not exist "%APPDIR%whisper_resources\ffmpeg.exe" (
  echo [警告] 缺少 whisper_resources\ffmpeg.exe（Windows 版）。
)
if not exist "%APPDIR%whisper_resources\main.exe" (
  echo [警告] 缺少 whisper_resources\main.exe（whisper.cpp 的 Windows 版）。
)

REM 檢查是否已有 venv
set "VENV_DIR=%APPDIR%venv"
set "PYTHONW=%VENV_DIR%\Scripts\pythonw.exe"
set "PYTHON=%VENV_DIR%\Scripts\python.exe"

if not exist "%PYTHON%" (
  echo [資訊] 建立 Python 虛擬環境...
  py -3 -m venv "%VENV_DIR%" 2>nul || python -m venv "%VENV_DIR%"
)

REM 升級 pip 並安裝依賴（可用 NO_PIP=1 跳過）
if /I not "%NO_PIP%"=="1" (
  echo [資訊] 檢查並安裝依賴套件（需網路）...
  "%PYTHON%" -m pip install --upgrade pip
  "%PYTHON%" -m pip install -r "%APPDIR%requirements.txt"
)

REM 建立桌面捷徑（若不存在）
for /f "usebackq tokens=*" %%D in (`powershell -NoProfile -Command "[Environment]::GetFolderPath('Desktop')"`) do set "DESKTOP=%%D"
if not exist "%DESKTOP%\AI 智慧工作站.lnk" (
  powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$p=$env:APPDIR; $s=New-Object -ComObject WScript.Shell; $lnk=$s.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'AI 智慧工作站.lnk')); $lnk.TargetPath = (Join-Path $p 'start_windows.bat'); $lnk.WorkingDirectory = $p; if (Test-Path (Join-Path $p 'icon.ico')) { $lnk.IconLocation = (Join-Path $p 'icon.ico') }; $lnk.Save()" >nul 2>nul
)

REM 啟動應用（優先使用 pythonw 隱藏主控台視窗）
if exist "%PYTHONW%" (
  start "AI Workstation" "%PYTHONW%" "%APPDIR%gui_main.py"
) else (
  start "AI Workstation" "%PYTHON%" "%APPDIR%gui_main.py"
)

popd >nul 2>nul
endlocal
exit /b 0

