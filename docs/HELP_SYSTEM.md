# 線上幫助系統

## 概述

AI 智慧工作站內建完整的線上幫助系統，提供即時幫助和支援功能。

## 幫助系統功能

### 1. 內建幫助

#### 快速幫助
- **快捷鍵**: `F1` 或 `Ctrl+H`
- **選單**: 說明 → 使用手冊
- **內容**: 當前功能的相關幫助

#### 上下文幫助
- 滑鼠懸停提示
- 狀態列說明
- 錯誤訊息解釋

### 2. 文件系統

#### 完整文件
- [使用者手冊](USER_MANUAL.md) - 詳細使用說明
- [API 參考](API_REFERENCE.md) - 開發者 API 文件
- [開發者指南](DEVELOPER_GUIDE.md) - 開發和擴展指南
- [常見問題](FAQ.md) - 常見問題解答

#### 快速參考
- 功能快速參考卡
- 快捷鍵清單
- 故障排除檢查清單

### 3. 互動式教學

#### 新手引導
- 首次使用引導
- 功能介紹導覽
- 最佳實踐建議

#### 範例和模板
- 使用範例
- 配置模板
- 工作流程範例

### 4. 社群支援

#### 線上資源
- [GitHub 討論區](https://github.com/kiro-ai/workstation/discussions)
- [問題回報](https://github.com/kiro-ai/workstation/issues)
- [功能請求](https://github.com/kiro-ai/workstation/issues/new?template=feature_request.md)

#### 社群貢獻
- 使用者貢獻的教學
- 社群問答
- 經驗分享

## 實作細節

### 幫助系統架構

```python
class HelpSystem:
    def __init__(self):
        self.help_content = self._load_help_content()
        self.context_help = self._load_context_help()
    
    def show_help(self, topic=None):
        """顯示幫助內容"""
        if topic:
            return self._show_topic_help(topic)
        else:
            return self._show_main_help()
    
    def get_context_help(self, widget_name):
        """取得上下文幫助"""
        return self.context_help.get(widget_name, "")
    
    def search_help(self, query):
        """搜尋幫助內容"""
        results = []
        for topic, content in self.help_content.items():
            if query.lower() in content.lower():
                results.append(topic)
        return results
```

### 幫助內容格式

```json
{
    "transcription": {
        "title": "語音轉錄",
        "description": "將音訊檔案轉換為文字",
        "steps": [
            "選擇音訊檔案",
            "設定輸出格式",
            "開始轉錄"
        ],
        "tips": [
            "支援多種音訊格式",
            "可啟用 AI 校正提高準確度"
        ],
        "related": ["ai_analysis", "search"]
    }
}
```

## 使用指南

### 存取幫助

1. **主選單**: 說明 → 使用手冊
2. **快捷鍵**: `F1` 開啟幫助
3. **右鍵選單**: 在功能區域右鍵選擇「幫助」
4. **狀態列**: 點擊狀態列的幫助圖示

### 搜尋幫助

1. 在幫助視窗中使用搜尋框
2. 輸入關鍵字或問題
3. 瀏覽搜尋結果
4. 點擊相關主題查看詳細內容

### 回報問題

1. 使用內建診斷工具收集資訊
2. 前往 GitHub Issues 頁面
3. 使用問題回報範本
4. 提供詳細的問題描述和重現步驟

## 維護和更新

### 內容更新

- 定期更新幫助內容
- 根據使用者回饋改進
- 新增常見問題解答
- 更新範例和教學

### 品質保證

- 定期檢查連結有效性
- 驗證範例程式碼
- 測試幫助系統功能
- 收集使用者回饋

---

如需更多幫助，請參考完整的[使用者手冊](USER_MANUAL.md)或聯繫我們的支援團隊。