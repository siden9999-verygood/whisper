# AI 媒體生成功能設計文件

## 概述

本設計文件基於 OkokGo 的成熟架構，為媒體工作站增加 AI 媒體生成能力。嚴格遵守管制開發流程，在新建的 **AI創意頁籤** 中實作，完全不影響已鎖定的語音轉錄和AI功能頁籤。

## 🏗️ **架構設計**

### **基於 OkokGo 的核心架構**

參考 `VideoGenerationSection.tsx` 和 `ImageGenerationSection.tsx` 的成功模式：

```
┌─────────────────────────────────────────────────────────────┐
│                    GUI 主介面 (gui_main.py)                    │
├─────────────────────────────────────────────────────────────┤
│  語音轉錄頁籤  │    AI功能頁籤    │    AI創意頁籤 (新建)      │
│   (已鎖定)    │    (已鎖定)     │                          │
├─────────────────────────────────────────────────────────────┤
│                    AI創意頁籤架構 (新建)                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │圖像生成區域  │ │影片生成區域  │ │批次處理區域  │ │結果管理區域  │ │
│  │Image        │ │Video        │ │Batch        │ │Results      │ │
│  │Generation   │ │Generation   │ │Processing   │ │Management   │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                     服務層 (Service Layer)                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │圖像生成管理器│ │影片生成管理器│ │API管理器     │ │結果管理器    │ │
│  │Image        │ │Video        │ │API          │ │Results      │ │
│  │Manager      │ │Manager      │ │Manager      │ │Manager      │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                     外部 API 服務                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │Google       │ │Google       │ │Google       │              │
│  │Gemini API   │ │Imagen API   │ │Veo API      │              │
│  │(提示詞生成)  │ │(圖像生成)    │ │(影片生成)    │              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
└─────────────────────────────────────────────────────────────┘
```

## 📊 **功能模組設計**

### **1. 圖像生成模組 (基於 OkokGo ImageGenerationSection)**

#### **核心架構 (完全參考 OkokGo)**
```python
class ImageGenerationManager:
    # 基於 OkokGo 的兩階段處理
    def generate_image_prompts(self, content: str) -> List[ImagePrompt]
    def generate_images(self, prompts: List[ImagePrompt]) -> List[ImageResult]
    
    # OkokGo 的配置系統
    def configure_api_settings(self, api_key: str, models: dict)
    def configure_generation_settings(self, style: str, aspect_ratio: str, count: int)
```

#### **OkokGo 原始功能對照**
- ✅ **API 配置** - API 金鑰、指令生成模型、圖像生成模型
- ✅ **藝術風格選擇** - 多種預設風格選項
- ✅ **長寬比控制** - 1:1, 16:9, 9:16 等比例
- ✅ **人物生成設定** - 允許/禁止人物生成
- ✅ **批次處理** - 支援多個提示詞同時生成
- ✅ **結果管理** - Base64 圖片預覽和下載

#### **Python/Tkinter 適配調整**
**調整項目：** UI 框架從 React 轉換為 Tkinter
**調整理由：** 配合現有系統的 GUI 架構
**具體調整：**
- React 組件 → Tkinter Frame 和 Widget
- useState → 類別屬性變數
- 事件處理從 onClick → command 回調
- CSS 樣式 → Tkinter 樣式配置

### **2. 影片生成模組 (基於 OkokGo VideoGenerationSection)**

#### **核心架構 (完全參考 OkokGo)**
```python
class VideoGenerationManager:
    # 基於 OkokGo 的兩階段處理
    def generate_video_prompts(self, transcript: str, count: int) -> List[VideoPrompt]
    def generate_videos(self, prompts: List[VideoPrompt]) -> List[VideoResult]
    
    # OkokGo 的專業提示詞工程
    def create_system_prompt(self, style: str, count: str) -> str
    def parse_json_response(self, response: str) -> List[PromptItem]
```

#### **OkokGo 原始功能對照**
- ✅ **逐字稿處理** - 支援 SRT/TXT 檔案上傳
- ✅ **專業提示詞工程** - 6層結構化提示詞 (品質→主體→情感→環境→技術→解析度)
- ✅ **影片風格選擇** - 多種預設影片風格
- ✅ **進階配置** - 比例、時長、人物生成、負面提示
- ✅ **起始圖片支援** - 圖片轉影片功能
- ✅ **批次處理** - 逐字稿批次生成多個影片
- ✅ **結果管理** - 影片 URL 預覽和下載

#### **Python/Tkinter 適配調整**
**調整項目：** 檔案處理和 API 呼叫方式
**調整理由：** Python 環境的檔案處理和 HTTP 請求方式不同
**具體調整：**
- FileReader → Python 內建檔案讀取
- fetch API → requests 或 urllib
- 檔案上傳處理 → tkinter.filedialog
- 進度顯示 → tkinter.ttk.Progressbar

### **3. 專業提示詞工程 (完全採用 OkokGo 標準)**

#### **OkokGo 的 6 層結構化提示詞**
```python
# 完全參考 VideoGenerationSection.tsx 的 systemPrompt
PROMPT_STRUCTURE = {
    "layer_1": "film-like quality and style",
    "layer_2": "main subject and action", 
    "layer_3": "vivid emotions and intricate details",
    "layer_4": "environment and atmosphere",
    "layer_5": "camera composition, movement, lens effects, lighting, and color",
    "layer_6": "final resolution or quality keywords"
}
```

#### **OkokGo 的安全性和本土化**
- ✅ **台灣本土化** - "LOCALIZATION: Feature Taiwanese people and scenes when relevant"
- ✅ **安全性考量** - "SAFETY: For sensitive topics, use symbolic or metaphorical imagery"
- ✅ **禁用詞彙** - 嚴格禁止 "photograph", "photo of", "realistic", "photorealistic", "4K", "HDR"

#### **JSON Schema 強制輸出 (完全採用 OkokGo 方法)**
```python
# 完全參考 OkokGo 的 generationConfig
JSON_SCHEMA = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT", 
        "properties": {
            "timestamp": {"type": "STRING"},
            "prompt": {"type": "STRING"},
            "zh": {"type": "STRING"}
        },
        "required": ["timestamp", "prompt", "zh"]
    }
}
```

## 🎨 **使用者介面設計**

### **AI創意頁籤佈局 (新建頁籤)**

```python
def create_creative_tab(self):
    """
    建立 AI創意頁籤 - 完全獨立的新頁籤
    嚴格遵守管制開發流程，不影響已鎖定頁籤
    """
    creative_frame = ttk.Frame(self.notebook)
    self.notebook.add(creative_frame, text="AI創意")
    
    # 基於 OkokGo 的區域劃分
    self.create_image_generation_section(creative_frame)  # 圖像生成區域
    self.create_video_generation_section(creative_frame)  # 影片生成區域
    self.create_batch_processing_section(creative_frame)  # 批次處理區域
    self.create_results_management_section(creative_frame) # 結果管理區域
```

### **圖像生成區域 (基於 OkokGo ImageGenerationSection)**

#### **UI 元件對照**
| OkokGo React 組件 | Python Tkinter 對應 | 功能說明 |
|------------------|-------------------|---------|
| `<input type="password">` | `ttk.Entry(show="*")` | API 金鑰輸入 |
| `<select>` | `ttk.Combobox` | 模型和風格選擇 |
| `<NumberInput>` | `ttk.Spinbox` | 數量控制 |
| `<Button>` | `ttk.Button` | 功能按鈕 |
| `<textarea>` | `tkinter.Text` | 提示詞編輯 |

#### **保持 OkokGo 的功能完整性**
- ✅ **配置區域** - API 設定、模型選擇、風格選擇
- ✅ **內容輸入** - 文字內容輸入區域
- ✅ **提示詞編輯** - 生成後可編輯的提示詞列表
- ✅ **結果展示** - 圖像預覽和下載功能

### **影片生成區域 (基於 OkokGo VideoGenerationSection)**

#### **完全保持 OkokGo 的複雜配置**
```python
# 基於 VideoGenerationSection.tsx 的配置選項
VIDEO_CONFIG = {
    "api_settings": ["api_key", "prompt_model", "video_model"],
    "style_settings": ["video_style", "aspect_ratio", "duration_seconds"],
    "generation_settings": ["number_of_prompts", "number_of_videos", "person_generation"],
    "advanced_settings": ["negative_prompt", "enhance_prompt", "start_image"]
}
```

## 🔄 **API 整合設計**

### **基於 OkokGo 的 API 呼叫模式**

#### **Gemini API 整合 (提示詞生成)**
```python
class GeminiAPIManager:
    def generate_prompts(self, content: str, config: dict) -> dict:
        """
        完全參考 OkokGo 的 API 呼叫方式
        - 使用相同的 payload 結構
        - 相同的 generationConfig
        - 相同的 responseSchema
        """
        payload = {
            "contents": [{
                "role": "user",
                "parts": [{"text": f"{system_prompt}\n\nContent:\n{content}"}]
            }],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": self.get_json_schema()
            }
        }
```

#### **Imagen/Veo API 整合 (媒體生成)**
```python
class MediaGenerationAPIManager:
    def generate_image(self, prompt: str, config: dict) -> str:
        """基於 OkokGo 的圖像生成 API 呼叫"""
        
    def generate_video(self, prompt: str, config: dict) -> str:
        """基於 OkokGo 的影片生成 API 呼叫"""
```

## 📁 **檔案結構設計**

### **新增檔案 (不影響現有檔案)**
```
├── gui_main.py (僅新增 create_creative_tab 方法)
├── creative_manager.py (新建)
├── image_generation_manager.py (新建)  
├── video_generation_manager.py (新建)
├── media_api_manager.py (新建)
└── creative_utils.py (新建)
```

### **嚴格的程式碼隔離**
- ✅ **獨立變數命名** - 所有變數加上 `creative_` 前綴
- ✅ **獨立方法命名** - 所有方法加上 `creative_` 前綴  
- ✅ **獨立檔案管理** - 結果儲存在獨立的 `creative_output/` 資料夾
- ✅ **獨立錯誤處理** - 不影響已鎖定功能的錯誤處理機制

## 🛡️ **與已鎖定功能的隔離設計**

### **嚴格遵守管制開發流程**
```python
# 在 gui_main.py 中的新增方式
class MediaWorkstationGUI:
    def __init__(self):
        # 現有的已鎖定變數 (嚴禁修改)
        # self.transcribe_xxx
        # self.ai_xxx
        
        # 新增的 AI創意 變數 (完全獨立)
        self.creative_api_key = ""
        self.creative_image_prompts = []
        self.creative_video_prompts = []
        self.creative_results = []
    
    def create_main_interface(self):
        # 現有的已鎖定頁籤 (嚴禁修改)
        self.create_transcribe_tab()  # 已鎖定
        self.create_ai_tab()          # 已鎖定
        
        # 新增的 AI創意頁籤 (完全獨立)
        self.create_creative_tab()    # 新建
```

## 🎯 **與 OkokGo 的差異說明**

### **必要調整項目**

#### **1. UI 框架調整**
**OkokGo 原始：** React + TypeScript + Tailwind CSS
**我們的調整：** Python + Tkinter + 自訂樣式
**調整理由：** 配合現有系統架構，保持技術棧一致性

#### **2. 檔案處理調整**  
**OkokGo 原始：** 瀏覽器 FileReader API
**我們的調整：** Python 檔案讀取 + tkinter.filedialog
**調整理由：** 桌面應用程式的檔案處理方式不同

#### **3. HTTP 請求調整**
**OkokGo 原始：** JavaScript fetch API
**我們的調整：** Python requests 庫
**調整理由：** Python 環境的標準 HTTP 請求方式

### **完全保持的核心功能**
- ✅ **提示詞工程** - 完全相同的 6 層結構和安全性規則
- ✅ **JSON Schema** - 完全相同的結構化輸出格式
- ✅ **API 呼叫邏輯** - 相同的 payload 和 config 結構
- ✅ **批次處理邏輯** - 相同的處理流程和錯誤處理
- ✅ **結果管理** - 相同的預覽、編輯、下載功能

## 🔧 **技術實作細節**

### **狀態管理 (參考 OkokGo 的 useState)**
```python
class CreativeTabState:
    """管理 AI創意頁籤的所有狀態，對應 OkokGo 的 useState"""
    def __init__(self):
        # 對應 OkokGo ImageGenerationSection 的狀態
        self.image_api_key = ""
        self.image_prompt_model = "gemini-2.5-flash"
        self.image_model = "imagen-3.0-generate-001"
        self.image_style = "realistic"
        self.image_prompts = []
        self.image_results = []
        
        # 對應 OkokGo VideoGenerationSection 的狀態  
        self.video_api_key = ""
        self.video_prompt_model = "gemini-2.5-flash"
        self.video_model = "veo-2.0-generate-001"
        self.video_style = "cinematic"
        self.video_prompts = []
        self.video_results = []
```

### **錯誤處理 (基於 OkokGo 的模式)**
```python
def handle_api_error(self, error, context):
    """
    基於 OkokGo 的錯誤處理模式
    - 區分 403 (API 未啟用) 和其他錯誤
    - 提供使用者友善的錯誤訊息
    - 記錄詳細的診斷資訊
    """
    if error.status == 403 or "SERVICE_DISABLED" in str(error):
        return "Generative Language API 尚未啟用，請至 Google Cloud Console 啟用後再試"
    else:
        return f"生成失敗，請檢查 API 金鑰或模型設定"
```

這個設計完全基於 OkokGo 的成功架構，同時嚴格遵守管制開發流程。所有調整都有明確的理由，核心功能保持完全一致。

您覺得這個設計方向如何？有需要調整或補充的地方嗎？