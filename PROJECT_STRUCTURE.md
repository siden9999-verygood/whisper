# AI 智慧工作站 - 程式檔案架構

## 專案概述
這是一個跨平台媒體處理工作站，整合語音轉錄、AI 分析、智能搜尋等功能。

## 核心程式檔案

### 主程式入口
- `gui_main.py` - 主程式入口，GUI 介面

### 核心管理模組
- `transcription_manager.py` - 語音轉錄管理（支援多種音訊格式）
- `enhanced_search_manager.py` - 智能搜尋管理（自然語言搜尋、複雜查詢）
- `archive_manager.py` - 媒體歸檔管理（自動分類、智能命名）
- `download_manager.py` - 下載管理（批次下載、斷點續傳）
- `monitoring_manager.py` - 資料夾監控管理（即時監控、自動處理）
- `update_manager.py` - 更新管理（自動更新、版本回滾）

### 系統服務模組
- `config_service.py` - 配置管理服務
- `logging_service.py` - 日誌服務
- `diagnostics_manager.py` - 診斷系統（完整日誌、一鍵診斷）
- `performance_monitor.py` - 效能監控（系統資源監控、最佳化建議）
- `error_handler.py` - 錯誤處理

### 搜尋和查詢模組
- `natural_language_search.py` - 自然語言搜尋
- `query_parser.py` - 查詢解析器

### 跨平台支援
- `platform_adapter.py` - 跨平台適配器（Windows/macOS/Linux）

## 安裝和配置檔案

### 安裝腳本
- `install.py` - Python 安裝腳本
- `install.sh` - Shell 安裝腳本
- `setup.sh` - 環境設定腳本
- `start.sh` - 程式啟動腳本

### 配置檔案
- `requirements.txt` - Python 依賴套件
- `version.json` - 版本資訊

## 測試檔案

### 正式測試
- `tests/` - 正式測試檔案目錄
  - `test_config_service.py` - 配置服務測試
  - `test_logging_service.py` - 日誌服務測試
  - `test_platform_adapter.py` - 跨平台適配器測試
  - `test_integration.py` - 整合測試
  - `test_cross_platform.py` - 跨平台測試
  - `test_performance.py` - 效能測試
  - `run_tests.py` - 測試執行器

### 測試執行器
- `run_all_tests.py` - 全部測試執行器

## 文件和資源

### 文件目錄 (`docs/`)
- `API_REFERENCE.md` - API 參考文件
- `USER_MANUAL.md` - 使用者手冊
- `DEVELOPER_GUIDE.md` - 開發者指南
- `FAQ.md` - 常見問題
- `HELP_SYSTEM.md` - 幫助系統
- `COMMUNITY_SUPPORT.md` - 社群支援
- `VIDEO_TUTORIALS.md` - 影片教學

### 專案文件
- `README.md` - 專案說明文件
- `CHANGELOG.md` - 版本更新記錄
- `TROUBLESHOOTING.md` - 故障排除指南

### 資源目錄
- `samples/` - 範例檔案目錄
  - `jfk.mp3` / `jfk.wav` - 測試音訊檔案
- `whisper_resources/` - Whisper 相關資源
- `build_scripts/` - 打包和發布腳本

## 開發和配置

### Kiro 配置 (`.kiro/`)
- `specs/` - 功能規格文件
- `steering/` - 開發指導文件

### 環境
- `venv/` - Python 虛擬環境
- `__pycache__/` - Python 快取檔案

## 檔案功能說明

### 主要功能模組
1. **語音轉錄** (`transcription_manager.py`)
   - 支援 MP3, WAV, M4A, FLAC, OGG 格式
   - 輸出 TXT, SRT, VTT, JSON 格式
   - 批次處理功能

2. **智能搜尋** (`enhanced_search_manager.py`, `natural_language_search.py`)
   - 自然語言搜尋
   - 複雜查詢解析
   - 多維度過濾

3. **媒體歸檔** (`archive_manager.py`)
   - 自動分類組織
   - 智能命名
   - 重複檔案檢測

4. **系統監控** (`monitoring_manager.py`, `performance_monitor.py`)
   - 資料夾即時監控
   - 系統效能監控
   - 資源使用最佳化

### 支援功能
- **跨平台相容** (`platform_adapter.py`)
- **配置管理** (`config_service.py`)
- **日誌系統** (`logging_service.py`)
- **錯誤處理** (`error_handler.py`)
- **診斷工具** (`diagnostics_manager.py`)

## 使用方式

### 快速啟動
```bash
./setup.sh    # 初始設定
./start.sh    # 啟動程式
```

### 開發模式
```bash
python gui_main.py --debug
```

### 執行測試
```bash
python run_all_tests.py
```

這個架構設計支援模組化開發，每個功能都有獨立的管理器，便於維護和擴展。