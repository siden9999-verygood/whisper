# 設計文件

## 概述

本設計文件描述了增強版媒體工作站的技術架構和實現方案。基於現有的跨平台媒體搜尋系統，我們將保持五大核心功能不變，並加入實用的增強功能，讓整個程式變得更好用、更智能。

## 架構設計

### 核心架構

```
┌─────────────────────────────────────────────────────────────┐
│                    GUI 主介面 (gui_main.py)                    │
├─────────────────────────────────────────────────────────────┤
│  轉錄頁籤    │    歸檔頁籤    │    搜尋頁籤    │    工作流程頁籤  │
├─────────────────────────────────────────────────────────────┤
│                      服務層 (Service Layer)                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │轉錄管理器    │ │歸檔管理器    │ │搜尋管理器    │ │工作流程管理器│ │
│  │Transcription│ │Archive      │ │Enhanced     │ │Workflow     │ │
│  │Manager      │ │Manager      │ │Search       │ │Manager      │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                     基礎設施層 (Infrastructure)                │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │平台適配器    │ │配置服務      │ │日誌服務      │ │檔案管理器    │ │
│  │Platform     │ │Config       │ │Logging      │ │File         │ │
│  │Adapter      │ │Service      │ │Service      │ │Manager      │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                     外部服務 (External Services)              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │Whisper.cpp  │ │Google       │ │FFmpeg       │ │檔案監控      │ │
│  │語音轉錄      │ │Gemini AI    │ │媒體轉換      │ │File Watcher │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 模組化設計

#### 1. 核心功能模組

**轉錄管理器 (TranscriptionManager)**
- 支援批次轉錄
- 多種輸出格式 (SRT, TXT, VTT, JSON)
- 自動 AI 校正和優化
- 即時進度顯示
- 繁體中文轉換

**歸檔管理器 (ArchiveManager)**
- AI 自動分析和標籤生成
- 智能分類和資料夾結構建議
- 批次處理和背景執行
- 元數據管理
- 檔案組織和移動

**搜尋管理器 (EnhancedSearchManager)**
- 自然語言搜尋
- 智能過濾和分面搜尋
- 搜尋建議和自動完成
- 結果排序和相關性評分
- 搜尋歷史和快取

#### 2. 新增增強功能模組

**監控管理器 (MonitoringManager)**
- 資料夾監控和自動處理
- 效能監控和系統資源管理
- 處理統計和歷史記錄

**進階搜尋引擎 (AdvancedSearchEngine)**
- 複雜查詢解析和執行
- 搜尋範本管理
- 智能分組和聚類

**診斷管理器 (DiagnosticsManager)**
- 詳細日誌記錄和管理
- 一鍵診斷和問題報告
- 效能分析和最佳化建議

## 組件和介面

### 1. 使用者介面組件

#### 主視窗 (MainWindow)
```python
class MainWindow:
    - notebook: ttk.Notebook  # 頁籤容器
    - status_bar: StatusBar   # 狀態列
    - menu_bar: MenuBar       # 選單列
    - toolbar: ToolBar        # 工具列
```

#### 轉錄頁籤 (TranscriptionTab)
```python
class TranscriptionTab:
    - file_selector: FileSelector
    - model_selector: ModelSelector
    - options_panel: OptionsPanel
    - progress_display: ProgressDisplay
    - log_area: LogArea
    - ai_correction_panel: AICorrectionPanel
```

#### 歸檔頁籤 (ArchiveTab)
```python
class ArchiveTab:
    - folder_selector: FolderSelector
    - ai_settings: AISettings
    - batch_processor: BatchProcessor
    - progress_monitor: ProgressMonitor
    - results_viewer: ResultsViewer
```

#### 搜尋頁籤 (SearchTab)
```python
class SearchTab:
    - search_bar: SearchBar
    - filter_panel: FilterPanel
    - results_tree: ResultsTree
    - preview_panel: PreviewPanel
    - download_manager: DownloadManager
```

#### 監控頁籤 (MonitoringTab) - 新增
```python
class MonitoringTab:
    - folder_monitor: FolderMonitor
    - performance_monitor: PerformanceMonitor
    - statistics_viewer: StatisticsViewer
    - diagnostics_panel: DiagnosticsPanel
```

### 2. 服務介面

#### 轉錄服務介面
```python
class ITranscriptionService:
    def create_task(options: TranscriptionOptions) -> str
    def start_transcription(task_id: str, callback: Callable) -> None
    def get_status(task_id: str) -> TranscriptionStatus
    def cancel_task(task_id: str) -> bool
    def get_results(task_id: str) -> TranscriptionResult
```

#### 歸檔服務介面
```python
class IArchiveService:
    def analyze_media(file_path: str) -> MediaAnalysis
    def generate_metadata(analysis: MediaAnalysis) -> MediaMetadata
    def organize_files(metadata_list: List[MediaMetadata]) -> None
    def create_report(results: List[MediaMetadata]) -> str
```

#### 搜尋服務介面
```python
class ISearchService:
    def search(query: str, options: SearchOptions) -> SearchResults
    def get_suggestions(query: str) -> List[str]
    def get_facets(results: SearchResults) -> Dict[str, Dict[str, int]]
    def build_index() -> None
```

## 資料模型

### 1. 核心資料模型

#### 媒體檔案模型
```python
@dataclass
class MediaFile:
    file_id: str
    file_path: str
    file_type: str  # 圖片/音訊/影片
    file_size: int
    created_date: datetime
    modified_date: datetime
    metadata: Dict[str, Any]
```

#### 轉錄結果模型
```python
@dataclass
class TranscriptionResult:
    task_id: str
    input_file: str
    output_files: List[str]
    transcription_text: str
    confidence_score: float
    language: str
    duration: float
    segments: List[TranscriptionSegment]
```

#### 媒體元數據模型
```python
@dataclass
class MediaMetadata:
    file_id: str
    title: str
    description: str
    tags: List[str]
    keywords: List[str]
    category: str
    subcategory: str
    mood: str
    technical_analysis: Dict[str, Any]
    ai_generated: bool
    processing_date: datetime
```

### 2. 工作流程模型

#### 工作流程定義
```python
@dataclass
class WorkflowDefinition:
    workflow_id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    triggers: List[WorkflowTrigger]
    settings: Dict[str, Any]
```

#### 工作流程步驟
```python
@dataclass
class WorkflowStep:
    step_id: str
    step_type: str  # transcribe/analyze/archive/search
    parameters: Dict[str, Any]
    dependencies: List[str]
    retry_policy: RetryPolicy
```

## 錯誤處理

### 錯誤分類

1. **系統錯誤**
   - 檔案系統錯誤
   - 網路連線錯誤
   - 記憶體不足錯誤

2. **業務邏輯錯誤**
   - 檔案格式不支援
   - API 配額超限
   - 轉錄失敗

3. **使用者輸入錯誤**
   - 無效的檔案路徑
   - 缺少必要參數
   - 權限不足

### 錯誤處理策略

```python
class ErrorHandler:
    def handle_system_error(error: SystemError) -> ErrorResponse
    def handle_business_error(error: BusinessError) -> ErrorResponse
    def handle_user_error(error: UserError) -> ErrorResponse
    def log_error(error: Exception, context: Dict[str, Any]) -> None
    def notify_user(error: Exception, message: str) -> None
```

## 測試策略

### 1. 單元測試
- 每個服務模組的獨立測試
- 資料模型驗證測試
- 工具函數測試

### 2. 整合測試
- 服務間互動測試
- 外部 API 整合測試
- 檔案系統操作測試

### 3. 端到端測試
- 完整工作流程測試
- 使用者介面測試
- 效能測試

### 4. 跨平台測試
- Windows 平台測試
- macOS 平台測試
- 路徑處理測試

## 效能考量

### 1. 記憶體管理
- 大檔案分塊處理
- 及時釋放資源
- 快取策略優化

### 2. 並發處理
- 多執行緒轉錄
- 非同步 AI 分析
- 背景任務處理

### 3. 儲存優化
- 索引建立和維護
- 資料壓縮
- 增量備份

## 安全性設計

### 1. API 金鑰管理
- 加密儲存
- 安全傳輸
- 存取控制

### 2. 檔案安全
- 路徑驗證
- 權限檢查
- 備份保護

### 3. 資料隱私
- 本地處理優先
- 敏感資料過濾
- 使用者同意機制

## 部署和維護

### 1. 打包策略
- 跨平台執行檔
- 依賴項管理
- 自動更新機制

### 2. 配置管理
- 環境變數
- 配置檔案
- 使用者偏好設定

### 3. 監控和日誌
- 效能監控
- 錯誤追蹤
- 使用統計

這個設計確保了系統的可擴展性、可維護性和跨平台相容性，同時保持了現有功能的穩定性並增加了實用的增強功能。