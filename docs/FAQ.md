# 常見問題 (FAQ)

## 目錄

1. [安裝和設定](#安裝和設定)
2. [語音轉錄](#語音轉錄)
3. [AI 分析](#ai-分析)
4. [搜尋功能](#搜尋功能)
5. [媒體歸檔](#媒體歸檔)
6. [系統監控](#系統監控)
7. [效能問題](#效能問題)
8. [錯誤處理](#錯誤處理)
9. [跨平台問題](#跨平台問題)
10. [更新和維護](#更新和維護)

## 安裝和設定

### Q: 支援哪些作業系統？

**A**: AI 智慧工作站支援以下作業系統：
- **Windows**: Windows 10 或更高版本
- **macOS**: macOS 10.14 (Mojave) 或更高版本  
- **Linux**: Ubuntu 18.04, CentOS 7 或更高版本

### Q: Python 版本需求是什麼？

**A**: 需要 Python 3.8 或更高版本。建議使用 Python 3.10 以獲得最佳效能和相容性。

```bash
# 檢查 Python 版本
python --version
# 或
python3 --version
```

### Q: 如何安裝依賴套件？

**A**: 有幾種安裝方式：

1. **自動安裝（推薦）**:
   ```bash
   python install.py
   ```

2. **手動安裝**:
   ```bash
   pip install -r requirements.txt
   ```

3. **使用虛擬環境**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   ```

### Q: 如何設定 Google Gemini API？

**A**: 
1. 前往 [Google AI Studio](https://makersuite.google.com/app/apikey)
2. 建立新的 API 金鑰
3. 在程式設定中輸入 API 金鑰
4. 或設定環境變數：
   ```bash
   export GEMINI_API_KEY="your-api-key-here"
   ```

### Q: 首次啟動程式失敗怎麼辦？

**A**: 請按照以下步驟排查：

1. **檢查 Python 環境**:
   ```bash
   python --version
   pip list
   ```

2. **檢查依賴套件**:
   ```bash
   pip install -r requirements.txt
   ```

3. **查看錯誤日誌**:
   - Windows: `%APPDATA%\AIWorkstation\logs\error.log`
   - macOS: `~/Library/Application Support/AIWorkstation/logs/error.log`
   - Linux: `~/.config/aiworkstation/logs/error.log`

4. **執行診斷**:
   ```bash
   python -c "from diagnostics_manager import diagnostics_manager; diagnostics_manager.run_full_diagnostics()"
   ```

## 語音轉錄

### Q: 支援哪些音訊格式？

**A**: 支援以下音訊格式：
- **輸入格式**: MP3, WAV, M4A, FLAC, OGG, WMA
- **輸出格式**: TXT, SRT, VTT, JSON

### Q: 轉錄速度很慢怎麼辦？

**A**: 可以嘗試以下最佳化方法：

1. **檢查系統資源**:
   - 確保有足夠的 RAM（建議 8GB+）
   - 關閉不必要的程式

2. **調整設定**:
   - 降低並行處理數量
   - 關閉 AI 校正功能（如果不需要）
   - 使用較低品質的音訊檔案

3. **檔案預處理**:
   - 壓縮大檔案
   - 分割長音訊檔案
   - 移除靜音段落

### Q: 轉錄結果不準確怎麼辦？

**A**: 提高轉錄準確度的方法：

1. **音訊品質**:
   - 使用高品質錄音設備
   - 減少背景噪音
   - 確保說話清晰

2. **設定調整**:
   - 啟用 AI 校正功能
   - 選擇正確的語言設定
   - 使用適當的音訊格式

3. **後處理**:
   - 手動校正重要內容
   - 使用 AI 分析功能進一步處理

### Q: 批次轉錄時部分檔案失敗？

**A**: 常見原因和解決方案：

1. **檔案問題**:
   - 檢查檔案是否損壞
   - 確認檔案格式支援
   - 檢查檔案權限

2. **系統資源**:
   - 檢查磁碟空間
   - 監控記憶體使用
   - 降低並行處理數量

3. **網路問題**:
   - 檢查網路連線
   - 確認 API 配額
   - 重試失敗的檔案

## AI 分析

### Q: AI 分析功能無法使用？

**A**: 請檢查以下項目：

1. **API 設定**:
   - 確認 API 金鑰正確
   - 檢查 API 配額狀態
   - 測試網路連線

2. **檔案格式**:
   - 確認檔案格式支援（TXT, SRT, VTT）
   - 檢查檔案編碼（建議 UTF-8）
   - 確認檔案內容不為空

3. **系統設定**:
   - 檢查防火牆設定
   - 確認代理伺服器設定
   - 查看錯誤日誌

### Q: AI 分析結果不理想？

**A**: 改善分析結果的方法：

1. **輸入品質**:
   - 提供清晰完整的文字
   - 移除無關內容
   - 確保文字結構良好

2. **參數調整**:
   - 選擇適當的分析類型
   - 調整分析深度
   - 使用不同的 AI 模型

3. **後處理**:
   - 結合多次分析結果
   - 手動調整分析結果
   - 使用自訂分析範本

### Q: API 配額用盡怎麼辦？

**A**: 管理 API 使用量的方法：

1. **監控使用量**:
   - 查看 API 使用統計
   - 設定使用量警告
   - 定期檢查配額狀態

2. **最佳化使用**:
   - 批次處理多個檔案
   - 避免重複分析
   - 使用快取機制

3. **升級方案**:
   - 考慮升級 API 方案
   - 使用多個 API 金鑰
   - 實作請求限制

## 搜尋功能

### Q: 搜尋找不到預期結果？

**A**: 改善搜尋結果的方法：

1. **重建索引**:
   ```python
   from enhanced_search_manager import enhanced_search_manager
   enhanced_search_manager.rebuild_index()
   ```

2. **檢查搜尋語法**:
   - 使用正確的搜尋語法
   - 嘗試不同的關鍵字
   - 使用進階搜尋功能

3. **更新資料**:
   - 確認檔案路徑正確
   - 重新載入媒體資料
   - 清除搜尋快取

### Q: 搜尋速度很慢？

**A**: 最佳化搜尋效能：

1. **索引最佳化**:
   - 定期重建索引
   - 清理過期資料
   - 使用增量索引

2. **查詢最佳化**:
   - 使用具體的搜尋詞
   - 限制搜尋範圍
   - 避免過於複雜的查詢

3. **系統最佳化**:
   - 增加記憶體配置
   - 使用 SSD 儲存
   - 關閉不必要的功能

### Q: 如何使用進階搜尋語法？

**A**: 進階搜尋語法範例：

```
# 基本搜尋
會議記錄

# 片語搜尋
"專案進度討論"

# 布林搜尋
會議 AND 記錄 NOT 草稿

# 日期範圍
date:2024-01-01..2024-01-31

# 檔案類型
type:srt ext:txt

# 檔案大小
size:>1MB size:<10MB

# 標籤過濾
tag:重要 tag:會議

# 路徑過濾
path:會議記錄/ path:2024/

# 組合查詢
會議 AND date:2024-01 AND type:srt
```

## 媒體歸檔

### Q: 歸檔功能無法正常工作？

**A**: 常見問題和解決方案：

1. **權限問題**:
   - 檢查檔案讀取權限
   - 確認目標目錄寫入權限
   - 以管理員權限執行

2. **路徑問題**:
   - 使用絕對路徑
   - 檢查路徑中的特殊字元
   - 確認目錄存在

3. **磁碟空間**:
   - 檢查可用磁碟空間
   - 清理暫存檔案
   - 使用磁碟清理工具

### Q: 如何自訂歸檔規則？

**A**: 建立自訂歸檔規則：

```python
from archive_manager import ArchiveRule, ArchiveCondition, ArchiveAction

# 建立自訂規則
custom_rule = ArchiveRule(
    name="自訂規則",
    description="按檔案類型和日期歸檔",
    pattern="{file_type}/{year}/{month}/{filename}",
    conditions=[
        ArchiveCondition("file_extension", "in", [".mp3", ".wav"]),
        ArchiveCondition("file_size", ">", 1024000)  # 大於 1MB
    ],
    actions=[
        ArchiveAction("create_directory", True),
        ArchiveAction("move_file", True),
        ArchiveAction("update_index", True)
    ],
    enabled=True
)

# 註冊規則
archive_manager.add_rule(custom_rule)
```

### Q: 重複檔案如何處理？

**A**: 重複檔案處理選項：

1. **跳過**: 保留原檔案，跳過重複檔案
2. **覆蓋**: 用新檔案覆蓋舊檔案
3. **重新命名**: 自動重新命名重複檔案
4. **詢問**: 每次遇到重複檔案時詢問用戶

```python
# 設定重複檔案處理方式
archive_result = archive_manager.archive_files(
    files=file_list,
    destination="archive/",
    rule="by_date",
    handle_duplicates="rename"  # skip, overwrite, rename, ask
)
```

## 系統監控

### Q: 資料夾監控無法啟動？

**A**: 排查監控問題：

1. **權限檢查**:
   - 確認監控目錄的讀取權限
   - 檢查系統檔案監控權限
   - 以適當權限執行程式

2. **路徑檢查**:
   - 確認監控路徑存在
   - 使用絕對路徑
   - 檢查路徑格式

3. **系統限制**:
   - 檢查系統檔案監控限制
   - 調整監控檔案數量
   - 重啟監控服務

### Q: 監控規則不生效？

**A**: 檢查監控規則設定：

```python
from monitoring_manager import MonitorRule

# 檢查規則設定
rule = MonitorRule(
    name="音訊轉錄",
    file_patterns=["*.mp3", "*.wav"],  # 確認檔案模式正確
    actions=["transcribe"],            # 確認動作有效
    enabled=True,                      # 確認規則已啟用
    conditions={
        "min_file_size": 1024,         # 最小檔案大小
        "max_file_size": 100*1024*1024 # 最大檔案大小
    }
)

# 驗證規則
if monitoring_manager.validate_rule(rule):
    monitoring_manager.add_rule(rule)
```

### Q: 系統效能監控顯示異常？

**A**: 效能監控問題排查：

1. **監控間隔**:
   - 調整監控更新間隔
   - 避免過於頻繁的監控
   - 平衡準確性和效能

2. **資源使用**:
   - 檢查監控程序的資源使用
   - 關閉不必要的監控項目
   - 最佳化監控演算法

3. **資料準確性**:
   - 比較不同監控工具的結果
   - 檢查系統時間同步
   - 驗證監控資料來源

## 效能問題

### Q: 程式啟動很慢？

**A**: 最佳化啟動速度：

1. **依賴最佳化**:
   - 延遲載入非必要模組
   - 使用輕量級替代方案
   - 預編譯 Python 檔案

2. **配置最佳化**:
   - 簡化初始配置
   - 使用快取配置
   - 並行初始化

3. **系統最佳化**:
   - 使用 SSD 儲存
   - 增加系統記憶體
   - 關閉防毒軟體即時掃描

### Q: 記憶體使用量過高？

**A**: 記憶體最佳化方法：

1. **監控記憶體使用**:
   ```python
   import psutil
   process = psutil.Process()
   memory_info = process.memory_info()
   print(f"記憶體使用: {memory_info.rss / 1024 / 1024:.1f} MB")
   ```

2. **最佳化策略**:
   - 及時釋放大物件
   - 使用生成器而非清單
   - 實作記憶體池
   - 定期執行垃圾回收

3. **設定調整**:
   - 降低快取大小
   - 減少並行處理數量
   - 限制檔案載入大小

### Q: CPU 使用率過高？

**A**: CPU 最佳化方法：

1. **程式碼最佳化**:
   - 使用更高效的演算法
   - 避免不必要的計算
   - 實作結果快取

2. **並行處理**:
   - 合理設定工作執行緒數量
   - 使用非同步處理
   - 實作工作佇列

3. **系統調整**:
   - 調整程序優先級
   - 使用 CPU 親和性
   - 監控系統負載

## 錯誤處理

### Q: 程式經常當機？

**A**: 穩定性問題排查：

1. **錯誤日誌分析**:
   - 查看詳細錯誤日誌
   - 識別當機模式
   - 記錄重現步驟

2. **記憶體問題**:
   - 檢查記憶體洩漏
   - 監控記憶體使用趨勢
   - 實作記憶體限制

3. **例外處理**:
   - 加強例外處理
   - 實作錯誤恢復機制
   - 使用防禦性程式設計

### Q: 如何報告錯誤？

**A**: 錯誤報告步驟：

1. **收集資訊**:
   ```bash
   # 執行診斷
   python -c "from diagnostics_manager import diagnostics_manager; diagnostics_manager.export_diagnostic_package()"
   ```

2. **準備報告**:
   - 詳細描述問題
   - 提供重現步驟
   - 包含系統資訊
   - 附上錯誤日誌

3. **提交報告**:
   - 前往 [GitHub Issues](https://github.com/kiro-ai/workstation/issues)
   - 使用錯誤報告範本
   - 上傳診斷套件

### Q: 如何啟用除錯模式？

**A**: 啟用除錯模式：

```bash
# 命令列啟用除錯
python gui_main.py --debug

# 環境變數啟用
export DEBUG=1
python gui_main.py

# 程式碼中啟用
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 跨平台問題

### Q: Windows 上的特殊問題？

**A**: Windows 常見問題：

1. **路徑問題**:
   - 使用正斜線或雙反斜線
   - 避免路徑過長
   - 處理 Unicode 字元

2. **權限問題**:
   - 以管理員權限執行
   - 檢查 UAC 設定
   - 確認防毒軟體設定

3. **編碼問題**:
   - 設定正確的編碼
   - 使用 UTF-8 編碼
   - 處理中文路徑

### Q: macOS 上的特殊問題？

**A**: macOS 常見問題：

1. **權限問題**:
   - 授予麥克風權限
   - 允許檔案存取權限
   - 檢查 Gatekeeper 設定

2. **Python 環境**:
   - 使用 Homebrew 安裝 Python
   - 避免系統 Python 衝突
   - 設定正確的 PATH

3. **依賴問題**:
   - 安裝 Xcode Command Line Tools
   - 使用正確的編譯器
   - 處理 M1/M2 晶片相容性

### Q: Linux 上的特殊問題？

**A**: Linux 常見問題：

1. **依賴安裝**:
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install python3-dev python3-pip ffmpeg
   
   # CentOS/RHEL
   sudo yum install python3-devel python3-pip ffmpeg
   ```

2. **權限設定**:
   - 設定適當的檔案權限
   - 配置 sudo 權限
   - 檢查 SELinux 設定

3. **音訊系統**:
   - 安裝音訊驅動程式
   - 配置 ALSA/PulseAudio
   - 測試音訊輸入輸出

## 更新和維護

### Q: 如何檢查更新？

**A**: 檢查和安裝更新：

```bash
# 檢查更新
python -c "from update_manager import update_manager; update_manager.check_for_updates(force=True)"

# 自動更新
python -c "from update_manager import update_manager; update_manager.auto_update()"

# 手動更新
git pull origin main
pip install -r requirements.txt
```

### Q: 更新後出現問題怎麼辦？

**A**: 更新問題處理：

1. **回滾更新**:
   ```bash
   # 查看可用備份
   python -c "from update_manager import update_manager; print(update_manager.get_available_backups())"
   
   # 回滾到指定版本
   python -c "from update_manager import update_manager; update_manager.rollback_update('backup_name')"
   ```

2. **重新安裝**:
   - 下載最新版本
   - 清除舊配置
   - 重新執行安裝

3. **尋求幫助**:
   - 查看更新日誌
   - 檢查已知問題
   - 聯繫技術支援

### Q: 如何備份設定和資料？

**A**: 備份重要資料：

1. **自動備份**:
   ```python
   from config_service import config_service
   
   # 匯出配置
   config_service.export_config("backup/config.json")
   
   # 備份資料庫
   enhanced_search_manager.export_index("backup/search_index.db")
   ```

2. **手動備份**:
   - 複製配置目錄
   - 備份工作目錄
   - 匯出搜尋索引

3. **定期維護**:
   - 設定自動備份
   - 清理舊備份
   - 驗證備份完整性

---

## 獲得更多幫助

如果以上 FAQ 無法解決您的問題，請：

1. **查看文件**:
   - [使用者手冊](USER_MANUAL.md)
   - [API 參考](API_REFERENCE.md)
   - [開發者指南](DEVELOPER_GUIDE.md)

2. **社群支援**:
   - [GitHub Discussions](https://github.com/kiro-ai/workstation/discussions)
   - [Issues 回報](https://github.com/kiro-ai/workstation/issues)

3. **聯繫我們**:
   - Email: support@example.com
   - 社群論壇: [討論區連結]

---

**最後更新**: 2024-01-25  
**版本**: 4.0.0