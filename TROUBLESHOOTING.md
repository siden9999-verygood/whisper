# 故障排除指南

## 常見問題

### 1. 程式無法啟動

#### 問題：`No module named 'psutil'`
**解決方案：**
```bash
# 確保使用虛擬環境
source venv/bin/activate
pip install -r requirements.txt
```

#### 問題：`jieba 初始化失敗`
**解決方案：**
這個問題已經在最新版本中修復。如果仍然遇到，請：
```bash
# 重新安裝 jieba
pip uninstall jieba
pip install jieba>=0.42.1
```

#### 問題：macOS 上的 tkinter 錯誤
**解決方案：**
```bash
# 安裝 tkinter（如果需要）
brew install python-tk
```

### 2. 依賴項問題

#### 問題：缺少 Whisper 相關檔案
**說明：** 這些是可選的語音轉錄功能，不影響基本使用。

**如果需要語音轉錄功能：**
```bash
# 安裝 Whisper
pip install openai-whisper

# 安裝 FFmpeg
brew install ffmpeg  # macOS
# 或
sudo apt install ffmpeg  # Ubuntu
```

#### 問題：Google AI API 金鑰未配置
**說明：** 這是可選的 AI 分析功能。

**配置方法：**
1. 在程式中進入設定頁面
2. 輸入你的 Google AI API 金鑰
3. 或設定環境變數：`export GOOGLE_AI_API_KEY=your_key_here`

### 3. 效能問題

#### 問題：程式運行緩慢
**解決方案：**
1. 檢查系統資源使用情況
2. 減少同時處理的檔案數量
3. 關閉不必要的背景程式

#### 問題：記憶體使用過高
**解決方案：**
1. 重新啟動程式
2. 清理暫存檔案
3. 減少索引的檔案數量

### 4. 檔案處理問題

#### 問題：無法讀取某些媒體檔案
**解決方案：**
1. 檢查檔案格式是否支援
2. 確認檔案沒有損壞
3. 檢查檔案權限

### 5. 搜尋功能問題

#### 問題：搜尋結果不準確
**解決方案：**
1. 重建搜尋索引
2. 檢查搜尋關鍵字拼寫
3. 使用更具體的搜尋條件

## 診斷工具

### 執行診斷
```bash
# 在程式中使用診斷功能
# 或手動執行
python3 diagnostics_manager.py
```

### 檢查日誌
日誌檔案位置：
- macOS: `~/Library/Application Support/AIWorkstation/logs/`
- Windows: `%APPDATA%\AIWorkstation\logs\`
- Linux: `~/.local/share/AIWorkstation/logs/`

## 聯絡支援

如果問題仍然存在，請：
1. 收集診斷報告
2. 查看日誌檔案
3. 提供詳細的錯誤訊息
4. 說明重現步驟

## 更新程式

```bash
# 拉取最新版本
git pull origin main

# 更新依賴
source venv/bin/activate
pip install -r requirements.txt --upgrade
```