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
- **GPU 加速** - Windows CUDA 版本支援 NVIDIA 顯卡加速
- **完全免費** - 開源軟體，永久免費

## 下載安裝

前往 [Releases](https://github.com/siden9999-verygood/whisper/releases) 頁面下載：

| 平台 | 檔案 | 說明 |
|------|------|------|
| **macOS** | `VoiceTranscriber-*.dmg` | 適用所有 Mac |
| **Windows** | `VoiceTranscriber-Windows.zip` | CPU 版本，適用所有電腦 |
| **Windows + NVIDIA** | `VoiceTranscriber-Windows-CUDA.zip` | GPU 加速版，速度快 10-50 倍 |

### 安裝步驟

1. 下載對應平台的安裝包
2. 解壓縮（Windows）或拖曳到應用程式（macOS）
3. 首次執行時會自動下載 AI 模型（約 3GB）

### 選擇 Windows 版本

- **沒有 NVIDIA 顯卡** → 下載 `VoiceTranscriber-Windows.zip`
- **有 NVIDIA 顯卡** → 下載 `VoiceTranscriber-Windows-CUDA.zip`（推薦）

> 💡 **如何確認顯卡？** 按 `Ctrl+Shift+Esc` 開啟工作管理員 → 效能 → GPU，查看顯卡名稱。名稱包含 "NVIDIA" 就可以用 CUDA 版本。

### macOS 安裝步驟

由於 App 未經 Apple 簽章，首次開啟需要額外步驟：

**步驟 1：安裝 App**

1. 雙擊下載的 `VoiceTranscriber-1.0.0.dmg` 檔案
2. 出現 DMG 視窗後，把 `VoiceTranscriber.app` **拖曳**到 `Applications` 圖示上
3. 等待複製完成，關閉 DMG 視窗

**步驟 2：解除安全限制**

開啟「終端機」（Spotlight 搜尋 Terminal），貼上以下指令並按 Enter：

```bash
xattr -cr /Applications/VoiceTranscriber.app
```

**步驟 3：開啟 App**

1. 前往 Finder →「應用程式」資料夾
2. 雙擊 `VoiceTranscriber` 開啟

> ⚠️ 這是所有未經 Apple 簽章的 App 的正常現象，不影響使用安全。

## 從原始碼執行

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
| **Windows CUDA** | Windows 10, NVIDIA GTX 10系列以上 | RTX 30/40 系列 |
| **macOS** | macOS 10.14, 4GB RAM | macOS 12+, Apple Silicon |

- 約 4GB 磁碟空間（含 AI 模型）
- CUDA 版本需約 350MB 額外空間

## 硬體加速說明

| 平台 | 硬體加速 | 說明 |
|------|----------|------|
| **macOS (Apple Silicon)** | Metal GPU | 自動啟用，速度最快 |
| **macOS (Intel)** | CPU | 可正常使用，速度較慢 |
| **Windows CPU 版** | CPU | 通用版本，適用所有電腦 |
| **Windows CUDA 版** | NVIDIA GPU | 自動啟用，速度快 10-50 倍 |

### 效能比較

以 20 分鐘音檔為例：

| 版本 | 處理時間 |
|------|----------|
| Windows CPU | 約 20-40 分鐘 |
| Windows CUDA (RTX 3060) | 約 1-2 分鐘 |
| macOS M1/M2/M3 | 約 2-5 分鐘 |

## 移除程式

### macOS

程式內建「完整移除」功能：

1. 開啟程式
2. 點擊右下角「完整移除程式」按鈕
3. 確認後會自動刪除模型並移到垃圾桶

或手動移除：

```bash
rm -rf /Applications/VoiceTranscriber.app
rm -rf ~/Library/Application\ Support/VoiceTranscriber
```

### Windows

1. 刪除解壓縮的資料夾即可
2. 模型在同資料夾的 `whisper_resources` 中，會一起刪除

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
