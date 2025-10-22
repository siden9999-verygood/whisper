# Windows 安裝包製作與離線部署說明

本指南協助你在 Windows 上產生一鍵安裝的 `Setup.exe`，安裝後自動建立桌面捷徑，並可在完全離線環境中使用 Whisper 轉錄功能。

## 1. 準備 Windows 專用二進位檔

將下列檔案放入專案根目錄下的 `whisper_resources/`：

- `ffmpeg.exe`（Windows 版 FFmpeg 可執行檔）
- `main.exe`（whisper.cpp 編譯出的 Windows 版主程式）
- 模型檔（已存在，`ggml-*.bin` 可跨平台重用）

說明：
- 本專案已預置 macOS 版本的 `ffmpeg` 與 `main`，在 Windows 上不可用，因此需更換為 `.exe` 版本。
- 是否需要 GPU/DirectML 加速版本，取決於你放入的 `main.exe`（可放 CPU 版或 DirectML 版）。

## 2. 建置打包輸出（PyInstaller）

在 Windows 機器上：

1. 安裝 Python 3.10+（已安裝可略過）。
2. 安裝打包工具（線上或事先準備離線安裝包）：
   - `pip install pyinstaller`
3. 執行打包（使用 onedir 形式；離線環境可加 `--skip-deps`）：

```
python build_scripts\build.py --type pyinstaller --skip-tests --skip-deps
```

完成後，PyInstaller 會在 `dist/AI智慧工作站/` 產生 `AI智慧工作站.exe` 與相依檔案。

## 3. 產生安裝器（NSIS）

1. 安裝 NSIS（線上或使用離線安裝包）。
2. 執行安裝器建立腳本：

```
python build_scripts\create_installer.py
```

成功後輸出檔案位於：

- `dist/AI智慧工作站_v<版本>_Setup.exe`

安裝後：
- 會安裝到 `C:\Program Files\AI智慧工作站`（預設），
- 自動建立桌面與開始功能表捷徑，直接啟動 `AI智慧工作站.exe`。

## 4. 完全離線安裝說明

- 只要你在打包前已將 `ffmpeg.exe`、`main.exe` 與模型檔放入 `whisper_resources/`，安裝後即可在離線環境下使用「本地轉錄」功能。
- 需要網路的功能（例如 Google Generative AI 分析）仍需可用的網路與 API 金鑰；不影響純轉錄。

## 5. 常見問題

- 啟動找不到 FFmpeg：
  - 確認 `C:\Program Files\AI智慧工作站\whisper_resources\ffmpeg.exe` 存在。
  - `config_service` 已優先尋找該位置，若仍失敗可檢查檔名或權限。

- 啟動找不到 Whisper 主程式：
  - 確認 `C:\Program Files\AI智慧工作站\whisper_resources\main.exe` 存在。

- 模型檔過大導致打包慢：
  - 屬正常情況，最終安裝檔較大屬預期（完整離線安裝）。

---

備註：
- 本流程採用 `--onedir` 模式（啟動較快，維護相依檔直觀）。如需 `--onefile` 請調整 `build_scripts/build.py` 的 PyInstaller 參數並測試啟動時間與防毒誤報情況。
