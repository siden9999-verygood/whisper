#!/usr/bin/env python3
"""
圖像生成模組 - 完全基於 OkokGo ImageGenerationSection.tsx 架構
增強版：整合智能預處理分析，確保時間分佈均勻和內容多樣化

作者: Kiro AI Assistant
描述: 完全按照 OkokGo 的 ImageGenerationSection.tsx 實作的圖像生成功能
版本: v2.0 - 基於 OkokGo 架構 + 智能預處理分析
"""

import os
import json
import threading
import time
import re
import statistics
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from typing import List, Dict, Any, Tuple
import requests

# 藝術風格選項 (完全基於 OkokGo ART_STYLE_OPTIONS)
ART_STYLE_OPTIONS = [
    {"label": "數位插畫", "value": "digital illustration"},
    {"label": "鉛筆素描", "value": "pencil sketch"},
    {"label": "炭筆畫", "value": "charcoal drawing"},
    {"label": "彩色鉛筆插畫", "value": "colored pencil illustration"},
    {"label": "水彩畫", "value": "watercolor painting"},
    {"label": "水墨畫", "value": "ink wash painting"},
    {"label": "漫畫小說風格", "value": "manga style"},
    {"label": "手繪風格", "value": "hand-drawn style"},
    {"label": "四格漫畫風", "value": "4-panel comic style"},
    {"label": "油畫風格", "value": "oil painting style"},
    {"label": "浮世風格", "value": "ukiyo-e style"},
    {"label": "像素藝術風格", "value": "pixel art style"},
    {"label": "霓虹賽博龐克風", "value": "neon cyberpunk style"},
    {"label": "版畫風格", "value": "printmaking style"},
    {"label": "柔和粉彩插畫", "value": "soft pastel illustration"},
    {"label": "途鴉風格", "value": "graffiti style"}
]

class SmartTranscriptAnalyzer:
    """智能逐字稿分析器 - 確保時間分佈均勻和內容多樣化"""
    
    def __init__(self):
        self.visual_keywords = [
            # 動作關鍵詞
            '走', '跑', '坐', '站', '躺', '跳', '舞', '開門', '關門', '拿', '放', '指', '看',
            # 情緒關鍵詞  
            '笑', '哭', '生氣', '驚訝', '害怕', '開心', '難過', '緊張', '興奮', '沮喪',
            # 環境關鍵詞
            '室內', '室外', '辦公室', '家', '餐廳', '公園', '街道', '車上', '教室', '舞台',
            # 視覺元素
            '燈光', '陽光', '夜晚', '雨', '雪', '火', '水', '樹', '花', '建築', '天空'
        ]
        
        self.scene_change_keywords = [
            '然後', '接著', '後來', '突然', '這時', '同時', '另一邊', '接下來', '現在', '剛才'
        ]
    
    def analyze_and_select_optimal_points(self, transcript_content: str, target_count: int) -> Dict:
        """
        分析逐字稿並選擇最佳時間點
        
        Args:
            transcript_content: SRT 格式的逐字稿內容
            target_count: 目標提示詞數量
            
        Returns:
            包含最佳時間點和對應內容的分析結果
        """
        
        # 步驟1: 解析 SRT 格式
        segments = self._parse_srt_content(transcript_content)
        if not segments:
            return {'error': '無法解析 SRT 格式'}
        
        # 步驟2: 計算總時長和基本統計
        total_duration = self._calculate_total_duration(segments)
        if total_duration <= 0:
            return {'error': '無法計算影片總時長'}
        
        # 步驟3: 分析每個段落的視覺豐富度
        visual_scores = self._calculate_visual_richness_scores(segments)
        
        # 步驟4: 檢測場景變化點
        scene_changes = self._detect_scene_change_points(segments)
        
        # 步驟5: 計算最佳時間分佈點
        optimal_points = self._calculate_optimal_time_distribution(
            segments, total_duration, target_count, visual_scores, scene_changes
        )
        
        # 步驟6: 確保內容多樣性
        diverse_points = self._ensure_content_diversity(optimal_points, segments)
        
        # 步驟7: 生成最終結果
        return {
            'success': True,
            'total_duration': total_duration,
            'total_segments': len(segments),
            'selected_points': diverse_points,
            'distribution_quality': self._evaluate_distribution_quality(diverse_points),
            'diversity_score': self._calculate_overall_diversity_score(diverse_points)
        }
    
    def _parse_srt_content(self, content: str) -> List[Dict]:
        """解析 SRT 格式內容"""
        segments = []
        
        # 更精確的 SRT 格式解析
        lines = content.strip().split('\n')
        i = 0
        
        while i < len(lines):
            # 跳過空行
            while i < len(lines) and lines[i].strip() == '':
                i += 1
            
            if i >= len(lines):
                break
            
            # 跳過序號行
            if lines[i].strip().isdigit():
                i += 1
            
            # 解析時間戳行
            if i < len(lines) and '-->' in lines[i]:
                time_line = lines[i].strip()
                try:
                    start_time, end_time = time_line.split(' --> ')
                    i += 1
                    
                    # 收集字幕文字
                    text_lines = []
                    while i < len(lines) and lines[i].strip() != '' and not lines[i].strip().isdigit():
                        text_lines.append(lines[i].strip())
                        i += 1
                    
                    if text_lines:
                        segments.append({
                            'start_seconds': self._time_string_to_seconds(start_time),
                            'end_seconds': self._time_string_to_seconds(end_time),
                            'start_time_str': start_time[:8],  # HH:MM:SS 格式
                            'text': ' '.join(text_lines)
                        })
                except:
                    i += 1
            else:
                i += 1
        
        return sorted(segments, key=lambda x: x['start_seconds'])
    
    def _time_string_to_seconds(self, time_str: str) -> float:
        """將時間字串轉換為秒數 (HH:MM:SS,mmm)"""
        try:
            time_part, ms_part = time_str.split(',')
            h, m, s = map(int, time_part.split(':'))
            ms = int(ms_part)
            return h * 3600 + m * 60 + s + ms / 1000
        except:
            return 0
    
    def _calculate_total_duration(self, segments: List[Dict]) -> float:
        """計算總時長"""
        if not segments:
            return 0
        return segments[-1]['end_seconds'] - segments[0]['start_seconds']
    
    def _calculate_visual_richness_scores(self, segments: List[Dict]) -> List[float]:
        """計算每個段落的視覺豐富度分數"""
        scores = []
        
        for segment in segments:
            text = segment['text'].lower()
            score = 0
            
            # 視覺關鍵詞加分
            for keyword in self.visual_keywords:
                if keyword in text:
                    score += 1
            
            # 動作詞加分
            action_indicators = ['了', '著', '在', '正在', '開始', '結束', '進行']
            for indicator in action_indicators:
                score += text.count(indicator) * 0.3
            
            # 對話場景減分 (視覺豐富度較低)
            if '說' in text or '講' in text or '問' in text:
                score *= 0.6
            
            # 描述性內容加分
            if len(text) > 30 and not ('說' in text or '講' in text):
                score += 1
            
            # 長度懲罰 (太短不適合視覺化)
            if len(text) < 8:
                score *= 0.3
            
            scores.append(max(score, 0.1))  # 最低分數 0.1
        
        return scores
    
    def _detect_scene_change_points(self, segments: List[Dict]) -> List[int]:
        """檢測場景變化點"""
        scene_changes = []
        
        for i in range(1, len(segments)):
            current_text = segments[i]['text'].lower()
            
            # 檢測場景轉換關鍵詞
            for keyword in self.scene_change_keywords:
                if keyword in current_text:
                    scene_changes.append(i)
                    break
            
            # 檢測時間跳躍 (超過 30 秒的間隔表示可能的場景切換)
            time_gap = segments[i]['start_seconds'] - segments[i-1]['end_seconds']
            if time_gap > 30:
                scene_changes.append(i)
        
        return list(set(scene_changes))  # 去重
    
    def _calculate_optimal_time_distribution(self, segments: List[Dict], total_duration: float, 
                                           target_count: int, visual_scores: List[float], 
                                           scene_changes: List[int]) -> List[Dict]:
        """計算最佳時間分佈點 - 修復版"""
        
        if not segments or total_duration <= 0:
            return []
        
        # 計算理想時間間隔
        ideal_interval = total_duration / target_count
        min_interval = 30  # 最小間隔 30 秒
        
        selected_points = []
        
        print(f"DEBUG: 總時長 {total_duration:.1f} 秒，目標 {target_count} 個點，理想間隔 {ideal_interval:.1f} 秒")
        
        # 將時間軸分成 target_count 個均勻區段
        for segment_index in range(target_count):
            # 計算當前區段的目標時間
            target_time = segment_index * ideal_interval
            
            print(f"DEBUG: 尋找第 {segment_index+1} 個點，目標時間 {target_time:.1f} 秒")
            
            # 在目標時間附近尋找最佳候選點
            best_candidate = None
            best_score = -1
            
            for i, segment in enumerate(segments):
                segment_time = segment['start_seconds']
                
                # 檢查是否已被選中（避免重複）
                already_selected = any(
                    abs(segment_time - point['segment']['start_seconds']) < 5 
                    for point in selected_points
                )
                
                if already_selected:
                    continue
                
                # 計算與目標時間的距離
                distance_from_target = abs(segment_time - target_time)
                
                # 如果距離太遠，跳過
                if distance_from_target > ideal_interval * 0.8:
                    continue
                
                # 計算候選點分數
                score = visual_scores[i] if i < len(visual_scores) else 0.1
                
                # 場景變化點額外加分
                if i in scene_changes:
                    score += 1.0
                
                # 距離目標時間越近越好
                distance_penalty = distance_from_target / ideal_interval
                score *= (1 - distance_penalty * 0.3)
                
                if score > best_score:
                    best_score = score
                    best_candidate = {
                        'segment_index': i,
                        'segment': segment,
                        'score': score,
                        'distance_from_target': distance_from_target
                    }
            
            # 如果沒有找到合適的候選點，選擇最接近的
            if not best_candidate:
                closest_segment = min(segments, 
                                    key=lambda s: abs(s['start_seconds'] - target_time))
                segment_index = segments.index(closest_segment)
                best_candidate = {
                    'segment_index': segment_index,
                    'segment': closest_segment,
                    'score': visual_scores[segment_index] if segment_index < len(visual_scores) else 0.1,
                    'distance_from_target': abs(closest_segment['start_seconds'] - target_time)
                }
            
            selected_points.append(best_candidate)
            print(f"DEBUG: 選中時間 {best_candidate['segment']['start_time_str']} (分數: {best_candidate['score']:.2f})")
        
        return selected_points
    
    def _ensure_content_diversity(self, points: List[Dict], segments: List[Dict]) -> List[Dict]:
        """確保選中點的內容多樣性"""
        
        # 為每個點分析內容特徵
        for point in points:
            text = point['segment']['text'].lower()
            
            point['content_features'] = {
                'has_action': any(word in text for word in ['走', '跑', '坐', '站', '跳', '拿']),
                'has_emotion': any(word in text for word in ['笑', '哭', '生氣', '開心', '驚訝']),
                'is_dialogue': '說' in text or '講' in text or '問' in text,
                'is_description': len(text) > 40 and not ('說' in text or '講' in text),
                'environment_type': self._classify_environment(text),
                'content_length': len(text)
            }
        
        # 檢查並調整過於相似的連續點
        for i in range(1, len(points)):
            current_point = points[i]
            previous_point = points[i-1]
            
            # 計算內容相似度
            similarity = self._calculate_content_similarity(
                current_point.get('content_features', {}), 
                previous_point.get('content_features', {})
            )
            
            # 如果相似度過高，嘗試尋找替代點
            if similarity > 0.75:
                alternative = self._find_alternative_point(
                    segments, current_point, points, i
                )
                if alternative:
                    points[i] = alternative
        
        return points
    
    def _classify_environment(self, text: str) -> str:
        """分類環境類型"""
        indoor_keywords = ['室內', '辦公室', '家', '房間', '教室', '會議室']
        outdoor_keywords = ['室外', '公園', '街道', '戶外', '廣場', '海邊']
        
        if any(keyword in text for keyword in indoor_keywords):
            return 'indoor'
        elif any(keyword in text for keyword in outdoor_keywords):
            return 'outdoor'
        else:
            return 'neutral'
    
    def _calculate_content_similarity(self, features1: Dict, features2: Dict) -> float:
        """計算內容特徵相似度"""
        if not features1 or not features2:
            return 0.0
            
        similarity_score = 0
        total_features = len(features1)
        
        if total_features == 0:
            return 0.0
        
        for key in features1:
            if key in features2:
                if key == 'content_length':
                    # 長度相似度 (差異小於 20 字符視為相似)
                    length_diff = abs(features1[key] - features2[key])
                    if length_diff < 20:
                        similarity_score += 1
                else:
                    # 其他特徵直接比較
                    if features1[key] == features2[key]:
                        similarity_score += 1
        
        return similarity_score / total_features
    
    def _find_alternative_point(self, segments: List[Dict], current_point: Dict, 
                               all_points: List[Dict], current_index: int) -> Dict:
        """尋找替代的時間點"""
        current_time = current_point['segment']['start_seconds']
        search_range = 45  # 在前後 45 秒內搜尋替代點
        
        alternatives = []
        
        for i, segment in enumerate(segments):
            segment_time = segment['start_seconds']
            
            # 檢查是否在搜尋範圍內
            if abs(segment_time - current_time) <= search_range:
                
                # 確保不與其他已選點時間衝突
                time_conflict = False
                for other_point in all_points:
                    if abs(segment_time - other_point['segment']['start_seconds']) < 20:
                        time_conflict = True
                        break
                
                if not time_conflict:
                    # 計算多樣性獎勵分數
                    diversity_bonus = self._calculate_diversity_bonus(
                        segment, all_points[:current_index]
                    )
                    
                    alternatives.append({
                        'segment_index': i,
                        'segment': segment,
                        'score': diversity_bonus,
                        'distance_from_center': abs(segment_time - current_time)
                    })
        
        # 返回多樣性分數最高的替代點
        return max(alternatives, key=lambda x: x['score']) if alternatives else None
    
    def _calculate_diversity_bonus(self, segment: Dict, existing_points: List[Dict]) -> float:
        """計算多樣性獎勵分數"""
        text = segment['text'].lower()
        bonus_score = 1.0
        
        # 與已選點的差異性獎勵
        for point in existing_points:
            existing_text = point['segment']['text'].lower()
            
            # 內容類型差異獎勵
            if ('說' in existing_text) and ('說' not in text):
                bonus_score += 0.4  # 對話 vs 非對話
            
            # 環境類型差異獎勵
            if any(word in existing_text for word in ['室內', '辦公室', '家']) and \
               any(word in text for word in ['室外', '公園', '街道']):
                bonus_score += 0.3  # 室內 vs 室外
            
            # 動作類型差異獎勵
            existing_has_action = any(word in existing_text for word in ['坐', '站', '走'])
            current_has_action = any(word in text for word in ['坐', '站', '走'])
            if existing_has_action != current_has_action:
                bonus_score += 0.2
        
        return bonus_score
    
    def _evaluate_distribution_quality(self, points: List[Dict]) -> Dict:
        """評估時間分佈品質"""
        if len(points) < 2:
            return {'quality': 'poor', 'score': 0, 'uniformity': 0}
        
        # 計算時間間隔
        intervals = []
        for i in range(1, len(points)):
            interval = points[i]['segment']['start_seconds'] - points[i-1]['segment']['start_seconds']
            intervals.append(interval)
        
        # 計算間隔的統計數據
        mean_interval = statistics.mean(intervals)
        std_deviation = statistics.stdev(intervals) if len(intervals) > 1 else 0
        
        # 均勻性分數 (標準差越小越均勻)
        uniformity_score = max(0, 1 - (std_deviation / mean_interval)) if mean_interval > 0 else 0
        
        # 品質評級
        if uniformity_score > 0.85:
            quality = 'excellent'
        elif uniformity_score > 0.7:
            quality = 'good'
        elif uniformity_score > 0.5:
            quality = 'fair'
        else:
            quality = 'poor'
        
        return {
            'quality': quality,
            'score': uniformity_score,
            'uniformity': uniformity_score,
            'mean_interval': mean_interval,
            'std_deviation': std_deviation
        }
    
    def _calculate_overall_diversity_score(self, points: List[Dict]) -> float:
        """計算整體多樣性分數"""
        if not points:
            return 0
        
        diversity_factors = []
        
        # 內容類型多樣性
        content_types = set()
        environment_types = set()
        
        for point in points:
            features = point.get('content_features', {})
            
            # 內容類型分類
            if features.get('is_dialogue'):
                content_types.add('dialogue')
            elif features.get('has_action'):
                content_types.add('action')
            else:
                content_types.add('description')
            
            # 環境類型分類
            environment_types.add(features.get('environment_type', 'neutral'))
        
        # 內容類型多樣性分數
        content_diversity = len(content_types) / 3  # 最多 3 種類型
        diversity_factors.append(content_diversity)
        
        # 環境類型多樣性分數
        environment_diversity = len(environment_types) / 3  # indoor, outdoor, neutral
        diversity_factors.append(environment_diversity)
        
        # 時間分佈均勻性
        distribution_quality = self._evaluate_distribution_quality(points)
        diversity_factors.append(distribution_quality['uniformity'])
        
        return sum(diversity_factors) / len(diversity_factors)

class ImageGenerationOkokGo:
    """圖像生成類 - 完全基於 OkokGo 架構"""
    
    def __init__(self, parent_window):
        self.parent = parent_window
        
        # 狀態變數 (對應 OkokGo 的 useState)
        self.api_key = ""
        self.prompt_model = "gemini-2.5-flash"
        self.image_model = "imagen-3.0-generate-002"
        self.art_style = ART_STYLE_OPTIONS[0]["value"]
        self.number_of_prompts = "20"
        self.number_of_images = "1"
        self.aspect_ratio = "16:9"
        self.person_generation = "allow_adult"
        self.file_name = ""
        self.transcript_content = ""
        
        # 結果狀態
        self.prompts = []
        self.images = []
        self.loading_prompts = False
        self.loading_images = False
        self.status_message = ""
        
        # UI 元件引用
        self.window = None
        self.status_var = None
        self.prompts_display_frame = None
        self.prompt_edit_entries = []
    
    def show_interface(self):
        """顯示圖像生成介面 - 完全基於 OkokGo 架構"""
        # 建立視窗
        self.window = tk.Toplevel(self.parent)
        self.window.title("逐字稿圖片生成器")
        self.window.geometry("1400x900")
        self.window.resizable(True, True)
        
        # 主框架
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 標題
        title_label = ttk.Label(main_frame, text="逐字稿圖片生成器", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # 設定區域
        self.create_settings_section(main_frame)
        
        # 檔案載入區域
        self.create_file_section(main_frame)
        
        # 按鈕和狀態區域
        self.create_button_section(main_frame)
        
        # 提示詞顯示區域
        self.create_prompts_display_section(main_frame)
        
        # 圖片結果顯示區域
        self.create_images_display_section(main_frame)
    
    def create_settings_section(self, parent):
        """建立設定區域"""
        settings_frame = ttk.LabelFrame(parent, text="設定", padding=10)
        settings_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 建立3列網格
        for i in range(3):
            settings_frame.columnconfigure(i, weight=1)
        
        # 第一行：API 金鑰、指令生成模型、圖片生成模型
        ttk.Label(settings_frame, text="API 金鑰").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.api_key_var = tk.StringVar(value=self.api_key)
        api_key_entry = ttk.Entry(settings_frame, textvariable=self.api_key_var, show="*", width=30)
        api_key_entry.grid(row=1, column=0, sticky='ew', padx=5, pady=2)
        
        ttk.Label(settings_frame, text="指令生成模型").grid(row=0, column=1, sticky='w', padx=5, pady=2)
        self.prompt_model_var = tk.StringVar(value=self.prompt_model)
        prompt_model_entry = ttk.Entry(settings_frame, textvariable=self.prompt_model_var, width=30)
        prompt_model_entry.grid(row=1, column=1, sticky='ew', padx=5, pady=2)
        
        ttk.Label(settings_frame, text="圖片生成模型").grid(row=0, column=2, sticky='w', padx=5, pady=2)
        self.image_model_var = tk.StringVar(value=self.image_model)
        image_model_entry = ttk.Entry(settings_frame, textvariable=self.image_model_var, width=30)
        image_model_entry.grid(row=1, column=2, sticky='ew', padx=5, pady=2)
        
        # 第二行：藝術風格、指令數量、每指令圖片數量
        ttk.Label(settings_frame, text="藝術風格").grid(row=2, column=0, sticky='w', padx=5, pady=2)
        self.art_style_var = tk.StringVar(value=ART_STYLE_OPTIONS[0]["label"])
        art_style_combo = ttk.Combobox(settings_frame, textvariable=self.art_style_var,
                                     values=[opt["label"] for opt in ART_STYLE_OPTIONS],
                                     state="readonly", width=27)
        art_style_combo.grid(row=3, column=0, sticky='ew', padx=5, pady=2)
        
        ttk.Label(settings_frame, text="指令數量").grid(row=2, column=1, sticky='w', padx=5, pady=2)
        self.number_of_prompts_var = tk.StringVar(value=self.number_of_prompts)
        prompts_entry = ttk.Entry(settings_frame, textvariable=self.number_of_prompts_var, width=30)
        prompts_entry.grid(row=3, column=1, sticky='ew', padx=5, pady=2)
        
        ttk.Label(settings_frame, text="每指令圖片數量").grid(row=2, column=2, sticky='w', padx=5, pady=2)
        self.number_of_images_var = tk.StringVar(value=self.number_of_images)
        images_combo = ttk.Combobox(settings_frame, textvariable=self.number_of_images_var,
                                  values=["1", "2", "3", "4"], state="readonly", width=27)
        images_combo.grid(row=3, column=2, sticky='ew', padx=5, pady=2)
        
        # 第三行：圖片長寬比、人物生成
        ttk.Label(settings_frame, text="圖片長寬比").grid(row=4, column=0, sticky='w', padx=5, pady=2)
        self.aspect_ratio_var = tk.StringVar(value=self.aspect_ratio)
        aspect_ratio_combo = ttk.Combobox(settings_frame, textvariable=self.aspect_ratio_var,
                                        values=["1:1", "4:3", "16:9", "3:4", "9:16"],
                                        state="readonly", width=27)
        aspect_ratio_combo.grid(row=5, column=0, sticky='ew', padx=5, pady=2)
        
        ttk.Label(settings_frame, text="人物生成").grid(row=4, column=1, sticky='w', padx=5, pady=2)
        self.person_generation_var = tk.StringVar(value=self.person_generation)
        person_generation_combo = ttk.Combobox(settings_frame, textvariable=self.person_generation_var,
                                             values=["不允許", "允許成人", "允許所有"],
                                             state="readonly", width=27)
        person_generation_combo.grid(row=5, column=1, sticky='ew', padx=5, pady=2)
        
        # 綁定人物生成選項的值轉換
        def on_person_generation_change(event):
            mapping = {"不允許": "dont_allow", "允許成人": "allow_adult", "允許所有": "allow_all"}
            self.person_generation = mapping.get(self.person_generation_var.get(), "allow_adult")
        
        person_generation_combo.bind('<<ComboboxSelected>>', on_person_generation_change)
        
        # 初始化時也要設定正確的值
        self.person_generation = "allow_adult"
    
    def create_file_section(self, parent):
        """建立檔案載入區域"""
        file_frame = ttk.LabelFrame(parent, text="逐字稿檔案", padding=10)
        file_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.file_name_var = tk.StringVar()
        self.transcript_content_var = tk.StringVar()
        
        ttk.Button(file_frame, text="選擇檔案", command=self.handle_file_change).pack(side=tk.LEFT)
        self.file_label = ttk.Label(file_frame, text="未選擇檔案")
        self.file_label.pack(side=tk.LEFT, padx=(10, 0))
    
    def create_button_section(self, parent):
        """建立按鈕和狀態區域"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 左側按鈕區域
        left_buttons = ttk.Frame(button_frame)
        left_buttons.pack(side=tk.LEFT)
        
        self.generate_button = ttk.Button(left_buttons, text="生成英文圖片指令", command=self.generate_prompts)
        self.generate_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.generate_images_button = ttk.Button(left_buttons, text="開始生成圖片", command=self.generate_images, state='disabled')
        self.generate_images_button.pack(side=tk.LEFT)
        
        # 右側狀態區域
        self.status_var = tk.StringVar()
        status_label = ttk.Label(button_frame, textvariable=self.status_var, foreground='blue')
        status_label.pack(side=tk.RIGHT)
    
    def create_prompts_display_section(self, parent):
        """建立提示詞顯示區域 - 徹底解決右邊空白問題"""
        self.prompts_display_frame = ttk.LabelFrame(parent, text="編輯指令與時間戳", padding=5)
        self.prompts_display_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 使用 Grid 佈局替代 Pack，確保完全控制空間分配
        self.prompts_display_frame.grid_rowconfigure(0, weight=1)
        self.prompts_display_frame.grid_columnconfigure(0, weight=1)
        
        # 建立滾動區域 - 使用 Grid 佈局
        self.prompts_canvas = tk.Canvas(self.prompts_display_frame, highlightthickness=0)
        self.prompts_scrollbar = ttk.Scrollbar(self.prompts_display_frame, orient="vertical", command=self.prompts_canvas.yview)
        self.prompts_scrollable_frame = ttk.Frame(self.prompts_canvas)
        
        # 配置滾動
        self.prompts_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.prompts_canvas.configure(scrollregion=self.prompts_canvas.bbox("all"))
        )
        
        self.prompts_canvas.create_window((0, 0), window=self.prompts_scrollable_frame, anchor="nw")
        self.prompts_canvas.configure(yscrollcommand=self.prompts_scrollbar.set)
        
        # 使用 Grid 佈局 - 徹底解決空白問題
        self.prompts_canvas.grid(row=0, column=0, sticky="nsew")
        self.prompts_scrollbar.grid(row=0, column=1, sticky="ns")
        
        # 綁定 Canvas 寬度自動調整
        self.prompts_canvas.bind('<Configure>', self._on_canvas_configure)
        
        # 初始化顯示
        self.initial_label = ttk.Label(self.prompts_scrollable_frame, text="請先生成指令", foreground='gray')
        self.initial_label.pack(expand=True)
    
    def _on_canvas_configure(self, event):
        """Canvas 大小變化時自動調整內容寬度"""
        # 讓滾動區域的寬度跟隨 Canvas 寬度
        canvas_width = event.width
        # 更新 canvas window 的寬度
        self.prompts_canvas.itemconfig(self.prompts_canvas.find_all()[0], width=canvas_width)
    
    def create_images_display_section(self, parent):
        """建立圖片結果顯示區域"""
        self.images_display_frame = ttk.LabelFrame(parent, text="生成結果", padding=10)
        self.images_display_frame.pack(fill=tk.BOTH, expand=True)
        
        # 初始化顯示
        self.images_initial_label = ttk.Label(self.images_display_frame, text="請先生成圖片", foreground='gray')
        self.images_initial_label.pack(expand=True)
    
    def handle_file_change(self):
        """處理檔案選擇 - 對應 OkokGo 的 handleFileChange"""
        file_path = filedialog.askopenfilename(
            title="選擇逐字稿檔案",
            filetypes=[("文字檔案", "*.txt"), ("SRT檔案", "*.srt"), ("Markdown檔案", "*.md"), ("所有檔案", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.file_name_var.set(os.path.basename(file_path))
                self.transcript_content_var.set(content)
                self.file_label.config(text=f"已選擇檔案：{os.path.basename(file_path)}")
                
                # 更新狀態
                self.file_name = os.path.basename(file_path)
                self.transcript_content = content
                
            except Exception as e:
                messagebox.showerror("錯誤", f"讀取檔案失敗：{str(e)}")
    
    def generate_prompts(self):
        """生成提示詞 - 對應 OkokGo 的 generatePrompts"""
        # 更新狀態
        self.api_key = self.api_key_var.get()
        self.prompt_model = self.prompt_model_var.get()
        self.image_model = self.image_model_var.get()
        
        # 找到對應的藝術風格值
        selected_label = self.art_style_var.get()
        self.art_style = next((opt["value"] for opt in ART_STYLE_OPTIONS if opt["label"] == selected_label), 
                             ART_STYLE_OPTIONS[0]["value"])
        
        self.number_of_prompts = self.number_of_prompts_var.get()
        self.number_of_images = self.number_of_images_var.get()
        self.aspect_ratio = self.aspect_ratio_var.get()
        
        # 確保人物生成參數使用英文值
        person_mapping = {"不允許": "dont_allow", "允許成人": "allow_adult", "允許所有": "allow_all"}
        self.person_generation = person_mapping.get(self.person_generation_var.get(), "allow_adult")
        
        # 驗證輸入
        if not self.api_key or not self.prompt_model or not self.transcript_content:
            self.status_var.set('請確認已輸入 API 金鑰與模型')
            return
        
        # 重置狀態
        self.loading_prompts = True
        self.status_var.set('')
        self.prompts = []
        self.images = []
        
        # 更新按鈕狀態
        self.generate_button.config(state='disabled', text='指令生成中...')
        
        # 在背景執行緒中生成
        threading.Thread(target=self._generate_prompts_thread, daemon=True).start()
    
    def _generate_prompts_thread(self):
        """生成提示詞的背景執行緒 - 整合智能預處理分析"""
        try:
            # 步驟1: 智能預處理分析
            self.window.after(0, lambda: self.status_var.set('正在分析逐字稿結構...'))
            
            analyzer = SmartTranscriptAnalyzer()
            analysis_result = analyzer.analyze_and_select_optimal_points(
                self.transcript_content, int(self.number_of_prompts)
            )
            
            if not analysis_result.get('success'):
                error_msg = analysis_result.get('error', '預處理分析失敗')
                self.window.after(0, lambda: self.status_var.set(f'分析失敗：{error_msg}'))
                return
            
            # 步驟2: 顯示分析結果
            selected_points = analysis_result['selected_points']
            distribution_quality = analysis_result['distribution_quality']
            diversity_score = analysis_result['diversity_score']
            
            self.window.after(0, lambda: self.status_var.set(
                f'分析完成 - 分佈品質: {distribution_quality["quality"]} | 多樣性: {diversity_score:.2f}'
            ))
            
            # 步驟3: 建立增強版系統提示詞
            print(f"DEBUG: 使用藝術風格: {self.art_style}")
            
            # 調試：顯示傳遞給 AI 的逐字稿內容
            print("DEBUG: 傳遞給 AI 的逐字稿片段：")
            for i, point in enumerate(selected_points[:3]):  # 只顯示前3個
                segment = point['segment']
                print(f"  {i+1}. {segment['start_time_str']} - {segment['text']}")
            
            enhanced_system_prompt = self.create_enhanced_system_prompt(
                self.art_style, selected_points, analysis_result
            )
            
            # 調試：顯示系統提示詞的一部分
            print(f"DEBUG: 系統提示詞長度: {len(enhanced_system_prompt)} 字符")
            print(f"DEBUG: 系統提示詞開頭: {enhanced_system_prompt[:200]}...")
            
            # 步驟4: 準備 API 請求
            self.window.after(0, lambda: self.status_var.set('正在生成圖像提示詞...'))
            
            payload = {
                "contents": [{
                    "role": "user",
                    "parts": [{"text": enhanced_system_prompt}]
                }],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "responseSchema": {
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
                }
            }
            
            # 呼叫 API
            api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.prompt_model}:generateContent?key={self.api_key}"
            
            print(f"DEBUG: 準備調用 API: {api_url}")
            print(f"DEBUG: Payload 大小: {len(str(payload))} 字符")
            
            response = requests.post(
                api_url,
                headers={'Content-Type': 'application/json'},
                json=payload,
                timeout=60
            )
            
            print(f"DEBUG: API 回應狀態碼: {response.status_code}")
            print(f"DEBUG: API 回應內容: {response.text[:500]}...")
            
            if response.status_code == 200:
                result = response.json()
                text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
                
                print(f"DEBUG: 提取的文字長度: {len(text) if text else 0}")
                
                if text:
                    try:
                        parsed_prompts = json.loads(text)
                        print(f"DEBUG: 成功解析 {len(parsed_prompts)} 個提示詞")
                        
                        # 按照 React 版本添加風格後綴
                        # 使用英文值而不是中文標籤
                        selected_label = self.art_style_var.get()
                        art_style_value = next((opt["value"] for opt in ART_STYLE_OPTIONS if opt["label"] == selected_label), 
                                             ART_STYLE_OPTIONS[0]["value"])
                        style_suffix = self.build_style_suffix(art_style_value)
                        self.prompts = []
                        for prompt_item in parsed_prompts:
                            enhanced_prompt = {
                                'timestamp': prompt_item.get('timestamp', ''),
                                'prompt': f"{prompt_item.get('prompt', '')} {style_suffix}".strip(),
                                'zh': prompt_item.get('zh', '')
                            }
                            self.prompts.append(enhanced_prompt)
                        
                        print(f"DEBUG: 已添加風格後綴: {style_suffix}")
                        # 更新 UI
                        self.window.after(0, self.update_prompts_display)
                    except json.JSONDecodeError as je:
                        print(f"DEBUG: JSON 解析錯誤: {je}")
                        print(f"DEBUG: 原始文字: {text}")
                        self.window.after(0, lambda: self.status_var.set(f'JSON 解析錯誤: {str(je)}'))
                else:
                    print("DEBUG: API 回應中沒有文字內容")
                    self.window.after(0, lambda: self.status_var.set('API 回應格式錯誤'))
            else:
                error_msg = f'API 錯誤: {response.status_code} - {response.text}'
                print(f"DEBUG: {error_msg}")
                self.window.after(0, lambda msg=error_msg: self.status_var.set(msg))
                
        except Exception as e:
            error_msg = f'指令生成失敗：{str(e)}'
            print(f"DEBUG: 異常錯誤: {e}")
            import traceback
            traceback.print_exc()
            self.window.after(0, lambda msg=error_msg: self.status_var.set(msg))
        
        finally:
            self.loading_prompts = False
            # 安全地更新按鈕狀態
            try:
                if self.window and self.window.winfo_exists() and hasattr(self, 'generate_button'):
                    self.window.after(0, lambda: self.generate_button.config(state='normal', text='生成英文圖片指令'))
            except:
                pass
    
    def create_enhanced_system_prompt(self, style: str, selected_points: List[Dict], analysis_result: Dict) -> str:
        """完全按照 React 版本的系統提示詞邏輯"""
        
        count = len(selected_points)
        
        # 按照 React 版本構建 transcript 內容
        transcript_segments = []
        for point in selected_points:
            seg = point['segment']
            timestamp = seg['start_time_str'].split(',')[0]  # 只取時間部分，去掉毫秒
            text = seg['text']
            transcript_segments.append(f"{timestamp} {text}")
        
        transcript_text = '\n'.join(transcript_segments)
        
        print(f"DEBUG: 傳遞給 AI 的逐字稿片段：")
        for i, point in enumerate(selected_points, 1):
            seg = point['segment']
            timestamp = seg['start_time_str']
            text = seg['text']
            print(f"  {i}. {timestamp} - {text}")
        
        print(f"DEBUG: 最終傳遞給 AI 的逐字稿:")
        for seg in transcript_segments:
            print(f"  {seg}")
        
        # 完全按照 React 版本的 systemPrompt 函數
        return f"""// ROLE: Visual Director AI
// TASK: Convert a Chinese transcript into {count} distinct, high-quality, English image generation prompts with a CONSISTENT style.
// OUTPUT FORMAT: A single, valid JSON array of {count} objects. No other text.
// JSON Object Schema: {{ "timestamp": "string", "prompt": "string", "zh": "string" }}

// --- RULES ---
// 1. **COVERAGE & DIVERSITY (CRITICAL):**
//    - You MUST analyze the ENTIRE transcript from start to finish.
//    - The {count} prompts MUST represent key moments distributed across the **beginning, middle, and end** of the story.
//    - Ensure maximum **visual and thematic diversity**. Do NOT generate multiple prompts for the same scene or emotional beat.

// 2. **FAITHFULNESS TO SOURCE (CRITICAL):**
//    - The English prompt must accurately reflect the specific actions, objects, and emotions described in the corresponding Chinese transcript segment.
//    - Translate the core meaning and nuance; do not add elements not present in the source text.

// 3. PROMPT LANGUAGE: All 'prompt' values must be in English.

// 4. PROMPT STYLE (MANDATORY):
//    - Do NOT include any style keywords in the prompt itself.
//    - The application will automatically append the user-selected style "{style}" to the end of every prompt.
//    - Strictly FORBIDDEN words: "photograph", "photo of", "realistic", "photorealistic", "4K", "HDR", "film still", "cinematic".

// 5. PROMPT CONTENT:
//    - Construct each prompt using this 6-layer structure:
//      (1) top-tier quality and artistic style,
//      (2) main subject and action,
//      (3) vivid emotions and intricate details,
//      (4) environment and atmosphere,
//      (5) composition, camera or illustration technique, lighting,
//      (6) final resolution or quality keywords.
//    - LOCALIZATION: Feature Taiwanese people and scenes (e.g., "a young Taiwanese woman", "in a Ximending alley").
//    - SAFETY: For sensitive topics, use symbolic or metaphorical imagery (e.g., "shadows representing pressure" instead of direct depiction of conflict). This is crucial to avoid content safety violations.

// 6. CHINESE TRANSLATION:
//    - Each object must include a "zh" field containing a faithful Chinese translation of the English prompt.

// 7. TIMESTAMP:
//    - If the input is SRT, the 'timestamp' value should be the most relevant start time in "HH:MM:SS" format.
//    - If the input is plain text, the 'timestamp' value must be an empty string ("").

// --- EXAMPLE ---
// Input: "00:15:30,100 --> 00:15:33,200\\n他終於走到了故事的結尾..."
// Output object: {{
//   "timestamp": "00:15:30",
//   "prompt": "an award-winning hyperrealistic masterpiece capturing a three-month-old golden retriever puppy leaping mid-air to chase a cherry-red ball, eyes filled with pure joy, playful pink tongue out, soft golden fur shimmering in the warm Taipei sunset, distant trees and white blossoms melting into lush bokeh, low-angle telephoto shot with gentle side light and crisp rim light, 8K resolution with impeccable details.",
//   "zh": "一幅獲獎的超寫實傑作，描繪三個月大的黃金獵犬幼犬躍起追逐鮮紅色皮球，眼神充滿喜悅，俏皮的粉紅舌頭探出，柔軟的金色毛髮在溫暖的台北夕陽下閃耀；遠處的樹木與白花化為柔和散景，低角度長焦鏡頭以輕柔側光與清晰輪廓光呈現，8K 超高解析度捕捉細節。"
// }}

// --- START OF TASK ---
// Analyze the following transcript and generate the JSON output.

Transcript:
{transcript_text}"""

    def build_style_suffix(self, art_style: str) -> str:
        """構建風格後綴 - 按照 React 版本的 buildStyleSuffix 邏輯"""
        style_mappings = {
            'realistic': 'hyperrealistic, photorealistic, ultra-detailed',
            'digital illustration': 'digital illustration, digital art, detailed illustration',
            'anime': 'anime style, manga style, Japanese animation',
            'oil painting': 'oil painting, traditional painting, fine art',
            'watercolor': 'watercolor painting, watercolor art, soft brushstrokes',
            'sketch': 'pencil sketch, hand-drawn, artistic sketch',
            'cartoon': 'cartoon style, animated style, colorful cartoon',
            'abstract': 'abstract art, modern art, artistic interpretation',
            'vintage': 'vintage style, retro aesthetic, classic art',
            'minimalist': 'minimalist design, clean lines, simple composition'
        }
        
        return style_mappings.get(art_style, art_style)
    
    def create_system_prompt(self, style: str, count: str) -> str:
        """建立系統提示詞 - 完全基於 OkokGo 的 systemPrompt"""
        return f"""// ROLE: Visual Director AI
// TASK: Convert a Chinese transcript into {count} distinct, high-quality, English image generation prompts with a CONSISTENT style.
// OUTPUT FORMAT: A single, valid JSON array of {count} objects. No other text.
// JSON Object Schema: {{ "timestamp": "string", "prompt": "string", "zh": "string" }}

// --- RULES ---
// 1. **COVERAGE & DIVERSITY (CRITICAL):**
//    - You MUST analyze the ENTIRE transcript from start to finish.
//    - The {count} prompts MUST represent key moments distributed across the **beginning, middle, and end** of the story.
//    - Ensure maximum **visual and thematic diversity**. Do NOT generate multiple prompts for the same scene or emotional beat.

// 2. **FAITHFULNESS TO SOURCE (CRITICAL):**
//    - The English prompt must accurately reflect the specific actions, objects, and emotions described in the corresponding Chinese transcript segment.
//    - Translate the core meaning and nuance; do not add elements not present in the source text.

// 3. PROMPT LANGUAGE: All 'prompt' values must be in English.

// 4. PROMPT STYLE (MANDATORY):
//    - EVERY prompt must start with the following user-selected artistic style: "{style}". Do NOT use any other style.
//    - Strictly FORBIDDEN words: "photograph", "photo of", "realistic", "photorealistic", "4K", "HDR", "film still", "cinematic".

// 5. PROMPT CONTENT:
//    - Construct each prompt using this 6-layer structure:
//      (1) top-tier quality and artistic style,
//      (2) main subject and action,
//      (3) vivid emotions and intricate details,
//      (4) environment and atmosphere,
//      (5) composition, camera or illustration technique, lighting,
//      (6) final resolution or quality keywords.
//    - LOCALIZATION: Feature Taiwanese people and scenes (e.g., "a young Taiwanese woman", "in a Ximending alley").
//    - SAFETY: For sensitive topics, use symbolic or metaphorical imagery (e.g., "shadows representing pressure" instead of direct depiction of conflict). This is crucial to avoid content safety violations.

// 6. CHINESE EXPLANATION:
//    - Each object must include a "zh" field containing a concise Chinese explanation of the English prompt.

// 7. TIMESTAMP:
//    - If the input is SRT, the 'timestamp' value should be the most relevant start time in "HH:MM:SS" format.
//    - If the input is plain text, the 'timestamp' value must be an empty string ("").

// --- EXAMPLE ---
// Input: "00:15:30,100 --> 00:15:33,200\\n他終於走到了故事的結尾..."
// Output object: {{
//   "timestamp": "00:15:30",
//   "prompt": "{style} an award-winning hyperrealistic masterpiece capturing a three-month-old golden retriever puppy leaping mid-air to chase a cherry-red ball, eyes filled with pure joy, playful pink tongue out, soft golden fur shimmering in the warm Taipei sunset, distant trees and white blossoms melting into lush bokeh, low-angle telephoto shot with gentle side light and crisp rim light, 8K resolution with impeccable details.",
//   "zh": "在炎熱的夏季午後，天空散發柔和又熾熱的陽光，一隻三個月大的黃金獵犬幼犬在綠油油的草地上興奮地追逐著鮮紅色皮球。牠的毛髮被金黃的陽光襯托得閃閃發亮，面容露出純真又雀躍的表情，粉嫩的小舌頭從嘴邊可愛地伸出。遠處樹木與白色野花在散景裡化成朦朧的色彩，整體氛圍洋溢著溫暖的生命力。攝影師採用低角度長焦鏡頭捕捉狗狗騰空的瞬間，並以柔和的側光與清晰的輪廓光勾勒每一根飄逸的毛髮。最終影像以8K解析度呈現，細節豐富無比。"
// }}

// --- START OF TASK ---
// Analyze the following transcript and generate the JSON output."""
    
    def update_prompts_display(self):
        """更新提示詞顯示 - 修復滾動條設計"""
        # 清除初始標籤
        if hasattr(self, 'initial_label'):
            self.initial_label.destroy()
        
        # 清除滾動區域內的現有內容，但保留滾動區域結構
        if hasattr(self, 'prompts_scrollable_frame'):
            for widget in self.prompts_scrollable_frame.winfo_children():
                widget.destroy()
        else:
            # 如果滾動區域不存在，重新建立
            for widget in self.prompts_display_frame.winfo_children():
                widget.destroy()
            self.create_prompts_scroll_area()
        
        if not self.prompts:
            return
        
        # 標題
        title_label = ttk.Label(self.prompts_scrollable_frame, 
                               text=f"編輯指令與時間戳 ({len(self.prompts)} 個指令)", 
                               font=('Arial', 12, 'bold'))
        title_label.pack(pady=(0, 5))
        
        # 建立提示詞編輯項目
        self.prompt_edit_entries = []
        for i, prompt_item in enumerate(self.prompts):
            self.create_prompt_edit_item(self.prompts_scrollable_frame, i, prompt_item)
        
        # 啟用生成圖片按鈕
        if hasattr(self, 'generate_images_button'):
            self.generate_images_button.config(state='normal')
        
        self.status_var.set(f'成功生成 {len(self.prompts)} 個指令')
    
    def create_prompts_scroll_area(self):
        """建立提示詞滾動區域 - 使用 Grid 佈局"""
        # 確保父容器使用 Grid
        self.prompts_display_frame.grid_rowconfigure(0, weight=1)
        self.prompts_display_frame.grid_columnconfigure(0, weight=1)
        
        # 建立滾動區域
        self.prompts_canvas = tk.Canvas(self.prompts_display_frame, highlightthickness=0)
        self.prompts_scrollbar = ttk.Scrollbar(self.prompts_display_frame, orient="vertical", command=self.prompts_canvas.yview)
        self.prompts_scrollable_frame = ttk.Frame(self.prompts_canvas)
        
        self.prompts_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.prompts_canvas.configure(scrollregion=self.prompts_canvas.bbox("all"))
        )
        
        self.prompts_canvas.create_window((0, 0), window=self.prompts_scrollable_frame, anchor="nw")
        self.prompts_canvas.configure(yscrollcommand=self.prompts_scrollbar.set)
        
        # 使用 Grid 佈局 - 徹底解決空白問題
        self.prompts_canvas.grid(row=0, column=0, sticky="nsew")
        self.prompts_scrollbar.grid(row=0, column=1, sticky="ns")
        
        # 綁定 Canvas 寬度自動調整
        self.prompts_canvas.bind('<Configure>', self._on_canvas_configure)
    
    def create_prompt_edit_item(self, parent, index, prompt_item):
        """建立單個提示詞編輯項目 - 緊湊版設計"""
        item_frame = ttk.Frame(parent, relief='solid', padding=5)
        item_frame.pack(fill=tk.X, pady=2, padx=2)
        
        # 標題行 - 更緊湊
        header_frame = ttk.Frame(item_frame)
        header_frame.pack(fill=tk.X, pady=(0, 3))
        
        ttk.Label(header_frame, text=f"指令 {index+1}", font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        
        timestamp_var = tk.StringVar(value=prompt_item.get('timestamp', 'N/A'))
        timestamp_entry = ttk.Entry(header_frame, textvariable=timestamp_var, 
                                  state='readonly', width=10, font=('Arial', 8))
        timestamp_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        ttk.Button(header_frame, text="刪除", 
                  command=lambda: self.delete_prompt_item(index, item_frame)).pack(side=tk.RIGHT)
        
        # 英文提示詞 - 減少高度
        prompt_label = ttk.Label(item_frame, text="英文提示詞:", font=('Arial', 8))
        prompt_label.pack(anchor='w', pady=(0, 2))
        
        prompt_text = tk.Text(item_frame, height=3, wrap=tk.WORD, font=('Arial', 8))
        prompt_text.insert('1.0', prompt_item.get('prompt', ''))
        prompt_text.pack(fill=tk.X, pady=(0, 3))
        
        # 中文說明 - 減少高度，確保內容正確
        zh_label = ttk.Label(item_frame, text="中文說明:", font=('Arial', 8))
        zh_label.pack(anchor='w', pady=(0, 2))
        
        zh_text = tk.Text(item_frame, height=2, wrap=tk.WORD, 
                        bg='#f8f8f8', fg='#333333', state='disabled', font=('Arial', 8))
        zh_text.config(state='normal')
        # 確保中文說明對應正確的英文指令
        zh_content = prompt_item.get('zh', '')
        if not zh_content or zh_content.strip() == '':
            zh_content = f"指令 {index+1} 的中文說明"
        zh_text.insert('1.0', zh_content)
        zh_text.config(state='disabled')
        zh_text.pack(fill=tk.X)
        
        # 儲存引用
        self.prompt_edit_entries.append({
            'frame': item_frame,
            'timestamp': timestamp_var,
            'prompt_text': prompt_text,
            'zh_text': zh_text,
            'index': index
        })
    
    def delete_prompt_item(self, index, frame):
        """刪除提示詞項目 - 對應 OkokGo 的 handleDeletePrompt"""
        result = messagebox.askyesno("確認刪除", f"確定要刪除指令 {index+1} 嗎？")
        if result:
            frame.destroy()
            # 從 prompts 列表中移除
            if 0 <= index < len(self.prompts):
                self.prompts.pop(index)
            # 重新整理編輯項目
            self.prompt_edit_entries = [entry for entry in self.prompt_edit_entries 
                                      if entry['frame'] != frame]
    
    def generate_images(self):
        """生成圖片 - 對應 OkokGo 的 generateImages"""
        if not self.api_key or not self.image_model or not self.prompts:
            return
        
        # 收集當前編輯的提示詞
        current_prompts = []
        for entry in self.prompt_edit_entries:
            if entry['frame'].winfo_exists():
                current_prompts.append({
                    'timestamp': entry['timestamp'].get(),
                    'prompt': entry['prompt_text'].get('1.0', tk.END).strip(),
                    'zh': entry['zh_text'].get('1.0', tk.END).strip()
                })
        
        self.prompts = current_prompts
        
        # 開始生成圖片
        self.loading_images = True
        self.images = []
        self.status_var.set('')
        
        # 在背景執行緒中生成
        threading.Thread(target=self._generate_images_thread, daemon=True).start()
    
    def _generate_images_thread(self):
        """生成圖片的背景執行緒"""
        sample_count = int(self.number_of_images)
        
        for i, prompt_item in enumerate(self.prompts):
            self.window.after(0, lambda i=i: self.status_var.set(f'處理指令 {i + 1} / {len(self.prompts)} ...'))
            
            try:
                urls = []
                
                # 根據設定的圖片生成模型選擇 API 調用方式
                print(f"DEBUG: 使用模型 {self.image_model} 生成圖片 {i+1}")
                print(f"DEBUG: 提示詞: {prompt_item['prompt'][:100]}...")
                
                if 'imagen-4' in self.image_model.lower():
                    # 使用 Google GenAI SDK (Imagen 4.0)
                    try:
                        from google import genai
                        from google.genai import types
                        from PIL import Image
                        from io import BytesIO
                        import base64
                        
                        client = genai.Client(api_key=self.api_key)
                        
                        response = client.models.generate_images(
                            model=self.image_model,
                            prompt=prompt_item['prompt'],
                            config=types.GenerateImagesConfig(
                                number_of_images=sample_count,
                                aspect_ratio=self.aspect_ratio,
                                person_generation=self.person_generation
                            )
                        )
                        
                        for generated_image in response.generated_images:
                            img_buffer = BytesIO()
                            generated_image.image.save(img_buffer, format='PNG')
                            img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
                            urls.append(f"data:image/png;base64,{img_base64}")
                        
                        print(f"DEBUG: Imagen 4.0 成功生成 {len(urls)} 張圖片")
                        
                    except Exception as e:
                        print(f"DEBUG: Imagen 4.0 生成錯誤: {e}")
                
                elif 'imagen-3' in self.image_model.lower():
                    # 使用 Imagen 3.0 API (按照 React 程式碼的邏輯)
                    try:
                        payload = {
                            "instances": [{"prompt": prompt_item['prompt']}],
                            "parameters": {
                                "sampleCount": sample_count,
                                "aspectRatio": self.aspect_ratio,
                                "personGeneration": self.person_generation
                            }
                        }
                        
                        # 使用正確的 Imagen API 端點 (按照 React 程式碼)
                        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.image_model}:predict?key={self.api_key}"
                        
                        response = requests.post(
                            api_url,
                            headers={'Content-Type': 'application/json'},
                            json=payload,
                            timeout=60
                        )
                        
                        print(f"DEBUG: API 回應狀態碼: {response.status_code}")
                        
                        if response.status_code == 200:
                            result = response.json()
                            if 'predictions' in result and len(result['predictions']) > 0:
                                for prediction in result['predictions']:
                                    if 'bytesBase64Encoded' in prediction:
                                        urls.append(f"data:image/png;base64,{prediction['bytesBase64Encoded']}")
                            
                            print(f"DEBUG: Imagen 3.0 成功生成 {len(urls)} 張圖片")
                        else:
                            print(f"DEBUG: API 錯誤: {response.status_code} - {response.text[:200]}")
                    
                    except Exception as e:
                        print(f"DEBUG: Imagen 3.0 生成錯誤: {e}")
                
                elif 'gemini' in self.image_model.lower():
                    # 使用 Gemini 多模態 API (按照 React 程式碼的邏輯)
                    try:
                        import google.generativeai as genai
                        
                        genai.configure(api_key=self.api_key)
                        model = genai.GenerativeModel(self.image_model)
                        
                        response = model.generate_content(
                            prompt_item['prompt'],
                            generation_config=genai.types.GenerationConfig(
                                response_modalities=['TEXT', 'IMAGE']
                            )
                        )
                        
                        if response.candidates and response.candidates[0].content.parts:
                            for part in response.candidates[0].content.parts:
                                if hasattr(part, 'inline_data') and part.inline_data:
                                    urls.append(f"data:image/png;base64,{part.inline_data.data}")
                        
                        print(f"DEBUG: Gemini 多模態成功生成 {len(urls)} 張圖片")
                    
                    except Exception as e:
                        print(f"DEBUG: Gemini 多模態生成錯誤: {e}")
                
                else:
                    # 其他模型或未知模型
                    print(f"DEBUG: 不支援的模型: {self.image_model}")
                    print("DEBUG: 支援的模型: imagen-3.0-generate-002, imagen-4.0-generate-preview-06-06")
                
                # 根據生成結果添加到圖片列表
                if urls:
                    new_item = {
                        "urls": urls,
                        "prompt_preview": prompt_item['prompt'],
                        "status": f"成功生成 {len(urls)} 張圖片"
                    }
                    self.images.append(new_item)
                else:
                    new_item = {
                        "urls": [],
                        "prompt_preview": prompt_item['prompt'],
                        "error": f"指令 {i + 1} 圖片生成失敗"
                    }
                    self.images.append(new_item)
                
            except Exception as e:
                new_item = {"urls": [], "error": f"指令 {i + 1} 圖片生成失敗: {str(e)}"}
                self.images.append(new_item)
            
            # 立即更新UI顯示新生成的圖片
            self.window.after(0, self.update_images_display)
            
            # 延遲避免 API 限制
            if i < len(self.prompts) - 1:
                time.sleep(1.5)
        
        # 最終狀態更新
        self.window.after(0, lambda: self.status_var.set('全部圖片已處理完畢'))
        self.loading_images = False
    
    def update_images_display(self):
        """更新圖片顯示 - 即時顯示新生成的圖片"""
        try:
            # 檢查視窗是否仍然存在
            if not self.window or not self.window.winfo_exists():
                return
            
            # 檢查是否需要初始化顯示區域
            if not hasattr(self, 'images_scroll_frame') or not self.images_scroll_frame.winfo_exists():
                self.init_images_display_area()
            
            if not self.images:
                return
            
            # 只添加新的圖片項目，不清除已有的
            try:
                current_displayed = len(self.images_scroll_frame.winfo_children())
                if current_displayed < 0:
                    current_displayed = 0
            except:
                current_displayed = 0
            
            # 添加新的圖片項目
            for i in range(current_displayed, len(self.images)):
                self.add_single_image_item(i, self.images[i])
                
        except Exception as e:
            print(f"DEBUG: UI 更新錯誤: {e}")
            # 如果 UI 更新失敗，嘗試重新初始化
            try:
                self.init_images_display_area()
                for i, image_item in enumerate(self.images):
                    self.add_single_image_item(i, image_item)
            except Exception as e2:
                print(f"DEBUG: UI 重新初始化也失敗: {e2}")
    
    def init_images_display_area(self):
        """初始化圖片顯示區域"""
        try:
            # 安全地清除現有內容
            if hasattr(self, 'images_display_frame') and self.images_display_frame.winfo_exists():
                for widget in self.images_display_frame.winfo_children():
                    try:
                        widget.destroy()
                    except:
                        pass
        except Exception as e:
            print(f"DEBUG: 清除顯示區域時出錯: {e}")
        
        # 計算成功和失敗的數量
        success_count = sum(1 for img in self.images if 'error' not in img and img.get('urls'))
        error_count = len(self.images) - success_count
        
        # 標題和統計
        header_frame = ttk.Frame(self.images_display_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.title_label = ttk.Label(header_frame, 
                                    text=f"生成結果 (成功: {success_count}, 失敗: {error_count})", 
                                    font=('Arial', 12, 'bold'))
        self.title_label.pack(side=tk.LEFT)
        
        # 批量下載按鈕
        if success_count > 0:
            ttk.Button(header_frame, text="批量下載全部圖片", 
                      command=self.download_all_images).pack(side=tk.RIGHT, padx=(10, 0))
        
        # 建立可滾動的結果區域
        canvas = tk.Canvas(self.images_display_frame, height=400)
        scrollbar = ttk.Scrollbar(self.images_display_frame, orient="vertical", command=canvas.yview)
        self.images_scroll_frame = ttk.Frame(canvas)
        
        self.images_scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.images_scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 佈局滾動區域
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
    
    def add_single_image_item(self, index, image_item):
        """添加單個圖片項目到顯示區域"""
        i = index
        result_frame = ttk.LabelFrame(self.images_scroll_frame, text=f"指令 {i+1}", padding=10)
        result_frame.pack(fill=tk.X, pady=5, padx=5)
        
        # 顯示對應的提示詞
        if i < len(self.prompts):
            prompt_text = self.prompts[i].get('prompt', '')[:100] + "..." if len(self.prompts[i].get('prompt', '')) > 100 else self.prompts[i].get('prompt', '')
            ttk.Label(result_frame, text=f"提示詞: {prompt_text}", 
                     wraplength=600, font=('Arial', 8)).pack(anchor='w')
        
        if 'error' in image_item:
            # 錯誤顯示
            ttk.Label(result_frame, text=f"❌ {image_item['error']}", 
                     foreground='red').pack(anchor='w', pady=(5, 0))
        else:
            # 顯示狀態
            status = image_item.get('status', '處理完成')
            ttk.Label(result_frame, text=f"📝 {status}", 
                     foreground='blue').pack(anchor='w', pady=(5, 0))
            
            # 如果有實際圖片URL，顯示預覽和下載按鈕
            urls = image_item.get('urls', [])
            if urls:
                success_frame = ttk.Frame(result_frame)
                success_frame.pack(fill=tk.X, pady=(5, 0))
                
                ttk.Label(success_frame, text=f"✅ 成功生成 {len(urls)} 張圖片", 
                         foreground='green').pack(side=tk.LEFT)
                
                # 圖片預覽和下載區域
                images_frame = ttk.Frame(result_frame)
                images_frame.pack(fill=tk.X, pady=(5, 0))
                
                for j, img_url in enumerate(urls):
                    img_container = ttk.Frame(images_frame)
                    img_container.pack(side=tk.LEFT, padx=(0, 10))
                    
                    # 顯示縮圖預覽
                    try:
                        preview_label = self.create_image_preview(img_container, img_url, size=(120, 120))
                        if preview_label:
                            preview_label.pack()
                    except Exception as e:
                        print(f"預覽生成失敗: {e}")
                        # 如果預覽失敗，顯示佔位符
                        ttk.Label(img_container, text=f"圖片 {j+1}\n(預覽失敗)", 
                                 background='lightgray', width=15, anchor='center').pack()
                    
                    # 下載按鈕
                    ttk.Button(img_container, text=f"下載 {j+1}", 
                              command=lambda url=img_url, idx=f"{i+1}_{j+1}": self.download_image(url, idx)).pack(pady=(5, 0))
        
        # 更新標題統計
        if hasattr(self, 'title_label'):
            success_count = sum(1 for img in self.images if 'error' not in img and img.get('urls'))
            error_count = len(self.images) - success_count
            self.title_label.config(text=f"生成結果 (成功: {success_count}, 失敗: {error_count})")
    
    def download_image(self, img_url, filename):
        """下載單張圖片 - 修復版"""
        try:
            print(f"DEBUG: 開始下載圖片 {filename}")
            print(f"DEBUG: URL 類型: {type(img_url)}")
            print(f"DEBUG: URL 開頭: {img_url[:50] if img_url else 'None'}...")
            
            if img_url and img_url.startswith('data:image/png;base64,'):
                import base64
                
                # 解碼 base64 圖片
                base64_data = img_url.split(',')[1]
                img_data = base64.b64decode(base64_data)
                
                print(f"DEBUG: 圖片數據大小: {len(img_data)} bytes")
                
                # 選擇儲存位置
                file_path = filedialog.asksaveasfilename(
                    title="儲存圖片",
                    defaultextension=".png",
                    initialfile=f"image_{filename}.png",
                    filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
                )
                
                if file_path:
                    with open(file_path, 'wb') as f:
                        f.write(img_data)
                    print(f"DEBUG: 圖片已儲存至: {file_path}")
                    messagebox.showinfo("成功", f"圖片已儲存至:\n{file_path}")
                else:
                    print("DEBUG: 用戶取消了儲存")
            else:
                print(f"DEBUG: 無效的圖片 URL: {img_url}")
                messagebox.showerror("錯誤", "無效的圖片數據")
        
        except Exception as e:
            print(f"DEBUG: 下載失敗: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("錯誤", f"下載失敗: {str(e)}")
    
    def download_all_images(self):
        """批量下載所有圖片"""
        try:
            # 選擇儲存資料夾
            folder_path = filedialog.askdirectory(title="選擇儲存資料夾")
            if not folder_path:
                return
            
            import base64
            downloaded_count = 0
            
            for i, image_item in enumerate(self.images):
                if 'error' not in image_item and image_item.get('urls'):
                    for j, img_url in enumerate(image_item['urls']):
                        if img_url.startswith('data:image/png;base64,'):
                            try:
                                # 解碼 base64 圖片
                                img_data = base64.b64decode(img_url.split(',')[1])
                                
                                # 生成檔案名稱
                                timestamp = self.prompts[i].get('timestamp', f'{i+1:02d}').replace(':', '-')
                                filename = f"image_{timestamp}_{j+1}.png"
                                file_path = os.path.join(folder_path, filename)
                                
                                # 儲存圖片
                                with open(file_path, 'wb') as f:
                                    f.write(img_data)
                                
                                downloaded_count += 1
                                
                            except Exception as e:
                                print(f"下載圖片 {i+1}-{j+1} 失敗: {e}")
            
            if downloaded_count > 0:
                messagebox.showinfo("批量下載完成", 
                                  f"成功下載 {downloaded_count} 張圖片至:\n{folder_path}")
            else:
                messagebox.showwarning("下載失敗", "沒有可下載的圖片")
        
        except Exception as e:
            messagebox.showerror("錯誤", f"批量下載失敗: {str(e)}")
    
    def create_image_preview(self, parent, img_url, size=(150, 150)):
        """創建圖片預覽"""
        try:
            if img_url.startswith('data:image/png;base64,'):
                import base64
                from PIL import Image, ImageTk
                from io import BytesIO
                
                # 解碼 base64 圖片
                img_data = base64.b64decode(img_url.split(',')[1])
                
                # 使用 PIL 處理圖片
                pil_image = Image.open(BytesIO(img_data))
                
                # 調整大小保持比例
                pil_image.thumbnail(size, Image.Resampling.LANCZOS)
                
                # 轉換為 Tkinter 可用的格式
                tk_image = ImageTk.PhotoImage(pil_image)
                
                # 創建標籤顯示圖片
                label = tk.Label(parent, image=tk_image)
                label.image = tk_image  # 保持引用避免被垃圾回收
                
                return label
            
        except Exception as e:
            print(f"圖片預覽創建失敗: {e}")
            return None