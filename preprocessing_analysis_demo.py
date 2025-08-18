#!/usr/bin/env python3
"""
預處理分析模組 - 智能分析逐字稿結構
解決時間分佈不均和內容相似問題
"""

import re
import json
from typing import List, Dict, Tuple
from datetime import datetime, timedelta

class TranscriptAnalyzer:
    """逐字稿預處理分析器"""
    
    def __init__(self):
        self.segments = []
        self.total_duration = 0
        self.visual_keywords = [
            # 動作關鍵詞
            '走', '跑', '坐', '站', '躺', '跳', '舞', '開門', '關門', '拿', '放',
            # 情緒關鍵詞  
            '笑', '哭', '生氣', '驚訝', '害怕', '開心', '難過', '緊張',
            # 環境關鍵詞
            '室內', '室外', '辦公室', '家', '餐廳', '公園', '街道', '車上',
            # 視覺元素
            '燈光', '陽光', '夜晚', '雨', '雪', '火', '水', '樹', '花'
        ]
    
    def analyze_transcript(self, transcript_content: str, target_count: int) -> Dict:
        """
        分析逐字稿並生成最佳時間點選擇
        
        Args:
            transcript_content: SRT 格式的逐字稿內容
            target_count: 目標提示詞數量
            
        Returns:
            分析結果包含：最佳時間點、內容摘要、多樣性評分
        """
        
        # 步驟1: 解析 SRT 格式
        segments = self._parse_srt(transcript_content)
        
        # 步驟2: 計算總時長
        total_duration = self._calculate_duration(segments)
        
        # 步驟3: 分析每個段落的視覺豐富度
        visual_scores = self._analyze_visual_richness(segments)
        
        # 步驟4: 檢測場景變化點
        scene_changes = self._detect_scene_changes(segments)
        
        # 步驟5: 計算最佳時間分佈
        optimal_points = self._calculate_optimal_distribution(
            segments, total_duration, target_count, visual_scores, scene_changes
        )
        
        # 步驟6: 確保多樣性
        diverse_points = self._ensure_diversity(optimal_points, segments)
        
        return {
            'total_duration': total_duration,
            'total_segments': len(segments),
            'optimal_points': diverse_points,
            'distribution_quality': self._evaluate_distribution(diverse_points),
            'diversity_score': self._calculate_diversity_score(diverse_points, segments)
        }
    
    def _parse_srt(self, content: str) -> List[Dict]:
        """解析 SRT 格式"""
        segments = []
        pattern = r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.+?)(?=\n\n|\n\d+\n|\Z)'
        
        matches = re.findall(pattern, content, re.DOTALL)
        
        for start_time, end_time, text in matches:
            segments.append({
                'start': self._time_to_seconds(start_time),
                'end': self._time_to_seconds(end_time),
                'start_str': start_time[:8],  # HH:MM:SS
                'text': text.strip().replace('\n', ' ')
            })
        
        return segments
    
    def _time_to_seconds(self, time_str: str) -> float:
        """將時間字串轉換為秒數"""
        # 格式: HH:MM:SS,mmm
        time_part, ms_part = time_str.split(',')
        h, m, s = map(int, time_part.split(':'))
        ms = int(ms_part)
        return h * 3600 + m * 60 + s + ms / 1000
    
    def _calculate_duration(self, segments: List[Dict]) -> float:
        """計算總時長"""
        if not segments:
            return 0
        return segments[-1]['end'] - segments[0]['start']
    
    def _analyze_visual_richness(self, segments: List[Dict]) -> List[float]:
        """分析每個段落的視覺豐富度"""
        scores = []
        
        for segment in segments:
            text = segment['text'].lower()
            score = 0
            
            # 檢查視覺關鍵詞
            for keyword in self.visual_keywords:
                if keyword in text:
                    score += 1
            
            # 檢查動詞密度 (動作豐富度)
            action_words = ['了', '著', '在', '正在', '開始', '結束']
            for word in action_words:
                score += text.count(word) * 0.5
            
            # 檢查對話 vs 描述比例 (描述更適合視覺化)
            if '說' in text or '講' in text:
                score *= 0.7  # 對話場景視覺豐富度較低
            
            # 長度懲罰 (太短的段落不適合)
            if len(text) < 10:
                score *= 0.5
            
            scores.append(score)
        
        return scores
    
    def _detect_scene_changes(self, segments: List[Dict]) -> List[int]:
        """檢測場景變化點"""
        scene_changes = []
        
        for i in range(1, len(segments)):
            current_text = segments[i]['text'].lower()
            prev_text = segments[i-1]['text'].lower()
            
            # 檢測場景轉換關鍵詞
            scene_keywords = ['然後', '接著', '後來', '突然', '這時', '同時', '另一邊']
            
            for keyword in scene_keywords:
                if keyword in current_text and keyword not in prev_text:
                    scene_changes.append(i)
                    break
            
            # 檢測時間跳躍 (超過30秒的間隔)
            time_gap = segments[i]['start'] - segments[i-1]['end']
            if time_gap > 30:
                scene_changes.append(i)
        
        return scene_changes
    
    def _calculate_optimal_distribution(self, segments: List[Dict], total_duration: float, 
                                      target_count: int, visual_scores: List[float], 
                                      scene_changes: List[int]) -> List[Dict]:
        """計算最佳時間分佈點"""
        
        # 計算理想間隔
        ideal_interval = total_duration / target_count
        min_interval = 30  # 最小間隔30秒
        
        selected_points = []
        last_selected_time = -min_interval
        
        # 將時間軸分成 target_count 個區段
        for i in range(target_count):
            # 計算目標時間範圍
            target_start = i * ideal_interval
            target_end = (i + 1) * ideal_interval
            
            # 在此範圍內找最佳候選點
            candidates = []
            
            for j, segment in enumerate(segments):
                segment_time = segment['start']
                
                # 檢查是否在目標範圍內
                if target_start <= segment_time <= target_end:
                    # 檢查最小間隔
                    if segment_time - last_selected_time >= min_interval:
                        
                        score = visual_scores[j]
                        
                        # 場景變化點加分
                        if j in scene_changes:
                            score += 2
                        
                        # 距離目標時間越近加分
                        target_center = (target_start + target_end) / 2
                        distance_penalty = abs(segment_time - target_center) / ideal_interval
                        score *= (1 - distance_penalty * 0.3)
                        
                        candidates.append({
                            'index': j,
                            'segment': segment,
                            'score': score
                        })
            
            # 選擇最佳候選點
            if candidates:
                best_candidate = max(candidates, key=lambda x: x['score'])
                selected_points.append(best_candidate)
                last_selected_time = best_candidate['segment']['start']
            else:
                # 如果沒有候選點，選擇最接近的
                target_time = (target_start + target_end) / 2
                closest_segment = min(segments, 
                                    key=lambda s: abs(s['start'] - target_time))
                selected_points.append({
                    'index': segments.index(closest_segment),
                    'segment': closest_segment,
                    'score': 0
                })
        
        return selected_points
    
    def _ensure_diversity(self, points: List[Dict], segments: List[Dict]) -> List[Dict]:
        """確保選中點的多樣性"""
        
        # 分析每個點的特徵
        for point in points:
            text = point['segment']['text'].lower()
            
            # 分類特徵
            point['features'] = {
                'has_action': any(word in text for word in ['走', '跑', '坐', '站']),
                'has_emotion': any(word in text for word in ['笑', '哭', '生氣', '開心']),
                'has_dialogue': '說' in text or '講' in text,
                'has_description': len(text) > 50 and not ('說' in text),
                'indoor_outdoor': 'indoor' if any(word in text for word in ['室內', '辦公室', '家']) else 'outdoor'
            }
        
        # 檢查並調整重複特徵
        for i in range(1, len(points)):
            current = points[i]
            previous = points[i-1]
            
            # 如果連續兩個點特徵太相似，嘗試替換
            similarity = self._calculate_feature_similarity(
                current['features'], previous['features']
            )
            
            if similarity > 0.7:  # 相似度過高
                # 在附近尋找替代點
                alternative = self._find_alternative_point(
                    segments, current, points, i
                )
                if alternative:
                    points[i] = alternative
        
        return points
    
    def _calculate_feature_similarity(self, features1: Dict, features2: Dict) -> float:
        """計算特徵相似度"""
        common_features = 0
        total_features = len(features1)
        
        for key in features1:
            if features1[key] == features2[key]:
                common_features += 1
        
        return common_features / total_features
    
    def _find_alternative_point(self, segments: List[Dict], current_point: Dict, 
                               all_points: List[Dict], current_index: int) -> Dict:
        """尋找替代點"""
        current_time = current_point['segment']['start']
        search_range = 60  # 在前後60秒內搜尋
        
        alternatives = []
        
        for i, segment in enumerate(segments):
            if abs(segment['start'] - current_time) <= search_range:
                # 確保不與其他已選點衝突
                conflict = False
                for other_point in all_points:
                    if abs(segment['start'] - other_point['segment']['start']) < 30:
                        conflict = True
                        break
                
                if not conflict:
                    alternatives.append({
                        'index': i,
                        'segment': segment,
                        'score': self._calculate_diversity_bonus(segment, all_points[:current_index])
                    })
        
        return max(alternatives, key=lambda x: x['score']) if alternatives else None
    
    def _calculate_diversity_bonus(self, segment: Dict, existing_points: List[Dict]) -> float:
        """計算多樣性獎勵分數"""
        text = segment['text'].lower()
        bonus = 1.0
        
        # 與已選點的差異性獎勵
        for point in existing_points:
            existing_text = point['segment']['text'].lower()
            
            # 不同類型內容獎勵
            if ('說' in existing_text) and ('說' not in text):
                bonus += 0.5  # 對話 vs 非對話
            
            if any(word in existing_text for word in ['室內', '辦公室']) and \
               any(word in text for word in ['室外', '公園', '街道']):
                bonus += 0.5  # 室內 vs 室外
        
        return bonus
    
    def _evaluate_distribution(self, points: List[Dict]) -> Dict:
        """評估分佈品質"""
        if len(points) < 2:
            return {'quality': 'poor', 'score': 0}
        
        # 計算時間間隔的標準差
        intervals = []
        for i in range(1, len(points)):
            interval = points[i]['segment']['start'] - points[i-1]['segment']['start']
            intervals.append(interval)
        
        import statistics
        mean_interval = statistics.mean(intervals)
        std_dev = statistics.stdev(intervals) if len(intervals) > 1 else 0
        
        # 標準差越小，分佈越均勻
        uniformity_score = max(0, 1 - (std_dev / mean_interval))
        
        return {
            'quality': 'excellent' if uniformity_score > 0.8 else 'good' if uniformity_score > 0.6 else 'fair',
            'score': uniformity_score,
            'mean_interval': mean_interval,
            'std_deviation': std_dev
        }
    
    def _calculate_diversity_score(self, points: List[Dict], segments: List[Dict]) -> float:
        """計算整體多樣性分數"""
        if not points:
            return 0
        
        diversity_factors = []
        
        # 檢查內容類型多樣性
        content_types = set()
        for point in points:
            text = point['segment']['text'].lower()
            if '說' in text:
                content_types.add('dialogue')
            elif any(word in text for word in ['走', '跑', '坐']):
                content_types.add('action')
            else:
                content_types.add('description')
        
        diversity_factors.append(len(content_types) / 3)  # 最多3種類型
        
        # 檢查時間分佈均勻性
        time_distribution = self._evaluate_distribution(points)
        diversity_factors.append(time_distribution['score'])
        
        return sum(diversity_factors) / len(diversity_factors)

# 使用示例
def demo_preprocessing():
    """預處理分析示例"""
    
    # 模擬 SRT 內容
    sample_srt = """1
00:00:05,000 --> 00:00:08,000
大家好，歡迎來到今天的節目

2
00:00:10,000 --> 00:00:15,000
今天我們要討論一個很重要的話題

3
00:02:30,000 --> 00:02:35,000
讓我們走到戶外，看看這美麗的風景

4
00:05:20,000 --> 00:05:25,000
突然間，天空開始下雨了

5
00:08:45,000 --> 00:08:50,000
我們趕緊跑回室內避雨"""
    
    analyzer = TranscriptAnalyzer()
    result = analyzer.analyze_transcript(sample_srt, 5)
    
    print("=== 預處理分析結果 ===")
    print(f"總時長: {result['total_duration']:.1f} 秒")
    print(f"總段落數: {result['total_segments']}")
    print(f"分佈品質: {result['distribution_quality']['quality']}")
    print(f"多樣性分數: {result['diversity_score']:.2f}")
    
    print("\n=== 最佳時間點 ===")
    for i, point in enumerate(result['optimal_points']):
        segment = point['segment']
        print(f"{i+1}. {segment['start_str']} - {segment['text'][:50]}...")

if __name__ == "__main__":
    demo_preprocessing()