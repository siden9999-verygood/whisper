@echo off
REM 語音轉錄工具 - 啟動腳本 (Windows)

cd /d "%~dp0"

REM 檢查虛擬環境
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM 啟動主程式
python app_main.py

pause
