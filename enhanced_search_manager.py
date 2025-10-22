"""
增強搜尋管理器模組
整合自然語言搜尋和媒體資料搜尋功能
"""

import time
import csv
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime
import re

from platform_adapter import CrossPlatformError, platform_adapter
from config_service import config_service
from logging_service import logging_service
from natural_language_search import (
    NaturalLanguageSearchEngine, SearchCriteria, SearchResult, SearchResults,
    nl_search_engine
)
from query_parser import query_parser, ParsedQuery, QueryCondition, QueryOperator, LogicalOperator

# 嘗試導入 pandas，如果沒有則使用 csv 模組
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None


@dataclass
class SearchOptions:
    """搜尋選項配置"""
    max_results: int = 100
    enable_fuzzy_search: bool = True
    enable_auto_suggestions: bool = True
    enable_faceted_search: bool = True
    relevance_threshold: float = 0.1
    search_timeout: int = 30  # seconds


class EnhancedSearchManager:
    """增強的媒體搜尋管理器"""
    
    def __init__(self):
        self.config = config_service.get_config()
        self.logger = logging_service.get_logger("EnhancedSearchManager")
        self.nl_engine = nl_search_engine
        
        # 搜尋資料
        self.media_data: List[Dict] = []
        self.search_index: Dict[str, List[int]] = {}
        self.search_history: List[str] = []
        
        # 快取
        self.search_cache: Dict[str, SearchResults] = {}
        self.cache_max_size = 100
        
        # 載入資料
        self._load_media_data()
        self._build_search_index()
    
    def _load_media_data(self) -> None:
        """載入媒體資料"""
        processed_folder = self.config.processed_folder
        if not processed_folder:
            self.logger.warning("未設定已處理資料夾路徑")
            return
        
        csv_path = Path(processed_folder) / "媒體入庫資訊.csv"
        if not csv_path.exists():
            self.logger.warning(f"媒體資料檔案不存在: {csv_path}")
            # 暫時跳過，不阻塞程式啟動
            self.media_data = []
            return
        
        try:
            if HAS_PANDAS:
                # 使用 pandas 讀取
                df = pd.read_csv(csv_path, keep_default_na=False)
                # 移除完全空白的列（避免因為 CSV 尾端空白行導致多 +1 筆）
                if not df.empty:
                    try:
                        df = df[~(df.apply(lambda r: all((str(v).strip() == '' for v in r)), axis=1))]
                    except Exception:
                        pass
                self.media_data = df.to_dict('records')
            else:
                # 使用 csv 模組讀取
                self.media_data = []
                with open(csv_path, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # 跳過完全空白的列
                        if row is None:
                            continue
                        try:
                            if all((str(v).strip() == '' for v in row.values())):
                                continue
                        except Exception:
                            pass
                        self.media_data.append(row)
            
            self.logger.info(f"載入了 {len(self.media_data)} 筆媒體資料")
            
        except Exception as e:
            self.logger.error(f"載入媒體資料失敗: {str(e)}")
            self.media_data = []
    
    def _build_search_index(self) -> None:
        """建立搜尋索引"""
        if not self.media_data:
            return
        
        self.search_index = {}
        
        # 定義要索引的欄位
        index_fields = [
            '建議標題', 'AI生成標籤', 'AI生成描述', 'AI生成關鍵字',
            '檔案名稱', '主分類', '子分類', '情緒氛圍', '檔案類型'
        ]
        
        for i, record in enumerate(self.media_data):
            # 合併所有可搜尋的文字
            searchable_text = []
            for field in index_fields:
                value = record.get(field, '')
                if value:
                    searchable_text.append(str(value))
            
            full_text = ' '.join(searchable_text).lower()
            
            # 分詞並建立索引
            words = re.split(r'[\s\u3000-\u303f\uff00-\uffef,，、。！？；：]+', full_text)
            words = [word.strip() for word in words if word.strip() and len(word.strip()) > 1]
            
            for word in words:
                if word not in self.search_index:
                    self.search_index[word] = []
                self.search_index[word].append(i)
        
        self.logger.info(f"建立了 {len(self.search_index)} 個索引詞")
    
    def search(self, query: str, options: SearchOptions = None) -> SearchResults:
        """執行搜尋"""
        start_time = time.time()
        
        if not query or not query.strip():
            return SearchResults(
                results=[],
                total_count=0,
                query=query,
                execution_time=0.0,
                suggestions=[]
            )
        
        query = query.strip()
        
        # 檢查快取
        cache_key = f"{query}_{hash(str(options))}"
        if cache_key in self.search_cache:
            cached_result = self.search_cache[cache_key]
            cached_result.execution_time = time.time() - start_time
            return cached_result
        
        if options is None:
            options = SearchOptions()
        
        self.logger.debug(f"執行搜尋: {query}")
        
        # 解析自然語言查詢
        criteria = self.nl_engine.parse_query(query)
        
        # 執行搜尋
        results = self._execute_search(criteria, options)
        
        # 排序結果
        results = self._rank_results(results, criteria, query)
        
        # 限制結果數量
        if len(results) > options.max_results:
            results = results[:options.max_results]
        
        # 生成建議
        suggestions = []
        if options.enable_auto_suggestions:
            suggestions = self._generate_suggestions(query, criteria)
        
        # 生成分面統計
        facets = {}
        if options.enable_faceted_search:
            facets = self._generate_facets(results)
        
        # 建立搜尋結果
        search_results = SearchResults(
            results=results,
            total_count=len(results),
            query=query,
            execution_time=time.time() - start_time,
            suggestions=suggestions,
            facets=facets
        )
        
        # 加入快取
        self._add_to_cache(cache_key, search_results)
        
        # 記錄搜尋歷史
        self._add_to_history(query)
        
        self.logger.info(f"搜尋完成: {len(results)} 個結果，耗時 {search_results.execution_time:.3f}s")
        
        return search_results
    
    def _execute_search(self, criteria: SearchCriteria, options: SearchOptions) -> List[SearchResult]:
        """執行實際搜尋"""
        if not self.media_data:
            return []
        
        candidate_indices = set()
        
        # 基於關鍵字搜尋
        if criteria.keywords:
            for keyword in criteria.keywords:
                keyword_lower = keyword.lower()
                
                # 精確匹配
                if keyword_lower in self.search_index:
                    candidate_indices.update(self.search_index[keyword_lower])
                
                # 模糊匹配
                if options.enable_fuzzy_search:
                    for index_word in self.search_index:
                        if (keyword_lower in index_word or 
                            index_word in keyword_lower or
                            self._calculate_similarity(keyword_lower, index_word) > 0.7):
                            candidate_indices.update(self.search_index[index_word])
        else:
            # 如果沒有關鍵字，搜尋所有記錄
            candidate_indices = set(range(len(self.media_data)))
        
        # 過濾結果
        filtered_results = []
        for idx in candidate_indices:
            if idx >= len(self.media_data):
                continue
                
            record = self.media_data[idx]
            
            # 應用過濾條件
            if not self._matches_criteria(record, criteria):
                continue
            
            # 計算相關性分數
            relevance_score = self._calculate_relevance(record, criteria)
            
            if relevance_score < options.relevance_threshold:
                continue
            
            # 建立搜尋結果
            result = self._create_search_result(record, relevance_score, criteria)
            filtered_results.append(result)
        
        return filtered_results
    
    def _matches_criteria(self, record: Dict, criteria: SearchCriteria) -> bool:
        """檢查記錄是否符合搜尋條件"""
        # 檢查檔案類型
        if criteria.file_types:
            record_type = record.get('檔案類型', '')
            if record_type not in criteria.file_types:
                return False
        
        # 檢查分類
        if criteria.categories:
            main_category = record.get('主分類', '')
            sub_category = record.get('子分類', '')
            
            category_match = False
            for category in criteria.categories:
                if category in main_category or category in sub_category:
                    category_match = True
                    break
            
            if not category_match:
                return False
        
        # 檢查情緒
        if criteria.emotions:
            record_mood = record.get('情緒氛圍', '')
            if record_mood not in criteria.emotions:
                return False
        
        # 檢查技術過濾條件
        if criteria.technical_filters:
            tech_analysis = record.get('AI技術分析', '{}')
            try:
                import json
                tech_data = json.loads(tech_analysis) if tech_analysis else {}
                
                for tech_key, tech_value in criteria.technical_filters.items():
                    if tech_data.get(tech_key) != tech_value:
                        return False
            except:
                pass
        
        # 檢查排除關鍵字
        if criteria.exclude_keywords:
            searchable_fields = [
                '建議標題', 'AI生成標籤', 'AI生成描述', 
                'AI生成關鍵字', '檔案名稱'
            ]
            
            full_text = ' '.join([
                str(record.get(field, '')) for field in searchable_fields
            ]).lower()
            
            for exclude_word in criteria.exclude_keywords:
                if exclude_word.lower() in full_text:
                    return False
        
        # 檢查日期範圍
        if criteria.date_range:
            processing_date = record.get('處理日期', '')
            if processing_date:
                try:
                    from datetime import datetime
                    record_date = datetime.strptime(processing_date, '%Y-%m-%d %H:%M:%S')
                    start_date, end_date = criteria.date_range
                    
                    if not (start_date <= record_date <= end_date):
                        return False
                except:
                    pass
        
        return True
    
    def _calculate_relevance(self, record: Dict, criteria: SearchCriteria) -> float:
        """計算相關性分數"""
        score = 0.0
        
        # 關鍵字匹配分數
        if criteria.keywords:
            searchable_fields = {
                '建議標題': 3.0,      # 標題權重最高
                'AI生成關鍵字': 2.5,   # 關鍵字權重次之
                'AI生成標籤': 2.0,     # 標籤權重
                'AI生成描述': 1.5,     # 描述權重
                '檔案名稱': 1.0        # 檔案名權重最低
            }
            
            for field, weight in searchable_fields.items():
                field_value = str(record.get(field, '')).lower()
                
                for keyword in criteria.keywords:
                    keyword_lower = keyword.lower()
                    
                    # 精確匹配
                    if keyword_lower in field_value:
                        score += weight * 2.0
                    
                    # 部分匹配
                    elif any(word in field_value for word in keyword_lower.split()):
                        score += weight * 1.0
        
        # 分類匹配分數
        if criteria.categories:
            main_category = record.get('主分類', '')
            sub_category = record.get('子分類', '')
            
            for category in criteria.categories:
                if category == main_category:
                    score += 2.0
                elif category == sub_category:
                    score += 1.5
                elif category in main_category or category in sub_category:
                    score += 1.0
        
        # 情緒匹配分數
        if criteria.emotions:
            record_mood = record.get('情緒氛圍', '')
            if record_mood in criteria.emotions:
                score += 1.5
        
        # 檔案類型匹配分數
        if criteria.file_types:
            record_type = record.get('檔案類型', '')
            if record_type in criteria.file_types:
                score += 1.0
        
        # 技術條件匹配分數
        if criteria.technical_filters:
            tech_analysis = record.get('AI技術分析', '{}')
            try:
                import json
                tech_data = json.loads(tech_analysis) if tech_analysis else {}
                
                for tech_key, tech_value in criteria.technical_filters.items():
                    if tech_data.get(tech_key) == tech_value:
                        score += 1.0
            except:
                pass
        
        # 正規化分數
        max_possible_score = len(criteria.keywords) * 3.0 + len(criteria.categories) * 2.0 + \
                           len(criteria.emotions) * 1.5 + len(criteria.file_types) * 1.0 + \
                           len(criteria.technical_filters) * 1.0
        
        if max_possible_score > 0:
            score = score / max_possible_score
        
        return min(score, 1.0)
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """計算字串相似度"""
        if not str1 or not str2:
            return 0.0
        
        # 簡單的 Jaccard 相似度
        set1 = set(str1)
        set2 = set(str2)
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def _create_search_result(self, record: Dict, relevance_score: float, 
                            criteria: SearchCriteria) -> SearchResult:
        """建立搜尋結果物件"""
        # 找出匹配的欄位
        matched_fields = []
        searchable_fields = ['建議標題', 'AI生成標籤', 'AI生成描述', 'AI生成關鍵字']
        
        for field in searchable_fields:
            field_value = str(record.get(field, '')).lower()
            for keyword in criteria.keywords:
                if keyword.lower() in field_value:
                    matched_fields.append(field)
                    break
        
        # 取得縮圖路徑
        thumbnail_path = None
        file_path = record.get('本地完整路徑', '')
        if file_path and record.get('檔案類型') == '圖片':
            thumbnail_path = file_path  # 可以後續實現縮圖生成
        
        return SearchResult(
            file_id=record.get('檔案ID', ''),
            title=record.get('建議標題', ''),
            file_type=record.get('檔案類型', ''),
            file_path=file_path,
            thumbnail_path=thumbnail_path,
            relevance_score=relevance_score,
            metadata=record,
            matched_fields=matched_fields
        )
    
    def _rank_results(self, results: List[SearchResult], criteria: SearchCriteria, 
                     query: str) -> List[SearchResult]:
        """排序搜尋結果"""
        if criteria.sort_by == "relevance":
            # 按相關性排序
            results.sort(key=lambda x: x.relevance_score, 
                        reverse=(criteria.sort_order == "desc"))
        elif criteria.sort_by == "date":
            # 按日期排序
            results.sort(key=lambda x: x.metadata.get('處理日期', ''), 
                        reverse=(criteria.sort_order == "desc"))
        elif criteria.sort_by == "name":
            # 按名稱排序
            results.sort(key=lambda x: x.title or x.metadata.get('檔案名稱', ''), 
                        reverse=(criteria.sort_order == "desc"))
        elif criteria.sort_by == "type":
            # 按類型排序
            results.sort(key=lambda x: x.file_type, 
                        reverse=(criteria.sort_order == "desc"))
        
        return results
    
    def _generate_suggestions(self, query: str, criteria: SearchCriteria) -> List[str]:
        """生成搜尋建議"""
        suggestions = []
        
        # 從自然語言引擎取得建議
        nl_suggestions = self.nl_engine.get_suggestions(query, self.search_history)
        suggestions.extend(nl_suggestions)
        
        # 基於搜尋歷史的建議
        for history_query in self.search_history[-10:]:  # 最近 10 個查詢
            if query.lower() in history_query.lower() and history_query != query:
                suggestions.append(f"{history_query} (歷史)")
        
        # 基於現有資料的建議
        if len(query) >= 2:
            for word in self.search_index:
                if query.lower() in word and word != query.lower():
                    suggestions.append(f"{word} (資料)")
        
        # 去重並限制數量
        suggestions = list(set(suggestions))
        return suggestions[:10]
    
    def _generate_facets(self, results: List[SearchResult]) -> Dict[str, Dict[str, int]]:
        """生成分面搜尋統計"""
        facets = {
            "檔案類型": {},
            "主分類": {},
            "情緒氛圍": {}
        }
        
        for result in results:
            metadata = result.metadata
            
            # 檔案類型統計
            file_type = metadata.get('檔案類型', '未知')
            facets["檔案類型"][file_type] = facets["檔案類型"].get(file_type, 0) + 1
            
            # 主分類統計
            main_category = metadata.get('主分類', '未知')
            facets["主分類"][main_category] = facets["主分類"].get(main_category, 0) + 1
            
            # 情緒統計
            mood = metadata.get('情緒氛圍', '未知')
            facets["情緒氛圍"][mood] = facets["情緒氛圍"].get(mood, 0) + 1
        
        return facets
    
    def _add_to_cache(self, key: str, results: SearchResults) -> None:
        """加入搜尋快取"""
        if len(self.search_cache) >= self.cache_max_size:
            # 移除最舊的快取項目
            oldest_key = next(iter(self.search_cache))
            del self.search_cache[oldest_key]
        
        self.search_cache[key] = results
    
    def _add_to_history(self, query: str) -> None:
        """加入搜尋歷史"""
        if query not in self.search_history:
            self.search_history.append(query)
            
            # 限制歷史記錄數量
            if len(self.search_history) > 50:
                self.search_history = self.search_history[-50:]
    
    def get_search_history(self) -> List[str]:
        """取得搜尋歷史"""
        return self.search_history.copy()
    
    def clear_search_history(self) -> None:
        """清除搜尋歷史"""
        self.search_history.clear()
    
    def clear_cache(self) -> None:
        """清除搜尋快取"""
        self.search_cache.clear()
    
    def reload_data(self) -> None:
        """重新載入媒體資料"""
        self._load_media_data()
        self._build_search_index()
        self.clear_cache()
        self.logger.info("媒體資料已重新載入")
    
    def get_statistics(self) -> Dict[str, Any]:
        """取得搜尋統計資訊"""
        return {
            "total_records": len(self.media_data),
            "index_words": len(self.search_index),
            "search_history_count": len(self.search_history),
            "cache_size": len(self.search_cache)
        }
    
    def advanced_search(self, query_dict: Dict[str, Any], options: SearchOptions = None) -> SearchResults:
        """進階搜尋功能"""
        start_time = time.time()
        
        if options is None:
            options = SearchOptions()
        
        self.logger.debug(f"執行進階搜尋: {query_dict}")
        
        # 建立進階搜尋條件
        criteria = self._build_advanced_criteria(query_dict)
        
        # 執行搜尋
        results = self._execute_search(criteria, options)
        
        # 排序結果
        results = self._rank_results(results, criteria, str(query_dict))
        
        # 限制結果數量
        if len(results) > options.max_results:
            results = results[:options.max_results]
        
        # 生成建議
        suggestions = []
        if options.enable_auto_suggestions:
            suggestions = self._generate_advanced_suggestions(query_dict)
        
        # 生成分面統計
        facets = {}
        if options.enable_faceted_search:
            facets = self._generate_facets(results)
        
        # 建立搜尋結果
        search_results = SearchResults(
            results=results,
            total_count=len(results),
            query=str(query_dict),
            execution_time=time.time() - start_time,
            suggestions=suggestions,
            facets=facets
        )
        
        self.logger.info(f"進階搜尋完成: {len(results)} 個結果，耗時 {search_results.execution_time:.3f}s")
        
        return search_results
    
    def _build_advanced_criteria(self, query_dict: Dict[str, Any]) -> SearchCriteria:
        """建立進階搜尋條件"""
        criteria = SearchCriteria(
            keywords=[],
            emotions=[],
            file_types=[],
            categories=[],
            technical_filters={},
            exclude_keywords=[],
            date_range=None,
            sort_by="relevance",
            sort_order="desc"
        )
        
        # 處理關鍵字
        if 'keywords' in query_dict:
            if isinstance(query_dict['keywords'], str):
                criteria.keywords = [query_dict['keywords']]
            else:
                criteria.keywords = query_dict['keywords']
        
        # 處理檔案類型
        if 'file_types' in query_dict:
            criteria.file_types = query_dict['file_types']
        
        # 處理分類
        if 'categories' in query_dict:
            criteria.categories = query_dict['categories']
        
        # 處理情緒
        if 'emotions' in query_dict:
            criteria.emotions = query_dict['emotions']
        
        # 處理日期範圍
        if 'date_from' in query_dict or 'date_to' in query_dict:
            from datetime import datetime
            date_from = query_dict.get('date_from')
            date_to = query_dict.get('date_to')
            
            if isinstance(date_from, str):
                date_from = datetime.fromisoformat(date_from)
            if isinstance(date_to, str):
                date_to = datetime.fromisoformat(date_to)
            
            if date_from or date_to:
                criteria.date_range = (date_from, date_to)
        
        # 處理檔案大小
        if 'min_size' in query_dict or 'max_size' in query_dict:
            criteria.technical_filters['file_size_range'] = (
                query_dict.get('min_size', 0),
                query_dict.get('max_size', float('inf'))
            )
        
        # 處理品質評分
        if 'min_quality' in query_dict:
            criteria.technical_filters['min_quality'] = query_dict['min_quality']
        
        # 處理排除關鍵字
        if 'exclude_keywords' in query_dict:
            criteria.exclude_keywords = query_dict['exclude_keywords']
        
        # 處理排序
        if 'sort_by' in query_dict:
            criteria.sort_by = query_dict['sort_by']
        if 'sort_order' in query_dict:
            criteria.sort_order = query_dict['sort_order']
        
        return criteria
    
    def _generate_advanced_suggestions(self, query_dict: Dict[str, Any]) -> List[str]:
        """生成進階搜尋建議"""
        suggestions = []
        
        # 基於現有資料生成建議
        if not self.media_data:
            return suggestions
        
        # 分析現有資料的分佈
        categories = set()
        emotions = set()
        file_types = set()
        
        for record in self.media_data:
            categories.add(record.get('主分類', ''))
            emotions.add(record.get('情緒氛圍', ''))
            file_types.add(record.get('檔案類型', ''))
        
        # 移除空值
        categories.discard('')
        emotions.discard('')
        file_types.discard('')
        
        # 生成分類建議
        if 'categories' not in query_dict and categories:
            suggestions.extend([f"分類:{cat}" for cat in list(categories)[:3]])
        
        # 生成情緒建議
        if 'emotions' not in query_dict and emotions:
            suggestions.extend([f"情緒:{emotion}" for emotion in list(emotions)[:3]])
        
        # 生成檔案類型建議
        if 'file_types' not in query_dict and file_types:
            suggestions.extend([f"類型:{ftype}" for ftype in list(file_types)[:3]])
        
        return suggestions[:10]
    
    def save_search_template(self, template_name: str, query_dict: Dict[str, Any]) -> bool:
        """儲存搜尋範本"""
        try:
            templates_file = platform_adapter.get_config_dir() / "search_templates.json"
            
            # 載入現有範本
            templates = {}
            if templates_file.exists():
                with open(templates_file, 'r', encoding='utf-8') as f:
                    templates = json.load(f)
            
            # 添加新範本
            templates[template_name] = {
                "query": query_dict,
                "created_at": datetime.now().isoformat(),
                "usage_count": 0
            }
            
            # 儲存範本
            with open(templates_file, 'w', encoding='utf-8') as f:
                json.dump(templates, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"搜尋範本已儲存: {template_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"儲存搜尋範本失敗: {str(e)}")
            return False
    
    def load_search_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """載入搜尋範本"""
        try:
            templates_file = platform_adapter.get_config_dir() / "search_templates.json"
            
            if not templates_file.exists():
                return None
            
            with open(templates_file, 'r', encoding='utf-8') as f:
                templates = json.load(f)
            
            if template_name in templates:
                # 更新使用次數
                templates[template_name]["usage_count"] += 1
                
                with open(templates_file, 'w', encoding='utf-8') as f:
                    json.dump(templates, f, indent=2, ensure_ascii=False)
                
                return templates[template_name]["query"]
            
            return None
            
        except Exception as e:
            self.logger.error(f"載入搜尋範本失敗: {str(e)}")
            return None
    
    def get_search_templates(self) -> Dict[str, Dict]:
        """取得所有搜尋範本"""
        try:
            templates_file = platform_adapter.get_config_dir() / "search_templates.json"
            
            if not templates_file.exists():
                return {}
            
            with open(templates_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            self.logger.error(f"取得搜尋範本失敗: {str(e)}")
            return {}
    
    def delete_search_template(self, template_name: str) -> bool:
        """刪除搜尋範本"""
        try:
            templates_file = platform_adapter.get_config_dir() / "search_templates.json"
            
            if not templates_file.exists():
                return False
            
            with open(templates_file, 'r', encoding='utf-8') as f:
                templates = json.load(f)
            
            if template_name in templates:
                del templates[template_name]
                
                with open(templates_file, 'w', encoding='utf-8') as f:
                    json.dump(templates, f, indent=2, ensure_ascii=False)
                
                self.logger.info(f"搜尋範本已刪除: {template_name}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"刪除搜尋範本失敗: {str(e)}")
            return False
    
    def get_smart_search_suggestions(self, partial_query: str) -> List[str]:
        """取得智能搜尋建議"""
        suggestions = []
        
        if len(partial_query) < 2:
            return suggestions
        
        partial_lower = partial_query.lower()
        
        # 從索引中尋找匹配的詞彙
        matching_words = []
        for word in self.search_index:
            if partial_lower in word:
                matching_words.append(word)
        
        # 按相關性排序
        matching_words.sort(key=lambda x: (
            0 if x.startswith(partial_lower) else 1,  # 開頭匹配優先
            len(x),  # 較短的詞彙優先
            -len(self.search_index[x])  # 出現頻率高的優先
        ))
        
        suggestions.extend(matching_words[:5])
        
        # 從搜尋歷史中尋找匹配
        for history_query in self.search_history:
            if partial_lower in history_query.lower() and history_query not in suggestions:
                suggestions.append(f"{history_query} (歷史)")
        
        # 從範本中尋找匹配
        templates = self.get_search_templates()
        for template_name, template_data in templates.items():
            if partial_lower in template_name.lower():
                suggestions.append(f"{template_name} (範本)")
        
        return suggestions[:10]
    
    def cluster_search_results(self, results: List[SearchResult]) -> Dict[str, List[SearchResult]]:
        """將搜尋結果進行聚類分組"""
        if not results:
            return {}
        
        clusters = {}
        
        # 按檔案類型分組
        type_clusters = {}
        for result in results:
            file_type = result.file_type or "未知"
            if file_type not in type_clusters:
                type_clusters[file_type] = []
            type_clusters[file_type].append(result)
        
        # 按主分類分組
        category_clusters = {}
        for result in results:
            main_category = result.metadata.get('主分類', '未分類')
            if main_category not in category_clusters:
                category_clusters[main_category] = []
            category_clusters[main_category].append(result)
        
        # 按情緒分組
        mood_clusters = {}
        for result in results:
            mood = result.metadata.get('情緒氛圍', '未知')
            if mood not in mood_clusters:
                mood_clusters[mood] = []
            mood_clusters[mood].append(result)
        
        # 選擇最有意義的分組方式
        if len(type_clusters) > 1 and len(type_clusters) <= 5:
            clusters.update({f"類型: {k}": v for k, v in type_clusters.items()})
        elif len(category_clusters) > 1 and len(category_clusters) <= 8:
            clusters.update({f"分類: {k}": v for k, v in category_clusters.items()})
        elif len(mood_clusters) > 1 and len(mood_clusters) <= 6:
            clusters.update({f"情緒: {k}": v for k, v in mood_clusters.items()})
        else:
            # 如果無法有效分組，按相關性分組
            high_relevance = [r for r in results if r.relevance_score > 0.7]
            medium_relevance = [r for r in results if 0.3 <= r.relevance_score <= 0.7]
            low_relevance = [r for r in results if r.relevance_score < 0.3]
            
            if high_relevance:
                clusters["高相關性"] = high_relevance
            if medium_relevance:
                clusters["中等相關性"] = medium_relevance
            if low_relevance:
                clusters["低相關性"] = low_relevance
        
        return clusters
    
    def generate_preview_data(self, result: SearchResult) -> Dict[str, Any]:
        """生成搜尋結果的預覽資料"""
        preview_data = {
            "title": result.title or result.metadata.get('檔案名稱', '未知'),
            "file_type": result.file_type,
            "file_path": result.file_path,
            "relevance_score": result.relevance_score,
            "matched_fields": result.matched_fields,
            "preview_content": None,
            "thumbnail": None,
            "metadata_summary": {},
            "technical_info": {}
        }
        
        # 生成內容預覽
        preview_data["preview_content"] = self._generate_content_preview(result)
        
        # 生成縮圖
        preview_data["thumbnail"] = self._generate_thumbnail(result)
        
        # 生成元資料摘要
        preview_data["metadata_summary"] = self._generate_metadata_summary(result)
        
        # 生成技術資訊
        preview_data["technical_info"] = self._generate_technical_info(result)
        
        return preview_data
    
    def _generate_content_preview(self, result: SearchResult) -> Optional[str]:
        """生成內容預覽"""
        try:
            # 對於文字檔案，讀取前幾行作為預覽
            if result.file_type in ['文字', 'SRT字幕']:
                file_path = Path(result.file_path)
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = []
                        for i, line in enumerate(f):
                            if i >= 5:  # 只讀取前5行
                                break
                            lines.append(line.strip())
                        return '\n'.join(lines)
            
            # 對於其他類型，使用 AI 生成的描述作為預覽
            description = result.metadata.get('AI生成描述', '')
            if description:
                # 限制描述長度
                if len(description) > 200:
                    return description[:200] + "..."
                return description
            
            # 使用關鍵字作為預覽
            keywords = result.metadata.get('AI生成關鍵字', '')
            if keywords:
                return f"關鍵字: {keywords}"
            
            return None
            
        except Exception as e:
            self.logger.error(f"生成內容預覽失敗: {str(e)}")
            return None
    
    def _generate_thumbnail(self, result: SearchResult) -> Optional[str]:
        """生成縮圖路徑"""
        try:
            if result.file_type == '圖片':
                # 對於圖片，直接使用原檔案作為縮圖
                return result.file_path
            elif result.file_type == '影片':
                # 對於影片，嘗試尋找對應的縮圖檔案
                file_path = Path(result.file_path)
                thumbnail_path = file_path.parent / f"{file_path.stem}_thumbnail.jpg"
                if thumbnail_path.exists():
                    return str(thumbnail_path)
                
                # 如果沒有縮圖，可以考慮生成一個
                return self._generate_video_thumbnail(result.file_path)
            
            return None
            
        except Exception as e:
            self.logger.error(f"生成縮圖失敗: {str(e)}")
            return None
    
    def _generate_video_thumbnail(self, video_path: str) -> Optional[str]:
        """為影片生成縮圖"""
        try:
            # 這裡可以使用 ffmpeg 或其他工具生成縮圖
            # 暫時返回 None，實際實現需要額外的依賴
            return None
        except Exception as e:
            self.logger.error(f"生成影片縮圖失敗: {str(e)}")
            return None
    
    def _generate_metadata_summary(self, result: SearchResult) -> Dict[str, str]:
        """生成元資料摘要"""
        summary = {}
        
        # 基本資訊
        if result.metadata.get('檔案大小'):
            summary['檔案大小'] = result.metadata['檔案大小']
        
        if result.metadata.get('處理日期'):
            summary['處理日期'] = result.metadata['處理日期']
        
        if result.metadata.get('主分類'):
            summary['主分類'] = result.metadata['主分類']
        
        if result.metadata.get('子分類'):
            summary['子分類'] = result.metadata['子分類']
        
        if result.metadata.get('情緒氛圍'):
            summary['情緒氛圍'] = result.metadata['情緒氛圍']
        
        # AI 生成的標籤
        if result.metadata.get('AI生成標籤'):
            tags = result.metadata['AI生成標籤']
            if len(tags) > 50:
                tags = tags[:50] + "..."
            summary['標籤'] = tags
        
        return summary
    
    def _generate_technical_info(self, result: SearchResult) -> Dict[str, Any]:
        """生成技術資訊"""
        tech_info = {}
        
        try:
            # 解析 AI 技術分析
            tech_analysis = result.metadata.get('AI技術分析', '{}')
            if tech_analysis:
                import json
                tech_data = json.loads(tech_analysis)
                
                # 提取有用的技術資訊
                if 'quality_score' in tech_data:
                    tech_info['品質評分'] = tech_data['quality_score']
                
                if 'resolution' in tech_data:
                    tech_info['解析度'] = tech_data['resolution']
                
                if 'duration' in tech_data:
                    tech_info['時長'] = tech_data['duration']
                
                if 'format' in tech_data:
                    tech_info['格式'] = tech_data['format']
        
        except Exception as e:
            self.logger.debug(f"解析技術資訊失敗: {str(e)}")
        
        return tech_info
    
    def get_search_analytics(self) -> Dict[str, Any]:
        """取得搜尋分析資料"""
        analytics = {
            "total_searches": len(self.search_history),
            "popular_queries": {},
            "search_patterns": {},
            "performance_metrics": {
                "average_results": 0,
                "cache_hit_rate": 0
            }
        }
        
        # 分析熱門查詢
        query_counts = {}
        for query in self.search_history:
            query_counts[query] = query_counts.get(query, 0) + 1
        
        # 取得前10個熱門查詢
        popular_queries = sorted(query_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        analytics["popular_queries"] = dict(popular_queries)
        
        # 分析搜尋模式
        if self.search_history:
            # 查詢長度分佈
            query_lengths = [len(query.split()) for query in self.search_history]
            analytics["search_patterns"]["average_query_length"] = sum(query_lengths) / len(query_lengths)
            analytics["search_patterns"]["max_query_length"] = max(query_lengths)
            analytics["search_patterns"]["min_query_length"] = min(query_lengths)
        
        return analytics
    
    def complex_query_search(self, query: str, options: SearchOptions = None) -> SearchResults:
        """複雜查詢搜尋"""
        start_time = time.time()
        
        if options is None:
            options = SearchOptions()
        
        try:
            # 解析複雜查詢
            parsed_query = query_parser.parse(query)
            
            # 驗證查詢
            validation_errors = query_parser.validate_query(parsed_query)
            if validation_errors:
                self.logger.warning(f"查詢驗證警告: {validation_errors}")
            
            # 執行查詢
            matching_results = []
            
            for i, item in enumerate(self.media_data):
                if self._evaluate_conditions(item, parsed_query.conditions):
                    result = SearchResult(
                        file_path=item.get('檔案路徑', ''),
                        file_name=item.get('檔案名稱', ''),
                        relevance_score=1.0,  # 複雜查詢的相關性分數可以後續優化
                        metadata=item
                    )
                    matching_results.append(result)
            
            # 應用排序
            if parsed_query.sort_fields:
                matching_results = self._apply_sorting(matching_results, parsed_query.sort_fields)
            
            # 應用分頁
            total_results = len(matching_results)
            if parsed_query.offset:
                matching_results = matching_results[parsed_query.offset:]
            if parsed_query.limit:
                matching_results = matching_results[:parsed_query.limit]
            
            execution_time = time.time() - start_time
            
            # 記錄搜尋歷史
            self._add_to_search_history(query)
            
            results = SearchResults(
                query=query,
                results=matching_results,
                total_results=total_results,
                execution_time=execution_time,
                suggestions=[]
            )
            
            # 快取結果
            cache_key = f"complex:{query}"
            self._cache_results(cache_key, results)
            
            self.logger.info(f"複雜查詢搜尋完成: {len(matching_results)} 個結果 (耗時: {execution_time:.2f}s)")
            return results
            
        except Exception as e:
            self.logger.error(f"複雜查詢搜尋失敗: {str(e)}")
            return SearchResults(
                query=query,
                results=[],
                total_results=0,
                execution_time=time.time() - start_time,
                suggestions=[],
                error=str(e)
            )
    
    def _evaluate_conditions(self, item: Dict, conditions: List) -> bool:
        """評估查詢條件"""
        if not conditions:
            return True
        
        result = True
        current_logical_op = LogicalOperator.AND
        
        for condition in conditions:
            condition_result = self._evaluate_single_condition(item, condition)
            
            if condition.logical_op:
                current_logical_op = condition.logical_op
            
            if current_logical_op == LogicalOperator.AND:
                result = result and condition_result
            elif current_logical_op == LogicalOperator.OR:
                result = result or condition_result
            elif current_logical_op == LogicalOperator.NOT:
                result = result and not condition_result
        
        return result
    
    def _evaluate_single_condition(self, item: Dict, condition) -> bool:
        """評估單個條件"""
        if not isinstance(condition, QueryCondition):
            return True
        
        # 取得欄位值
        field_value = self._get_field_value(item, condition.field)
        
        # 處理 NULL 檢查
        if condition.operator == QueryOperator.IS_NULL:
            return field_value is None or field_value == ""
        elif condition.operator == QueryOperator.IS_NOT_NULL:
            return field_value is not None and field_value != ""
        
        # 如果欄位值為空且不是 NULL 檢查，返回 False
        if field_value is None or field_value == "":
            return False
        
        # 執行比較
        try:
            if condition.operator == QueryOperator.EQUALS:
                return str(field_value).lower() == str(condition.value).lower()
            elif condition.operator == QueryOperator.NOT_EQUALS:
                return str(field_value).lower() != str(condition.value).lower()
            elif condition.operator == QueryOperator.CONTAINS:
                return str(condition.value).lower() in str(field_value).lower()
            elif condition.operator == QueryOperator.NOT_CONTAINS:
                return str(condition.value).lower() not in str(field_value).lower()
            elif condition.operator == QueryOperator.STARTS_WITH:
                return str(field_value).lower().startswith(str(condition.value).lower())
            elif condition.operator == QueryOperator.ENDS_WITH:
                return str(field_value).lower().endswith(str(condition.value).lower())
            elif condition.operator == QueryOperator.REGEX:
                import re
                return bool(re.search(str(condition.value), str(field_value), re.IGNORECASE))
            elif condition.operator == QueryOperator.GREATER_THAN:
                return self._compare_values(field_value, condition.value) > 0
            elif condition.operator == QueryOperator.LESS_THAN:
                return self._compare_values(field_value, condition.value) < 0
            elif condition.operator == QueryOperator.GREATER_EQUAL:
                return self._compare_values(field_value, condition.value) >= 0
            elif condition.operator == QueryOperator.LESS_EQUAL:
                return self._compare_values(field_value, condition.value) <= 0
            elif condition.operator == QueryOperator.IN:
                return field_value in condition.value
            elif condition.operator == QueryOperator.NOT_IN:
                return field_value not in condition.value
            elif condition.operator == QueryOperator.BETWEEN:
                if len(condition.value) == 2:
                    return (self._compare_values(field_value, condition.value[0]) >= 0 and
                           self._compare_values(field_value, condition.value[1]) <= 0)
        except Exception as e:
            self.logger.warning(f"條件評估失敗: {e}")
            return False
        
        return False
    
    def _get_field_value(self, item: Dict, field: str) -> Any:
        """取得欄位值"""
        if field == '_fulltext':
            # 全文搜尋：合併所有文字欄位
            text_fields = ['檔案名稱', '轉錄內容', 'AI標籤', 'AI分類', 'AI描述']
            combined_text = ' '.join(str(item.get(f, '')) for f in text_fields)
            return combined_text
        
        # 欄位名稱映射
        field_mapping = {
            'file_name': '檔案名稱',
            'file_path': '檔案路徑',
            'file_type': '檔案類型',
            'file_size': '檔案大小',
            'creation_date': '建立時間',
            'modification_date': '修改時間',
            'transcription': '轉錄內容',
            'ai_tags': 'AI標籤',
            'ai_category': 'AI分類',
            'ai_description': 'AI描述',
            'duration': '時長',
            'resolution': '解析度',
            'format': '格式'
        }
        
        mapped_field = field_mapping.get(field, field)
        return item.get(mapped_field)
    
    def _compare_values(self, value1: Any, value2: Any) -> int:
        """比較兩個值"""
        try:
            # 嘗試數值比較
            if isinstance(value1, (int, float)) and isinstance(value2, (int, float)):
                return (value1 > value2) - (value1 < value2)
            
            # 嘗試日期比較
            if isinstance(value1, datetime) and isinstance(value2, datetime):
                return (value1 > value2) - (value1 < value2)
            
            # 字串比較
            str1, str2 = str(value1), str(value2)
            return (str1 > str2) - (str1 < str2)
        except:
            return 0
    
    def _apply_sorting(self, results: List[SearchResult], sort_fields: List[Dict]) -> List[SearchResult]:
        """應用排序"""
        def sort_key(result):
            keys = []
            for sort_field in sort_fields:
                field = sort_field['field']
                direction = sort_field['direction']
                
                value = self._get_field_value(result.metadata, field)
                if value is None:
                    value = ""
                
                # 根據排序方向調整
                if direction == 'DESC':
                    if isinstance(value, (int, float)):
                        value = -value
                    elif isinstance(value, str):
                        # 字串反向排序的簡單實現
                        value = ''.join(chr(255 - ord(c)) for c in value[:100])
                
                keys.append(value)
            
            return keys
        
        try:
            return sorted(results, key=sort_key)
        except Exception as e:
            self.logger.warning(f"排序失敗: {e}")
            return results
    
    def get_query_suggestions(self, partial_query: str) -> List[str]:
        """取得查詢建議"""
        suggestions = []
        
        # 欄位建議
        field_names = list(query_parser.field_types.keys())
        for field in field_names:
            if field.startswith(partial_query.lower()):
                suggestions.append(f"{field}:")
        
        # 操作符建議
        operators = ['=', '!=', '>', '<', '>=', '<=', 'contains', 'starts_with', 'ends_with', 'in', 'between']
        for op in operators:
            if op.startswith(partial_query.lower()):
                suggestions.append(op)
        
        # 邏輯操作符建議
        logical_ops = ['and', 'or', 'not']
        for op in logical_ops:
            if op.startswith(partial_query.lower()):
                suggestions.append(op)
        
        # 修飾符建議
        modifiers = ['ORDER BY', 'LIMIT', 'OFFSET']
        for mod in modifiers:
            if mod.lower().startswith(partial_query.lower()):
                suggestions.append(mod)
        
        return suggestions[:10]
    
    def export_search_results(self, results: SearchResults, format: str = 'csv') -> Optional[str]:
        """匯出搜尋結果"""
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if format.lower() == 'csv':
                filename = f"search_results_{timestamp}.csv"
                filepath = platform_adapter.get_temp_dir() / filename
                
                with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                    fieldnames = [
                        '標題', '檔案類型', '檔案路徑', '相關性分數',
                        '主分類', '子分類', '情緒氛圍', 'AI生成標籤',
                        'AI生成描述', '處理日期'
                    ]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for result in results.results:
                        writer.writerow({
                            '標題': result.title,
                            '檔案類型': result.file_type,
                            '檔案路徑': result.file_path,
                            '相關性分數': f"{result.relevance_score:.3f}",
                            '主分類': result.metadata.get('主分類', ''),
                            '子分類': result.metadata.get('子分類', ''),
                            '情緒氛圍': result.metadata.get('情緒氛圍', ''),
                            'AI生成標籤': result.metadata.get('AI生成標籤', ''),
                            'AI生成描述': result.metadata.get('AI生成描述', ''),
                            '處理日期': result.metadata.get('處理日期', '')
                        })
                
                self.logger.info(f"搜尋結果已匯出至: {filepath}")
                return str(filepath)
            
            elif format.lower() == 'json':
                filename = f"search_results_{timestamp}.json"
                filepath = platform_adapter.get_temp_dir() / filename
                
                export_data = {
                    "query": results.query,
                    "total_count": results.total_count,
                    "execution_time": results.execution_time,
                    "export_time": datetime.now().isoformat(),
                    "results": []
                }
                
                for result in results.results:
                    export_data["results"].append({
                        "title": result.title,
                        "file_type": result.file_type,
                        "file_path": result.file_path,
                        "relevance_score": result.relevance_score,
                        "matched_fields": result.matched_fields,
                        "metadata": result.metadata
                    })
                
                import json
                with open(filepath, 'w', encoding='utf-8') as jsonfile:
                    json.dump(export_data, jsonfile, indent=2, ensure_ascii=False)
                
                self.logger.info(f"搜尋結果已匯出至: {filepath}")
                return str(filepath)
            
            else:
                self.logger.error(f"不支援的匯出格式: {format}")
                return None
                
        except Exception as e:
            self.logger.error(f"匯出搜尋結果失敗: {str(e)}")
            return None


# 全域搜尋管理器實例
enhanced_search_manager = EnhancedSearchManager()


if __name__ == "__main__":
    # 測試程式
    print("=== 增強搜尋管理器測試 ===")
    
    # 測試基本搜尋
    results = enhanced_search_manager.search("音樂")
    print(f"搜尋 '音樂' 找到 {results.total_count} 個結果")
    
    # 測試進階搜尋
    advanced_query = {
        "keywords": ["音樂"],
        "file_types": ["音訊"],
        "emotions": ["快樂"]
    }
    advanced_results = enhanced_search_manager.advanced_search(advanced_query)
    print(f"進階搜尋找到 {advanced_results.total_count} 個結果")
    
    # 測試搜尋建議
    suggestions = enhanced_search_manager.get_smart_search_suggestions("音")
    print(f"搜尋建議: {suggestions}")
    
    # 測試統計資訊
    stats = enhanced_search_manager.get_statistics()
    print(f"統計資訊: {stats}")
    
    # 測試搜尋分析
    analytics = enhanced_search_manager.get_search_analytics()
    print(f"搜尋分析: {analytics}")
    
    print("測試完成")


# 全域增強搜尋管理器實例
enhanced_search_manager = EnhancedSearchManager()


if __name__ == "__main__":
    # 測試程式
    print("=== 增強搜尋管理器測試 ===")
    
    stats = enhanced_search_manager.get_statistics()
    print(f"總記錄數: {stats['total_records']}")
    print(f"索引詞數: {stats['index_words']}")
    print(f"搜尋歷史: {stats['search_history_count']}")
    print(f"快取大小: {stats['cache_size']}")
    
    # 測試搜尋
    if stats['total_records'] > 0:
        test_queries = ["圖片", "音樂", "快樂"]
        
        for query in test_queries:
            print(f"\n搜尋: {query}")
            results = enhanced_search_manager.search(query)
            print(f"結果數量: {results.total_count}")
            print(f"執行時間: {results.execution_time:.3f}s")
            
            if results.results:
                print(f"第一個結果: {results.results[0].title}")
                print(f"相關性分數: {results.results[0].relevance_score:.3f}")
    else:
        print("沒有媒體資料可供搜尋")
