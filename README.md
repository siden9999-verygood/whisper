# AI 智慧工作站 v4.0

> 跨平台媒體處理工作站，整合語音轉錄、AI 分析、智能搜尋等功能

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](https://github.com/kiro-ai/workstation)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-4.0.0-orange.svg)](CHANGELOG.md)

## 🌟 功能特色

### 核心功能
- **🎤 語音轉錄**: 支援多種音訊格式，批次處理，AI 自動校正
- **🤖 AI 分析**: 智能內容分析，自動標籤生成，分類建議
- **🔍 智能搜尋**: 自然語言搜尋，複雜查詢，搜尋範本
- **🗂️ 媒體歸檔**: 自動分類組織，智能命名，重複檔案檢測
- **📥 下載管理**: 批次下載，斷點續傳，佇列管理

### 增強功能
- **📁 資料夾監控**: 即時監控，自動處理新檔案
- **🔎 進階搜尋**: 複雜查詢解析，多維度過濾
- **📊 效能監控**: 系統資源監控，效能最佳化建議
- **🛠️ 診斷系統**: 完整日誌，一鍵診斷，問題報告

## 🚀 快速開始

### 系統需求

| 平台 | 最低需求 | 建議配置 |
|------|----------|----------|
| **Windows** | Windows 10, Python 3.8+, 4GB RAM | Windows 11, Python 3.10+, 8GB RAM |
| **macOS** | macOS 10.14, Python 3.8+, 4GB RAM | macOS 12+, Python 3.10+, 8GB RAM |
| **Linux** | Ubuntu 18.04, Python 3.8+, 4GB RAM | Ubuntu 22.04, Python 3.10+, 8GB RAM |

### 安裝方式

#### 方式一：快速安裝（推薦）
```bash
# 1. 執行安裝腳本
./setup.sh

# 2. 啟動程式
./start.sh
```

#### 方式二：手動安裝
```bash
# 1. 創建虛擬環境
python3 -m venv venv

# 2. 啟用虛擬環境
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate     # Windows

# 3. 安裝依賴
pip install -r requirements.txt

# 4. 啟動程式
python3 gui_main.py

# 3. 執行程式
python gui_main.py
```

#### 方式三：可攜式版本
1. 下載最新的可攜式版本
2. 解壓到任意目錄
3. 執行 `start.bat` (Windows) 或 `start.sh` (macOS/Linux)

### 首次設定

1. **啟動程式**: 執行安裝完成後的啟動腳本
2. **配置 API**: 在設定中輸入 Google Gemini API 金鑰
3. **選擇路徑**: 設定工作目錄和輸出路徑
4. **測試功能**: 嘗試轉錄一個小音訊檔案

## 📖 使用指南

### 語音轉錄

1. **單檔案轉錄**
   - 點擊「選擇音訊檔案」
   - 選擇輸出格式（TXT、SRT、VTT）
   - 點擊「開始轉錄」

2. **批次轉錄**
   - 點擊「批次轉錄」標籤
   - 選擇包含音訊檔案的資料夾
   - 設定輸出選項
   - 開始批次處理

3. **支援格式**
   - 輸入：MP3, WAV, M4A, FLAC, OGG
   - 輸出：TXT, SRT, VTT, JSON

### AI 分析

1. **內容分析**
   - 選擇已轉錄的文字檔案
   - 點擊「AI 分析」
   - 查看生成的標籤和摘要

2. **批次分析**
   - 在批次處理中啟用 AI 分析
   - 系統會自動分析所有轉錄結果

### 智能搜尋

1. **基本搜尋**
   ```
   搜尋關鍵字：會議記錄
   ```

2. **進階搜尋**
   ```
   標題包含"會議" AND 日期在"2024-01" AND 標籤包含"重要"
   ```

3. **自然語言搜尋**
   ```
   找出上個月關於專案討論的會議記錄
   ```

### 媒體歸檔

1. **自動歸檔**
   - 啟用資料夾監控
   - 新檔案會自動分類到對應資料夾

2. **手動歸檔**
   - 選擇要歸檔的檔案
   - 點擊「開始歸檔」
   - 選擇歸檔規則

## 🔧 進階功能

### 資料夾監控

```python
# 設定監控規則
monitor_rules = {
    "audio_files": {
        "extensions": [".mp3", ".wav", ".m4a"],
        "action": "transcribe",
        "output_format": "srt"
    },
    "video_files": {
        "extensions": [".mp4", ".avi", ".mkv"],
        "action": "extract_audio_and_transcribe"
    }
}
```

### 自訂搜尋範本

```json
{
  "name": "會議記錄搜尋",
  "query": "type:transcript AND tags:meeting",
  "filters": {
    "date_range": "last_month",
    "file_type": "srt"
  }
}
```

### API 使用

```python
from enhanced_search_manager import enhanced_search_manager

# 搜尋檔案
results = enhanced_search_manager.search("會議記錄", max_results=10)

# 進階搜尋
advanced_results = enhanced_search_manager.advanced_search({
    "query": "專案討論",
    "date_range": {"start": "2024-01-01", "end": "2024-01-31"},
    "tags": ["重要", "會議"]
})
```

## 🛠️ 開發指南

### 專案結構

```
workstation/
├── gui_main.py              # 主程式入口
├── platform_adapter.py     # 跨平台適配器
├── config_service.py       # 配置管理
├── logging_service.py      # 日誌服務
├── transcription_manager.py # 轉錄管理
├── enhanced_search_manager.py # 搜尋管理
├── archive_manager.py      # 歸檔管理
├── monitoring_manager.py   # 監控管理
├── diagnostics_manager.py  # 診斷管理
├── update_manager.py       # 更新管理
├── build_scripts/          # 打包腳本
├── tests/                  # 測試檔案
└── docs/                   # 文件
```

### 開發環境設定

```bash
# 1. 克隆專案
git clone https://github.com/kiro-ai/workstation.git
cd workstation

# 2. 建立虛擬環境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows

# 3. 安裝開發依賴
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. 執行測試
python run_all_tests.py

# 5. 啟動開發模式
python gui_main.py --debug
```

### 貢獻指南

1. **Fork 專案**
2. **建立功能分支**: `git checkout -b feature/amazing-feature`
3. **提交變更**: `git commit -m 'Add amazing feature'`
4. **推送分支**: `git push origin feature/amazing-feature`
5. **建立 Pull Request**

### 程式碼規範

- 使用 Python 3.8+ 語法
- 遵循 PEP 8 程式碼風格
- 編寫完整的文件字串
- 包含單元測試
- 支援跨平台相容性

## 📊 效能最佳化

### 系統調整

1. **記憶體使用**
   - 大檔案處理時增加虛擬記憶體
   - 關閉不必要的背景程式

2. **磁碟空間**
   - 定期清理臨時檔案
   - 使用 SSD 提升 I/O 效能

3. **網路設定**
   - 使用穩定的網路連線
   - 考慮使用本地 AI 模型

### 效能監控

程式內建效能監控功能：
- CPU 使用率監控
- 記憶體使用量追蹤
- 磁碟 I/O 統計
- 網路流量監控

## 🐛 故障排除

### 常見問題

#### 1. 轉錄失敗
**問題**: 音訊檔案無法轉錄
**解決方案**:
- 檢查檔案格式是否支援
- 確認檔案沒有損壞
- 檢查磁碟空間是否足夠

#### 2. AI 分析錯誤
**問題**: AI 分析功能無法使用
**解決方案**:
- 檢查 API 金鑰是否正確
- 確認網路連線正常
- 查看 API 配額是否用盡

#### 3. 搜尋結果不準確
**問題**: 搜尋無法找到預期結果
**解決方案**:
- 重建搜尋索引
- 檢查搜尋語法
- 更新媒體資料庫

### 診斷工具

程式內建診斷功能：
```bash
# 執行完整診斷
python -c "from diagnostics_manager import diagnostics_manager; diagnostics_manager.run_full_diagnostics()"

# 匯出診斷報告
python -c "from diagnostics_manager import diagnostics_manager; diagnostics_manager.export_diagnostic_package()"
```

### 日誌分析

日誌檔案位置：
- **Windows**: `%APPDATA%\AIWorkstation\logs\`
- **macOS**: `~/Library/Application Support/AIWorkstation/logs/`
- **Linux**: `~/.config/aiworkstation/logs/`

## 🔄 更新和維護

### 自動更新

程式支援自動更新功能：
1. 啟動時自動檢查更新
2. 背景定期檢查新版本
3. 一鍵下載和安裝更新

### 手動更新

```bash
# 檢查更新
python update_manager.py check

# 下載更新
python update_manager.py download

# 安裝更新
python update_manager.py install
```

### 版本回滾

如果更新後出現問題：
```bash
# 查看可用備份
python update_manager.py list-backups

# 回滾到指定版本
python update_manager.py rollback backup_name
```

## 📚 API 參考

### 核心 API

#### TranscriptionManager
```python
from transcription_manager import transcription_manager

# 轉錄單個檔案
result = transcription_manager.transcribe_file(
    audio_file="audio.mp3",
    output_format="srt",
    language="zh"
)

# 批次轉錄
results = transcription_manager.batch_transcribe(
    input_dir="audio_files/",
    output_dir="transcripts/",
    formats=["txt", "srt"]
)
```

#### EnhancedSearchManager
```python
from enhanced_search_manager import enhanced_search_manager

# 基本搜尋
results = enhanced_search_manager.search("關鍵字")

# 進階搜尋
results = enhanced_search_manager.advanced_search({
    "query": "會議記錄",
    "filters": {
        "date_range": {"start": "2024-01-01", "end": "2024-01-31"},
        "file_type": "srt",
        "tags": ["重要"]
    }
})
```

#### ArchiveManager
```python
from archive_manager import archive_manager

# 歸檔檔案
result = archive_manager.archive_files(
    files=["file1.mp3", "file2.wav"],
    destination="archive/",
    rules="auto_classify"
)
```

### 事件系統

```python
from monitoring_manager import monitoring_manager

# 註冊事件監聽器
def on_file_added(file_path):
    print(f"新檔案: {file_path}")

monitoring_manager.add_event_listener("file_added", on_file_added)
```

## 🤝 社群和支援

### 獲得幫助

- **文件**: [完整文件](docs/)
- **FAQ**: [常見問題](docs/FAQ.md)
- **教學影片**: [YouTube 頻道](https://youtube.com/channel/example)
- **社群論壇**: [討論區](https://github.com/kiro-ai/workstation/discussions)

### 回報問題

1. **檢查已知問題**: 查看 [Issues](https://github.com/kiro-ai/workstation/issues)
2. **收集診斷資訊**: 使用內建診斷工具
3. **建立問題報告**: 提供詳細的重現步驟
4. **追蹤進度**: 關注問題狀態更新

### 功能請求

歡迎提出新功能建議：
1. 在 [Discussions](https://github.com/kiro-ai/workstation/discussions) 中討論
2. 建立 [Feature Request](https://github.com/kiro-ai/workstation/issues/new?template=feature_request.md)
3. 參與投票和討論

## 📄 授權條款

本專案採用 MIT 授權條款。詳見 [LICENSE](LICENSE) 檔案。

## 🙏 致謝

感謝以下開源專案和貢獻者：
- [Google Generative AI](https://github.com/google/generative-ai-python)
- [OpenCC](https://github.com/BYVoid/OpenCC)
- [Whisper.cpp](https://github.com/ggerganov/whisper.cpp)
- 所有貢獻者和使用者

## 📈 專案統計

![GitHub stars](https://img.shields.io/github/stars/kiro-ai/workstation?style=social)
![GitHub forks](https://img.shields.io/github/forks/kiro-ai/workstation?style=social)
![GitHub issues](https://img.shields.io/github/issues/kiro-ai/workstation)
![GitHub pull requests](https://img.shields.io/github/issues-pr/kiro-ai/workstation)

---

<div align="center">
  <p>如果這個專案對您有幫助，請給我們一個 ⭐️</p>
  <p>Made with ❤️ by Kiro AI Assistant</p>
</div>