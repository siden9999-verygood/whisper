"""
複雜查詢解析器模組
支援多維度過濾條件和複雜查詢語法
"""

import re
import json
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from logging_service import logging_service


class QueryOperator(Enum):
    """查詢操作符"""
    EQUALS = "="
    NOT_EQUALS = "!="
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    REGEX = "regex"
    IN = "in"
    NOT_IN = "not_in"
    BETWEEN = "between"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


class LogicalOperator(Enum):
    """邏輯操作符"""
    AND = "and"
    OR = "or"
    NOT = "not"


@dataclass
class QueryCondition:
    """查詢條件"""
    field: str
    operator: QueryOperator
    value: Any
    logical_op: Optional[LogicalOperator] = None


@dataclass
class QueryGroup:
    """查詢組（用於括號分組）"""
    conditions: List[Union[QueryCondition, 'QueryGroup']]
    logical_op: Optional[LogicalOperator] = None


@dataclass
class ParsedQuery:
    """解析後的查詢"""
    conditions: List[Union[QueryCondition, QueryGroup]]
    sort_fields: List[Dict[str, str]] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    
    def __post_init__(self):
        if self.sort_fields is None:
            self.sort_fields = []


class QueryParser:
    """複雜查詢解析器"""
    
    def __init__(self):
        self.logger = logging_service.get_logger("QueryParser")
        
        # 支援的欄位類型
        self.field_types = {
            'file_name': 'string',
            'file_path': 'string',
            'file_type': 'string',
            'file_size': 'number',
            'creation_date': 'date',
            'modification_date': 'date',
            'transcription': 'text',
            'ai_tags': 'array',
            'ai_category': 'string',
            'ai_description': 'text',
            'duration': 'number',
            'resolution': 'string',
            'format': 'string'
        }
        
        # 操作符映射
        self.operator_mapping = {
            '=': QueryOperator.EQUALS,
            '==': QueryOperator.EQUALS,
            '!=': QueryOperator.NOT_EQUALS,
            '<>': QueryOperator.NOT_EQUALS,
            '>': QueryOperator.GREATER_THAN,
            '<': QueryOperator.LESS_THAN,
            '>=': QueryOperator.GREATER_EQUAL,
            '<=': QueryOperator.LESS_EQUAL,
            'contains': QueryOperator.CONTAINS,
            'not_contains': QueryOperator.NOT_CONTAINS,
            'starts_with': QueryOperator.STARTS_WITH,
            'ends_with': QueryOperator.ENDS_WITH,
            'regex': QueryOperator.REGEX,
            'in': QueryOperator.IN,
            'not_in': QueryOperator.NOT_IN,
            'between': QueryOperator.BETWEEN,
            'is_null': QueryOperator.IS_NULL,
            'is_not_null': QueryOperator.IS_NOT_NULL
        }
        
        # 邏輯操作符映射
        self.logical_mapping = {
            'and': LogicalOperator.AND,
            '&&': LogicalOperator.AND,
            'or': LogicalOperator.OR,
            '||': LogicalOperator.OR,
            'not': LogicalOperator.NOT,
            '!': LogicalOperator.NOT
        }
    
    def parse(self, query: str) -> ParsedQuery:
        """解析查詢字串"""
        try:
            # 預處理查詢
            query = self._preprocess_query(query)
            
            # 提取排序和限制條件
            query, sort_fields, limit, offset = self._extract_modifiers(query)
            
            # 解析主要查詢條件
            conditions = self._parse_conditions(query)
            
            return ParsedQuery(
                conditions=conditions,
                sort_fields=sort_fields,
                limit=limit,
                offset=offset
            )
            
        except Exception as e:
            self.logger.error(f"查詢解析失敗: {str(e)}")
            raise QueryParseError(f"查詢解析失敗: {str(e)}")
    
    def _preprocess_query(self, query: str) -> str:
        """預處理查詢字串"""
        # 移除多餘空白
        query = re.sub(r'\s+', ' ', query.strip())
        
        # 標準化邏輯操作符
        query = re.sub(r'\b(AND|And)\b', 'and', query)
        query = re.sub(r'\b(OR|Or)\b', 'or', query)
        query = re.sub(r'\b(NOT|Not)\b', 'not', query)
        
        return query
    
    def _extract_modifiers(self, query: str) -> tuple:
        """提取排序和限制修飾符"""
        sort_fields = []
        limit = None
        offset = None
        
        # 提取 ORDER BY
        order_match = re.search(r'\bORDER\s+BY\s+(.+?)(?:\s+LIMIT|\s+OFFSET|$)', query, re.IGNORECASE)
        if order_match:
            order_clause = order_match.group(1)
            query = query.replace(order_match.group(0), '')
            
            # 解析排序欄位
            for field_spec in order_clause.split(','):
                field_spec = field_spec.strip()
                if ' ' in field_spec:
                    field, direction = field_spec.rsplit(' ', 1)
                    direction = direction.upper()
                    if direction not in ['ASC', 'DESC']:
                        direction = 'ASC'
                else:
                    field = field_spec
                    direction = 'ASC'
                
                sort_fields.append({'field': field.strip(), 'direction': direction})
        
        # 提取 LIMIT
        limit_match = re.search(r'\bLIMIT\s+(\d+)', query, re.IGNORECASE)
        if limit_match:
            limit = int(limit_match.group(1))
            query = query.replace(limit_match.group(0), '')
        
        # 提取 OFFSET
        offset_match = re.search(r'\bOFFSET\s+(\d+)', query, re.IGNORECASE)
        if offset_match:
            offset = int(offset_match.group(1))
            query = query.replace(offset_match.group(0), '')
        
        return query.strip(), sort_fields, limit, offset
    
    def _parse_conditions(self, query: str) -> List[Union[QueryCondition, QueryGroup]]:
        """解析查詢條件"""
        if not query:
            return []
        
        # 處理括號分組
        return self._parse_expression(query)
    
    def _parse_expression(self, expression: str) -> List[Union[QueryCondition, QueryGroup]]:
        """解析表達式（處理括號和邏輯操作符）"""
        conditions = []
        current_logical_op = None
        
        # 簡化實現：先處理基本條件，後續可以擴展支援複雜括號
        parts = self._split_by_logical_operators(expression)
        
        for i, (part, logical_op) in enumerate(parts):
            if i > 0:
                current_logical_op = logical_op
            
            condition = self._parse_single_condition(part.strip())
            if condition:
                condition.logical_op = current_logical_op
                conditions.append(condition)
        
        return conditions
    
    def _split_by_logical_operators(self, expression: str) -> List[tuple]:
        """按邏輯操作符分割表達式"""
        parts = []
        current_part = ""
        i = 0
        
        while i < len(expression):
            # 檢查邏輯操作符
            found_op = None
            for op_text, op_enum in self.logical_mapping.items():
                if expression[i:].lower().startswith(op_text.lower()):
                    # 確保是完整的單詞（避免部分匹配）
                    if op_text.isalpha():
                        if (i == 0 or not expression[i-1].isalnum()) and \
                           (i + len(op_text) >= len(expression) or not expression[i + len(op_text)].isalnum()):
                            found_op = (op_enum, len(op_text))
                            break
                    else:
                        found_op = (op_enum, len(op_text))
                        break
            
            if found_op:
                op_enum, op_len = found_op
                if current_part.strip():
                    parts.append((current_part.strip(), None))
                current_part = ""
                i += op_len
                
                # 下一個部分將使用這個邏輯操作符
                next_part_start = i
                while next_part_start < len(expression) and expression[next_part_start].isspace():
                    next_part_start += 1
                
                # 找到下一個邏輯操作符或表達式結束
                next_op_pos = len(expression)
                for j in range(next_part_start, len(expression)):
                    for op_text in self.logical_mapping.keys():
                        if expression[j:].lower().startswith(op_text.lower()):
                            if op_text.isalpha():
                                if (j == 0 or not expression[j-1].isalnum()) and \
                                   (j + len(op_text) >= len(expression) or not expression[j + len(op_text)].isalnum()):
                                    next_op_pos = j
                                    break
                            else:
                                next_op_pos = j
                                break
                    if next_op_pos < len(expression):
                        break
                
                next_part = expression[i:next_op_pos].strip()
                if next_part:
                    parts.append((next_part, op_enum))
                
                i = next_op_pos
            else:
                current_part += expression[i]
                i += 1
        
        if current_part.strip():
            parts.append((current_part.strip(), None))
        
        return parts
    
    def _parse_single_condition(self, condition_str: str) -> Optional[QueryCondition]:
        """解析單個條件"""
        condition_str = condition_str.strip()
        if not condition_str:
            return None
        
        # 嘗試匹配各種操作符模式
        patterns = [
            # field operator value
            r'^(\w+)\s*(>=|<=|!=|<>|>|<|=|==)\s*(.+)$',
            # field function(value)
            r'^(\w+)\s+(contains|not_contains|starts_with|ends_with|regex)\s*\(\s*(.+?)\s*\)$',
            # field in (value1, value2, ...)
            r'^(\w+)\s+(in|not_in)\s*\(\s*(.+?)\s*\)$',
            # field between value1 and value2
            r'^(\w+)\s+between\s+(.+?)\s+and\s+(.+)$',
            # field is null/not null
            r'^(\w+)\s+(is_null|is_not_null)$',
            # 簡單的 field:value 格式
            r'^(\w+):(.+)$'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, condition_str, re.IGNORECASE)
            if match:
                return self._create_condition_from_match(match, pattern)
        
        # 如果沒有匹配到任何模式，嘗試作為全文搜尋
        return QueryCondition(
            field='_fulltext',
            operator=QueryOperator.CONTAINS,
            value=condition_str
        )
    
    def _create_condition_from_match(self, match, pattern: str) -> QueryCondition:
        """根據匹配結果創建條件"""
        groups = match.groups()
        
        if 'between' in pattern:
            # BETWEEN 操作
            field = groups[0]
            value1 = self._parse_value(groups[1], field)
            value2 = self._parse_value(groups[2], field)
            return QueryCondition(
                field=field,
                operator=QueryOperator.BETWEEN,
                value=[value1, value2]
            )
        elif 'is_null' in pattern or 'is_not_null' in pattern:
            # NULL 檢查
            field = groups[0]
            operator_str = groups[1].lower()
            return QueryCondition(
                field=field,
                operator=self.operator_mapping[operator_str],
                value=None
            )
        elif 'in' in pattern:
            # IN 操作
            field = groups[0]
            operator_str = groups[1].lower()
            values_str = groups[2]
            values = [self._parse_value(v.strip(), field) for v in values_str.split(',')]
            return QueryCondition(
                field=field,
                operator=self.operator_mapping[operator_str],
                value=values
            )
        elif ':' in pattern:
            # 簡單格式 field:value
            field = groups[0]
            value = self._parse_value(groups[1], field)
            return QueryCondition(
                field=field,
                operator=QueryOperator.CONTAINS,
                value=value
            )
        else:
            # 標準格式 field operator value
            field = groups[0]
            operator_str = groups[1].lower() if len(groups) > 1 else 'contains'
            value_str = groups[2] if len(groups) > 2 else groups[1]
            
            operator = self.operator_mapping.get(operator_str, QueryOperator.CONTAINS)
            value = self._parse_value(value_str, field)
            
            return QueryCondition(
                field=field,
                operator=operator,
                value=value
            )
    
    def _parse_value(self, value_str: str, field: str) -> Any:
        """解析值"""
        value_str = value_str.strip()
        
        # 移除引號
        if (value_str.startswith('"') and value_str.endswith('"')) or \
           (value_str.startswith("'") and value_str.endswith("'")):
            value_str = value_str[1:-1]
        
        field_type = self.field_types.get(field, 'string')
        
        try:
            if field_type == 'number':
                if '.' in value_str:
                    return float(value_str)
                else:
                    return int(value_str)
            elif field_type == 'date':
                return self._parse_date(value_str)
            elif field_type == 'array':
                # 如果是陣列類型，嘗試解析為 JSON
                try:
                    return json.loads(value_str)
                except:
                    return value_str.split(',')
            else:
                return value_str
        except:
            return value_str
    
    def _parse_date(self, date_str: str) -> datetime:
        """解析日期"""
        date_str = date_str.lower().strip()
        
        # 相對日期
        if date_str == 'today':
            return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_str == 'yesterday':
            return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
        elif date_str.endswith('days ago'):
            days = int(date_str.split()[0])
            return datetime.now() - timedelta(days=days)
        elif date_str.endswith('hours ago'):
            hours = int(date_str.split()[0])
            return datetime.now() - timedelta(hours=hours)
        
        # 絕對日期格式
        date_formats = [
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%Y-%m-%d %H:%M:%S',
            '%Y/%m/%d %H:%M:%S',
            '%m/%d/%Y',
            '%d/%m/%Y'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        raise ValueError(f"無法解析日期: {date_str}")
    
    def to_dict(self, parsed_query: ParsedQuery) -> Dict[str, Any]:
        """將解析結果轉換為字典"""
        return {
            'conditions': [self._condition_to_dict(c) for c in parsed_query.conditions],
            'sort_fields': parsed_query.sort_fields,
            'limit': parsed_query.limit,
            'offset': parsed_query.offset
        }
    
    def _condition_to_dict(self, condition: Union[QueryCondition, QueryGroup]) -> Dict[str, Any]:
        """將條件轉換為字典"""
        if isinstance(condition, QueryCondition):
            return {
                'type': 'condition',
                'field': condition.field,
                'operator': condition.operator.value,
                'value': condition.value,
                'logical_op': condition.logical_op.value if condition.logical_op else None
            }
        elif isinstance(condition, QueryGroup):
            return {
                'type': 'group',
                'conditions': [self._condition_to_dict(c) for c in condition.conditions],
                'logical_op': condition.logical_op.value if condition.logical_op else None
            }
    
    def validate_query(self, parsed_query: ParsedQuery) -> List[str]:
        """驗證查詢"""
        errors = []
        
        for condition in parsed_query.conditions:
            if isinstance(condition, QueryCondition):
                # 檢查欄位是否存在
                if condition.field not in self.field_types and condition.field != '_fulltext':
                    errors.append(f"未知的欄位: {condition.field}")
                
                # 檢查操作符是否適用於欄位類型
                field_type = self.field_types.get(condition.field, 'string')
                if not self._is_operator_valid_for_type(condition.operator, field_type):
                    errors.append(f"操作符 {condition.operator.value} 不適用於 {field_type} 類型的欄位 {condition.field}")
        
        return errors
    
    def _is_operator_valid_for_type(self, operator: QueryOperator, field_type: str) -> bool:
        """檢查操作符是否適用於欄位類型"""
        if field_type == 'string' or field_type == 'text':
            return True  # 字串類型支援所有操作符
        elif field_type == 'number':
            return operator in [
                QueryOperator.EQUALS, QueryOperator.NOT_EQUALS,
                QueryOperator.GREATER_THAN, QueryOperator.LESS_THAN,
                QueryOperator.GREATER_EQUAL, QueryOperator.LESS_EQUAL,
                QueryOperator.BETWEEN, QueryOperator.IN, QueryOperator.NOT_IN,
                QueryOperator.IS_NULL, QueryOperator.IS_NOT_NULL
            ]
        elif field_type == 'date':
            return operator in [
                QueryOperator.EQUALS, QueryOperator.NOT_EQUALS,
                QueryOperator.GREATER_THAN, QueryOperator.LESS_THAN,
                QueryOperator.GREATER_EQUAL, QueryOperator.LESS_EQUAL,
                QueryOperator.BETWEEN, QueryOperator.IS_NULL, QueryOperator.IS_NOT_NULL
            ]
        elif field_type == 'array':
            return operator in [
                QueryOperator.CONTAINS, QueryOperator.NOT_CONTAINS,
                QueryOperator.IN, QueryOperator.NOT_IN,
                QueryOperator.IS_NULL, QueryOperator.IS_NOT_NULL
            ]
        
        return False


class QueryParseError(Exception):
    """查詢解析錯誤"""
    pass


# 全域查詢解析器實例
query_parser = QueryParser()


if __name__ == "__main__":
    # 測試程式
    parser = QueryParser()
    
    test_queries = [
        'file_name contains "test" and file_size > 1000',
        'ai_category = "音樂" or ai_category = "影片"',
        'creation_date > "2024-01-01" and file_type in ("mp3", "wav")',
        'transcription contains "重要" and duration between 60 and 300',
        'file_name:"報告" and creation_date > "7 days ago"',
        'ai_tags contains("會議") and file_size > 5000000 ORDER BY creation_date DESC LIMIT 10'
    ]
    
    for query in test_queries:
        print(f"\n查詢: {query}")
        try:
            result = parser.parse(query)
            print(f"解析結果: {parser.to_dict(result)}")
            
            errors = parser.validate_query(result)
            if errors:
                print(f"驗證錯誤: {errors}")
            else:
                print("驗證通過")
        except Exception as e:
            print(f"解析失敗: {e}")