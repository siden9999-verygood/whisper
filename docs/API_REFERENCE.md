# API 參考文件

## 概述

AI 智慧工作站提供完整的 Python API，允許開發者整合和擴展功能。本文件詳細說明所有可用的 API 介面。

## 目錄

1. [核心模組](#核心模組)
2. [轉錄管理](#轉錄管理)
3. [搜尋管理](#搜尋管理)
4. [歸檔管理](#歸檔管理)
5. [監控管理](#監控管理)
6. [診斷管理](#診斷管理)
7. [配置管理](#配置管理)
8. [平台適配](#平台適配)
9. [事件系統](#事件系統)
10. [錯誤處理](#錯誤處理)

## 核心模組

### 匯入方式

```python
# 匯入核心模組
from transcription_manager import transcription_manager
from enhanced_search_manager import enhanced_search_manager
from archive_manager import archive_manager
from monitoring_manager import monitoring_manager
from diagnostics_manager import diagnostics_manager
from config_service import config_service
from platform_adapter import platform_adapter
from logging_service import logging_service
```

## 轉錄管理

### TranscriptionManager

語音轉錄管理器，提供音訊轉文字功能。

#### 類別定義

```python
class TranscriptionManager:
    def __init__(self)
    def transcribe_file(self, audio_file: str, **kwargs) -> TranscriptionResult
    def batch_transcribe(self, input_dir: str, **kwargs) -> List[TranscriptionResult]
    def get_supported_formats(self) -> List[str]
    def cancel_transcription(self, task_id: str) -> bool
```

#### 方法詳解

##### transcribe_file()

轉錄單個音訊檔案。

**參數**:
- `audio_file` (str): 音訊檔案路徑
- `output_format` (str, optional): 輸出格式 ('txt', 'srt', 'vtt', 'json')
- `output_path` (str, optional): 輸出檔案路徑
- `language` (str, optional): 語言代碼 ('zh', 'en', 'auto')
- `enable_ai_correction` (bool, optional): 啟用 AI 校正
- `include_timestamps` (bool, optional): 包含時間戳記
- `progress_callback` (callable, optional): 進度回調函數

**返回值**:
- `TranscriptionResult`: 轉錄結果物件

**範例**:
```python
# 基本轉錄
result = transcription_manager.transcribe_file("audio.mp3")

# 進階轉錄
result = transcription_manager.transcribe_file(
    audio_file="meeting.wav",
    output_format="srt",
    output_path="transcripts/meeting.srt",
    language="zh",
    enable_ai_correction=True,
    include_timestamps=True,
    progress_callback=lambda p: print(f"進度: {p}%")
)
```

##### batch_transcribe()

批次轉錄多個音訊檔案。

**參數**:
- `input_dir` (str): 輸入目錄路徑
- `output_dir` (str, optional): 輸出目錄路徑
- `formats` (List[str], optional): 輸出格式清單
- `file_pattern` (str, optional): 檔案過濾模式
- `recursive` (bool, optional): 遞迴搜尋子目錄
- `max_workers` (int, optional): 最大並行工作數
- `progress_callback` (callable, optional): 進度回調函數

**返回值**:
- `List[TranscriptionResult]`: 轉錄結果清單

**範例**:
```python
# 批次轉錄
results = transcription_manager.batch_transcribe(
    input_dir="audio_files/",
    output_dir="transcripts/",
    formats=["txt", "srt"],
    file_pattern="*.mp3",
    recursive=True,
    max_workers=4
)

# 處理結果
for result in results:
    if result.success:
        print(f"轉錄成功: {result.input_file}")
    else:
        print(f"轉錄失敗: {result.error_message}")
```

#### TranscriptionResult

轉錄結果資料類別。

```python
@dataclass
class TranscriptionResult:
    input_file: str
    output_files: List[str]
    text_content: str
    duration: float
    language: str
    confidence: float
    success: bool
    error_message: str
    processing_time: float
    metadata: Dict[str, Any]
```

**屬性說明**:
- `input_file`: 輸入檔案路徑
- `output_files`: 輸出檔案路徑清單
- `text_content`: 轉錄文字內容
- `duration`: 音訊時長（秒）
- `language`: 檢測到的語言
- `confidence`: 轉錄信心度 (0-1)
- `success`: 是否成功
- `error_message`: 錯誤訊息
- `processing_time`: 處理時間（秒）
- `metadata`: 額外元資料

## 搜尋管理

### EnhancedSearchManager

增強搜尋管理器，提供智能搜尋功能。

#### 類別定義

```python
class EnhancedSearchManager:
    def __init__(self)
    def search(self, query: str, **kwargs) -> SearchResults
    def advanced_search(self, criteria: Dict[str, Any]) -> SearchResults
    def create_search_template(self, name: str, criteria: Dict[str, Any]) -> bool
    def get_search_templates(self) -> List[SearchTemplate]
    def rebuild_index(self) -> bool
```

#### 方法詳解

##### search()

執行基本搜尋。

**參數**:
- `query` (str): 搜尋查詢字串
- `max_results` (int, optional): 最大結果數量
- `file_types` (List[str], optional): 檔案類型過濾
- `date_range` (Tuple[str, str], optional): 日期範圍
- `sort_by` (str, optional): 排序方式
- `include_content` (bool, optional): 包含檔案內容

**返回值**:
- `SearchResults`: 搜尋結果物件

**範例**:
```python
# 基本搜尋
results = enhanced_search_manager.search("會議記錄")

# 進階搜尋
results = enhanced_search_manager.search(
    query="專案討論",
    max_results=50,
    file_types=["srt", "txt"],
    date_range=("2024-01-01", "2024-01-31"),
    sort_by="relevance",
    include_content=True
)
```

##### advanced_search()

執行進階搜尋。

**參數**:
- `criteria` (Dict[str, Any]): 搜尋條件字典

**搜尋條件格式**:
```python
criteria = {
    "query": "搜尋關鍵字",
    "filters": {
        "file_type": ["srt", "txt"],
        "date_range": {
            "start": "2024-01-01",
            "end": "2024-01-31"
        },
        "file_size": {
            "min": 1024,  # bytes
            "max": 1048576
        },
        "tags": ["重要", "會議"],
        "path": "會議記錄/",
        "language": "zh"
    },
    "sort": {
        "field": "relevance",  # relevance, date, size, name
        "order": "desc"  # asc, desc
    },
    "limit": 100,
    "offset": 0
}
```

**範例**:
```python
# 複雜搜尋條件
criteria = {
    "query": "預算討論",
    "filters": {
        "file_type": ["srt"],
        "date_range": {
            "start": "2024-01-01",
            "end": "2024-03-31"
        },
        "tags": ["重要"],
        "file_size": {"min": 1024}
    },
    "sort": {"field": "date", "order": "desc"},
    "limit": 20
}

results = enhanced_search_manager.advanced_search(criteria)
```

#### SearchResults

搜尋結果資料類別。

```python
@dataclass
class SearchResults:
    query: str
    total_count: int
    results: List[SearchResult]
    processing_time: float
    suggestions: List[str]
    facets: Dict[str, List[FacetItem]]
```

#### SearchResult

單個搜尋結果。

```python
@dataclass
class SearchResult:
    file_path: str
    file_name: str
    file_type: str
    file_size: int
    modified_time: datetime
    relevance_score: float
    highlights: List[str]
    content_preview: str
    tags: List[str]
    metadata: Dict[str, Any]
```

## 歸檔管理

### ArchiveManager

媒體歸檔管理器，提供自動分類和組織功能。

#### 類別定義

```python
class ArchiveManager:
    def __init__(self)
    def archive_files(self, files: List[str], **kwargs) -> ArchiveResult
    def create_archive_rule(self, rule: ArchiveRule) -> bool
    def get_archive_rules(self) -> List[ArchiveRule]
    def preview_archive(self, files: List[str], rule: str) -> ArchivePreview
```

#### 方法詳解

##### archive_files()

歸檔檔案清單。

**參數**:
- `files` (List[str]): 要歸檔的檔案路徑清單
- `destination` (str): 目標目錄
- `rule` (str): 歸檔規則名稱
- `create_structure` (bool, optional): 建立目錄結構
- `handle_duplicates` (str, optional): 重複檔案處理方式
- `progress_callback` (callable, optional): 進度回調函數

**範例**:
```python
# 基本歸檔
result = archive_manager.archive_files(
    files=["audio1.mp3", "audio2.wav"],
    destination="archive/",
    rule="by_date"
)

# 進階歸檔
result = archive_manager.archive_files(
    files=file_list,
    destination="organized/",
    rule="by_type_and_date",
    create_structure=True,
    handle_duplicates="rename",
    progress_callback=lambda p: print(f"歸檔進度: {p}%")
)
```

#### ArchiveRule

歸檔規則資料類別。

```python
@dataclass
class ArchiveRule:
    name: str
    description: str
    pattern: str
    conditions: List[ArchiveCondition]
    actions: List[ArchiveAction]
    enabled: bool
```

**內建歸檔規則**:
- `by_date`: 按日期歸檔 (YYYY/MM/)
- `by_type`: 按檔案類型歸檔
- `by_size`: 按檔案大小歸檔
- `by_tags`: 按標籤歸檔
- `custom`: 自訂規則

## 監控管理

### MonitoringManager

系統監控管理器，提供資料夾監控和效能監控功能。

#### 類別定義

```python
class MonitoringManager:
    def __init__(self)
    def start_folder_monitoring(self, path: str, rules: List[MonitorRule]) -> bool
    def stop_folder_monitoring(self, path: str) -> bool
    def get_system_stats(self) -> SystemStats
    def add_event_listener(self, event_type: str, callback: callable) -> bool
```

#### 方法詳解

##### start_folder_monitoring()

開始監控資料夾。

**參數**:
- `path` (str): 要監控的資料夾路徑
- `rules` (List[MonitorRule]): 監控規則清單

**範例**:
```python
# 建立監控規則
rules = [
    MonitorRule(
        name="音訊轉錄",
        file_patterns=["*.mp3", "*.wav"],
        actions=["transcribe"],
        output_format="srt"
    ),
    MonitorRule(
        name="自動歸檔",
        file_patterns=["*.srt", "*.txt"],
        actions=["archive"],
        archive_rule="by_date"
    )
]

# 開始監控
success = monitoring_manager.start_folder_monitoring(
    path="watch_folder/",
    rules=rules
)
```

##### add_event_listener()

添加事件監聽器。

**支援的事件類型**:
- `file_added`: 檔案新增
- `file_modified`: 檔案修改
- `file_deleted`: 檔案刪除
- `transcription_completed`: 轉錄完成
- `analysis_completed`: 分析完成
- `archive_completed`: 歸檔完成

**範例**:
```python
def on_file_added(file_path):
    print(f"新檔案: {file_path}")
    # 執行自訂處理邏輯

def on_transcription_completed(result):
    print(f"轉錄完成: {result.input_file}")
    # 執行後續處理

# 註冊事件監聽器
monitoring_manager.add_event_listener("file_added", on_file_added)
monitoring_manager.add_event_listener("transcription_completed", on_transcription_completed)
```

#### SystemStats

系統統計資料類別。

```python
@dataclass
class SystemStats:
    cpu_usage: float
    memory_usage: MemoryInfo
    disk_usage: DiskInfo
    network_stats: NetworkInfo
    process_stats: ProcessInfo
    timestamp: datetime
```

## 診斷管理

### DiagnosticsManager

診斷管理器，提供系統診斷和問題排除功能。

#### 類別定義

```python
class DiagnosticsManager:
    def __init__(self)
    def run_full_diagnostics(self) -> DiagnosticInfo
    def quick_health_check(self) -> HealthStatus
    def export_diagnostic_package(self, info: DiagnosticInfo) -> str
    def get_system_info(self) -> Dict[str, Any]
```

#### 方法詳解

##### run_full_diagnostics()

執行完整系統診斷。

**返回值**:
- `DiagnosticInfo`: 診斷資訊物件

**範例**:
```python
# 執行診斷
diagnostic_info = diagnostics_manager.run_full_diagnostics()

# 檢查結果
if diagnostic_info.overall_status == "healthy":
    print("系統狀態良好")
else:
    print("發現問題:")
    for issue in diagnostic_info.issues:
        print(f"- {issue.description}")
```

##### export_diagnostic_package()

匯出診斷套件。

**參數**:
- `info` (DiagnosticInfo): 診斷資訊

**返回值**:
- `str`: 診斷套件檔案路徑

**範例**:
```python
# 執行診斷並匯出
diagnostic_info = diagnostics_manager.run_full_diagnostics()
package_path = diagnostics_manager.export_diagnostic_package(diagnostic_info)
print(f"診斷套件已匯出: {package_path}")
```

## 配置管理

### ConfigService

配置管理服務，提供應用程式設定管理功能。

#### 類別定義

```python
class ConfigService:
    def __init__(self)
    def get_config(self) -> AppConfig
    def update_config(self, updates: Dict[str, Any]) -> bool
    def reset_config(self) -> bool
    def export_config(self, file_path: str) -> bool
    def import_config(self, file_path: str) -> bool
```

#### 方法詳解

##### get_config()

取得當前配置。

**返回值**:
- `AppConfig`: 應用程式配置物件

**範例**:
```python
# 取得配置
config = config_service.get_config()

# 存取配置值
print(f"AI 模型: {config.ai_model}")
print(f"工作目錄: {config.work_directory}")
print(f"輸出目錄: {config.output_directory}")
```

##### update_config()

更新配置。

**參數**:
- `updates` (Dict[str, Any]): 要更新的配置項目

**範例**:
```python
# 更新配置
updates = {
    "ai_model": "gemini-pro",
    "work_directory": "/new/work/path",
    "enable_auto_backup": True,
    "max_concurrent_tasks": 4
}

success = config_service.update_config(updates)
if success:
    print("配置更新成功")
```

#### AppConfig

應用程式配置資料類別。

```python
@dataclass
class AppConfig:
    # AI 設定
    ai_model: str
    api_key: str
    api_endpoint: str
    
    # 路徑設定
    work_directory: str
    output_directory: str
    temp_directory: str
    
    # 效能設定
    max_concurrent_tasks: int
    memory_limit: int
    cpu_limit: float
    
    # 功能設定
    enable_auto_backup: bool
    enable_folder_monitoring: bool
    enable_ai_correction: bool
    
    # 介面設定
    theme: str
    language: str
    window_width: int
    window_height: int
```

## 平台適配

### PlatformAdapter

跨平台適配器，處理不同作業系統的差異。

#### 類別定義

```python
class PlatformAdapter:
    def __init__(self)
    def get_platform(self) -> str
    def get_config_dir(self) -> Path
    def get_temp_dir(self) -> Path
    def run_command(self, command: List[str], **kwargs) -> subprocess.CompletedProcess
    def get_system_info(self) -> Dict[str, str]
```

#### 方法詳解

##### get_platform()

取得當前平台類型。

**返回值**:
- `str`: 平台類型 ('windows', 'macos', 'linux')

##### get_config_dir()

取得配置目錄路徑。

**返回值**:
- `Path`: 配置目錄路徑

**平台差異**:
- Windows: `%APPDATA%\AIWorkstation`
- macOS: `~/Library/Application Support/AIWorkstation`
- Linux: `~/.config/aiworkstation`

##### run_command()

執行系統命令。

**參數**:
- `command` (List[str]): 命令和參數清單
- `cwd` (str, optional): 工作目錄
- `capture_output` (bool, optional): 捕獲輸出

**範例**:
```python
# 執行命令
result = platform_adapter.run_command(
    command=["python", "--version"],
    capture_output=True
)

if result.returncode == 0:
    print(f"Python 版本: {result.stdout}")
```

## 事件系統

### 事件類型

系統支援以下事件類型：

#### 檔案事件
- `file_added`: 檔案新增
- `file_modified`: 檔案修改
- `file_deleted`: 檔案刪除
- `file_moved`: 檔案移動

#### 處理事件
- `transcription_started`: 轉錄開始
- `transcription_progress`: 轉錄進度
- `transcription_completed`: 轉錄完成
- `transcription_failed`: 轉錄失敗

#### 系統事件
- `system_startup`: 系統啟動
- `system_shutdown`: 系統關閉
- `config_changed`: 配置變更
- `error_occurred`: 錯誤發生

### 事件監聽

```python
# 註冊事件監聽器
def handle_transcription_completed(event_data):
    result = event_data['result']
    print(f"轉錄完成: {result.input_file}")
    
    # 自動執行 AI 分析
    if result.success:
        ai_analysis_manager.analyze_file(result.output_files[0])

# 註冊監聽器
monitoring_manager.add_event_listener(
    "transcription_completed", 
    handle_transcription_completed
)
```

### 事件發送

```python
# 發送自訂事件
event_data = {
    'file_path': '/path/to/file.mp3',
    'timestamp': datetime.now(),
    'metadata': {'size': 1024000}
}

monitoring_manager.emit_event('custom_event', event_data)
```

## 錯誤處理

### 例外類別

系統定義了以下例外類別：

#### 基礎例外
```python
class WorkstationError(Exception):
    """工作站基礎例外"""
    pass

class ConfigurationError(WorkstationError):
    """配置錯誤"""
    pass

class TranscriptionError(WorkstationError):
    """轉錄錯誤"""
    pass

class SearchError(WorkstationError):
    """搜尋錯誤"""
    pass

class ArchiveError(WorkstationError):
    """歸檔錯誤"""
    pass
```

#### 使用範例

```python
try:
    result = transcription_manager.transcribe_file("audio.mp3")
except TranscriptionError as e:
    print(f"轉錄失敗: {e}")
    # 處理轉錄錯誤
except ConfigurationError as e:
    print(f"配置錯誤: {e}")
    # 處理配置錯誤
except WorkstationError as e:
    print(f"系統錯誤: {e}")
    # 處理一般錯誤
```

### 錯誤回調

```python
def error_handler(error_info):
    print(f"錯誤類型: {error_info['type']}")
    print(f"錯誤訊息: {error_info['message']}")
    print(f"錯誤時間: {error_info['timestamp']}")
    
    # 記錄錯誤
    logging_service.error(f"API 錯誤: {error_info['message']}")

# 註冊錯誤處理器
monitoring_manager.add_event_listener('error_occurred', error_handler)
```

## 完整範例

### 基本使用範例

```python
#!/usr/bin/env python3
"""
AI 智慧工作站 API 使用範例
"""

from transcription_manager import transcription_manager
from enhanced_search_manager import enhanced_search_manager
from archive_manager import archive_manager
from monitoring_manager import monitoring_manager
from config_service import config_service

def main():
    # 1. 設定配置
    config_updates = {
        "work_directory": "/path/to/work",
        "output_directory": "/path/to/output",
        "max_concurrent_tasks": 4
    }
    config_service.update_config(config_updates)
    
    # 2. 轉錄音訊檔案
    print("開始轉錄...")
    result = transcription_manager.transcribe_file(
        audio_file="meeting.mp3",
        output_format="srt",
        enable_ai_correction=True
    )
    
    if result.success:
        print(f"轉錄成功: {result.output_files[0]}")
        
        # 3. 搜尋轉錄結果
        print("搜尋相關內容...")
        search_results = enhanced_search_manager.search(
            query="專案討論",
            file_types=["srt"],
            max_results=10
        )
        
        print(f"找到 {search_results.total_count} 個相關結果")
        
        # 4. 歸檔檔案
        print("歸檔檔案...")
        archive_result = archive_manager.archive_files(
            files=result.output_files,
            destination="archive/",
            rule="by_date"
        )
        
        if archive_result.success:
            print("歸檔完成")
    
    else:
        print(f"轉錄失敗: {result.error_message}")

if __name__ == "__main__":
    main()
```

### 進階使用範例

```python
#!/usr/bin/env python3
"""
進階 API 使用範例：批次處理和監控
"""

import os
from pathlib import Path
from transcription_manager import transcription_manager
from monitoring_manager import monitoring_manager, MonitorRule

def setup_folder_monitoring():
    """設定資料夾監控"""
    
    # 定義監控規則
    rules = [
        MonitorRule(
            name="自動轉錄",
            file_patterns=["*.mp3", "*.wav", "*.m4a"],
            actions=["transcribe"],
            output_format="srt",
            enable_ai_correction=True
        ),
        MonitorRule(
            name="自動歸檔",
            file_patterns=["*.srt", "*.txt"],
            actions=["archive"],
            archive_rule="by_type_and_date"
        )
    ]
    
    # 事件處理器
    def on_file_processed(event_data):
        file_path = event_data['file_path']
        action = event_data['action']
        success = event_data['success']
        
        if success:
            print(f"✓ {action} 完成: {file_path}")
        else:
            print(f"✗ {action} 失敗: {file_path}")
    
    # 註冊事件監聽器
    monitoring_manager.add_event_listener("file_processed", on_file_processed)
    
    # 開始監控
    watch_folder = "/path/to/watch"
    success = monitoring_manager.start_folder_monitoring(watch_folder, rules)
    
    if success:
        print(f"開始監控資料夾: {watch_folder}")
    else:
        print("監控啟動失敗")

def batch_process_files():
    """批次處理檔案"""
    
    input_dir = "/path/to/audio/files"
    output_dir = "/path/to/transcripts"
    
    # 批次轉錄
    results = transcription_manager.batch_transcribe(
        input_dir=input_dir,
        output_dir=output_dir,
        formats=["txt", "srt"],
        recursive=True,
        max_workers=4,
        progress_callback=lambda p: print(f"批次進度: {p:.1f}%")
    )
    
    # 處理結果
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]
    
    print(f"批次處理完成:")
    print(f"  成功: {len(successful)} 個檔案")
    print(f"  失敗: {len(failed)} 個檔案")
    
    # 顯示失敗的檔案
    if failed:
        print("失敗的檔案:")
        for result in failed:
            print(f"  - {result.input_file}: {result.error_message}")

def main():
    print("=== AI 智慧工作站進階範例 ===")
    
    # 設定資料夾監控
    setup_folder_monitoring()
    
    # 批次處理現有檔案
    batch_process_files()
    
    # 保持程式運行以監控檔案
    try:
        print("監控中... (按 Ctrl+C 停止)")
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n停止監控")
        monitoring_manager.stop_all_monitoring()

if __name__ == "__main__":
    main()
```

## 版本資訊

- **API 版本**: 4.0.0
- **相容性**: Python 3.8+
- **最後更新**: 2024-01-25

## 支援和回饋

如有 API 相關問題或建議，請：

1. 查看 [使用者手冊](USER_MANUAL.md)
2. 檢查 [常見問題](FAQ.md)
3. 提交 [Issue](https://github.com/kiro-ai/workstation/issues)
4. 參與 [討論](https://github.com/kiro-ai/workstation/discussions)

---

更多資訊請參考：
- [使用者手冊](USER_MANUAL.md)
- [開發者指南](DEVELOPER_GUIDE.md)
- [故障排除](TROUBLESHOOTING.md)