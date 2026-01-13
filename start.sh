#!/bin/bash
# 語音轉錄工具 - 啟動腳本

cd "$(dirname "$0")"

# 直接使用 venv 的 Python
./venv/bin/python3 app_main.py