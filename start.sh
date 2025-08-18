#!/bin/bash

# AI 工作站啟動腳本
echo "正在啟動 AI 工作站..."

# 檢查虛擬環境是否存在
if [ ! -d "venv" ]; then
    echo "錯誤: 找不到虛擬環境，請先運行 ./setup.sh"
    exit 1
fi

# 啟用虛擬環境並運行程式
source venv/bin/activate

# 檢查功能狀態
echo "檢查功能狀態..."
python3 test_simple_conversion.py

echo ""
echo "啟動 GUI..."
python3 gui_main.py

echo "AI 工作站已關閉"