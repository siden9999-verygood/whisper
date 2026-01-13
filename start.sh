#!/bin/bash
# 語音轉錄工具 - 啟動腳本 (macOS/Linux)

cd "$(dirname "$0")"

# 檢查虛擬環境
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 啟動主程式
python app_main.py