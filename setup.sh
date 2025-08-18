#!/bin/bash

# AI 工作站安裝腳本
echo "正在設置 AI 工作站環境..."

# 檢查 Python 3 是否安裝
if ! command -v python3 &> /dev/null; then
    echo "錯誤: 未找到 Python 3，請先安裝 Python 3"
    exit 1
fi

# 創建虛擬環境（如果不存在）
if [ ! -d "venv" ]; then
    echo "創建虛擬環境..."
    python3 -m venv venv
fi

# 啟用虛擬環境
echo "啟用虛擬環境..."
source venv/bin/activate

# 升級 pip
echo "升級 pip..."
pip install --upgrade pip

# 安裝依賴套件
echo "安裝依賴套件..."
pip install -r requirements.txt

echo "設置完成！"
echo "使用 ./start.sh 來啟動程式"