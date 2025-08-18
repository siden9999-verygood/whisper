#!/bin/bash

echo "=== Cross-Platform Media Search System 安裝腳本 ==="

# 檢查Python版本
python3 --version
if [ $? -ne 0 ]; then
    echo "錯誤: 需要Python 3.8或更高版本"
    exit 1
fi

# 安裝Python套件
echo "正在安裝Python套件..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ 安裝完成！"
    echo ""
    echo "使用方法："
    echo "  python3 run_search.py    # 啟動搜尋系統"
    echo "  python3 test_complete_system.py    # 執行系統測試"
    echo ""
else
    echo "❌ 安裝失敗，請檢查錯誤訊息"
    exit 1
fi
