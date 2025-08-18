"""
自然語言搜尋引擎模組
處理自然語言查詢的解析和搜尋功能
"""

import re
# 嘗試導入 jieba，如果沒有則使用簡單分詞
try:
    import jieba
    HAS_JIEBA = True
except ImportError:
    HAS_JIEBA = False
    jieba = None
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

from platform_adapter import CrossPlatformError
from logging_service import logging_service


class QueryType(Enum):
    """查詢類型枚舉"""
    KEYWORD = "keyword"
    EMOTION = "emotion"
    CATEGORY = "category"
    TECHNICAL = "technical"
    DATE = "date"
    SIZE = "size"
    COMPLEX = "complex"


@dataclass
class SearchCriteria:
    """搜尋條件資料模型"""
    keywords: List[str] = None
    emotions: List[str] = None
    file_types: List[str] = None
    categories: List[str] = None
    date_range: Optional[Tuple[datetime, datetime]] = None
    technical_filters: Dict[str, Any] = None
    sort_by: str = "relevance"
    sort_order: str = "desc"
    exclude_keywords: List[str] = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.emotions is None:
            self.emotions = []
        if self.file_types is None:
            self.file_types = []
        if self.categories is None:
            self.categories = []
        if self.technical_filters is None:
            self.technical_filters = {}
        if self.exclude_keywords is None:
            self.exclude_keywords = []


@dataclass
class SearchResult:
    """單個搜尋結果"""
    file_id: str
    title: str
    file_type: str
    file_path: str
    thumbnail_path: Optional[str]
    relevance_score: float
    metadata: Dict[str, Any]
    matched_fields: List[str]
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.matched_fields is None:
            self.matched_fields = []


@dataclass
class SearchResults:
    """搜尋結果集合"""
    results: List[SearchResult]
    total_count: int
    query: str
    execution_time: float
    suggestions: List[str]
    facets: Dict[str, Dict[str, int]]  # 分面搜尋統計
    
    def __post_init__(self):
        if self.results is None:
            self.results = []
        if self.suggestions is None:
            self.suggestions = []
        if self.facets is None:
            self.facets = {}


class NaturalLanguageSearchEngine:
    """自然語言搜尋引擎"""
    
    def __init__(self):
        self.logger = logging_service.get_logger("NLSearchEngine")
        
        # 情緒關鍵字映射
        self.emotion_keywords = {
            "快樂": ["快樂", "開心", "愉快", "歡樂", "喜悅", "高興", "興奮", "歡喜"],
            "溫馨": ["溫馨", "溫暖", "溫柔", "親情", "家庭", "和諧", "舒適"],
            "悲傷": ["悲傷", "難過", "憂鬱", "哀傷", "痛苦", "傷心", "沮喪"],
            "寧靜": ["寧靜", "平靜", "安靜", "祥和", "寂靜", "靜謐", "安詳"],
            "懷舊": ["懷舊", "回憶", "往昔", "過去", "舊時", "懷念", "復古"],
            "緊張": ["緊張", "刺激", "激烈", "緊迫", "焦慮", "壓力", "急促"],
            "史詩感": ["史詩", "壯觀", "宏偉", "磅礴", "震撼", "氣勢", "雄偉"],
            "神秘": ["神秘", "詭異", "奇幻", "超自然", "未知", "隱秘", "玄妙"],
            "浪漫": ["浪漫", "愛情", "情侶", "約會", "甜蜜", "溫情", "柔情"]
        }
        
        # 技術關鍵字映射
        self.technical_keywords = {
            # 攝影技術
            "特寫": ["特寫", "近景", "close-up", "微距"],
            "中景": ["中景", "中等", "medium", "半身"],
            "全景": ["全景", "廣角", "wide", "遠景"],
            "鳥瞰": ["鳥瞰", "俯視", "aerial", "空拍"],
            "低角度": ["低角度", "仰視", "low angle", "仰拍"],
            
            # 構圖風格
            "三分法": ["三分法", "rule of thirds", "黃金比例"],
            "引導線": ["引導線", "leading lines", "線條"],
            "對稱": ["對稱", "symmetry", "平衡"],
            "框架構圖": ["框架", "frame", "邊框"],
            
            # 光線風格
            "自然光": ["自然光", "日光", "陽光", "natural light"],
            "攝影棚光": ["攝影棚", "人工光", "studio light"],
            "輪廓光": ["輪廓光", "背光", "rim light"],
            "柔光": ["柔光", "soft light", "散射"],
            "硬光": ["硬光", "hard light", "直射"],
            
            # 音樂類型
            "古典": ["古典", "classical", "交響", "管弦"],
            "爵士": ["爵士", "jazz", "藍調", "blues"],
            "搖滾": ["搖滾", "rock", "重金屬", "metal"],
            "流行": ["流行", "pop", "主流", "熱門"],
            "電子": ["電子", "electronic", "合成", "techno"],
            
            # 人聲類型
            "男聲": ["男聲", "男性", "male voice"],
            "女聲": ["女聲", "女性", "female voice"],
            "童聲": ["童聲", "兒童", "child voice"],
            "合唱": ["合唱", "choir", "群唱"],
            "旁白": ["旁白", "narration", "解說"]
        }
        
        # 分類關鍵字映射
        self.category_keywords = {
            "人物": ["人物", "人像", "肖像", "人", "臉", "表情", "人群"],
            "自然": ["自然", "風景", "山", "水", "樹", "花", "天空", "雲"],
            "動物": ["動物", "寵物", "貓", "狗", "鳥", "魚", "昆蟲"],
            "地點": ["地點", "建築", "城市", "街道", "室內", "戶外"],
            "物件": ["物件", "物品", "工具", "食物", "車", "機器"],
            "事件": ["事件", "活動", "慶典", "會議", "表演", "運動"],
            "藝術與記錄": ["藝術", "繪畫", "雕塑", "文件", "記錄", "歷史"]
        }
        
        # 檔案類型關鍵字
        self.file_type_keywords = {
            "圖片": ["圖片", "照片", "圖像", "相片", "影像"],
            "影片": ["影片", "視頻", "電影", "短片", "錄影"],
            "音訊": ["音訊", "音樂", "聲音", "歌曲", "錄音"]
        }
        
        # 時間關鍵字
        self.time_keywords = {
            "今天": 0,
            "昨天": 1,
            "前天": 2,
            "本週": 7,
            "上週": 14,
            "本月": 30,
            "上月": 60,
            "今年": 365,
            "去年": 730
        }
        
        # 排序關鍵字
        self.sort_keywords = {
            "相關性": "relevance",
            "時間": "date",
            "名稱": "name",
            "大小": "size",
            "類型": "type"
        }
        
        # 初始化中文分詞（在所有屬性定義完成後）
        self._initialize_jieba()
    
    def _initialize_jieba(self):
        """初始化 jieba 中文分詞"""
        if not HAS_JIEBA:
            self.logger.warning("jieba 未安裝，將使用簡單分詞")
            return
            
        try:
            # 添加自定義詞彙
            for emotion_words in self.emotion_keywords.values():
                for word in emotion_words:
                    jieba.add_word(word)
            
            for tech_words in self.technical_keywords.values():
                for word in tech_words:
                    jieba.add_word(word)
            
            self.logger.info("jieba 中文分詞初始化完成")
            
        except Exception as e:
            self.logger.error(f"jieba 初始化失敗: {str(e)}")
    
    def parse_query(self, query: str) -> SearchCriteria:
        """解析自然語言查詢為搜尋條件"""
        if not query or not query.strip():
            return SearchCriteria()
        
        query = query.strip()
        self.logger.debug(f"解析查詢: {query}")
        
        criteria = SearchCriteria()
        
        # 處理排除關鍵字 (以 - 開頭)
        exclude_pattern = r'-(\w+)'
        exclude_matches = re.findall(exclude_pattern, query)
        criteria.exclude_keywords = exclude_matches
        query = re.sub(exclude_pattern, '', query).strip()
        
        # 處理引號內的精確匹配
        exact_matches = re.findall(r'"([^"]+)"', query)
        for match in exact_matches:
            criteria.keywords.append(match)
        query = re.sub(r'"[^"]+"', '', query).strip()
        
        # 中文分詞
        if HAS_JIEBA:
            words = list(jieba.cut(query))
        else:
            # 簡單分詞：按空格和標點符號分割
            words = re.split(r'[\s\u3000-\u303f\uff00-\uffef]+', query)
        
        words = [word.strip() for word in words if word.strip() and len(word.strip()) > 1]
        
        # 解析各種類型的關鍵字
        criteria.emotions = self._extract_emotions(words)
        criteria.file_types = self._extract_file_types(words)
        criteria.categories = self._extract_categories(words)
        criteria.technical_filters = self._extract_technical_filters(words)
        criteria.date_range = self._extract_date_range(words)
        
        # 提取排序條件
        sort_info = self._extract_sort_criteria(words)
        if sort_info:
            criteria.sort_by, criteria.sort_order = sort_info
        
        # 剩餘的詞作為一般關鍵字
        remaining_words = self._get_remaining_keywords(words, criteria)
        criteria.keywords.extend(remaining_words)
        
        # 去重
        criteria.keywords = list(set(criteria.keywords))
        criteria.emotions = list(set(criteria.emotions))
        criteria.file_types = list(set(criteria.file_types))
        criteria.categories = list(set(criteria.categories))
        
        self.logger.debug(f"解析結果: {criteria}")
        return criteria
    
    def _extract_emotions(self, words: List[str]) -> List[str]:
        """提取情緒關鍵字"""
        emotions = []
        for word in words:
            for emotion, keywords in self.emotion_keywords.items():
                if word in keywords:
                    emotions.append(emotion)
                    break
        return emotions
    
    def _extract_file_types(self, words: List[str]) -> List[str]:
        """提取檔案類型關鍵字"""
        file_types = []
        for word in words:
            for file_type, keywords in self.file_type_keywords.items():
                if word in keywords:
                    file_types.append(file_type)
                    break
        return file_types
    
    def _extract_categories(self, words: List[str]) -> List[str]:
        """提取分類關鍵字"""
        categories = []
        for word in words:
            for category, keywords in self.category_keywords.items():
                if word in keywords:
                    categories.append(category)
                    break
        return categories
    
    def _extract_technical_filters(self, words: List[str]) -> Dict[str, Any]:
        """提取技術關鍵字"""
        technical_filters = {}
        
        for word in words:
            for tech_type, keywords in self.technical_keywords.items():
                if word in keywords:
                    # 根據技術類型分組
                    if tech_type in ["特寫", "中景", "全景", "鳥瞰", "低角度"]:
                        technical_filters["shot_type"] = tech_type
                    elif tech_type in ["三分法", "引導線", "對稱", "框架構圖"]:
                        technical_filters["composition_style"] = tech_type
                    elif tech_type in ["自然光", "攝影棚光", "輪廓光", "柔光", "硬光"]:
                        technical_filters["lighting_style"] = tech_type
                    elif tech_type in ["古典", "爵士", "搖滾", "流行", "電子"]:
                        technical_filters["music_genre"] = tech_type
                    elif tech_type in ["男聲", "女聲", "童聲", "合唱", "旁白"]:
                        technical_filters["vocal_style"] = tech_type
                    break
        
        return technical_filters
    
    def _extract_date_range(self, words: List[str]) -> Optional[Tuple[datetime, datetime]]:
        """提取日期範圍"""
        now = datetime.now()
        
        for word in words:
            if word in self.time_keywords:
                days_ago = self.time_keywords[word]
                start_date = now - timedelta(days=days_ago)
                return (start_date, now)
        
        # 檢查具體日期格式
        date_patterns = [
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',
            r'(\d{4})-(\d{1,2})-(\d{1,2})',
            r'(\d{1,2})/(\d{1,2})/(\d{4})'
        ]
        
        query_text = ' '.join(words)
        for pattern in date_patterns:
            matches = re.findall(pattern, query_text)
            if matches:
                try:
                    if len(matches[0]) == 3:
                        year, month, day = map(int, matches[0])
                        target_date = datetime(year, month, day)
                        return (target_date, target_date + timedelta(days=1))
                except ValueError:
                    continue
        
        return None
    
    def _extract_sort_criteria(self, words: List[str]) -> Optional[Tuple[str, str]]:
        """提取排序條件"""
        sort_by = "relevance"
        sort_order = "desc"
        
        # 檢查排序關鍵字
        for word in words:
            if word in self.sort_keywords:
                sort_by = self.sort_keywords[word]
                break
        
        # 檢查排序順序
        if "升序" in words or "從小到大" in words:
            sort_order = "asc"
        elif "降序" in words or "從大到小" in words:
            sort_order = "desc"
        
        return (sort_by, sort_order)
    
    def _get_remaining_keywords(self, words: List[str], criteria: SearchCriteria) -> List[str]:
        """取得剩餘的關鍵字"""
        used_words = set()
        
        # 收集已使用的詞
        for emotion_words in self.emotion_keywords.values():
            used_words.update(emotion_words)
        
        for file_type_words in self.file_type_keywords.values():
            used_words.update(file_type_words)
        
        for category_words in self.category_keywords.values():
            used_words.update(category_words)
        
        for tech_words in self.technical_keywords.values():
            used_words.update(tech_words)
        
        used_words.update(self.time_keywords.keys())
        used_words.update(self.sort_keywords.keys())
        used_words.update(["升序", "降序", "從小到大", "從大到小"])
        
        # 過濾剩餘關鍵字
        remaining = []
        for word in words:
            if (word not in used_words and 
                len(word) > 1 and 
                not word.isdigit() and
                word not in ["的", "了", "在", "是", "有", "和", "與", "或"]):
                remaining.append(word)
        
        return remaining
    
    def get_suggestions(self, partial_query: str, history: List[str] = None) -> List[str]:
        """提供搜尋建議"""
        if not partial_query or len(partial_query) < 2:
            return []
        
        suggestions = []
        partial_query = partial_query.lower()
        
        # 從情緒關鍵字中找建議
        for emotion, keywords in self.emotion_keywords.items():
            for keyword in keywords:
                if keyword.lower().startswith(partial_query):
                    suggestions.append(f"{keyword} (情緒)")
        
        # 從分類關鍵字中找建議
        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                if keyword.lower().startswith(partial_query):
                    suggestions.append(f"{keyword} (分類)")
        
        # 從技術關鍵字中找建議
        for tech_type, keywords in self.technical_keywords.items():
            for keyword in keywords:
                if keyword.lower().startswith(partial_query):
                    suggestions.append(f"{keyword} (技術)")
        
        # 從歷史記錄中找建議
        if history:
            for query in history:
                if partial_query in query.lower():
                    suggestions.append(f"{query} (歷史)")
        
        # 去重並限制數量
        suggestions = list(set(suggestions))
        return suggestions[:10]
    
    def expand_query(self, criteria: SearchCriteria) -> SearchCriteria:
        """擴展查詢條件"""
        expanded_criteria = SearchCriteria(
            keywords=criteria.keywords.copy(),
            emotions=criteria.emotions.copy(),
            file_types=criteria.file_types.copy(),
            categories=criteria.categories.copy(),
            date_range=criteria.date_range,
            technical_filters=criteria.technical_filters.copy(),
            sort_by=criteria.sort_by,
            sort_order=criteria.sort_order,
            exclude_keywords=criteria.exclude_keywords.copy()
        )
        
        # 擴展情緒關鍵字
        for emotion in criteria.emotions:
            if emotion in self.emotion_keywords:
                expanded_criteria.keywords.extend(self.emotion_keywords[emotion])
        
        # 擴展分類關鍵字
        for category in criteria.categories:
            if category in self.category_keywords:
                expanded_criteria.keywords.extend(self.category_keywords[category])
        
        # 擴展檔案類型關鍵字
        for file_type in criteria.file_types:
            if file_type in self.file_type_keywords:
                expanded_criteria.keywords.extend(self.file_type_keywords[file_type])
        
        # 去重
        expanded_criteria.keywords = list(set(expanded_criteria.keywords))
        
        return expanded_criteria


# 自定義例外類別
class SearchError(CrossPlatformError):
    """搜尋相關錯誤"""
    pass


class QueryParseError(SearchError):
    """查詢解析錯誤"""
    pass


# 全域搜尋引擎實例
nl_search_engine = NaturalLanguageSearchEngine()


if __name__ == "__main__":
    # 測試程式
    print("=== 自然語言搜尋引擎測試 ===")
    
    test_queries = [
        "快樂的照片",
        "悲傷的音樂",
        "自然風景圖片",
        "昨天的影片",
        "特寫人物照片",
        "古典音樂 -搖滾",
        '"美麗風景" 今年',
        "溫馨家庭照片 按時間排序"
    ]
    
    for query in test_queries:
        print(f"\n查詢: {query}")
        criteria = nl_search_engine.parse_query(query)
        print(f"關鍵字: {criteria.keywords}")
        print(f"情緒: {criteria.emotions}")
        print(f"檔案類型: {criteria.file_types}")
        print(f"分類: {criteria.categories}")
        print(f"技術過濾: {criteria.technical_filters}")
        print(f"排序: {criteria.sort_by} ({criteria.sort_order})")
        if criteria.exclude_keywords:
            print(f"排除: {criteria.exclude_keywords}")
    
    # 測試搜尋建議
    print(f"\n搜尋建議 '快': {nl_search_engine.get_suggestions('快')}")
    print(f"搜尋建議 '自然': {nl_search_engine.get_suggestions('自然')}")