# OkokGo AI 功能完整分析報告

## 🎯 **專案概述**

OkokGo 是一個基於 React/TypeScript 的 Web 應用程式，專門用於 SRT 字幕檔案的 AI 處理。它使用 Google Gemini AI 提供多種智能功能。

## 🤖 **AI 功能架構**

### **核心 AI 服務**
- **服務檔案**: `services/geminiService.ts`
- **AI 引擎**: Google Generative AI (`@google/genai`)
- **預設模型**: `gemini-2.5-flash`
- **安全設定**: 所有安全限制都設為 `BLOCK_NONE`

### **AI 操作類型** (`types.ts`)
```typescript
export enum AiOperation {
  CORRECT = 'Correcting Subtitles',           // 字幕校正
  ANALYZE = 'Analyzing Subtitles',            // 字幕分析
  NEWS = 'Generating News Report',            // 新聞報導生成
  TRANSLATE = 'Translating Subtitles',        // 字幕翻譯
  PRINCIPLES = 'Checking Reporting Principles', // 報導原則檢查
  SOCIAL_MEDIA = 'Generating Social Media Suggestions', // 社群媒體建議
  CHAPTER_MARKERS = 'Generating Chapter Markers', // 章節標記
  NOVEL_FROM_TRANSCRIPT = 'Generating Novel from Transcript', // 小說生成
  IMAGE_PROMPTS = 'Generating Image Prompts', // 圖像提示生成
}
```

---

## 📋 **詳細 AI 功能分析**

### **1. 字幕校正 (aiCorrectSrt)**

#### **功能描述**
- 修正 SRT 字幕中的錯別字、用詞錯誤、語音辨識錯誤
- **特殊限制**: 絕對不修改標點符號，只修正文字內容

#### **技術特點**
- **分批處理**: 支援自訂批次大小 (預設 15 條)
- **進度回調**: 實時進度更新
- **重試機制**: 內建錯誤處理
- **使用者提示詞**: 支援專有名詞參考

#### **提示詞策略**
```
你是一位專注於文字內容校對的AI助手，對於標點符號的處理有嚴格的限制。
主要任務：請仔細檢查以下「原始字幕文字」，「僅僅」修正「文字本身」的錯別字、用詞錯誤、或語音辨識導致的文字內容不通順之處。
「最重要指令」：對於「所有」標點符號（包括句號、逗號、問號、引號、頓號等），你「絕對不可以」進行任何形式的修改、添加或刪除。
```

#### **輸出格式**
```typescript
interface CorrectionDataItem {
  index: number;
  start: string;
  end: string;
  original: string;
  corrected: string;
  changed: boolean;
  ai_skipped_mismatch: boolean;
  ai_failed_chunk: boolean;
}
```

---

### **2. 字幕分析 (aiAnalyzeSrt)**

#### **功能描述**
- 生成內容摘要 (3-5 句話)
- 識別語音辨識錯誤並提供修正建議
- 提取關鍵詞與專有名詞

#### **技術特點**
- **溫度設定**: 0.5 (平衡創意與準確性)
- **JSON 格式**: 強制 JSON 回應格式
- **台灣本地化**: 專注於台灣常用表達方式

#### **輸出格式**
```typescript
interface AnalysisResult {
  summary: string;
  correction_suggestions: CorrectionSuggestion[];
  keywords: string[];
}

interface CorrectionSuggestion {
  original: string;
  corrected: string;
  explanation: string;
}
```

---

### **3. 新聞報導生成 (aiGenerateNewsReport)**

#### **功能描述**
- 將字幕內容轉換為專業新聞報導
- 生成新聞標題和內容

#### **技術特點**
- **溫度設定**: 0.7 (較高創意性)
- **風格要求**: 繁體中文、正式、客觀、專業
- **內容限制**: 不可捏造原始記錄中未提及的事實

#### **輸出格式**
```typescript
interface NewsReportResult {
  title: string;
  content: string;
}
```

---

### **4. 字幕翻譯 (aiTranslateSrt)**

#### **功能描述**
- 將字幕翻譯成指定語言
- 支援分批處理和進度追蹤

#### **技術特點**
- **分批處理**: 支援自訂批次大小
- **溫度設定**: 0.3 (低溫度確保準確性)
- **多語言支援**: 可指定目標語言
- **上下文保持**: 維持一致語調

#### **輸出格式**
```typescript
interface TranslationDataItem {
  index: number;
  start: string;
  end: string;
  original_text: string;
  translated_text: string;
  ai_generated_translation: boolean;
  translation_skipped_mismatch: boolean;
}
```

---

### **5. 報導原則檢查 (aiCheckReportingPrinciples)**

#### **功能描述**
- 檢查內容是否違反新聞報導原則
- 特別關注自殺防治相關原則

#### **技術特點**
- **專業檢查**: 基於台灣新聞倫理規範
- **違規識別**: 精確標示違規片段
- **解釋說明**: 提供違規原因說明

#### **預設原則** (constants.ts)
```typescript
export const SUICIDE_PREVENTION_PRINCIPLES: ReportingPrinciple[] = [
  {
    "id": "原則1A 教導",
    "text": "第一款所稱「教導自殺方法之訊息」，指媒體對不特定人提供自殺方法之具體可操作性計畫或步驟..."
  },
  // ... 更多原則
];
```

---

### **6. 社群媒體建議 (aiGenerateSocialMediaSuggestions)**

#### **功能描述**
- 為不同平台生成最佳化的社群媒體文案
- 包含 YouTube、Podcast、SEO 關鍵字、封面建議

#### **技術特點**
- **溫度設定**: 0.8 (高創意性)
- **多平台優化**: 針對不同平台特性調整
- **SEO 優化**: 提供 10-15 個相關關鍵字

#### **輸出格式**
```typescript
interface SocialMediaSuggestions {
  youtube: YouTubeSuggestions;
  podcast: PodcastSuggestions;
  seo_keywords: string[];
  thumbnail_suggestions: ThumbnailSuggestions;
  overall_analysis: string;
}
```

---

### **7. 章節標記生成 (aiGenerateChapterMarkers)**

#### **功能描述**
- 自動為長篇內容生成章節標記
- 包含時間戳和章節標題

#### **技術特點**
- **時間軸分析**: 基於 SRT 時間戳
- **內容分段**: 智能識別內容轉折點
- **標題生成**: 簡潔有力的章節標題

---

### **8. 小說生成 (aiGenerateNovelFromTranscript)**

#### **功能描述**
- 將逐字稿改編成懸疑小說
- 包含故事大綱規劃和章節生成

#### **技術特點**
- **兩階段生成**:
  1. `aiGenerateStoryPlan`: 生成故事大綱
  2. `aiGenerateNovelChapter`: 逐章生成內容
- **角色映射**: 將真實人名轉換為虛構角色
- **台灣本土化**: 融入台灣社會文化語境
- **第三人稱視角**: 適合單人朗讀

#### **故事結構** (7章結構)
```typescript
interface StoryPlan {
  character_mapping: CharacterMapping;
  story_summary: string;
  chapter_plan: ChapterOutline[]; // 7章大綱
}
```

---

## 🛠️ **技術架構特點**

### **1. 錯誤處理機制**
```typescript
const safeGenerateContent = async (params: GenerateContentParameters, operationName: string): Promise<GenerateContentResponse> => {
  if (!genAiInstance) {
    throw new Error('AI 服務未初始化。');
  }
  try {
    return await genAiInstance.models.generateContent(params);
  } catch (err: any) {
    const detail = err?.response?.status ? `HTTP ${err.response.status}` : err.message || String(err);
    throw new Error(`${operationName} 失敗: ${detail}`);
  }
};
```

### **2. JSON 回應解析**
```typescript
const parseJsonResponse = <T,>(responseText: string, operationName: string): T | null => {
  // 支援多種 JSON 格式 (```json, 純 JSON 等)
  // 詳細錯誤處理和日誌記錄
};
```

### **3. 進度追蹤系統**
- 所有長時間操作都支援進度回調
- 實時狀態更新
- 批次處理進度顯示

### **4. 安全設定**
```typescript
export const GEMINI_SAFETY_SETTINGS_BLOCK_NONE = [
  { category: HarmCategory.HARM_CATEGORY_HARASSMENT, threshold: HarmBlockThreshold.BLOCK_NONE },
  { category: HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold: HarmBlockThreshold.BLOCK_NONE },
  { category: HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold: HarmBlockThreshold.BLOCK_NONE },
  { category: HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold: HarmBlockThreshold.BLOCK_NONE },
];
```

---

## 🎨 **使用者介面特點**

### **1. 模態視窗系統**
- 每個 AI 功能都有專用的結果顯示視窗
- 支援結果編輯和匯出
- 統一的視覺設計

### **2. 進度顯示**
- 實時進度條
- 詳細狀態訊息
- 操作取消功能

### **3. 日誌系統**
- 完整的操作日誌
- 錯誤追蹤
- 成功/警告/錯誤分類

### **4. 設定管理**
- API 金鑰管理
- 模型選擇
- 批次大小設定
- RPM 限制設定

---

## 📊 **配置參數**

### **預設設定** (constants.ts)
```typescript
export const DEFAULT_MODEL_NAME = 'gemini-2.5-flash';
export const DEFAULT_RPM_LIMIT = 10;
export const DEFAULT_CHUNK_SIZE = 15;
```

### **可調整參數**
- **AI 模型**: 使用者可選擇不同的 Gemini 模型
- **批次大小**: 1-50 條字幕/批次
- **RPM 限制**: API 呼叫頻率限制
- **溫度設定**: 各功能有不同的創意度設定

---

## 🔄 **工作流程**

### **典型使用流程**
1. **檔案上傳**: 上傳 SRT 字幕檔案
2. **API 設定**: 輸入 Google AI API 金鑰
3. **功能選擇**: 選擇需要的 AI 功能
4. **參數調整**: 設定批次大小、模型等參數
5. **執行處理**: 開始 AI 處理，顯示進度
6. **結果查看**: 在模態視窗中查看結果
7. **結果編輯**: 可選的結果編輯和調整
8. **匯出下載**: 下載處理後的檔案

---

## 💡 **創新特點**

### **1. 專業化提示詞工程**
- 每個功能都有精心設計的提示詞
- 針對台灣本土化需求優化
- 嚴格的輸出格式控制

### **2. 分批處理機制**
- 避免 API 限制問題
- 支援大型檔案處理
- 實時進度追蹤

### **3. 多模態 AI 應用**
- 不只是簡單的文字處理
- 包含創意寫作 (小說生成)
- 專業內容生成 (新聞報導)
- 行銷內容優化 (社群媒體)

### **4. 完整的錯誤處理**
- 詳細的錯誤分類
- 使用者友善的錯誤訊息
- 自動重試機制

---

## 🎯 **適用於你的專案的建議**

### **1. 可直接移植的功能**
- **字幕校正**: 完整的分批處理邏輯
- **字幕分析**: 結構化的分析結果
- **進度追蹤**: 實時進度顯示系統
- **錯誤處理**: 完善的錯誤處理機制

### **2. 可參考的設計模式**
- **模組化 AI 服務**: 每個功能獨立的服務函數
- **統一的回應格式**: JSON 格式強制和解析
- **配置管理**: 使用者可調整的參數系統
- **狀態管理**: 操作狀態的統一管理

### **3. 可擴展的功能**
- **新聞報導生成**: 可改為其他類型的內容生成
- **社群媒體建議**: 可擴展為更多平台
- **小說生成**: 可改為其他創意寫作類型
- **原則檢查**: 可自訂檢查規則

---

## 📝 **總結**

OkokGo 是一個功能完整、技術成熟的 AI 字幕處理系統，具有以下優勢：

1. **功能豐富**: 9 種不同的 AI 功能
2. **技術完善**: 完整的錯誤處理、進度追蹤、分批處理
3. **使用者友善**: 直觀的介面、詳細的狀態顯示
4. **本土化**: 針對台灣使用者需求優化
5. **可擴展**: 模組化設計，易於添加新功能

這個系統可以作為你的 AI 功能獨立頁籤的絕佳參考，特別是在提示詞工程、錯誤處理、和使用者體驗設計方面。