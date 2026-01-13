# 免費語音轉錄工具

> 使用 OpenAI Whisper large-v2 模型進行高精度語音轉文字，完全免費、開源

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS-lightgrey.svg)](https://github.com/siden9999-verygood/whisper)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 功能特色

- **高精度轉錄** - 使用 Whisper large-v2 模型，業界領先的語音辨識精準度
- **多語言支援** - 中文、英文、日文、韓文等 99 種語言
- **多格式輸出** - SRT 字幕、TXT 純文字、VTT 等格式
- **簡繁轉換** - 自動將簡體中文轉換為繁體中文
- **跨平台** - 支援 Windows 和 macOS
- **完全免費** - 開源軟體，永久免費

## 安裝方式

### 方式一：下載安裝包（推薦）

1. 前往 [Releases](https://github.com/siden9999-verygood/whisper/releases) 頁面
2. 下載對應平台的安裝包：
   - Windows：`VoiceTranscriber-Setup.exe`
   - macOS：`VoiceTranscriber.dmg`
3. 雙擊安裝，首次執行時會自動下載 AI 模型（約 3GB）

### 方式二：從原始碼執行

```bash
# 1. 克隆專案
git clone https://github.com/siden9999-verygood/whisper.git
cd whisper

# 2. 建立虛擬環境
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate     # Windows

# 3. 安裝依賴
pip install -r requirements.txt

# 4. 執行程式
python app_main.py
```

## 使用方法

1. 啟動程式
2. 點擊選擇音訊或影片檔案（支援 MP3, WAV, M4A, MP4, MOV 等）
3. 選擇語言和輸出格式
4. 點擊「開始轉錄」
5. 等待處理完成，輸出檔案會儲存在原檔案同目錄

### 支援格式

**音訊**：MP3, WAV, M4A, FLAC, OGG, AAC  
**影片**：MP4, MOV, AVI, MKV, WMV, FLV, WebM

## 系統需求

| 平台 | 最低需求 | 建議配置 |
|------|----------|----------|
| **Windows** | Windows 10, 4GB RAM | Windows 11, 8GB RAM |
| **macOS** | macOS 10.14, 4GB RAM | macOS 12+, 8GB RAM |

- Python 3.8 或以上版本（從原始碼執行時需要）
- 約 4GB 磁碟空間（含 AI 模型）

## 硬體加速說明

本工具使用 [whisper.cpp](https://github.com/ggerganov/whisper.cpp) 作為轉錄引擎，各平台硬體使用方式如下：

| 平台 | 硬體加速 | 說明 |
|------|----------|------|
| **macOS (M1/M2/M3/M4)** | Apple Metal GPU | 自動啟用，速度最快 |
| **macOS (Intel)** | CPU | 可正常使用，速度較慢 |
| **Windows** | CPU | 預設使用 CPU 運算 |
| **Windows + NVIDIA** | 需手動設定 | 見下方說明 |

### Windows 啟用 NVIDIA GPU 加速

目前提供的 Windows 版本使用 CPU 運算。如需使用 NVIDIA GPU 加速，請依照以下步驟：

1. 安裝 [NVIDIA CUDA Toolkit](https://developer.nvidia.com/cuda-downloads)
2. 從 [whisper.cpp Releases](https://github.com/ggerganov/whisper.cpp/releases) 下載 CUDA 版本的執行檔
3. 將下載的 `main.exe` 替換 `whisper_resources/main.exe`
4. 重新執行程式

> 注意：CPU 版本對大多數使用情境已足夠。5 分鐘的音檔約需 1-3 分鐘處理。

## 致謝 / Credits

本專案使用以下開源專案：

- [OpenAI Whisper](https://github.com/openai/whisper) - 語音辨識模型 (MIT License)
- [whisper.cpp](https://github.com/ggerganov/whisper.cpp) by Georgi Gerganov - C++ 高效能實作 (MIT License)
- [FFmpeg](https://ffmpeg.org/) - 音訊處理 (LGPL/GPL)
- [CustomTkinter](https://github.com/TomSchimansky/customtkinter) - 現代化 UI 框架 (MIT License)
- [OpenCC](https://github.com/BYVoid/OpenCC) - 簡繁轉換 (Apache 2.0)

模型來源：[Hugging Face - ggerganov/whisper.cpp](https://huggingface.co/ggerganov/whisper.cpp)

## 授權條款

本專案採用 MIT 授權條款。詳見 [LICENSE](LICENSE) 檔案。
