#!/usr/bin/env python3
"""
AI 智慧工作站 v4.0 (增強版跨平台媒體工作站)

作者: Kiro AI Assistant & 使用者
描述: 跨平台媒體處理工作站，整合語音轉錄、AI 分析、媒體歸檔、智能搜尋等功能
版本: v4.0 - 增強版，加入資料夾監控、進階搜尋、效能監控、診斷系統

核心功能:
1. 語音轉錄功能 (基於 Whisper.cpp)
2. AI 分析、校正功能 (基於 Google Gemini)
3. 媒體歸檔功能 (智能分類和組織)
4. 媒體搜尋、預覽、下載功能 (自然語言搜尋)
5. Windows、macOS 雙平台支援

增強功能:
- 資料夾監控和自動處理
- 進階搜尋和過濾
- 效能監控和最佳化
- 診斷和支援系統
"""

import os
import sys
import threading
import time
import traceback
import math
from pathlib import Path
from typing import Dict, Any
from queue import Queue

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

# 檢查並導入可選依賴
_IMPORT_ERROR_LIBS = []
_PIL_IMPORTED = False
_PANDAS_IMPORTED = False
_OPENCC_IMPORTED = False

try:
    from PIL import Image, ImageTk
    _PIL_IMPORTED = True
    PIL_AVAILABLE = True
except ImportError:
    _IMPORT_ERROR_LIBS.append("Pillow")
    PIL_AVAILABLE = False

try:
    import pandas as pd
    _PANDAS_IMPORTED = True
    PANDAS_AVAILABLE = True
except ImportError:
    _IMPORT_ERROR_LIBS.append("pandas")
    PANDAS_AVAILABLE = False

try:
    import opencc
    _OPENCC_IMPORTED = True
except ImportError:
    _IMPORT_ERROR_LIBS.append("opencc-python-reimplemented")

# 檢查 Google Generative AI 和 SRT 導入
_GENAI_IMPORTED = False
_SRT_IMPORTED = False

try:
    import google.generativeai as genai
    _GENAI_IMPORTED = True
except ImportError:
    _IMPORT_ERROR_LIBS.append("google-generativeai")

try:
    import srt
    _SRT_IMPORTED = True
except ImportError:
    _IMPORT_ERROR_LIBS.append("srt")

# 導入自定義模組
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from platform_adapter import platform_adapter
    from config_service import config_service
    from logging_service import logging_service
    from enhanced_search_manager import enhanced_search_manager
    from natural_language_search import nl_search_engine
    from transcription_manager import transcription_manager
    from archive_manager import archive_manager
    from monitoring_manager import monitoring_manager
    from diagnostics_manager import diagnostics_manager
    from image_generation_okokgo import ImageGenerationOkokGo
except ImportError as e:
    print(f"導入核心模組失敗: {e}")
    print("請確保所有必要的模組檔案都存在")
    sys.exit(1)

# 應用程式常數
APP_NAME = "AI 智慧工作站"

# ===============================================================
# 響應式佈局管理器
# ===============================================================

class ResponsiveLayoutManager:
    """響應式佈局管理器 - 負責管理整體響應式行為"""
    
    def __init__(self, app_instance):
        """初始化響應式佈局管理器"""
        self.app = app_instance
        self.root = app_instance.root
        
        # 響應式斷點定義
        self.breakpoints = {
            'small': {'max_width': 900, 'description': '緊湊模式'},
            'medium': {'min_width': 901, 'max_width': 1200, 'description': '中等模式'},
            'large': {'min_width': 1201, 'description': '完整模式'}
        }
        
        # 當前佈局模式
        self.current_mode = 'large'
        
        # 防抖計時器
        self.debounce_timer = None
        self.debounce_delay = 100  # ms
        
        # 佈局配置 - 優化比例和間距
        self.layout_configs = {
            'compact': {
                'button_arrangement': 'vertical',
                'log_height': 5,  # 稍微增加一點，讓日誌更實用
                'spacing': 'tight',
                'button_padding': 2,
                'collapsible_sections': ['logs', 'help_text'],
                'hidden_elements': ['description_text', 'status_info']
            },
            'balanced': {
                'button_arrangement': 'grid',
                'log_height': 9,  # 更合理的中等高度
                'spacing': 'normal',
                'button_padding': 3,
                'collapsible_sections': ['advanced_settings'],
                'hidden_elements': []
            },
            'full': {
                'button_arrangement': 'horizontal',
                'log_height': 14,  # 稍微增加，充分利用大螢幕
                'spacing': 'comfortable',
                'button_padding': 4,
                'collapsible_sections': [],
                'hidden_elements': []
            }
        }
        
        # 綁定視窗大小變化事件
        self.root.bind('<Configure>', self.on_window_resize)
        
        print("響應式佈局管理器已初始化")
    
    def on_window_resize(self, event):
        """視窗大小變化處理 (使用防抖機制)"""
        if event.widget == self.root:  # 只處理主視窗的變化
            # 取消之前的計時器
            if self.debounce_timer:
                self.root.after_cancel(self.debounce_timer)
            
            # 設定新的計時器
            self.debounce_timer = self.root.after(
                self.debounce_delay, 
                self._apply_responsive_layout
            )
    
    def _apply_responsive_layout(self):
        """應用響應式佈局"""
        try:
            # 取得當前視窗大小
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            
            # 決定佈局模式
            new_mode = self._determine_layout_mode(width)
            
            # 只在模式改變時重新佈局
            if new_mode != self.current_mode:
                old_mode = self.current_mode
                self.current_mode = new_mode
                
                print(f"佈局模式切換: {old_mode} -> {new_mode} ({width}x{height})")
                
                # 更新所有頁籤的佈局
                self._update_all_tabs_layout(new_mode, width, height)
                
                # 更新狀態顯示
                self._update_layout_status(new_mode, width, height)
        
        except Exception as e:
            print(f"響應式佈局錯誤: {e}")
            import traceback
            traceback.print_exc()
    
    def _determine_layout_mode(self, width):
        """根據視窗寬度決定佈局模式"""
        if width <= self.breakpoints['small']['max_width']:
            return 'compact'
        elif width <= self.breakpoints['medium']['max_width']:
            return 'balanced'
        else:
            return 'full'
    
    def _update_all_tabs_layout(self, mode, width, height):
        """更新所有頁籤的佈局"""
        layout_config = self.layout_configs[mode]
        
        try:
            # 更新語音轉錄頁籤
            if hasattr(self.app, 'transcribe_log_area'):
                self._update_transcribe_tab_layout(layout_config)
            
            # 更新 AI 功能頁籤
            if hasattr(self.app, 'ai_log_area'):
                self._update_ai_tab_layout(layout_config)
            
            # 更新其他頁籤 (未來擴展)
            # self._update_other_tabs_layout(layout_config)
            
        except Exception as e:
            print(f"更新頁籤佈局錯誤: {e}")
    
    def _update_transcribe_tab_layout(self, layout_config):
        """更新語音轉錄頁籤的佈局 - 針對內容特性優化"""
        try:
            # 語音轉錄頁籤的特點：左側內容豐富，右側較空
            # 所以不需要左右分欄，使用單欄佈局更合適
            
            # 調整日誌區域高度
            if hasattr(self.app, 'transcribe_log_area'):
                log_height = layout_config['log_height']
                self.app.transcribe_log_area.config(height=log_height)
            
            # 調整日誌框架的擴展行為
            if hasattr(self.app, 'transcribe_log_frame'):
                if layout_config['log_height'] <= 5:
                    # 緊湊模式：不擴展，給上方功能更多空間
                    self.app.transcribe_log_frame.pack_configure(expand=False, fill=tk.X)
                else:
                    # 其他模式：可擴展
                    self.app.transcribe_log_frame.pack_configure(expand=True, fill=tk.BOTH)
            
            print(f"語音轉錄頁籤佈局已更新 (日誌高度: {layout_config['log_height']})")
            
        except Exception as e:
            print(f"更新語音轉錄頁籤佈局錯誤: {e}")
    
    def _update_ai_tab_layout(self, layout_config):
        """更新 AI 功能頁籤的佈局 - 優化視覺效果和比例"""
        try:
            # 調整左右分欄比例
            self._adjust_ai_tab_column_ratio(layout_config)
            
            # 調整日誌區域高度
            if hasattr(self.app, 'ai_log_area'):
                log_height = layout_config['log_height']
                self.app.ai_log_area.config(height=log_height)
            
            # 調整日誌框架的擴展行為和間距
            if hasattr(self.app, 'ai_log_frame'):
                spacing = layout_config.get('spacing', 'normal')
                if layout_config['log_height'] <= 5:
                    # 緊湊模式：不擴展，減少間距
                    self.app.ai_log_frame.pack_configure(expand=False, pady=(2,0))
                elif layout_config['log_height'] <= 9:
                    # 中等模式：部分擴展，正常間距
                    self.app.ai_log_frame.pack_configure(expand=True, pady=(5,0))
                else:
                    # 完整模式：完全擴展，舒適間距
                    self.app.ai_log_frame.pack_configure(expand=True, pady=(8,0))
            
            # 更新 AI 按鈕佈局
            if hasattr(self.app, 'ai_analyze_button_tab'):
                self._update_ai_buttons_layout(layout_config['button_arrangement'])
            
            # 調整整體間距
            self._adjust_ai_tab_spacing(layout_config)
            
            print(f"AI功能頁籤佈局已更新 (日誌高度: {layout_config['log_height']}, 按鈕排列: {layout_config['button_arrangement']})")
            
        except Exception as e:
            print(f"更新AI功能頁籤佈局錯誤: {e}")
    
    def _adjust_ai_tab_column_ratio(self, layout_config):
        """調整 AI 頁籤的左右分欄比例 - 基於內容需求的智能分配"""
        try:
            # AI功能頁籤的特點：左側日誌內容少，右側設定和按鈕內容多
            # 根據按鈕排列方式和視窗大小智能調整比例
            
            current_width = self.root.winfo_width()
            
            if layout_config['button_arrangement'] == 'vertical':
                # 緊湊模式：右側垂直按鈕需要更多空間
                if current_width < 800:
                    left_weight = 25  # 極小視窗，左側最小化
                    right_weight = 75
                else:
                    left_weight = 30
                    right_weight = 70
                    
            elif layout_config['button_arrangement'] == 'grid':
                # 中等模式：右側網格按鈕需要適中空間
                left_weight = 25  # 左側日誌區域不需要太多空間
                right_weight = 75
                
            else:  # horizontal
                # 完整模式：右側水平按鈕需要最多空間
                left_weight = 20  # 左側最小化
                right_weight = 80
            
            # 尋找並調整 content_frame 的 grid 權重
            self._find_and_adjust_content_frame_ratio(left_weight, right_weight)
                    
        except Exception as e:
            print(f"調整分欄比例錯誤: {e}")
    
    def _find_and_adjust_content_frame_ratio(self, left_weight, right_weight):
        """尋找並調整 content_frame 的比例"""
        try:
            if hasattr(self.app, 'ai_analyze_button_tab'):
                # 從按鈕往上找到 content_frame
                button = self.app.ai_analyze_button_tab
                current = button.master
                
                # 向上遍歷找到使用 grid 的父容器
                for _ in range(10):  # 最多向上找10層
                    if current is None or current.winfo_class() == 'Toplevel':
                        break
                        
                    try:
                        # 檢查是否有 grid_columnconfigure 方法且有兩欄
                        if hasattr(current, 'grid_columnconfigure'):
                            # 嘗試調整權重
                            current.grid_columnconfigure(0, weight=left_weight)
                            current.grid_columnconfigure(1, weight=right_weight)
                            print(f"✅ 成功調整分欄比例: 左側 {left_weight}%, 右側 {right_weight}%")
                            return
                    except Exception:
                        pass
                    
                    current = current.master
                
                print("⚠️ 未找到可調整的 content_frame")
                
        except Exception as e:
            print(f"尋找 content_frame 錯誤: {e}")
    
    def _adjust_ai_tab_spacing(self, layout_config):
        """調整 AI 頁籤的整體間距"""
        try:
            spacing = layout_config.get('spacing', 'normal')
            
            # 根據間距模式調整各區域的 pady
            if spacing == 'tight':
                info_pady = (0, 5)
                config_pady = (0, 8)
                button_pady = (0, 5)
            elif spacing == 'comfortable':
                info_pady = (0, 15)
                config_pady = (0, 15)
                button_pady = (0, 10)
            else:  # normal
                info_pady = (0, 10)
                config_pady = (0, 10)
                button_pady = (0, 8)
            
            # 這裡可以進一步調整各區域的間距
            # 但需要確保不影響已鎖定功能的邏輯
            
        except Exception as e:
            print(f"調整間距錯誤: {e}")
    
    def _update_ai_buttons_layout(self, arrangement):
        """更新 AI 功能按鈕的排列方式"""
        try:
            buttons = [
                self.app.ai_analyze_button_tab,
                self.app.ai_correct_button_tab,
                self.app.ai_translate_button_tab,
                self.app.ai_social_button_tab,
                self.app.ai_news_button_tab
            ]
            
            # 檢查所有按鈕是否存在
            if not all(hasattr(self.app, attr) for attr in 
                      ['ai_analyze_button_tab', 'ai_correct_button_tab', 'ai_translate_button_tab', 
                       'ai_social_button_tab', 'ai_news_button_tab']):
                return
            
            # 清除現有佈局
            for button in buttons:
                if button and button.winfo_exists():
                    button.grid_forget()
            
            # 根據排列方式重新佈局
            if arrangement == 'vertical':
                self._apply_vertical_button_layout(buttons)
            elif arrangement == 'grid':
                self._apply_grid_button_layout(buttons)
            else:  # horizontal
                self._apply_horizontal_button_layout(buttons)
                
        except Exception as e:
            print(f"更新AI按鈕佈局錯誤: {e}")
    
    def _apply_vertical_button_layout(self, buttons):
        """應用垂直按鈕佈局 (緊湊模式) - 更美觀的排列"""
        for i, button in enumerate(buttons):
            if button and button.winfo_exists():
                button.grid(row=i, column=0, padx=3, pady=2, sticky="ew")
                button.config(width=12)  # 適中的按鈕寬度
        
        # 調整父容器
        if buttons[0] and buttons[0].winfo_exists():
            buttons_frame = buttons[0].master
            buttons_frame.grid_columnconfigure(0, weight=1, minsize=120)
    
    def _apply_grid_button_layout(self, buttons):
        """應用網格按鈕佈局 (中等模式) - 更緊湊美觀的 2x3 排列"""
        # 更美觀的 2x3 排列：前3個一行，後2個一行並居中
        positions = [(0,0), (0,1), (0,2), (1,0), (1,1)]
        for button, (row, col) in zip(buttons, positions):
            if button and button.winfo_exists():
                button.grid(row=row, column=col, padx=3, pady=3, sticky="ew")
                button.config(width=9)  # 稍微緊湊的按鈕
        
        # 調整父容器，讓第二行居中
        if buttons[0] and buttons[0].winfo_exists():
            buttons_frame = buttons[0].master
            for i in range(3):
                buttons_frame.grid_columnconfigure(i, weight=1, minsize=90)
            
            # 讓第二行的按鈕居中顯示
            buttons_frame.grid_columnconfigure(2, weight=2)  # 右側多一些空間
    
    def _apply_horizontal_button_layout(self, buttons):
        """應用水平按鈕佈局 (完整模式) - 更均勻美觀的排列"""
        for i, button in enumerate(buttons):
            if button and button.winfo_exists():
                button.grid(row=0, column=i, padx=4, pady=3, sticky="ew")
                button.config(width=8)  # 保持適中寬度
        
        # 調整父容器，確保按鈕均勻分佈
        if buttons[0] and buttons[0].winfo_exists():
            buttons_frame = buttons[0].master
            for i in range(len(buttons)):
                buttons_frame.grid_columnconfigure(i, weight=1, minsize=85)
    
    def _update_layout_status(self, mode, width, height):
        """更新佈局狀態顯示"""
        try:
            status_text = f"佈局: {self.breakpoints[mode]['description']} ({width}x{height})"
            
            # 更新 AI 功能頁籤的狀態標籤
            if hasattr(self.app, 'ai_status_label'):
                current_text = self.app.ai_status_label.cget('text')
                if not current_text.startswith('佈局:'):
                    # 只有在不是佈局狀態時才更新
                    if '請載入 SRT 檔案' in current_text or '佈局:' in current_text:
                        self.app.ai_status_label.config(text=status_text)
                        
        except Exception as e:
            print(f"更新佈局狀態錯誤: {e}")
    
    def initialize_responsive_layout(self):
        """初始化響應式佈局"""
        try:
            # 取得當前視窗大小
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            
            # 決定初始佈局模式
            initial_mode = self._determine_layout_mode(width)
            self.current_mode = initial_mode
            
            # 應用初始佈局
            self._update_all_tabs_layout(initial_mode, width, height)
            self._update_layout_status(initial_mode, width, height)
            
            print(f"響應式佈局已初始化: {initial_mode} 模式 ({width}x{height})")
            
        except Exception as e:
            print(f"響應式佈局初始化錯誤: {e}")
            import traceback
            traceback.print_exc()
    
    def get_current_mode(self):
        """取得當前佈局模式"""
        return self.current_mode
    
    def get_layout_config(self, mode=None):
        """取得佈局配置"""
        if mode is None:
            mode = self.current_mode
        return self.layout_configs.get(mode, self.layout_configs['full'])
APP_VERSION = "v4.0"
APP_TITLE = f"{APP_NAME} {APP_VERSION} (增強版)"

# 自動偵測應用程式路徑
if getattr(sys, 'frozen', False):
    BASE_PATH = Path(sys.executable).parent
else:
    BASE_PATH = Path(__file__).parent

# 跨平台資源路徑
WHISPER_CPP_FOLDER_NAME = "whisper_resources"
WHISPER_CPP_PATH = BASE_PATH / WHISPER_CPP_FOLDER_NAME
FFMPEG_PATH = WHISPER_CPP_PATH / "ffmpeg"

# 可用模型 (移除有問題的v3模型)
AVAILABLE_MODELS = {
    "Medium (中等)": "ggml-medium.bin",
    "Large-v2 (大型)": "ggml-large-v2.bin"
}
DEFAULT_MODEL_KEY = "Medium (中等)"

# 配置檔案 - 現在由 config_service 管理

# ===============================================================
# SECTION 1: 主應用程式 - AI 智慧工作站 (Tkinter)
# ===============================================================
class AIWorkstationApp:
    def __init__(self, root):
        """初始化應用程式"""
        self.root = root
        self.root.title("AI 智慧工作站 v4.0 (增強版)")
        
        # 初始化樣式系統
        self.style = ttk.Style()
        
        # 響應式視窗設計
        self.setup_responsive_window()
        
        # 設定應用程式圖示和樣式
        self.setup_app_style()
        
        # --- 全域變數與狀態 ---
        self.opencc_converter = None
        self.processor_instance = None
        self.log_queue = Queue()
        self.media_df = pd.DataFrame() if _PANDAS_IMPORTED else None
        self.search_results_data = []
        self.photo_image_cache = {}
        
        # --- 初始化服務 ---
        self.config_service = config_service
        self.logger = logging_service
        self.platform_adapter = platform_adapter
        
        try:
            self.search_manager = enhanced_search_manager
            self.nl_search = nl_search_engine
            self.transcription_manager = transcription_manager
            self.archive_manager = archive_manager
        except Exception as e:
            self.logger.error(f"服務初始化失敗: {str(e)}")
            messagebox.showerror("初始化錯誤", f"服務初始化失敗: {str(e)}")
        
        # --- 轉錄相關變數 ---
        self.output_srt = tk.BooleanVar(value=True)
        self.output_txt = tk.BooleanVar(value=False)
        self.output_vtt = tk.BooleanVar(value=False)
        self.output_wts = tk.BooleanVar(value=False)
        self.output_lrc = tk.BooleanVar(value=False)
        self.output_csv = tk.BooleanVar(value=False)
        self.output_json = tk.BooleanVar(value=False)
        self.output_json_full = tk.BooleanVar(value=False)
        self.enable_segmentation = tk.BooleanVar(value=False)
        self.remove_punctuation = tk.BooleanVar(value=False)
        self.convert_to_traditional_chinese = tk.BooleanVar(value=False)
        self.selected_model_key = tk.StringVar(value=DEFAULT_MODEL_KEY)
        self.selected_language = tk.StringVar(value="zh")
        self.prompt_text = tk.StringVar(value="")
        self.threads_value = tk.StringVar(value='4')
        self.temperature_value = tk.StringVar(value='0.0')
        self.translate_to_english = tk.BooleanVar(value=False)
        self.selected_file = None
        self.output_dir = None
        self.last_srt_path = None
        self.external_srt_path = None
        self.is_ai_correcting = False
        self.is_ai_analyzing = False
        self.is_ai_translating = False
        self.is_ai_generating_news = False
        self.is_ai_generating_social = False
        
        # AI 設定變數
        self.ai_model_var = tk.StringVar(value="gemini-1.5-pro-latest")
        self.batch_size_var = tk.StringVar(value="15")
        
        # 分離提示詞變數
        self.transcribe_prompt_text = ""  # 語音轉錄用的提示詞
        self.ai_prompt_text = ""  # AI 功能用的提示詞
        
        # --- 初始化 ---
        self._initialize_styles()
        self._load_config()
        self.create_main_widgets()
        self._initialize_opencc_converter()
        self.check_required_files()
        self.root.after(100, self.process_log_queue)
        
        # 初始化完成後的處理
        self.root.after(100, self.process_log_queue)
    
    def setup_responsive_window(self):
        """設定響應式視窗 - 佈局優化版"""
        # 取得螢幕尺寸
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 計算適當的視窗大小（螢幕的85%，提供更多空間）
        window_width = int(screen_width * 0.85)
        window_height = int(screen_height * 0.85)
        
        # 確保最小尺寸（提高最小尺寸以避免截斷）
        window_width = max(window_width, 1400)
        window_height = max(window_height, 900)
        
        # 計算視窗置中位置
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        # 設定視窗大小和位置
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 設定更小的最小視窗大小，允許更靈活的縮放
        self.root.minsize(800, 600)
        
        # 設定視窗可調整大小
        self.root.resizable(True, True)
        
        # 設定主視窗的網格權重（確保響應式佈局）
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # 初始化響應式佈局系統
        self.current_layout_mode = 'large'
        self.layout_breakpoints = {
            'small': 900,   # 小於900px為小螢幕
            'medium': 1200, # 900-1200px為中等螢幕
            'large': 1200   # 大於1200px為大螢幕
        }
        
        # 綁定視窗大小變更事件
        self.root.bind('<Configure>', self.on_window_resize)
        
        # 綁定視窗狀態變更事件（最大化/還原）
        self.root.bind('<Map>', self._on_window_map)
        self.root.bind('<Unmap>', self._on_window_unmap)
    
    def on_window_resize(self, event):
        """視窗大小變化時的響應式佈局處理"""
        if event.widget == self.root:  # 只處理主視窗的變化
            width = event.width
            height = event.height
            
            # 決定佈局模式
            if width < self.layout_breakpoints['small']:
                new_mode = 'small'
            elif width < self.layout_breakpoints['medium']:
                new_mode = 'medium'
            else:
                new_mode = 'large'
            
            # 只在模式改變時重新佈局（避免頻繁重繪）
            if new_mode != self.current_layout_mode:
                self.current_layout_mode = new_mode
                self.apply_responsive_layout(new_mode, width, height)
    
    def apply_responsive_layout(self, mode, width, height):
        """應用響應式佈局"""
        try:
            if mode == 'small':
                self.apply_compact_layout(width, height)
            elif mode == 'medium':
                self.apply_medium_layout(width, height)
            else:
                self.apply_full_layout(width, height)
                
            # 更新狀態顯示
            if hasattr(self, 'ai_status_label'):
                status_text = f"佈局模式: {mode} ({width}x{height})"
                self.root.after_idle(lambda: self.ai_status_label.config(text=status_text))
                
        except Exception as e:
            print(f"響應式佈局錯誤: {e}")
    

            print(f"水平佈局錯誤: {e}")
    
    def update_ui_scale(self, mode):
        """根據螢幕大小更新UI縮放"""
        try:
            if mode == 'small':
                button_font = ('Arial', 9)
                label_font = ('Arial', 9)
                padding = 1
            elif mode == 'medium':
                button_font = ('Arial', 10)
                label_font = ('Arial', 10)
                padding = 2
            else:
                button_font = ('Arial', 11)
                label_font = ('Arial', 11)
                padding = 3
            
            # 更新按鈕樣式（如果存在的話）
            if hasattr(self, 'style'):
                self.style.configure('AI.TButton', font=button_font, padding=padding)
                self.style.configure('TLabel', font=label_font)
                
        except Exception as e:
            print(f"UI縮放錯誤: {e}")
    
    def initialize_responsive_layout(self):
        """初始化響應式佈局"""
        try:
            # 取得當前視窗大小
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            
            # 決定初始佈局模式
            if width < self.layout_breakpoints['small']:
                initial_mode = 'small'
            elif width < self.layout_breakpoints['medium']:
                initial_mode = 'medium'
            else:
                initial_mode = 'large'
            
            self.current_layout_mode = initial_mode
            self.apply_responsive_layout(initial_mode, width, height)
            
            print(f"響應式佈局已初始化: {initial_mode} 模式 ({width}x{height})")
            
        except Exception as e:
            print(f"響應式佈局初始化錯誤: {e}")
    
    def _on_window_map(self, event):
        """視窗顯示事件處理"""
        if event.widget == self.root:
            # 確保佈局正確更新
            self.root.after(100, self._update_tab_layouts)
    
    def _on_window_unmap(self, event):
        """視窗隱藏事件處理"""
        # 預留給未來需要的處理
        pass
    
    def setup_app_style(self):
        """設定應用程式樣式和主題"""
        # 初始化字型系統
        self.initialize_font_system()
        
        # 設定視窗圖示（如果有的話）
        try:
            # 這裡可以設定應用程式圖示
            # self.root.iconbitmap('icon.ico')  # Windows
            # self.root.iconphoto(True, tk.PhotoImage(file='icon.png'))  # 跨平台
            pass
        except:
            pass
        
        # 設定視窗關閉事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 設定視窗標題欄
        self.root.title(f"{APP_TITLE} - {platform_adapter.get_platform().title()}")
        
        # 設定主題和顏色
        self.setup_theme_and_colors()
        
        # 設定視窗狀態
        if platform_adapter.is_windows():
            self.root.state('zoomed')  # Windows 最大化
        elif platform_adapter.is_macos():
            # macOS 使用 -fullscreen 或手動設定大小
            try:
                self.root.attributes('-fullscreen', False)
                # 獲取螢幕尺寸並設定視窗大小
                screen_width = self.root.winfo_screenwidth()
                screen_height = self.root.winfo_screenheight()
                self.root.geometry(f"{screen_width-100}x{screen_height-100}+50+50")
            except Exception as e:
                print(f"macOS 視窗設定警告: {e}")
    
    def setup_theme_and_colors(self):
        """設定主題和顏色"""
        try:
            # 設定主題
            available_themes = self.style.theme_names()
            if 'aqua' in available_themes:
                self.style.theme_use('aqua')
            elif 'clam' in available_themes:
                self.style.theme_use('clam')
            else:
                self.style.theme_use('default')
            
            # 設定顏色方案
            self.colors = {
                "bg": "#f0f0f0",
                "fg": "#333333",
                "accent_green": "#4CAF50",
                "accent_blue": "#2196F3",
                "accent_purple": "#9C27B0",
                "input_bg": "#ffffff",
                "input_fg": "#333333"
            }
            
            # 應用顏色到樣式
            self.style.configure('TFrame', background=self.colors["bg"])
            self.style.configure('TLabel', background=self.colors["bg"], foreground=self.colors["fg"])
            self.style.configure('TEntry', fieldbackground=self.colors["input_bg"], foreground=self.colors["input_fg"])
            self.style.configure('TButton', padding=6)
            self.style.configure('Accent.TButton', background=self.colors["accent_green"], foreground='white')
            self.style.configure('Optional.TButton', background=self.colors["accent_blue"], foreground='white')
            self.style.configure('AI.TButton', background=self.colors["accent_purple"], foreground='white')
            
        except Exception as e:
            print(f"主題設定錯誤: {e}")
    
    def initialize_font_system(self):
        """初始化統一的字型系統"""
        # 預設字型大小
        self.default_font_size = 10
        
        # 定義字型系列
        self.fonts = {
            'default': ('Arial', self.default_font_size),
            'bold': ('Arial', self.default_font_size, 'bold'),
            'large': ('Arial', self.default_font_size + 2),
            'large_bold': ('Arial', self.default_font_size + 2, 'bold'),
            'small': ('Arial', self.default_font_size - 1),
            'console': ('Consolas', self.default_font_size - 1),
            'title': ('Arial', self.default_font_size + 4, 'bold'),
            'subtitle': ('Arial', self.default_font_size + 2, 'bold'),
        }
        
        # 應用字型到 ttk 樣式
        self.apply_fonts_to_styles()
    
    def apply_fonts_to_styles(self):
        """將字型應用到所有 ttk 樣式"""
        try:
            # 基本元件樣式
            self.style.configure('TLabel', font=self.fonts['default'])
            self.style.configure('TButton', font=self.fonts['default'])
            self.style.configure('TEntry', font=self.fonts['default'])
            self.style.configure('TCombobox', font=self.fonts['default'])
            self.style.configure('TSpinbox', font=self.fonts['default'])
            self.style.configure('TCheckbutton', font=self.fonts['default'])
            self.style.configure('TRadiobutton', font=self.fonts['default'])
            self.style.configure('TFrame', font=self.fonts['default'])
            self.style.configure('TLabelFrame', font=self.fonts['default'])
            self.style.configure('TLabelFrame.Label', font=self.fonts['default'])
            # 同時支援 Labelframe（小寫 f）
            self.style.configure('TLabelframe', font=self.fonts['default'])
            self.style.configure('TLabelframe.Label', font=self.fonts['default'])
            self.style.configure('TNotebook', font=self.fonts['default'])
            self.style.configure('TNotebook.Tab', font=self.fonts['default'])
            self.style.configure('TTreeview', font=self.fonts['default'])
            self.style.configure('TTreeview.Heading', font=self.fonts['bold'])
            self.style.configure('TScale', font=self.fonts['default'])
            self.style.configure('TProgressbar', font=self.fonts['default'])
            self.style.configure('TSeparator', font=self.fonts['default'])
            self.style.configure('TPanedwindow', font=self.fonts['default'])
            
            # 下拉選單的特殊樣式（包含選項內容）
            self.style.configure('TCombobox', font=self.fonts['default'])
            # 設定下拉選單的選項字型
            self.root.option_add('*TCombobox*Listbox.font', self.fonts['default'])
            self.root.option_add('*TCombobox*Listbox*Font', self.fonts['default'])
            
            # 選單樣式
            self.style.configure('TMenu', font=self.fonts['default'])
            self.style.configure('TMenubutton', font=self.fonts['default'])
            
            # 特殊樣式
            self.style.configure('Title.TLabel', font=self.fonts['title'])
            self.style.configure('Subtitle.TLabel', font=self.fonts['subtitle'])
            self.style.configure('Bold.TLabel', font=self.fonts['bold'])
            self.style.configure('Large.TLabel', font=self.fonts['large'])
            self.style.configure('Small.TLabel', font=self.fonts['small'])
            
            # 按鈕樣式
            self.style.configure('Accent.TButton', font=self.fonts['bold'])
            self.style.configure('Optional.TButton', font=self.fonts['default'])
            self.style.configure('AI.TButton', font=self.fonts['default'])
            
            # 更新根視窗的選項設定，確保所有子元件都使用統一字型
            self.root.option_add('*Font', self.fonts['default'])
            self.root.option_add('*Menu.font', self.fonts['default'])
            self.root.option_add('*Menubutton.font', self.fonts['default'])
            self.root.option_add('*Text.font', self.fonts['console'])
            self.root.option_add('*Listbox.font', self.fonts['default'])
            self.root.option_add('*Entry.font', self.fonts['default'])
            self.root.option_add('*Labelframe.font', self.fonts['default'])
            self.root.option_add('*LabelFrame.font', self.fonts['default'])
            
            # 強制更新所有現有元件
            self.root.update_idletasks()
            
        except Exception as e:
            print(f"字型應用錯誤: {e}")
    
    def update_font_size(self, new_size):
        """更新所有字型大小"""
        self.default_font_size = new_size
        
        # 更新字型定義
        self.fonts = {
            'default': ('Arial', new_size),
            'bold': ('Arial', new_size, 'bold'),
            'large': ('Arial', new_size + 2),
            'large_bold': ('Arial', new_size + 2, 'bold'),
            'small': ('Arial', new_size - 1),
            'console': ('Consolas', new_size - 1),
            'title': ('Arial', new_size + 4, 'bold'),
            'subtitle': ('Arial', new_size + 2, 'bold'),
        }
        
        # 重新應用字型
        self.apply_fonts_to_styles()
        
        # 立即強制更新 LabelFrame 樣式
        self.force_update_labelframe_styles()
        
        # 更新所有現有的 Text 和 ScrolledText 元件
        self.update_text_widgets_font()
        
        # 強制更新所有元件
        self.force_update_all_widgets()
    
    def update_text_widgets_font(self):
        """更新所有 Text 和 ScrolledText 元件的字型"""
        try:
            # 更新系統資訊文字區域
            if hasattr(self, 'system_info_text'):
                self.system_info_text.configure(font=self.fonts['console'])
            
            # 更新資料夾活動文字區域
            if hasattr(self, 'folder_activity_text'):
                self.folder_activity_text.configure(font=self.fonts['console'])
            
            # 更新診斷結果區域
            if hasattr(self, 'diagnostic_result_area'):
                self.diagnostic_result_area.configure(font=self.fonts['console'])
            
            # 更新轉錄日誌區域
            if hasattr(self, 'transcribe_log_area'):
                self.transcribe_log_area.configure(font=self.fonts['console'])
            
            # 更新歸檔日誌區域
            if hasattr(self, 'archive_log_area'):
                self.archive_log_area.configure(font=self.fonts['console'])
            
            # 更新詳細資訊文字區域
            if hasattr(self, 'details_text'):
                self.details_text.configure(font=self.fonts['console'])
            
            # 更新搜尋結果區域
            if hasattr(self, 'search_results_text'):
                self.search_results_text.configure(font=self.fonts['default'])
            
            # 更新所有 Combobox 的下拉選項字型
            self.update_combobox_fonts()
            
            # 更新根視窗選項，確保新創建的元件也使用正確字型
            self.root.option_add('*Font', self.fonts['default'])
            self.root.option_add('*TCombobox*Listbox.font', self.fonts['default'])
            self.root.option_add('*Menu.font', self.fonts['default'])
            
            # 遞迴更新所有 ScrolledText 元件
            self.update_all_scrolledtext_fonts()
            
            # 遞迴更新所有 LabelFrame 標題字型
            self.update_all_labelframe_fonts()
                
        except Exception as e:
            print(f"更新文字元件字型錯誤: {e}")
    
    def update_all_scrolledtext_fonts(self):
        """遞迴更新所有 ScrolledText 元件的字型"""
        try:
            def update_widget_fonts(widget):
                try:
                    # 檢查是否為 ScrolledText
                    if hasattr(widget, 'text') and hasattr(widget.text, 'configure'):
                        widget.text.configure(font=self.fonts['console'])
                    elif hasattr(widget, 'configure') and 'font' in widget.configure():
                        # 對於一般的 Text 元件
                        widget.configure(font=self.fonts['console'])
                    
                    # 遞迴處理子元件
                    for child in widget.winfo_children():
                        update_widget_fonts(child)
                        
                except Exception:
                    # 忽略個別元件的錯誤，繼續處理其他元件
                    pass
            
            # 從根視窗開始更新
            update_widget_fonts(self.root)
            
        except Exception as e:
            print(f"更新 ScrolledText 字型錯誤: {e}")
    
    def update_all_labelframe_fonts(self):
        """遞迴更新所有 LabelFrame 標題的字型"""
        try:
            def update_labelframe_fonts(widget):
                try:
                    # 檢查是否為 LabelFrame
                    if isinstance(widget, ttk.LabelFrame):
                        # 更新 LabelFrame 的標題字型
                        widget.configure(font=self.fonts['default'])
                    
                    # 遞迴處理子元件
                    for child in widget.winfo_children():
                        update_labelframe_fonts(child)
                        
                except Exception:
                    # 忽略個別元件的錯誤，繼續處理其他元件
                    pass
            
            # 從根視窗開始更新
            update_labelframe_fonts(self.root)
            
        except Exception as e:
            print(f"更新 LabelFrame 字型錯誤: {e}")
    
    def force_update_all_widgets(self):
        """強制更新所有元件的字型"""
        try:
            def force_update_widget(widget):
                try:
                    widget_class = widget.winfo_class()
                    
                    # 處理 LabelFrame
                    if widget_class == 'TLabelframe':
                        widget.configure(font=self.fonts['default'])
                    
                    # 處理其他 ttk 元件
                    elif widget_class in ['TLabel', 'TButton', 'TEntry', 'TCombobox', 'TSpinbox', 
                                        'TCheckbutton', 'TRadiobutton']:
                        widget.configure(font=self.fonts['default'])
                    
                    # 處理 ScrolledText
                    elif hasattr(widget, 'text') and hasattr(widget.text, 'configure'):
                        widget.text.configure(font=self.fonts['console'])
                    
                    # 遞迴處理子元件
                    for child in widget.winfo_children():
                        force_update_widget(child)
                        
                except Exception:
                    # 忽略個別元件的錯誤，繼續處理其他元件
                    pass
            
            # 從根視窗開始強制更新
            force_update_widget(self.root)
            
            # 強制重繪
            self.root.update_idletasks()
            
        except Exception as e:
            print(f"強制更新元件字型錯誤: {e}")
    
    def force_update_labelframe_styles(self):
        """強制更新 LabelFrame 樣式"""
        try:
            # 使用測試中證實有效的方法
            self.style.configure('TLabelframe', font=self.fonts['default'])
            self.style.configure('TLabelframe.Label', font=self.fonts['default'])
            self.style.configure('TLabelFrame', font=self.fonts['default'])
            self.style.configure('TLabelFrame.Label', font=self.fonts['default'])
            
            # 使用 option_add 方法
            self.root.option_add('*TLabelframe*font', self.fonts['default'])
            self.root.option_add('*TLabelframe*Label*font', self.fonts['default'])
            self.root.option_add('*Labelframe*font', self.fonts['default'])
            self.root.option_add('*LabelFrame*font', self.fonts['default'])
            
            # 強制重繪
            self.root.update_idletasks()
            
            print(f"LabelFrame 樣式已強制更新為字型: {self.fonts['default']}")
            
        except Exception as e:
            print(f"強制更新 LabelFrame 樣式錯誤: {e}")
    
    def update_combobox_fonts(self):
        """更新所有 Combobox 元件的字型"""
        try:
            # 遞迴尋找所有 Combobox 元件並更新字型
            def update_widget_fonts(widget):
                try:
                    if isinstance(widget, ttk.Combobox):
                        widget.configure(font=self.fonts['default'])
                        # 設定下拉選項的字型
                        widget.option_add('*TCombobox*Listbox.font', self.fonts['default'])
                    
                    # 遞迴處理子元件
                    for child in widget.winfo_children():
                        update_widget_fonts(child)
                        
                except Exception as e:
                    # 忽略個別元件的錯誤，繼續處理其他元件
                    pass
            
            # 從根視窗開始更新
            update_widget_fonts(self.root)
            
        except Exception as e:
            print(f"更新 Combobox 字型錯誤: {e}")

    def on_window_resize(self, event):
        """視窗大小變更事件處理 - 響應式佈局優化"""
        # 只處理主視窗的調整事件
        if event.widget == self.root:
            try:
                # 取消之前的延遲更新
                if hasattr(self, '_resize_after_id'):
                    self.root.after_cancel(self._resize_after_id)
                
                # 延遲更新佈局，避免頻繁調整造成的性能問題
                self._resize_after_id = self.root.after(50, self._delayed_layout_update)
                
            except Exception as e:
                # 靜默處理佈局更新錯誤，不影響功能
                pass
    
    def _delayed_layout_update(self):
        """延遲的佈局更新 - 提升響應式性能"""
        try:
            # 確保主容器正確調整大小
            if hasattr(self, 'main_container'):
                self.main_container.update_idletasks()
            
            # 確保頁籤容器正確調整大小
            if hasattr(self, 'notebook'):
                self.notebook.update_idletasks()
            
            # 更新所有頁籤的佈局
            self._update_tab_layouts()
            
        except Exception as e:
            # 靜默處理佈局更新錯誤，不影響功能
            pass
    
    def _update_tab_layouts(self):
        """更新所有頁籤的響應式佈局 - 不修改功能，只調整佈局"""
        try:
            # 獲取當前視窗大小
            window_width = self.root.winfo_width()
            window_height = self.root.winfo_height()
            
            # 只更新佈局相關的設定，不修改功能邏輯
            if hasattr(self, 'notebook'):
                # 強制更新主容器佈局
                if hasattr(self, 'main_container'):
                    self.main_container.update_idletasks()
                
                # 確保頁籤容器填滿可用空間
                self.notebook.update_idletasks()
                
                # 更新每個頁籤的佈局
                for tab_id in self.notebook.tabs():
                    tab_widget = self.notebook.nametowidget(tab_id)
                    if hasattr(tab_widget, 'update_idletasks'):
                        tab_widget.update_idletasks()
                        
                        # 確保頁籤內容的響應式佈局
                        for child in tab_widget.winfo_children():
                            if hasattr(child, 'update_idletasks'):
                                child.update_idletasks()
                        
        except Exception as e:
            # 靜默處理，不影響功能
            pass
    
    def on_closing(self):
        """應用程式關閉事件處理"""
        try:
            # 停止監控
            if hasattr(self, 'monitoring_running') and self.monitoring_running:
                self.stop_monitoring()
            
            # 停止資料夾監控
            if hasattr(self, 'folder_monitoring_var') and self.folder_monitoring_var.get():
                self.stop_folder_monitoring()
            
            # 儲存配置
            self._save_config()
            
            # 記錄關閉事件
            logging_service.info("應用程式正常關閉")
            
        except Exception as e:
            logging_service.error(f"關閉應用程式時發生錯誤: {e}")
        finally:
            self.root.destroy()
        
    def _initialize_styles(self):
        """設定應用程式的 TTK 樣式"""
        self.style = ttk.Style()
        
        # 根據平台選擇最佳主題
        available_themes = self.style.theme_names()
        selected_theme = 'default'
        
        if platform_adapter.is_macos() and 'aqua' in available_themes:
            selected_theme = 'aqua'
        elif platform_adapter.is_windows() and 'vista' in available_themes:
            selected_theme = 'vista'
        elif 'clam' in available_themes:
            selected_theme = 'clam'
        
        self.style.theme_use(selected_theme)
        logging_service.info(f"使用主題: {selected_theme}")
        
        self.colors = {
            "background": "#2E2E2E",
            "foreground": "#DCDCDC", 
            "frame_bg": "#3C3C3C",
            "accent_green": "#50C878",
            "accent_blue": "#6495ED",
            "accent_purple": "#9370DB",
            "status_bg": "#4A4A4A",
            "border_color": "#555555",
            "input_bg": "#4A4A4A",
            "input_fg": "#DCDCDC",
            "fail_red": "#FF6347"
        }
        
        self.root.configure(bg=self.colors["background"])
        self.style.configure('.', background=self.colors["background"], foreground=self.colors["foreground"])
        self.style.configure('TFrame', background=self.colors["background"])
        self.style.configure('TNotebook', background=self.colors["background"], borderwidth=0)
        self.style.configure('TNotebook.Tab', background="#505050", foreground="#FFFFFF", padding=[10, 5])
        self.style.map('TNotebook.Tab', background=[('selected', self.colors["accent_blue"])])
        self.style.configure('TLabelframe', background=self.colors["background"], bordercolor=self.colors["border_color"])
        self.style.configure('TLabelframe.Label', background=self.colors["background"], foreground=self.colors["foreground"])
        self.style.configure('TLabel', background=self.colors["background"], foreground=self.colors["foreground"])
        self.style.configure('TEntry', fieldbackground=self.colors["input_bg"], foreground=self.colors["input_fg"], insertcolor=self.colors["input_fg"])
        self.style.configure('TButton', padding=6)
        self.style.configure('Accent.TButton', background=self.colors["accent_green"], foreground='white')
        self.style.configure('Optional.TButton', background=self.colors["accent_blue"], foreground='white')
        self.style.configure('AI.TButton', background=self.colors["accent_purple"], foreground='white')
        self.style.configure('Stop.TButton', background=self.colors["fail_red"], foreground='white')
        self.style.configure('Treeview', fieldbackground=self.colors["input_bg"], background=self.colors["input_bg"], foreground=self.colors["input_fg"])
        self.style.map('Treeview', background=[('selected', self.colors["accent_blue"])])
        
    def _load_config(self):
        """載入配置設定"""
        config = self.config_service.get_config()
        
        self.api_key_var = tk.StringVar(value=config.api_key)
        self.ai_model_var = tk.StringVar(value=config.ai_model)
        self.source_folder_var = tk.StringVar(value=config.source_folder)
        self.processed_folder_var = tk.StringVar(value=config.processed_folder)
        
    def _save_config(self):
        """儲存目前的設定"""
        try:
            self.config_service.update_config(
                api_key=self.api_key_var.get(),
                ai_model=self.ai_model_var.get(),
                source_folder=self.source_folder_var.get(),
                processed_folder=self.processed_folder_var.get()
            )
        except Exception as e:
            self.log_message(f"儲存設定失敗: {e}", is_error=True)
            
    def _initialize_opencc_converter(self):
        """初始化 OpenCC 轉換器"""
        if not _OPENCC_IMPORTED:
            self.log_message("OpenCC 函式庫未導入，繁體中文轉換功能將不可用。", is_warning=True, log_area_ref=self.transcribe_log_area)
            return
            
        try:
            self.opencc_converter = opencc.OpenCC('s2t')
            self.log_message("OpenCC 轉換器初始化成功。", log_area_ref=self.transcribe_log_area)
        except Exception as e:
            self.opencc_converter = None
            self.log_message(f"初始化 OpenCC 轉換器失敗: {e}", is_error=True, log_area_ref=self.transcribe_log_area)
            
    def process_log_queue(self):
        """處理來自背景執行緒的日誌訊息"""
        while not self.log_queue.empty():
            try:
                message, log_area_ref = self.log_queue.get_nowait()
                timestamp = time.strftime("%H:%M:%S")
                full_message = f"[{timestamp}] {message}\n"
                
                log_area_ref.config(state=tk.NORMAL)
                log_area_ref.insert(tk.END, full_message)
                log_area_ref.see(tk.END)
                log_area_ref.config(state=tk.DISABLED)
            except Exception:
                pass
                
        self.root.after(100, self.process_log_queue)
        
    def create_main_widgets(self):
        """建立主視窗的頁籤介面 - 響應式佈局優化"""
        # 建立主容器框架，確保響應式佈局
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # 設定主容器的網格權重 - 確保完全響應式
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)
        
        # 建立頁籤容器，使用 pack 佈局以獲得更好的響應式控制
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # 建立滾動容器包裝系統 - 確保所有內容都可見
        self.transcribe_scroll_container = self._create_scrollable_tab_container(self.notebook)
        self.ai_scroll_container = self._create_scrollable_tab_container(self.notebook)
        self.ai_image_scroll_container = self._create_scrollable_tab_container(self.notebook)
        self.archive_scroll_container = self._create_scrollable_tab_container(self.notebook)
        self.search_scroll_container = self._create_scrollable_tab_container(self.notebook)
        self.monitoring_scroll_container = self._create_scrollable_tab_container(self.notebook)
        self.diagnostic_scroll_container = self._create_scrollable_tab_container(self.notebook)
        self.settings_scroll_container = self._create_scrollable_tab_container(self.notebook)
        
        # 建立頁籤內容框架 (放在滾動容器內)
        self.transcribe_tab = self.transcribe_scroll_container['content_frame']
        self.ai_tab = self.ai_scroll_container['content_frame']
        self.ai_image_tab = self.ai_image_scroll_container['content_frame']
        self.archive_tab = self.archive_scroll_container['content_frame']
        self.search_tab = self.search_scroll_container['content_frame']
        self.monitoring_tab = self.monitoring_scroll_container['content_frame']
        self.diagnostic_tab = self.diagnostic_scroll_container['content_frame']
        self.settings_tab = self.settings_scroll_container['content_frame']
        
        # 將滾動容器加入到 notebook
        self.notebook.add(self.transcribe_scroll_container['container'], text=' 🎤 語音轉錄 ')
        self.notebook.add(self.ai_scroll_container['container'], text=' 🤖 AI 功能 ')
        self.notebook.add(self.ai_image_scroll_container['container'], text=' 🎨 AI 圖像生成 ')
        self.notebook.add(self.archive_scroll_container['container'], text=' 🗂️ AI 媒體庫歸檔 ')
        self.notebook.add(self.search_scroll_container['container'], text=' 🔍 媒體搜尋 ')
        self.notebook.add(self.monitoring_scroll_container['container'], text=' 📊 系統監控 ')
        self.notebook.add(self.diagnostic_scroll_container['container'], text=' 🔧 系統診斷 ')
        self.notebook.add(self.settings_scroll_container['container'], text=' ⚙️ 設定 ')
        
        self.create_transcribe_tab()
        self.create_ai_tab()
        self.create_ai_image_tab()
        self.create_archive_tab()
        self.create_search_tab()
        self.create_monitoring_tab()
        self.create_diagnostic_tab()
        self.create_settings_tab()
    
    def _create_scrollable_tab_container(self, parent):
        """建立滾動頁籤容器 - 確保內容始終可見"""
        # 外層容器
        container = ttk.Frame(parent)
        
        # 建立畫布和滾動條
        canvas = tk.Canvas(container, highlightthickness=0)
        v_scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        h_scrollbar = ttk.Scrollbar(container, orient="horizontal", command=canvas.xview)
        
        # 內容框架 (這是實際放置功能的地方)
        content_frame = ttk.Frame(canvas, padding=5)
        
        # 配置滾動
        def update_scroll_region(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # 讓內容框架適應畫布寬度
            canvas_width = canvas.winfo_width()
            if canvas_width > 1:
                canvas.itemconfig(canvas_window, width=canvas_width)
        
        content_frame.bind("<Configure>", update_scroll_region)
        
        # 建立畫布視窗
        canvas_window = canvas.create_window((0, 0), window=content_frame, anchor="nw")
        
        # 配置滾動條
        canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # 佈局
        canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # 設定權重
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        
        # 滑鼠滾輪支援
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def bind_mousewheel(event):
            canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        def unbind_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
        
        canvas.bind('<Enter>', bind_mousewheel)
        canvas.bind('<Leave>', unbind_mousewheel)
        
        # 畫布大小調整處理
        def on_canvas_configure(event):
            update_scroll_region()
        
        canvas.bind('<Configure>', on_canvas_configure)
        
        return {
            'container': container,
            'canvas': canvas,
            'content_frame': content_frame,
            'v_scrollbar': v_scrollbar,
            'h_scrollbar': h_scrollbar
        }
    



    def _setup_scrollable_container(self, container, scrollable_content):
        """設定滾動容器 - 響應式佈局優化 (保留舊方法以防相容性問題)"""
        # 建立畫布和滾動條
        canvas = tk.Canvas(container, highlightthickness=0)
        v_scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        h_scrollbar = ttk.Scrollbar(container, orient="horizontal", command=canvas.xview)
        
        # 配置滾動
        def _configure_scroll_region(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        scrollable_content.bind("<Configure>", _configure_scroll_region)
        
        # 建立視窗
        canvas_window = canvas.create_window((0, 0), window=scrollable_content, anchor="nw")
        
        # 配置畫布滾動
        canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # 佈局滾動條和畫布
        canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # 設定網格權重
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        
        # 綁定滑鼠滾輪事件
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
        
        canvas.bind('<Enter>', _bind_mousewheel)
        canvas.bind('<Leave>', _unbind_mousewheel)
        
        # 處理畫布大小調整
        def _on_canvas_configure(event):
            # 更新滾動區域
            canvas.configure(scrollregion=canvas.bbox("all"))
            # 調整內容框架寬度以適應畫布
            if event.width > 1:  # 避免無效寬度
                canvas.itemconfig(canvas_window, width=event.width)
        
        canvas.bind('<Configure>', _on_canvas_configure)
        
    def log_message(self, message, is_error=False, is_warning=False, is_success=False, log_area_ref=None):
        """在指定的日誌區域顯示訊息"""
        if not hasattr(self, 'notebook'):
            print(f"LOG (UI not ready): {message}")
            return
            
        if log_area_ref is None:
            try:
                current_tab_widget = self.notebook.nametowidget(self.notebook.select())
                if current_tab_widget == self.transcribe_tab:
                    log_area_ref = self.transcribe_log_area
                elif current_tab_widget == self.archive_tab:
                    log_area_ref = self.archive_log_area
                else:
                    print(message)
                    return
            except tk.TclError:
                print(message)
                return
                
        timestamp = time.strftime("%H:%M:%S")
        prefix = f"[{timestamp}] "
        tag = None
        
        if is_error:
            prefix += "錯誤: "
            tag = "error"
        elif is_warning:
            prefix += "警告: "
            tag = "warning"
        elif is_success:
            prefix += "成功: "
            tag = "success"
            
        full_message = prefix + str(message) + "\n"
        
        def _append_log():
            if not log_area_ref.winfo_exists():
                return
            log_area_ref.config(state=tk.NORMAL)
            log_area_ref.insert(tk.END, full_message, tag)
            log_area_ref.see(tk.END)
            log_area_ref.config(state=tk.DISABLED)
            
        if self.root.winfo_exists():
            self.root.after(0, _append_log)

    # ===============================================================
    # SECTION 2.1: 語音轉錄頁籤
    # ===============================================================
    def create_transcribe_tab(self):
        # --- 介面佈局 ---
        main_frame = ttk.Frame(self.transcribe_tab)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        top_frame.columnconfigure(1, weight=1)
        
        # 檔案選擇區域
        file_section = ttk.LabelFrame(top_frame, text="📁 檔案選擇", padding=10)
        file_section.pack(fill=tk.X, pady=(0, 10))
        
        # 音頻/視頻檔案選擇
        file_frame = ttk.Frame(file_section)
        file_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(file_frame, text="選擇音頻/視頻檔案", command=self.select_file, width=20).pack(side=tk.LEFT)
        self.file_label = ttk.Label(file_frame, text="未選擇檔案", anchor="w", foreground="gray")
        self.file_label.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)
        
        # 輸出目錄選擇
        output_frame = ttk.Frame(file_section)
        output_frame.pack(fill=tk.X)
        ttk.Button(output_frame, text="選擇輸出目錄", command=self.select_output_dir, width=20).pack(side=tk.LEFT)
        self.output_dir_label = ttk.Label(output_frame, text="預設為來源檔案目錄", anchor="w", foreground="gray")
        self.output_dir_label.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)
        
        # 設定區域 - 重新設計為更協調的佈局
        settings_container = ttk.Frame(main_frame)
        settings_container.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 左側設定區
        left_panel = ttk.Frame(settings_container)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # 轉錄設定
        transcribe_settings = ttk.LabelFrame(left_panel, text="🎯 轉錄設定", padding=10)
        transcribe_settings.pack(fill=tk.X, pady=(0, 10))
        
        # 模型選擇
        model_row = ttk.Frame(transcribe_settings)
        model_row.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(model_row, text="轉錄模型:", width=12).pack(side=tk.LEFT)
        
        # 重新定義模型選項，移除有問題的v3模型
        self.model_display_options = [
            "Medium (中等) - 預設推薦",
            "Large-v2 (大型) - 較少幻覺，建議使用"
        ]
        
        # 對應的實際模型鍵值
        self.model_key_mapping = {
            "Medium (中等) - 預設推薦": "Medium (中等)",
            "Large-v2 (大型) - 較少幻覺，建議使用": "Large-v2 (大型)"
        }
        
        self.model_combobox = ttk.Combobox(model_row, values=self.model_display_options, 
                                          state="readonly", width=35)
        self.model_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.model_combobox.set("Medium (中等) - 預設推薦")
        
        # 綁定選擇事件來更新實際的模型變數
        def on_model_select(event):
            selected_display = self.model_combobox.get()
            actual_key = self.model_key_mapping.get(selected_display, "Medium (中等)")
            self.selected_model_key.set(actual_key)
        
        self.model_combobox.bind('<<ComboboxSelected>>', on_model_select)
        self.selected_model_key.set("Medium (中等)")
        
        # 語言選擇
        lang_row = ttk.Frame(transcribe_settings)
        lang_row.pack(fill=tk.X)
        ttk.Label(lang_row, text="音檔語言:", width=12).pack(side=tk.LEFT)
        
        # 語言選項
        self.language_options = [
            ("中文", "zh"),
            ("英文", "en"), 
            ("韓文", "ko"),
            ("日文", "ja")
        ]
        
        self.language_combobox = ttk.Combobox(lang_row, 
                                            values=[option[0] for option in self.language_options],
                                            state="readonly", width=15)
        self.language_combobox.pack(side=tk.LEFT)
        self.language_combobox.set("中文")  # 預設為中文
        
        # 綁定選擇事件來更新語言變數
        def on_language_select(event):
            selected_display = self.language_combobox.get()
            for display, code in self.language_options:
                if display == selected_display:
                    self.selected_language.set(code)
                    break
        
        self.language_combobox.bind('<<ComboboxSelected>>', on_language_select)
        
        # 輸出格式設定
        output_settings = ttk.LabelFrame(left_panel, text="📄 輸出格式", padding=10)
        output_settings.pack(fill=tk.X)
        
        # 格式選項 - 重新排列
        format_row1 = ttk.Frame(output_settings)
        format_row1.pack(fill=tk.X, pady=(0, 5))
        ttk.Checkbutton(format_row1, text="SRT", variable=self.output_srt).pack(side=tk.LEFT, padx=(0, 15))
        ttk.Checkbutton(format_row1, text="TXT", variable=self.output_txt).pack(side=tk.LEFT, padx=(0, 15))
        ttk.Checkbutton(format_row1, text="VTT", variable=self.output_vtt).pack(side=tk.LEFT, padx=(0, 15))
        
        format_row2 = ttk.Frame(output_settings)
        format_row2.pack(fill=tk.X, pady=(0, 8))
        ttk.Checkbutton(format_row2, text="LRC", variable=self.output_lrc).pack(side=tk.LEFT, padx=(0, 15))
        ttk.Checkbutton(format_row2, text="CSV", variable=self.output_csv).pack(side=tk.LEFT, padx=(0, 15))
        
        # 後處理選項
        ttk.Separator(output_settings, orient='horizontal').pack(fill=tk.X, pady=(0, 8))
        
        post_process_row1 = ttk.Frame(output_settings)
        post_process_row1.pack(fill=tk.X, pady=(0, 3))
        self.segmentation_checkbox = ttk.Checkbutton(post_process_row1, text="啟用智能斷句", variable=self.enable_segmentation)
        self.segmentation_checkbox.pack(anchor='w')
        
        post_process_row2 = ttk.Frame(output_settings)
        post_process_row2.pack(fill=tk.X, pady=(0, 3))
        self.remove_punct_checkbox = ttk.Checkbutton(post_process_row2, text="移除輸出標點符號", variable=self.remove_punctuation)
        self.remove_punct_checkbox.pack(anchor='w')
        
        post_process_row3 = ttk.Frame(output_settings)
        post_process_row3.pack(fill=tk.X)
        self.traditional_chinese_checkbox = ttk.Checkbutton(post_process_row3, text="簡體轉繁體中文", variable=self.convert_to_traditional_chinese)
        self.traditional_chinese_checkbox.pack(anchor='w')
        
        # 右側設定區
        right_panel = ttk.Frame(settings_container)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # 提示詞設定
        prompt_settings = ttk.LabelFrame(right_panel, text="💡 提示詞 (可選)", padding=10)
        prompt_settings.pack(fill=tk.BOTH, expand=True)
        
        # 提示詞說明
        prompt_help = ttk.Label(prompt_settings, text="輸入提示詞可提高轉錄準確度，詞彙間用空格分隔", 
                               font=('Arial', 9), foreground='gray')
        prompt_help.pack(anchor='w', pady=(0, 8))
        
        # 提示詞輸入框
        self.transcribe_prompt_widget = tk.Text(prompt_settings, height=8, wrap=tk.WORD, font=('Arial', 10),
                                               bg=self.colors.get("input_bg", "#3A3A3A"),
                                               fg='white',
                                               insertbackground='white')
        self.transcribe_prompt_widget.pack(fill=tk.BOTH, expand=True)
        
        # 在 Text 元件中加入佔位符文字
        transcribe_placeholder_text = "範例：張三 李四 王五 台積電 聯發科 機器學習 深度學習\n\n• 詞彙間用空格分隔\n• 輸入專有名詞、人名、公司名等\n• 可提高特定詞彙的識別準確度"
        self.transcribe_prompt_widget.insert('1.0', transcribe_placeholder_text)
        self.transcribe_prompt_widget.config(foreground='gray')
        
        # 綁定焦點事件來處理佔位符
        def on_transcribe_prompt_focus_in(event):
            if self.transcribe_prompt_widget.get('1.0', 'end-1c') == transcribe_placeholder_text:
                self.transcribe_prompt_widget.delete('1.0', tk.END)
                self.transcribe_prompt_widget.config(foreground='white')
        
        def on_transcribe_prompt_focus_out(event):
            if not self.transcribe_prompt_widget.get('1.0', 'end-1c').strip():
                self.transcribe_prompt_widget.insert('1.0', transcribe_placeholder_text)
                self.transcribe_prompt_widget.config(foreground='gray')
        
        self.transcribe_prompt_widget.bind('<FocusIn>', on_transcribe_prompt_focus_in)
        self.transcribe_prompt_widget.bind('<FocusOut>', on_transcribe_prompt_focus_out)
        

        
        # 動作按鈕區域
        action_section = ttk.Frame(main_frame)
        action_section.pack(fill=tk.X, pady=(10, 5))
        
        # 按鈕容器
        button_container = ttk.Frame(action_section)
        button_container.pack()
        
        self.transcribe_btn = ttk.Button(button_container, text="🚀 開始轉錄", 
                                       command=self.start_transcription_thread, 
                                       style='Accent.TButton',
                                       width=15)
        self.transcribe_btn.pack(pady=5)
        
        # 日誌區域
        log_section = ttk.LabelFrame(main_frame, text="📋 執行日誌", padding=10)
        log_section.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        self.transcribe_log_area = scrolledtext.ScrolledText(log_section, 
                                                           wrap=tk.WORD, 
                                                           height=8, 
                                                           font=self.fonts['console'],
                                                           bg=self.colors.get("input_bg", "#2B2B2B"),
                                                           fg='white',
                                                           insertbackground='white')
        self.transcribe_log_area.pack(fill=tk.BOTH, expand=True)
        self.transcribe_log_area.config(state=tk.DISABLED)
        self.transcribe_log_area.tag_config("error", foreground=self.colors["fail_red"])
        self.transcribe_log_area.tag_config("warning", foreground="#FFA500")
        self.transcribe_log_area.tag_config("success", foreground=self.colors["accent_green"])

    # ===============================================================
    # SECTION 2.2: AI 功能頁籤
    # ===============================================================
    def create_ai_tab(self):
        """建立 AI 功能頁籤"""
        # 主框架
        main_frame = ttk.Frame(self.ai_tab)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 標題
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(title_frame, text="🤖 AI 智能處理功能", style='Title.TLabel').pack(side=tk.LEFT)
        
        # 說明文字
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(0, 15))
        info_text = "使用 Google Gemini AI 對 SRT 字幕檔案進行智能分析、校正、翻譯等處理。請先載入 SRT 檔案並設定 API 金鑰。"
        ttk.Label(info_frame, text=info_text, style='Info.TLabel', wraplength=800).pack(anchor='w')
        
        # 建立左右分欄 - 使用 grid 精確控制比例
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 配置 grid 權重：左側 35%，右側 65%
        content_frame.grid_columnconfigure(0, weight=35)  # 左側較窄
        content_frame.grid_columnconfigure(1, weight=65)  # 右側較寬
        content_frame.grid_rowconfigure(0, weight=1)
        
        # 左側：檔案載入和日誌
        left_frame = ttk.Frame(content_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # 右側：AI 設定和功能
        right_frame = ttk.Frame(content_frame)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        # === 左側內容 ===
        
        # SRT 檔案載入區塊
        file_frame = ttk.Labelframe(left_frame, text="SRT 檔案載入", padding=10)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 檔案選擇按鈕
        file_button_frame = ttk.Frame(file_frame)
        file_button_frame.pack(fill=tk.X, pady=2)
        ttk.Button(file_button_frame, text="選擇 SRT 檔案", command=self.select_srt_for_ai).pack(side=tk.LEFT)
        self.ai_file_label = ttk.Label(file_button_frame, text="未選擇檔案", anchor="w")
        self.ai_file_label.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)
        
        # 檔案資訊顯示
        self.ai_file_info_label = ttk.Label(file_frame, text="", style='Info.TLabel')
        self.ai_file_info_label.pack(anchor='w', pady=(5, 0))
        
        # AI 處理日誌 - 限制高度，確保按鈕可見
        self.ai_log_frame = ttk.Labelframe(left_frame, text="處理日誌", padding=5)
        self.ai_log_frame.pack(fill=tk.X, expand=False)  # 改為不擴展
        
        # 建立日誌顯示區域
        log_text_frame = ttk.Frame(self.ai_log_frame)
        log_text_frame.pack(fill=tk.BOTH, expand=False)  # 改為不擴展
        
        # 設定較小的固定高度，讓按鈕更容易看到
        self.ai_log_area = tk.Text(log_text_frame, height=6, wrap=tk.WORD, font=('Consolas', 9))  # 減少高度
        ai_log_scrollbar = ttk.Scrollbar(log_text_frame, orient=tk.VERTICAL, command=self.ai_log_area.yview)
        self.ai_log_area.configure(yscrollcommand=ai_log_scrollbar.set)
        
        self.ai_log_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=False)  # 改為不擴展
        ai_log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # === 右側內容 ===
        
        # AI 基本設定
        ai_config_frame = ttk.Labelframe(right_frame, text="AI 設定", padding=10)
        ai_config_frame.pack(fill=tk.X, pady=(0, 10))
        ai_config_frame.columnconfigure(1, weight=1)
        
        # API 金鑰
        ttk.Label(ai_config_frame, text="Google AI API 金鑰:").grid(row=0, column=0, sticky="w", pady=2)
        self.ai_api_key_entry = ttk.Entry(ai_config_frame, textvariable=self.api_key_var, show="*")
        self.ai_api_key_entry.grid(row=0, column=1, sticky="ew", pady=2, padx=5)
        
        # AI 模型名稱
        ttk.Label(ai_config_frame, text="AI 模型名稱:").grid(row=1, column=0, sticky="w", pady=2)
        self.ai_model_entry_tab = ttk.Entry(ai_config_frame, textvariable=self.ai_model_var)
        self.ai_model_entry_tab.grid(row=1, column=1, sticky="ew", pady=2, padx=5)
        
        # 批次大小設定
        ttk.Label(ai_config_frame, text="批次大小:").grid(row=2, column=0, sticky="w", pady=2)
        batch_frame_ai = ttk.Frame(ai_config_frame)
        batch_frame_ai.grid(row=2, column=1, sticky="ew", pady=2, padx=5)
        self.ai_batch_size_entry = ttk.Entry(batch_frame_ai, textvariable=self.batch_size_var, width=5)
        self.ai_batch_size_entry.pack(side=tk.LEFT)
        ttk.Label(batch_frame_ai, text="條字幕/批次", font=('Arial', 9)).pack(side=tk.LEFT, padx=(5,0))
        
        # 翻譯目標語言設定
        ttk.Label(ai_config_frame, text="翻譯語言:").grid(row=3, column=0, sticky="w", pady=2)
        self.translation_language_var = tk.StringVar(value="English")
        translation_languages = [
            "Chinese (中文繁體)",
            "English (英文)",
            "Japanese (日文)", 
            "Korean (韓文)",
            "French (法文)",
            "German (德文)",
            "Spanish (西班牙文)",
            "Italian (義大利文)",
            "Russian (俄文)",
            "Thai (泰文)",
            "Vietnamese (越南文)"
        ]
        self.translation_language_combo = ttk.Combobox(ai_config_frame, textvariable=self.translation_language_var, 
                                                      values=translation_languages, state="readonly", width=20)
        self.translation_language_combo.grid(row=3, column=1, sticky="ew", pady=2, padx=5)
        
        # AI 專用提示詞
        ai_prompt_frame = ttk.Labelframe(right_frame, text="AI 提示詞 (可選)", padding=5)
        ai_prompt_frame.pack(fill=tk.X, pady=(0, 10))
        
        # AI 提示詞說明
        ai_prompt_help = ttk.Label(ai_prompt_frame, text="輸入提示詞可提高 AI 處理準確度，詞彙間用空格分隔", 
                                  font=('Arial', 9), foreground='gray')
        ai_prompt_help.pack(anchor='w', pady=(0,5))
        
        # AI 提示詞輸入框
        self.ai_prompt_widget = tk.Text(ai_prompt_frame, height=4, wrap=tk.WORD, font=('Arial', 10),
                                       bg=self.colors.get("input_bg", "#3A3A3A"),
                                       fg='white',
                                       insertbackground='white')
        self.ai_prompt_widget.pack(fill=tk.BOTH, expand=True)
        
        # AI 提示詞佔位符
        ai_placeholder_text = "範例：張三 李四 王五 台積電 聯發科 機器學習 深度學習\n\n• 詞彙間用空格分隔\n• 輸入專有名詞、人名、公司名等"
        self.ai_prompt_widget.insert('1.0', ai_placeholder_text)
        self.ai_prompt_widget.config(foreground='gray')
        
        # 綁定 AI 提示詞焦點事件
        def on_ai_prompt_focus_in(event):
            if self.ai_prompt_widget.get('1.0', 'end-1c') == ai_placeholder_text:
                self.ai_prompt_widget.delete('1.0', tk.END)
                self.ai_prompt_widget.config(foreground='white')
        
        def on_ai_prompt_focus_out(event):
            if not self.ai_prompt_widget.get('1.0', 'end-1c').strip():
                self.ai_prompt_widget.insert('1.0', ai_placeholder_text)
                self.ai_prompt_widget.config(foreground='gray')
        
        self.ai_prompt_widget.bind('<FocusIn>', on_ai_prompt_focus_in)
        self.ai_prompt_widget.bind('<FocusOut>', on_ai_prompt_focus_out)
        
        # AI 功能區塊
        ai_functions_frame = ttk.Labelframe(right_frame, text="AI 功能", padding=10)
        ai_functions_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 功能按鈕
        button_grid = ttk.Frame(ai_functions_frame)
        button_grid.pack(fill=tk.X)
        
        # AI功能按鈕 - 響應式網格佈局
        buttons_frame = ttk.Frame(button_grid)
        buttons_frame.pack(fill=tk.X, pady=2)
        
        # 使用 grid 佈局實現響應式按鈕排列
        # 第一行：AI分析、AI校正、AI翻譯
        self.ai_analyze_button_tab = ttk.Button(buttons_frame, text="AI 分析", command=self.ai_analyze_srt, style='AI.TButton', state=tk.DISABLED, width=8)
        self.ai_analyze_button_tab.grid(row=0, column=0, padx=1, pady=1, sticky="ew")
        
        self.ai_correct_button_tab = ttk.Button(buttons_frame, text="AI 校正", command=self.ai_correct_srt, style='AI.TButton', state=tk.DISABLED, width=8)
        self.ai_correct_button_tab.grid(row=0, column=1, padx=1, pady=1, sticky="ew")
        
        self.ai_translate_button_tab = ttk.Button(buttons_frame, text="AI 翻譯", command=self.ai_translate_srt_placeholder, style='AI.TButton', state=tk.DISABLED, width=8)
        self.ai_translate_button_tab.grid(row=0, column=2, padx=1, pady=1, sticky="ew")
        
        # 第二行：AI社群、AI新聞
        self.ai_social_button_tab = ttk.Button(buttons_frame, text="AI 社群", command=self.ai_generate_social_media, style='AI.TButton', state=tk.DISABLED, width=8)
        self.ai_social_button_tab.grid(row=1, column=0, padx=1, pady=1, sticky="ew")
        
        self.ai_news_button_tab = ttk.Button(buttons_frame, text="AI 新聞", command=self.ai_generate_news_report, style='AI.TButton', state=tk.DISABLED, width=8)
        self.ai_news_button_tab.grid(row=1, column=1, padx=1, pady=1, sticky="ew")
        
        # 設定列權重，讓按鈕能夠平均分配寬度，但設定最小寬度
        buttons_frame.grid_columnconfigure(0, weight=1, minsize=80)
        buttons_frame.grid_columnconfigure(1, weight=1, minsize=80)
        buttons_frame.grid_columnconfigure(2, weight=1, minsize=80)
        
        # 狀態顯示
        status_frame = ttk.Labelframe(right_frame, text="狀態", padding=5)
        status_frame.pack(fill=tk.X)
        
        self.ai_status_label = ttk.Label(status_frame, text="請載入 SRT 檔案並設定 API 金鑰", style='Info.TLabel')
        self.ai_status_label.pack(anchor='w')
        
        # 初始化 AI 頁籤的變數
        self.ai_srt_file_path = None
        self.ai_srt_entries = []
        
        # 記錄初始化完成
        self.log_message("AI 功能頁籤已初始化", log_area_ref=self.ai_log_area)
    
    def select_srt_for_ai(self):
        """為 AI 功能選擇 SRT 檔案"""
        filetypes = [("SRT 字幕檔案", "*.srt"), ("所有檔案", "*.*")]
        selected = filedialog.askopenfilename(filetypes=filetypes)
        if selected:
            self.ai_srt_file_path = selected
            filename = os.path.basename(selected)
            self.ai_file_label.config(text=filename)
            
            # 讀取並解析 SRT 檔案
            try:
                import srt
                with open(selected, 'r', encoding='utf-8') as f:
                    srt_content = f.read()
                
                self.ai_srt_entries = list(srt.parse(srt_content))
                entry_count = len(self.ai_srt_entries)
                
                # 更新檔案資訊
                self.ai_file_info_label.config(text=f"已載入 {entry_count} 條字幕")
                
                # 更新狀態
                api_key = self.api_key_var.get().strip()
                if api_key:
                    self.ai_status_label.config(text=f"已載入 {filename} ({entry_count} 條字幕)，可開始 AI 處理")
                else:
                    self.ai_status_label.config(text=f"已載入 {filename}，請設定 API 金鑰")
                
                # 更新按鈕狀態
                self.update_ai_buttons_state_tab()
                
                self.log_message(f"已載入 SRT 檔案: {filename} ({entry_count} 條字幕)", log_area_ref=self.ai_log_area)
                
            except Exception as e:
                error_msg = f"載入 SRT 檔案失敗: {str(e)}"
                self.log_message(error_msg, is_error=True, log_area_ref=self.ai_log_area)
                messagebox.showerror("檔案載入錯誤", error_msg)
    
    def update_ai_buttons_state_tab(self):
        """更新 AI 頁籤中的按鈕狀態"""
        api_key_present = bool(self.api_key_var.get().strip())
        srt_loaded = bool(self.ai_srt_file_path and self.ai_srt_entries)
        ai_idle = not self.is_ai_correcting and not self.is_ai_analyzing and not self.is_ai_translating and not self.is_ai_generating_news and not self.is_ai_generating_social
        
        state = tk.NORMAL if api_key_present and srt_loaded and ai_idle else tk.DISABLED
        
        # 更新 AI 頁籤中的按鈕
        if hasattr(self, 'ai_correct_button_tab'):
            self.ai_correct_button_tab.config(state=state)
        if hasattr(self, 'ai_analyze_button_tab'):
            self.ai_analyze_button_tab.config(state=state)
        if hasattr(self, 'ai_translate_button_tab'):
            self.ai_translate_button_tab.config(state=state)
        if hasattr(self, 'ai_news_button_tab'):
            self.ai_news_button_tab.config(state=state)
        if hasattr(self, 'ai_social_button_tab'):
            self.ai_social_button_tab.config(state=state)
# 圖像生成按鈕已移至獨立頁籤
    
    # SECTION 2.3: 圖像生成功能 (已整合至 AI 功能頁籤)
    # ===============================================================
        # 圖像生成功能已整合至 AI 功能頁籤
        # 初始化必要的狀態變數供圖像生成功能使用
        
        # 圖像生成狀態 (基於 OkokGo 架構)
        self.image_generation_state = {
            'api_key': '',
            'prompt_model': 'gemini-2.5-flash',
            'image_model': 'imagen-3.0-generate-002',
            'art_style': 'digital illustration',
            'number_of_prompts': '20',
            'number_of_images': '1',
            'aspect_ratio': '16:9',
            'person_generation': 'allow_adult',
            'file_name': '',
            'transcript_content': '',
            'prompts': [],
            'images': [],
            'loading_prompts': False,
            'loading_images': False,
            'status_message': ''
        }
        
        # 初始化必要的變數供圖像生成功能使用
        self.creative_srt_file_path = None
        self.creative_srt_entries = []
        self.creative_api_key_var = tk.StringVar()
    
    # 移除的方法：browse_creative_srt_file, load_creative_srt_file, update_creative_buttons_state
    # 這些方法已不再需要，因為圖像生成功能已整合至 AI 功能頁籤
    
    def show_image_generation_interface(self):
        """顯示圖像生成介面 - 完全基於 OkokGo ImageGenerationSection 架構"""
        try:
            # 建立並顯示 OkokGo 圖像生成介面
            image_generator = ImageGenerationOkokGo(self.root)
            
            # 如果有現有的 API 金鑰，預設填入
            if hasattr(self, 'api_key_var') and self.api_key_var.get():
                image_generator.api_key = self.api_key_var.get()
            
            # 顯示介面
            image_generator.show_interface()
            
            self.log_message("圖像生成介面已開啟")
            
        except Exception as e:
            error_msg = f"開啟圖像生成介面失敗: {str(e)}"
            self.log_message(error_msg, is_error=True)
            messagebox.showerror("錯誤", error_msg)
        
        preview_frame = ttk.Frame(left_frame)
        preview_frame.grid(row=3, column=0, sticky='nsew')
        preview_frame.grid_columnconfigure(0, weight=1)
        preview_frame.grid_rowconfigure(0, weight=1)
        
        self.creative_srt_preview = tk.Text(preview_frame, wrap=tk.WORD, 
                                          bg=self.colors.get("input_bg", "#3A3A3A"), 
                                          fg=self.colors.get("input_fg", "#00FFFF"),
                                          insertbackground=self.colors.get("input_fg", "#00FFFF"))
        creative_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.creative_srt_preview.yview)
        self.creative_srt_preview.configure(yscrollcommand=creative_scrollbar.set)
        
        self.creative_srt_preview.grid(row=0, column=0, sticky='nsew')
        creative_scrollbar.grid(row=0, column=1, sticky='ns')
        
        # 右側框架 - AI創意功能區域（響應式 grid 佈局）
        right_frame = ttk.LabelFrame(main_frame, text="AI 創意功能", padding=10)
        right_frame.grid(row=0, column=1, sticky='nsew', padx=(5, 0))
        
        # 設定右側框架內部的響應式佈局
        right_frame.grid_columnconfigure(0, weight=1)
        right_frame.grid_rowconfigure(3, weight=1)  # 日誌區域可擴展
        
        # API設定區域
        api_frame = ttk.LabelFrame(right_frame, text="API 設定", padding=5)
        api_frame.grid(row=0, column=0, sticky='ew', pady=(0, 10))
        api_frame.grid_columnconfigure(0, weight=1)
        
        ttk.Label(api_frame, text="Google AI API 金鑰:", style='TLabel').grid(row=0, column=0, sticky='w')
        self.creative_api_key_var = tk.StringVar()
        try:
            # 新版本 Tkinter
            self.creative_api_key_var.trace_add('write', lambda *args: self.update_creative_buttons_state())
        except AttributeError:
            # 舊版本 Tkinter
            self.creative_api_key_var.trace('w', lambda *args: self.update_creative_buttons_state())
        self.creative_api_entry = ttk.Entry(api_frame, textvariable=self.creative_api_key_var, show="*")
        self.creative_api_entry.grid(row=1, column=0, sticky='ew', pady=(5, 0))
        
        # AI模型選擇
        model_frame = ttk.Frame(api_frame)
        model_frame.grid(row=2, column=0, sticky='ew', pady=(10, 0))
        model_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(model_frame, text="AI 模型:", style='TLabel').grid(row=0, column=0, sticky='w')
        self.creative_ai_model_var = tk.StringVar(value="gemini-2.5-flash")
        creative_model_combo = ttk.Combobox(model_frame, textvariable=self.creative_ai_model_var, 
                                          values=["gemini-2.5-flash", "gemini-1.5-pro", "gemini-1.5-flash"], 
                                          state="readonly")
        creative_model_combo.grid(row=0, column=1, sticky='ew', padx=(10, 0))
        
        # AI創意功能按鈕區域
        buttons_frame = ttk.LabelFrame(right_frame, text="創意AI功能", padding=10)
        buttons_frame.grid(row=1, column=0, sticky='ew', pady=(0, 10))
        buttons_frame.grid_columnconfigure(0, weight=1)
        
        # 功能按鈕網格
        button_grid = ttk.Frame(buttons_frame)
        button_grid.grid(row=0, column=0, sticky='ew')
        button_grid.grid_columnconfigure(0, weight=1)
        
        # 第一排：圖像相關功能
        image_row = ttk.Frame(button_grid)
        image_row.grid(row=0, column=0, sticky='ew', pady=2)
        
# 圖像生成功能已移至獨立頁籤
        
        # 預留未來功能按鈕位置
        # self.ai_video_prompt_button = ttk.Button(image_row, text="AI 影片提示", command=self.ai_generate_video_prompt, style='AI.TButton', state=tk.DISABLED)
        # self.ai_video_prompt_button.pack(side=tk.LEFT, padx=5)
        
        # 狀態顯示
        status_frame = ttk.Labelframe(right_frame, text="狀態", padding=5)
        status_frame.grid(row=2, column=0, sticky='ew')
        status_frame.grid_columnconfigure(0, weight=1)
        
        self.creative_status_label = ttk.Label(status_frame, text="請載入 SRT 檔案並設定 API 金鑰", style='Info.TLabel')
        self.creative_status_label.grid(row=0, column=0, sticky='w')
        
        # 日誌區域（可擴展）
        log_frame = ttk.LabelFrame(right_frame, text="執行日誌", padding=5)
        log_frame.grid(row=3, column=0, sticky='nsew', pady=(10, 0))
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)
        
        self.creative_log_area = tk.Text(log_frame, wrap=tk.WORD, 
                                       bg=self.colors.get("log_bg", "#2A2A2A"), 
                                       fg=self.colors.get("log_fg", "#00FF00"),
                                       insertbackground=self.colors.get("log_fg", "#00FF00"))
        creative_log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.creative_log_area.yview)
        self.creative_log_area.configure(yscrollcommand=creative_log_scrollbar.set)
        
        self.creative_log_area.grid(row=0, column=0, sticky='nsew')
        creative_log_scrollbar.grid(row=0, column=1, sticky='ns')
        
        # 初始化變數
        self.creative_srt_file_path = None
        self.creative_srt_entries = []
        
        # 圖像生成狀態 (基於 OkokGo 架構)
        self.image_generation_state = {
            'api_key': '',
            'prompt_model': 'gemini-2.5-flash',
            'image_model': 'imagen-3.0-generate-002',
            'art_style': 'a hyperrealistic masterpiece',
            'number_of_prompts': '20',
            'number_of_images': '1',
            'aspect_ratio': '16:9',
            'person_generation': 'allow_adult',
            'file_name': '',
            'transcript_content': '',
            'prompts': [],
            'images': [],
            'loading_prompts': False,
            'loading_images': False,
            'status_message': ''
        }
        
        # 初始日誌訊息
        self.log_message("AI 創意頁籤已初始化", log_area_ref=self.creative_log_area)
        self.log_message("支援功能：圖像提示生成（更多功能開發中...）", log_area_ref=self.creative_log_area)
    
    def browse_creative_srt_file(self):
        """瀏覽並載入SRT檔案到AI創意頁籤"""
        file_path = filedialog.askopenfilename(
            title="選擇 SRT 檔案",
            filetypes=[("SRT files", "*.srt"), ("All files", "*.*")]
        )
        
        if file_path:
            self.creative_srt_path_var.set(file_path)
            self.creative_srt_file_path = file_path
            self.load_creative_srt_file(file_path)
    
    def load_creative_srt_file(self, file_path):
        """載入SRT檔案到AI創意頁籤"""
        try:
            if not _SRT_IMPORTED:
                self.log_message("錯誤: 缺少 srt 函式庫", is_error=True, log_area_ref=self.creative_log_area)
                return
            
            import srt
            with open(file_path, 'r', encoding='utf-8') as f:
                srt_content = f.read()
            
            self.creative_srt_entries = list(srt.parse(srt_content))
            
            # 更新預覽
            self.creative_srt_preview.delete('1.0', tk.END)
            preview_text = ""
            for i, entry in enumerate(self.creative_srt_entries[:10]):  # 只顯示前10條
                preview_text += f"{entry.start} --> {entry.end}\n{entry.content}\n\n"
            
            if len(self.creative_srt_entries) > 10:
                preview_text += f"... 還有 {len(self.creative_srt_entries) - 10} 條字幕"
            
            self.creative_srt_preview.insert('1.0', preview_text)
            
            self.log_message(f"成功載入 SRT 檔案: {os.path.basename(file_path)}", log_area_ref=self.creative_log_area)
            self.log_message(f"共 {len(self.creative_srt_entries)} 條字幕", log_area_ref=self.creative_log_area)
            
            # 更新按鈕狀態
            self.update_creative_buttons_state()
            
        except Exception as e:
            self.log_message(f"載入 SRT 檔案失敗: {str(e)}", is_error=True, log_area_ref=self.creative_log_area)
    
    def update_creative_buttons_state(self):
        """更新AI創意頁籤按鈕狀態"""
        api_key_present = bool(self.creative_api_key_var.get().strip())
        srt_loaded = bool(self.creative_srt_file_path and self.creative_srt_entries)
        ai_idle = not (self.image_generation_state['loading_prompts'] or self.image_generation_state['loading_images'])
        
        state = tk.NORMAL if api_key_present and srt_loaded and ai_idle else tk.DISABLED
        
        if hasattr(self, 'ai_image_prompt_button'):
            self.ai_image_prompt_button.config(state=state)
        
        # 更新狀態標籤
        if not api_key_present:
            status_text = "請設定 API 金鑰"
        elif not srt_loaded:
            status_text = "請載入 SRT 檔案"
        elif not ai_idle:
            status_text = "AI 功能執行中..."
        else:
            status_text = "就緒"
        
        self.creative_status_label.config(text=status_text)
    
    def show_image_generation_interface(self):
        """顯示圖像生成介面 - 完全基於 OkokGo ImageGenerationSection 架構"""
        try:
            # 建立並顯示 OkokGo 圖像生成介面
            image_generator = ImageGenerationOkokGo(self.root)
            
            # 如果有現有的 API 金鑰，預設填入
            if hasattr(self, 'creative_api_key_var') and self.creative_api_key_var.get():
                image_generator.api_key = self.creative_api_key_var.get()
            
            # 如果有載入的 SRT 內容，預設填入
            if hasattr(self, 'creative_srt_entries') and self.creative_srt_entries:
                # 將 SRT 條目轉換為文字內容
                srt_content = ""
                for entry in self.creative_srt_entries:
                    srt_content += f"{entry.start} --> {entry.end}\n{entry.content}\n\n"
                image_generator.transcript_content = srt_content
                image_generator.file_name = "已載入的SRT檔案"
            
            # 顯示介面
            image_generator.show_interface()
            
            self.log_message("圖像生成介面已開啟")
            
        except Exception as e:
            error_msg = f"開啟圖像生成介面失敗: {str(e)}"
            self.log_message(error_msg, is_error=True)
            messagebox.showerror("錯誤", error_msg)
    
    def start_prompt_generation_okokgo(self, status_var, display_frame):
        """顯示提示詞生成設定視窗 - 第一步：只生成提示詞"""
        # 建立設定視窗
        settings_window = tk.Toplevel(self.root)
        settings_window.title("圖像提示詞生成設定")
        settings_window.geometry("600x600")
        settings_window.resizable(True, True)
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # 藝術風格選項 (基於OkokGo ART_STYLE_OPTIONS)
        art_styles = [
            ("超寫實傑作", "a hyperrealistic masterpiece"),
            ("動漫風格插畫", "an anime-style illustration"),
            ("油畫傑作", "an oil painting masterpiece"),
            ("水彩畫", "a watercolor painting"),
            ("詳細鉛筆素描", "a detailed pencil sketch"),
            ("數位藝術傑作", "a digital art masterpiece"),
            ("概念藝術插畫", "a concept art illustration"),
            ("印象派繪畫", "an impressionist painting"),
            ("抽象藝術作品", "an abstract art piece"),
            ("復古風格插畫", "a vintage-style illustration")
        ]
        
        # 主框架
        main_frame = ttk.Frame(settings_window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # API 設定區域
        api_frame = ttk.LabelFrame(main_frame, text="API 設定", padding=10)
        api_frame.pack(fill=tk.X, pady=(0, 10))
        
        # API 金鑰
        ttk.Label(api_frame, text="API 金鑰:").grid(row=0, column=0, sticky='w', pady=5)
        api_key_var = tk.StringVar(value=self.creative_api_key_var.get())
        api_key_entry = ttk.Entry(api_frame, textvariable=api_key_var, show="*", width=50)
        api_key_entry.grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=5)
        
        # 指令生成模型 (文字輸入框)
        ttk.Label(api_frame, text="指令生成模型:").grid(row=1, column=0, sticky='w', pady=5)
        prompt_model_var = tk.StringVar(value="gemini-2.5-flash")
        prompt_model_entry = ttk.Entry(api_frame, textvariable=prompt_model_var, width=30)
        prompt_model_entry.grid(row=1, column=1, sticky='w', padx=(10, 0), pady=5)
        
        api_frame.columnconfigure(1, weight=1)
        
        # 生成設定區域
        settings_frame = ttk.LabelFrame(main_frame, text="提示詞生成設定", padding=10)
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 藝術風格選擇
        ttk.Label(settings_frame, text="藝術風格:").grid(row=0, column=0, sticky='w', pady=5)
        art_style_var = tk.StringVar(value=art_styles[0][1])
        art_style_combo = ttk.Combobox(settings_frame, textvariable=art_style_var, 
                                     values=[f"{style[0]} ({style[1]})" for style in art_styles], 
                                     state="readonly", width=40)
        art_style_combo.grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=5)
        
        # 指令數量
        ttk.Label(settings_frame, text="指令數量:").grid(row=1, column=0, sticky='w', pady=5)
        prompt_count_var = tk.StringVar(value="20")
        prompt_count_spinbox = ttk.Spinbox(settings_frame, from_=1, to=50, textvariable=prompt_count_var, width=10)
        prompt_count_spinbox.grid(row=1, column=1, sticky='w', padx=(10, 0), pady=5)
        
        settings_frame.columnconfigure(1, weight=1)
        
        # SRT 內容預覽區域
        preview_frame = ttk.LabelFrame(main_frame, text="SRT 內容預覽", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        preview_text = tk.Text(preview_frame, height=8, wrap=tk.WORD, state='disabled')
        preview_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=preview_text.yview)
        preview_text.configure(yscrollcommand=preview_scrollbar.set)
        
        preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        preview_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 顯示SRT內容預覽
        preview_content = ""
        for i, entry in enumerate(self.creative_srt_entries[:5]):
            preview_content += f"{entry.start} --> {entry.end}\n{entry.content}\n\n"
        if len(self.creative_srt_entries) > 5:
            preview_content += f"... 還有 {len(self.creative_srt_entries) - 5} 條字幕"
        
        preview_text.config(state='normal')
        preview_text.insert('1.0', preview_content)
        preview_text.config(state='disabled')
        
        # 按鈕區域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="取消", 
                  command=settings_window.destroy).pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(button_frame, text="生成英文圖片指令", 
                  command=lambda: self.start_prompt_generation(
                      settings_window, api_key_var.get(), prompt_model_var.get(),
                      art_style_var.get(), prompt_count_var.get()
                  )).pack(side=tk.RIGHT)
    
    def start_prompt_generation(self, settings_window, api_key, prompt_model, art_style, prompt_count):
        """開始提示詞生成 - 第一步：只生成提示詞"""
        settings_window.destroy()
        
        # 設定生成狀態
        self.is_ai_generating_image_prompt = True
        self.update_creative_buttons_state()
        
        # 解析藝術風格值
        art_style_value = art_style.split(" (")[1].rstrip(")") if " (" in art_style else art_style
        
        # 儲存設定供後續使用
        self.image_generation_settings = {
            'api_key': api_key,
            'prompt_model': prompt_model
        }
        
        # 在背景執行緒中執行提示詞生成
        threading.Thread(
            target=self._do_prompt_generation_thread,
            args=(api_key, prompt_model, art_style_value, prompt_count),
            daemon=True
        ).start()
    
    def _do_prompt_generation_thread(self, api_key, prompt_model, art_style, prompt_count):
        """提示詞生成背景執行緒 - 第一步：只生成提示詞"""
        try:
            self.log_message("開始生成圖像提示詞...", log_area_ref=self.creative_log_area)
            
            # 準備SRT內容
            srt_content = ""
            for entry in self.creative_srt_entries:
                srt_content += f"{entry.start} --> {entry.end}\n{entry.content}\n\n"
            
            # 使用OkokGo的完整提示詞邏輯
            system_prompt = self._create_okokgo_image_system_prompt(art_style, prompt_count)
            
            # 呼叫Gemini API
            if not _GENAI_IMPORTED:
                raise Exception("缺少 google-generativeai 函式庫")
            
            import google.generativeai as genai
            
            # 設定API金鑰
            genai.configure(api_key=api_key)
            
            # 建立提示詞生成模型
            prompt_generation_model = genai.GenerativeModel(prompt_model)
            
            # 準備生成配置 (JSON Schema強制輸出)
            generation_config = genai.types.GenerationConfig(
                response_mime_type="application/json",
                response_schema={
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "timestamp": {"type": "string"},
                            "prompt": {"type": "string"},
                            "zh": {"type": "string"}
                        },
                        "required": ["timestamp", "prompt", "zh"]
                    }
                }
            )
            
            # 生成提示詞
            full_prompt = f"{system_prompt}\n\nTranscript:\n{srt_content}"
            
            self.log_message("正在呼叫 Gemini API 生成提示詞...", log_area_ref=self.creative_log_area)
            
            response = prompt_generation_model.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            
            # 解析回應
            import json
            prompts = json.loads(response.text)
            
            self.log_message(f"成功生成 {len(prompts)} 個圖像提示詞", log_area_ref=self.creative_log_area)
            
            # 儲存提示詞供後續使用
            self.generated_prompts = prompts
            
            # 顯示提示詞編輯介面
            self.root.after(0, lambda: self.show_prompt_editing_interface(prompts))
            
        except Exception as e:
            error_msg = f"提示詞生成失敗: {str(e)}"
            self.log_message(error_msg, is_error=True, log_area_ref=self.creative_log_area)
            self.root.after(0, lambda: messagebox.showerror("錯誤", error_msg))
        
        finally:
            # 重設狀態
            self.is_ai_generating_image_prompt = False
            self.root.after(0, self.update_creative_buttons_state)
    
    def _create_okokgo_image_system_prompt(self, art_style, prompt_count):
        """建立圖像生成系統提示詞 - 修正版：強調分段選擇和視覺多樣性"""
        return f"""// ROLE: Visual Director AI
// TASK: Convert a Chinese transcript into {prompt_count} distinct, high-quality, English image generation prompts with a CONSISTENT style.
// OUTPUT FORMAT: A single, valid JSON array of {prompt_count} objects. No other text.
// JSON Object Schema: {{ "timestamp": "string", "prompt": "string", "zh": "string" }}

// --- RULES ---
// 1. **SEGMENT SELECTION & DISTRIBUTION (CRITICAL):**
//    - You MUST first divide the transcript into beginning (0-33%), middle (33-66%), and end (66-100%) sections.
//    - Select {prompt_count} SPECIFIC segments that are visually interesting and worth generating images for.
//    - Distribute the selections EVENLY: roughly 1/3 from beginning, 1/3 from middle, 1/3 from end.
//    - Each prompt should be based on a SPECIFIC segment's content, NOT a general summary of the entire transcript.

// 2. **VISUAL DIVERSITY (CRITICAL):**
//    - Ensure MAXIMUM visual and thematic diversity between all {prompt_count} prompts.
//    - Each prompt should represent a DIFFERENT scene, emotion, action, or visual concept.
//    - Avoid generating similar scenes, poses, or compositions.
//    - Focus on different characters, locations, times of day, weather, emotions, and activities.

// 3. **FAITHFULNESS TO SPECIFIC SEGMENTS (CRITICAL):**
//    - Each English prompt must accurately reflect the SPECIFIC actions, objects, and emotions described in that PARTICULAR segment.
//    - Do NOT add elements not present in the source segment.
//    - Base each prompt on the actual content of that timestamp, not general themes.

// 4. PROMPT LANGUAGE: All 'prompt' values must be in English.

// 5. PROMPT STYLE (MANDATORY):
//    - EVERY prompt must start with the following user-selected artistic style: "{art_style}". Do NOT use any other style.
//    - Strictly FORBIDDEN words: "photograph", "photo of", "realistic", "photorealistic", "4K", "HDR", "film still", "cinematic".

// 6. PROMPT CONTENT STRUCTURE:
//    - Construct each prompt using this 6-layer structure:
//      (1) top-tier quality and artistic style,
//      (2) main subject and action (from specific segment),
//      (3) vivid emotions and intricate details (from specific segment),
//      (4) environment and atmosphere (from specific segment),
//      (5) composition, camera or illustration technique, lighting,
//      (6) final resolution or quality keywords.
//    - LOCALIZATION: Feature Taiwanese people and scenes when relevant.
//    - SAFETY: For sensitive topics, use symbolic or metaphorical imagery.

// 7. CHINESE EXPLANATION:
//    - Each object must include a "zh" field containing a concise Chinese explanation of the English prompt.

// 8. TIMESTAMP:
//    - If the input is SRT, the 'timestamp' value should be the most relevant start time in "HH:MM:SS" format.
//    - If the input is plain text, the 'timestamp' value must be an empty string ("").

// --- EXAMPLE WORKFLOW ---
// 1. Analyze entire transcript and identify visually interesting segments
// 2. Select segments distributed across beginning, middle, end
// 3. Generate diverse prompts based on each specific segment's content

// --- EXAMPLE ---
// Input segment: "00:15:30,100 --> 00:15:33,200\\n她在雨中奔跑，追趕著最後一班公車..."
// Output object: {{
//   "timestamp": "00:15:30",
//   "prompt": "{art_style} depicting a young Taiwanese woman running through heavy rain on a city street, desperation and determination in her expression, long black hair soaked and flowing behind her, wearing a light blue raincoat, chasing after a departing bus with glowing taillights, wet asphalt reflecting neon signs, dynamic side-angle shot with motion blur and dramatic lighting, ultra high definition with rain droplets clearly visible.",
//   "zh": "一位年輕的台灣女子在大雨中奔跑於城市街道上，臉上帶著絕望與決心的表情，濕透的黑色長髮在身後飄動，穿著淺藍色雨衣，追趕著一輛正在離開、尾燈發光的公車。濕潤的柏油路面反射著霓虹招牌的光芒，採用動態側角度拍攝，帶有動態模糊和戲劇性照明效果，以超高解析度呈現，雨滴清晰可見。"
// }}

// --- START OF TASK ---
// Analyze the following transcript, select {prompt_count} diverse segments distributed across the timeline, and generate the JSON output."""
    
    def show_prompt_editing_interface(self, prompts):
        """顯示提示詞編輯介面 - 完全基於OkokGo架構"""
        # 建立編輯視窗
        edit_window = tk.Toplevel(self.root)
        edit_window.title("編輯指令與時間戳")
        edit_window.geometry("1000x700")
        edit_window.resizable(True, True)
        
        # 主框架
        main_frame = ttk.Frame(edit_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 標題
        title_label = ttk.Label(main_frame, text=f"成功生成 {len(prompts)} 個圖像提示詞", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # 建立可滾動的編輯區域
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 建立編輯介面
        self.prompt_edit_entries = []
        for i, prompt_item in enumerate(prompts):
            item_frame = ttk.Frame(scrollable_frame, relief='solid', padding=10)
            item_frame.pack(fill=tk.X, pady=5, padx=5)
            
            # 標題行：序號 + 時間戳 + 刪除按鈕
            header_frame = ttk.Frame(item_frame)
            header_frame.pack(fill=tk.X, pady=(0, 10))
            
            # 序號和時間戳
            ttk.Label(header_frame, text=f"指令 {i+1}", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
            
            timestamp_var = tk.StringVar(value=prompt_item.get('timestamp', 'N/A'))
            timestamp_entry = ttk.Entry(header_frame, textvariable=timestamp_var, 
                                      state='readonly', width=12)
            timestamp_entry.pack(side=tk.LEFT, padx=(10, 0))
            
            # 刪除按鈕
            delete_button = ttk.Button(header_frame, text="刪除", 
                                     command=lambda idx=i, frame=item_frame: self.delete_prompt_item_from_edit(idx, frame))
            delete_button.pack(side=tk.RIGHT)
            
            # 英文提示詞區域
            prompt_label = ttk.Label(item_frame, text="英文提示詞:")
            prompt_label.pack(anchor='w', pady=(0, 5))
            
            prompt_text = tk.Text(item_frame, height=4, wrap=tk.WORD, 
                                bg='white', fg='black', 
                                insertbackground='black',
                                font=('Arial', 9))
            prompt_text.insert('1.0', prompt_item.get('prompt', ''))
            prompt_text.pack(fill=tk.X, pady=(0, 10))
            
            # 中文說明區域
            zh_label = ttk.Label(item_frame, text="中文說明:")
            zh_label.pack(anchor='w', pady=(0, 5))
            
            zh_text = tk.Text(item_frame, height=3, wrap=tk.WORD, 
                            bg='#f8f8f8', fg='#333333',
                            state='disabled',
                            font=('Arial', 9))
            zh_text.config(state='normal')
            zh_text.insert('1.0', prompt_item.get('zh', ''))
            zh_text.config(state='disabled')
            zh_text.pack(fill=tk.X)
            
            # 儲存編輯項目的引用
            self.prompt_edit_entries.append({
                'frame': item_frame,
                'timestamp': timestamp_var,
                'prompt_text': prompt_text,
                'zh_text': zh_text,
                'original_data': prompt_item,
                'index': i
            })
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 底部按鈕區域
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 圖像生成設定按鈕
        ttk.Button(bottom_frame, text="開始生成圖片", 
                  command=lambda: self.show_image_generation_settings_from_prompts(edit_window)).pack(side=tk.RIGHT)
        
        ttk.Button(bottom_frame, text="儲存提示詞", 
                  command=lambda: self.save_edited_prompts()).pack(side=tk.RIGHT, padx=(0, 10))
        
        ttk.Button(bottom_frame, text="關閉", 
                  command=edit_window.destroy).pack(side=tk.LEFT)
        
        self.log_message("提示詞編輯介面已開啟，請檢視和編輯提示詞", log_area_ref=self.creative_log_area)
    
    def delete_prompt_item_from_edit(self, index, frame):
        """從編輯介面刪除提示詞項目"""
        # 確認刪除
        result = messagebox.askyesno("確認刪除", f"確定要刪除指令 {index+1} 嗎？")
        if not result:
            return
        
        # 銷毀框架
        frame.destroy()
        
        # 從列表中移除對應項目
        self.prompt_edit_entries = [entry for entry in self.prompt_edit_entries 
                                  if entry['frame'] != frame]
        
        self.log_message(f"已刪除指令 {index+1}", log_area_ref=self.creative_log_area)
    
    def save_edited_prompts(self):
        """儲存編輯後的提示詞"""
        try:
            # 收集編輯後的提示詞
            edited_prompts = []
            for entry in self.prompt_edit_entries:
                if entry['frame'].winfo_exists():  # 檢查框架是否還存在
                    edited_prompts.append({
                        'timestamp': entry['timestamp'].get(),
                        'prompt': entry['prompt_text'].get('1.0', tk.END).strip(),
                        'zh': entry['zh_text'].get('1.0', tk.END).strip()
                    })
            
            # 更新儲存的提示詞
            self.generated_prompts = edited_prompts
            
            # 儲存到檔案
            file_path = filedialog.asksaveasfilename(
                title="儲存編輯後的提示詞",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if file_path:
                import json
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(edited_prompts, f, ensure_ascii=False, indent=2)
                
                self.log_message(f"編輯後的提示詞已儲存: {os.path.basename(file_path)}", log_area_ref=self.creative_log_area)
                messagebox.showinfo("成功", f"提示詞已儲存至:\n{file_path}")
        
        except Exception as e:
            error_msg = f"儲存失敗: {str(e)}"
            self.log_message(error_msg, is_error=True, log_area_ref=self.creative_log_area)
            messagebox.showerror("錯誤", error_msg)
    
    def show_image_generation_settings_from_prompts(self, edit_window):
        """從提示詞編輯介面開啟圖像生成設定 - 第二步"""
        # 收集當前編輯的提示詞
        current_prompts = []
        for entry in self.prompt_edit_entries:
            if entry['frame'].winfo_exists():
                current_prompts.append({
                    'timestamp': entry['timestamp'].get(),
                    'prompt': entry['prompt_text'].get('1.0', tk.END).strip(),
                    'zh': entry['zh_text'].get('1.0', tk.END).strip()
                })
        
        if not current_prompts:
            messagebox.showwarning("警告", "沒有可用的提示詞")
            return
        
        # 更新儲存的提示詞
        self.generated_prompts = current_prompts
        
        # 關閉編輯視窗
        edit_window.destroy()
        
        # 開啟圖像生成設定視窗
        self.show_image_generation_settings_step2()
    
    def show_image_generation_settings_step2(self):
        """顯示圖像生成設定視窗 - 第二步：生成圖片"""
        # 建立設定視窗
        settings_window = tk.Toplevel(self.root)
        settings_window.title("圖片生成設定")
        settings_window.geometry("600x500")
        settings_window.resizable(True, True)
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # 主框架
        main_frame = ttk.Frame(settings_window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # API 設定區域
        api_frame = ttk.LabelFrame(main_frame, text="API 設定", padding=10)
        api_frame.pack(fill=tk.X, pady=(0, 10))
        
        # API 金鑰
        ttk.Label(api_frame, text="API 金鑰:").grid(row=0, column=0, sticky='w', pady=5)
        api_key_var = tk.StringVar(value=self.image_generation_settings.get('api_key', ''))
        api_key_entry = ttk.Entry(api_frame, textvariable=api_key_var, show="*", width=50)
        api_key_entry.grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=5)
        
        # 圖片生成模型
        ttk.Label(api_frame, text="圖片生成模型:").grid(row=1, column=0, sticky='w', pady=5)
        image_model_var = tk.StringVar(value="imagen-3.0-generate-002")
        image_model_entry = ttk.Entry(api_frame, textvariable=image_model_var, width=30)
        image_model_entry.grid(row=1, column=1, sticky='w', padx=(10, 0), pady=5)
        
        api_frame.columnconfigure(1, weight=1)
        
        # 圖像生成設定區域
        settings_frame = ttk.LabelFrame(main_frame, text="圖像生成設定", padding=10)
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 每指令圖片數量
        ttk.Label(settings_frame, text="每指令圖片數量:").grid(row=0, column=0, sticky='w', pady=5)
        images_per_prompt_var = tk.StringVar(value="1")
        images_per_prompt_combo = ttk.Combobox(settings_frame, textvariable=images_per_prompt_var,
                                             values=["1", "2", "3", "4"],
                                             state="readonly", width=10)
        images_per_prompt_combo.grid(row=0, column=1, sticky='w', padx=(10, 0), pady=5)
        
        # 圖片長寬比
        ttk.Label(settings_frame, text="圖片長寬比:").grid(row=1, column=0, sticky='w', pady=5)
        aspect_ratio_var = tk.StringVar(value="16:9")
        aspect_ratio_combo = ttk.Combobox(settings_frame, textvariable=aspect_ratio_var,
                                        values=["1:1", "4:3", "16:9", "3:4", "9:16"],
                                        state="readonly", width=15)
        aspect_ratio_combo.grid(row=1, column=1, sticky='w', padx=(10, 0), pady=5)
        
        # 人物生成設定
        ttk.Label(settings_frame, text="人物生成:").grid(row=2, column=0, sticky='w', pady=5)
        person_generation_var = tk.StringVar(value="allow_adult")
        person_generation_combo = ttk.Combobox(settings_frame, textvariable=person_generation_var,
                                             values=["dont_allow", "allow_adult", "allow_all"],
                                             state="readonly", width=15)
        person_generation_combo.grid(row=2, column=1, sticky='w', padx=(10, 0), pady=5)
        
        settings_frame.columnconfigure(1, weight=1)
        
        # 提示詞預覽區域
        preview_frame = ttk.LabelFrame(main_frame, text=f"將生成 {len(self.generated_prompts)} 張圖片", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        preview_text = tk.Text(preview_frame, height=8, wrap=tk.WORD, state='disabled')
        preview_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=preview_text.yview)
        preview_text.configure(yscrollcommand=preview_scrollbar.set)
        
        preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        preview_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 顯示提示詞預覽
        preview_content = ""
        for i, prompt_item in enumerate(self.generated_prompts[:5]):
            preview_content += f"{i+1}. {prompt_item.get('timestamp', 'N/A')}\n"
            preview_content += f"{prompt_item.get('prompt', '')[:100]}...\n\n"
        if len(self.generated_prompts) > 5:
            preview_content += f"... 還有 {len(self.generated_prompts) - 5} 個提示詞"
        
        preview_text.config(state='normal')
        preview_text.insert('1.0', preview_content)
        preview_text.config(state='disabled')
        
        # 按鈕區域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="取消", 
                  command=settings_window.destroy).pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(button_frame, text="開始生成圖片", 
                  command=lambda: self.start_image_generation_step2(
                      settings_window, api_key_var.get(), image_model_var.get(),
                      images_per_prompt_var.get(), aspect_ratio_var.get(), person_generation_var.get()
                  )).pack(side=tk.RIGHT)
    
    def start_image_generation_step2(self, settings_window, api_key, image_model, 
                                   images_per_prompt, aspect_ratio, person_generation):
        """開始圖像生成 - 第二步：根據提示詞生成圖片"""
        settings_window.destroy()
        
        # 設定生成狀態
        self.is_ai_generating_image_prompt = True
        self.update_creative_buttons_state()
        
        # 在背景執行緒中執行圖像生成
        threading.Thread(
            target=self._do_image_generation_step2_thread,
            args=(api_key, image_model, images_per_prompt, aspect_ratio, person_generation),
            daemon=True
        ).start()
    
    def _do_image_generation_step2_thread(self, api_key, image_model, images_per_prompt, aspect_ratio, person_generation):
        """圖像生成背景執行緒 - 第二步：只生成圖片"""
        images = []
        
        try:
            self.log_message("開始生成圖像...", log_area_ref=self.creative_log_area)
            
            sample_count = int(images_per_prompt)
            
            for i, prompt_item in enumerate(self.generated_prompts):
                self.log_message(f"處理指令 {i + 1} / {len(self.generated_prompts)} ...", log_area_ref=self.creative_log_area)
                
                try:
                    urls = []
                    
                    if image_model.startswith('gemini'):
                        # 使用 Gemini 多模態生成
                        import google.generativeai as genai
                        genai.configure(api_key=api_key)
                        
                        image_generation_model = genai.GenerativeModel(image_model)
                        
                        response = image_generation_model.generate_content(
                            prompt_item['prompt'],
                            generation_config=genai.types.GenerationConfig(
                                response_modalities=['TEXT', 'IMAGE']
                            )
                        )
                        
                        # 處理回應中的圖像
                        if response.candidates and response.candidates[0].content.parts:
                            for part in response.candidates[0].content.parts:
                                if hasattr(part, 'inline_data') and part.inline_data:
                                    urls.append(f"data:image/png;base64,{part.inline_data.data}")
                    
                    else:
                        # 使用 Imagen API
                        import requests
                        
                        payload = {
                            "instances": [{"prompt": prompt_item['prompt']}],
                            "parameters": {
                                "sampleCount": sample_count,
                                "aspectRatio": aspect_ratio,
                                "personGeneration": person_generation
                            }
                        }
                        
                        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{image_model}:predict?key={api_key}"
                        
                        response = requests.post(
                            api_url,
                            headers={'Content-Type': 'application/json'},
                            json=payload,
                            timeout=60
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            if 'predictions' in result:
                                for prediction in result['predictions']:
                                    if 'bytesBase64Encoded' in prediction:
                                        urls.append(f"data:image/png;base64,{prediction['bytesBase64Encoded']}")
                        else:
                            self.log_message(f"圖像生成 API 錯誤: {response.status_code}", is_error=True, log_area_ref=self.creative_log_area)
                    
                    if urls:
                        images.append({"urls": urls})
                        self.log_message(f"指令 {i + 1} 成功生成 {len(urls)} 張圖像", log_area_ref=self.creative_log_area)
                    else:
                        images.append({"urls": [], "error": f"指令 {i + 1} 圖片生成失敗"})
                        self.log_message(f"指令 {i + 1} 圖片生成失敗", is_error=True, log_area_ref=self.creative_log_area)
                
                except Exception as e:
                    error_msg = f"指令 {i + 1} 圖片生成失敗: {str(e)}"
                    self.log_message(error_msg, is_error=True, log_area_ref=self.creative_log_area)
                    images.append({"urls": [], "error": error_msg})
                
                # 延遲避免API限制
                if i < len(self.generated_prompts) - 1:
                    import time
                    time.sleep(1.5)
            
            self.log_message("全部圖片已處理完畢", log_area_ref=self.creative_log_area)
            
            # 顯示結果
            self.root.after(0, lambda: self.show_final_image_results(self.generated_prompts, images, aspect_ratio))
            
        except Exception as e:
            error_msg = f"圖像生成失敗: {str(e)}"
            self.log_message(error_msg, is_error=True, log_area_ref=self.creative_log_area)
            self.root.after(0, lambda: messagebox.showerror("錯誤", error_msg))
        
        finally:
            # 重設狀態
            self.is_ai_generating_image_prompt = False
            self.root.after(0, self.update_creative_buttons_state)
    
    def show_final_image_results(self, prompts, images, aspect_ratio):
        """顯示最終圖像生成結果 - 完全基於OkokGo架構"""
        # 建立結果視窗
        results_window = tk.Toplevel(self.root)
        results_window.title("生成結果")
        results_window.geometry("1200x800")
        results_window.resizable(True, True)
        
        # 主框架
        main_frame = ttk.Frame(results_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 標題
        title_label = ttk.Label(main_frame, text=f"生成結果", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # 建立圖像網格顯示
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 顯示圖像結果網格
        self._display_final_image_grid(scrollable_frame, images, aspect_ratio)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 按鈕區域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="關閉", 
                  command=results_window.destroy).pack(side=tk.RIGHT)
        
        self.log_message("圖像生成完成，請檢視結果視窗", log_area_ref=self.creative_log_area)
    
    def _display_final_image_grid(self, parent_frame, images, aspect_ratio):
        """顯示最終圖像結果網格 - 基於OkokGo架構"""
        # 計算網格佈局
        cols = 4  # 每行4張圖
        
        for i, image_item in enumerate(images):
            row = i // cols
            col = i % cols
            
            # 建立圖像框架
            image_frame = ttk.Frame(parent_frame, relief='ridge', padding=5)
            image_frame.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')
            
            if image_item.get('error'):
                # 顯示錯誤
                error_label = ttk.Label(image_frame, text=image_item['error'], 
                                      foreground='red', wraplength=200)
                error_label.pack(expand=True, fill='both')
            else:
                # 顯示圖像
                for j, img_url in enumerate(image_item.get('urls', [])):
                    try:
                        if img_url.startswith('data:image'):
                            # 處理 base64 圖像
                            import base64
                            from io import BytesIO
                            
                            # 提取 base64 資料
                            base64_data = img_url.split(',')[1]
                            image_data = base64.b64decode(base64_data)
                            
                            if PIL_AVAILABLE:
                                # 使用 PIL 顯示圖像
                                pil_image = Image.open(BytesIO(image_data))
                                pil_image.thumbnail((200, 150), Image.Resampling.LANCZOS)
                                photo = ImageTk.PhotoImage(pil_image)
                                
                                img_label = ttk.Label(image_frame, image=photo)
                                img_label.image = photo  # 保持引用
                                img_label.pack(pady=2)
                                
                                # 下載按鈕
                                download_btn = ttk.Button(image_frame, text="下載",
                                                        command=lambda url=img_url, idx=i, j_idx=j: 
                                                        self.download_base64_image(url, f"image_{idx+1}_{j_idx+1}.png"))
                                download_btn.pack()
                            else:
                                # 沒有 PIL，顯示文字
                                ttk.Label(image_frame, text=f"圖像 {i+1}-{j+1}\n(需要 Pillow 庫顯示)").pack()
                                
                                # 仍然提供下載功能
                                download_btn = ttk.Button(image_frame, text="下載",
                                                        command=lambda url=img_url, idx=i, j_idx=j: 
                                                        self.download_base64_image(url, f"image_{idx+1}_{j_idx+1}.png"))
                                download_btn.pack()
                        
                    except Exception as e:
                        ttk.Label(image_frame, text=f"圖像載入失敗: {str(e)}", 
                                foreground='red').pack()
        
        # 設定網格權重
        for i in range(cols):
            parent_frame.columnconfigure(i, weight=1)
    
    def download_base64_image(self, image_url, filename):
        """下載 base64 圖像"""
        try:
            file_path = filedialog.asksaveasfilename(
                title="儲存圖像",
                defaultextension=".png",
                initialvalue=filename,
                filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
            )
            
            if file_path:
                if image_url.startswith('data:image'):
                    # 處理 base64 圖像
                    import base64
                    base64_data = image_url.split(',')[1]
                    image_data = base64.b64decode(base64_data)
                    
                    with open(file_path, 'wb') as f:
                        f.write(image_data)
                    
                    self.log_message(f"圖像已儲存: {os.path.basename(file_path)}", log_area_ref=self.creative_log_area)
                    messagebox.showinfo("成功", f"圖像已儲存至:\n{file_path}")
                else:
                    messagebox.showerror("錯誤", "無效的圖像格式")
        
        except Exception as e:
            error_msg = f"圖像儲存失敗: {str(e)}"
            self.log_message(error_msg, is_error=True, log_area_ref=self.creative_log_area)
            messagebox.showerror("錯誤", error_msg)
    
    def _display_image_results(self, parent_frame, images, aspect_ratio):
        """顯示圖像結果網格"""
        # 計算網格佈局
        cols = 4  # 每行4張圖
        
        for i, image_item in enumerate(images):
            row = i // cols
            col = i % cols
            
            # 建立圖像框架
            image_frame = ttk.Frame(parent_frame, relief='ridge', padding=5)
            image_frame.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')
            
            if image_item.get('error'):
                # 顯示錯誤
                error_label = ttk.Label(image_frame, text=image_item['error'], 
                                      foreground='red', wraplength=200)
                error_label.pack(expand=True, fill='both')
            else:
                # 顯示圖像
                for j, img_url in enumerate(image_item.get('urls', [])):
                    try:
                        if img_url.startswith('data:image'):
                            # 處理 base64 圖像
                            import base64
                            from io import BytesIO
                            
                            # 提取 base64 資料
                            base64_data = img_url.split(',')[1]
                            image_data = base64.b64decode(base64_data)
                            
                            if PIL_AVAILABLE:
                                # 使用 PIL 顯示圖像
                                pil_image = Image.open(BytesIO(image_data))
                                pil_image.thumbnail((200, 150), Image.Resampling.LANCZOS)
                                photo = ImageTk.PhotoImage(pil_image)
                                
                                img_label = ttk.Label(image_frame, image=photo)
                                img_label.image = photo  # 保持引用
                                img_label.pack(pady=2)
                                
                                # 下載按鈕
                                download_btn = ttk.Button(image_frame, text="下載",
                                                        command=lambda url=img_url, idx=i, j_idx=j: 
                                                        self.download_image(url, f"image_{idx+1}_{j_idx+1}.png"))
                                download_btn.pack()
                            else:
                                # 沒有 PIL，顯示文字
                                ttk.Label(image_frame, text=f"圖像 {i+1}-{j+1}\n(需要 Pillow 庫顯示)").pack()
                        
                    except Exception as e:
                        ttk.Label(image_frame, text=f"圖像載入失敗: {str(e)}", 
                                foreground='red').pack()
        
        # 設定網格權重
        for i in range(cols):
            parent_frame.columnconfigure(i, weight=1)
    
    def download_image(self, image_url, filename):
        """下載圖像"""
        try:
            file_path = filedialog.asksaveasfilename(
                title="儲存圖像",
                defaultextension=".png",
                initialvalue=filename,
                filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
            )
            
            if file_path:
                if image_url.startswith('data:image'):
                    # 處理 base64 圖像
                    import base64
                    base64_data = image_url.split(',')[1]
                    image_data = base64.b64decode(base64_data)
                    
                    with open(file_path, 'wb') as f:
                        f.write(image_data)
                    
                    self.log_message(f"圖像已儲存: {os.path.basename(file_path)}", log_area_ref=self.creative_log_area)
                    messagebox.showinfo("成功", f"圖像已儲存至:\n{file_path}")
        
        except Exception as e:
            error_msg = f"圖像儲存失敗: {str(e)}"
            self.log_message(error_msg, is_error=True, log_area_ref=self.creative_log_area)
            messagebox.showerror("錯誤", error_msg)
    
    def delete_prompt_item(self, index, frame):
        """刪除提示詞項目"""
        frame.destroy()
        # 這裡可以加入更多刪除邏輯
    
    def save_image_prompts_json(self, prompt_data):
        """儲存圖像提示詞為JSON格式"""
        try:
            file_path = filedialog.asksaveasfilename(
                title="儲存圖像提示詞 (JSON)",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if file_path:
                import json
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(prompt_data, f, ensure_ascii=False, indent=2)
                
                self.log_message(f"圖像提示詞已儲存: {os.path.basename(file_path)}", log_area_ref=self.creative_log_area)
                messagebox.showinfo("成功", f"圖像提示詞已儲存至:\n{file_path}")
        
        except Exception as e:
            error_msg = f"儲存失敗: {str(e)}"
            self.log_message(error_msg, is_error=True, log_area_ref=self.creative_log_area)
            messagebox.showerror("錯誤", error_msg)
    
    def save_image_prompts_txt(self, prompt_data):
        """儲存圖像提示詞為TXT格式"""
        try:
            file_path = filedialog.asksaveasfilename(
                title="儲存圖像提示詞 (TXT)",
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("AI 圖像提示詞生成結果\n")
                    f.write("=" * 50 + "\n\n")
                    
                    for i, item in enumerate(prompt_data, 1):
                        f.write(f"提示詞 {i}\n")
                        f.write(f"時間戳: {item.get('timestamp', 'N/A')}\n")
                        f.write(f"英文提示詞: {item.get('prompt', '')}\n")
                        f.write(f"中文說明: {item.get('zh', '')}\n")
                        f.write("-" * 50 + "\n\n")
                
                self.log_message(f"圖像提示詞已儲存: {os.path.basename(file_path)}", log_area_ref=self.creative_log_area)
                messagebox.showinfo("成功", f"圖像提示詞已儲存至:\n{file_path}")
        
        except Exception as e:
            error_msg = f"儲存失敗: {str(e)}"
            self.log_message(error_msg, is_error=True, log_area_ref=self.creative_log_area)
            messagebox.showerror("錯誤", error_msg)
    
    # SECTION 2.3: AI 圖像生成頁籤
    # ===============================================================
    def create_ai_image_tab(self):
        """建立 AI 圖像生成頁籤 - 直接嵌入功能"""
        try:
            # 導入圖像生成功能
            from image_generation_okokgo import ImageGenerationOkokGo
            
            # 創建圖像生成工具實例，但不顯示獨立視窗
            self.image_gen_tool = ImageGenerationOkokGo(self.root)
            
            # 直接在頁籤中建立圖像生成介面
            self.create_embedded_image_generation_interface()
            
        except Exception as e:
            # 如果導入失敗，顯示錯誤信息
            error_frame = ttk.Frame(self.ai_image_tab)
            error_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
            
            error_label = ttk.Label(error_frame, 
                                   text=f"❌ 圖像生成功能載入失敗: {str(e)}", 
                                   font=("Arial", 12))
            error_label.pack(pady=20)
            
            print(f"DEBUG: 圖像生成功能載入失敗: {e}")
            traceback.print_exc()
    
    def create_embedded_image_generation_interface(self):
        """在頁籤中建立嵌入式圖像生成介面"""
        # 主框架
        main_frame = ttk.Frame(self.ai_image_tab)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 設定區域
        self.create_image_settings_section(main_frame)
        
        # 檔案載入區域
        self.create_image_file_section(main_frame)
        
        # 按鈕和狀態區域
        self.create_image_button_section(main_frame)
        
        # 提示詞顯示區域
        self.create_image_prompts_display_section(main_frame)
        
        # 圖片結果顯示區域
        self.create_image_results_display_section(main_frame)
    
    def create_image_settings_section(self, parent):
        """建立圖像生成設定區域"""
        settings_frame = ttk.LabelFrame(parent, text="🎨 圖像生成設定", padding=10)
        settings_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 建立3列網格
        for i in range(3):
            settings_frame.columnconfigure(i, weight=1)
        
        # 第一行：API 金鑰、指令生成模型、圖片生成模型
        ttk.Label(settings_frame, text="API 金鑰").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.image_api_key_var = tk.StringVar(value=getattr(self, 'api_key', ''))
        api_key_entry = ttk.Entry(settings_frame, textvariable=self.image_api_key_var, show="*", width=30)
        api_key_entry.grid(row=1, column=0, sticky='ew', padx=5, pady=2)
        
        ttk.Label(settings_frame, text="指令生成模型").grid(row=0, column=1, sticky='w', padx=5, pady=2)
        self.image_prompt_model_var = tk.StringVar(value="gemini-2.5-flash")
        prompt_model_entry = ttk.Entry(settings_frame, textvariable=self.image_prompt_model_var, width=30)
        prompt_model_entry.grid(row=1, column=1, sticky='ew', padx=5, pady=2)
        
        ttk.Label(settings_frame, text="圖片生成模型").grid(row=0, column=2, sticky='w', padx=5, pady=2)
        self.image_model_var = tk.StringVar(value="imagen-3.0-generate-002")
        image_model_entry = ttk.Entry(settings_frame, textvariable=self.image_model_var, width=30)
        image_model_entry.grid(row=1, column=2, sticky='ew', padx=5, pady=2)
        
        # 第二行：藝術風格、指令數量、每指令圖片數量
        from image_generation_okokgo import ART_STYLE_OPTIONS
        
        ttk.Label(settings_frame, text="藝術風格").grid(row=2, column=0, sticky='w', padx=5, pady=2)
        self.image_art_style_var = tk.StringVar(value=ART_STYLE_OPTIONS[0]["label"])
        art_style_combo = ttk.Combobox(settings_frame, textvariable=self.image_art_style_var,
                                     values=[opt["label"] for opt in ART_STYLE_OPTIONS],
                                     state="readonly", width=27)
        art_style_combo.grid(row=3, column=0, sticky='ew', padx=5, pady=2)
        
        ttk.Label(settings_frame, text="指令數量").grid(row=2, column=1, sticky='w', padx=5, pady=2)
        self.image_number_of_prompts_var = tk.StringVar(value="20")
        prompts_entry = ttk.Entry(settings_frame, textvariable=self.image_number_of_prompts_var, width=30)
        prompts_entry.grid(row=3, column=1, sticky='ew', padx=5, pady=2)
        
        ttk.Label(settings_frame, text="上下文範圍").grid(row=2, column=2, sticky='w', padx=5, pady=2)
        self.image_context_radius_var = tk.StringVar(value="1")
        context_entry = ttk.Entry(settings_frame, textvariable=self.image_context_radius_var, width=30)
        context_entry.grid(row=3, column=2, sticky='ew', padx=5, pady=2)
        
        # 第三行：每指令圖片數量、人物生成
        ttk.Label(settings_frame, text="每指令圖片數量").grid(row=4, column=0, sticky='w', padx=5, pady=2)
        self.image_number_of_images_var = tk.StringVar(value="1")
        images_combo = ttk.Combobox(settings_frame, textvariable=self.image_number_of_images_var,
                                   values=["1", "2", "3", "4"], state="readonly", width=27)
        images_combo.grid(row=5, column=0, sticky='ew', padx=5, pady=2)
        
        ttk.Label(settings_frame, text="人物生成").grid(row=4, column=1, sticky='w', padx=5, pady=2)
        self.image_person_generation_var = tk.StringVar(value="allow_adult")
        person_combo = ttk.Combobox(settings_frame, textvariable=self.image_person_generation_var,
                                   values=["dont_allow", "allow_adult", "allow_all"], state="readonly", width=27)
        person_combo.grid(row=5, column=1, sticky='ew', padx=5, pady=2)
    
    def create_image_file_section(self, parent):
        """建立檔案載入區域"""
        file_frame = ttk.LabelFrame(parent, text="📁 逐字稿檔案", padding=10)
        file_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.image_file_var = tk.StringVar(value="請選擇逐字稿檔案...")
        file_button = ttk.Button(file_frame, text="選擇檔案", command=self.select_image_file)
        file_button.pack(side=tk.LEFT, padx=(0, 10))
        
        file_label = ttk.Label(file_frame, textvariable=self.image_file_var)
        file_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def create_image_button_section(self, parent):
        """建立按鈕和狀態區域"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.image_generate_button = ttk.Button(button_frame, text="🚀 生成英文圖片指令", 
                                               command=self.generate_image_prompts,
                                               style='Accent.TButton')
        self.image_generate_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.image_generate_images_button = ttk.Button(button_frame, text="🖼️ 開始生成圖片", 
                                                      command=self.generate_images_from_prompts,
                                                      style='Accent.TButton')
        self.image_generate_images_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.image_status_var = tk.StringVar(value="準備就緒")
        status_label = ttk.Label(button_frame, textvariable=self.image_status_var)
        status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def create_image_prompts_display_section(self, parent):
        """建立提示詞顯示區域"""
        self.image_prompts_frame = ttk.LabelFrame(parent, text="📝 編輯指令與時間戳", padding=5)
        self.image_prompts_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 初始提示
        initial_label = ttk.Label(self.image_prompts_frame, text="請先載入逐字稿檔案並生成指令")
        initial_label.pack(pady=20)
    
    def create_image_results_display_section(self, parent):
        """建立圖片結果顯示區域"""
        self.image_results_frame = ttk.LabelFrame(parent, text="🖼️ 生成結果", padding=10)
        self.image_results_frame.pack(fill=tk.BOTH, expand=True)
        
        # 初始提示
        initial_label = ttk.Label(self.image_results_frame, text="圖片生成結果將顯示在這裡")
        initial_label.pack(pady=20)
    
    def select_image_file(self):
        """選擇逐字稿檔案"""
        file_path = filedialog.askopenfilename(
            title="選擇逐字稿檔案",
            filetypes=[
                ("文字檔案", "*.txt"),
                ("SRT字幕檔", "*.srt"),
                ("Markdown檔案", "*.md"),
                ("RTF檔案", "*.rtf"),
                ("所有檔案", "*.*")
            ]
        )
        
        if file_path:
            self.image_file_var.set(file_path)
            self.image_transcript_content = self.load_transcript_file(file_path)
    
    def load_transcript_file(self, file_path):
        """載入逐字稿檔案"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.image_status_var.set(f"已載入檔案: {os.path.basename(file_path)}")
            return content
        except Exception as e:
            error_msg = f"檔案載入失敗: {str(e)}"
            self.image_status_var.set(error_msg)
            messagebox.showerror("錯誤", error_msg)
            return ""
    
    def generate_image_prompts(self):
        """生成圖像提示詞"""
        if not hasattr(self, 'image_transcript_content') or not self.image_transcript_content:
            messagebox.showwarning("警告", "請先選擇逐字稿檔案")
            return
        
        if not self.image_api_key_var.get():
            messagebox.showwarning("警告", "請輸入 API 金鑰")
            return
        
        # 更新狀態
        self.image_status_var.set("正在生成圖像提示詞...")
        self.image_generate_button.config(state='disabled', text='生成中...')
        
        # 在背景執行緒中執行生成
        threading.Thread(target=self._generate_image_prompts_thread, daemon=True).start()
    
    def _generate_image_prompts_thread(self):
        """生成圖像提示詞的背景執行緒 - 完全按照 React 版本邏輯"""
        try:
            # 導入必要的模組
            from image_generation_okokgo import ART_STYLE_OPTIONS
            import json
            import requests
            
            # 設定參數
            api_key = self.image_api_key_var.get()
            prompt_model = self.image_prompt_model_var.get()
            number_of_prompts = int(self.image_number_of_prompts_var.get())
            context_radius = max(0, int(self.image_context_radius_var.get()) or 0)
            
            # 設定藝術風格
            selected_label = self.image_art_style_var.get()
            art_style = next((opt["value"] for opt in ART_STYLE_OPTIONS if opt["label"] == selected_label), 
                           ART_STYLE_OPTIONS[0]["value"])
            
            # 步驟1: 解析 SRT 內容（模仿 React 版本的 parseSrt）
            self.root.after(0, lambda: self.image_status_var.set('正在解析逐字稿...'))
            
            srt_entries = self._parse_srt_content(self.image_transcript_content)
            if not srt_entries:
                self.root.after(0, lambda: self.image_status_var.set('無法解析 SRT 格式'))
                return
            
            print(f"DEBUG: 解析得到 {len(srt_entries)} 個 SRT 條目")
            
            # 步驟2: 選擇關鍵條目（模仿 React 版本的 selectKeyEntries）
            self.root.after(0, lambda: self.image_status_var.set('正在選擇關鍵時間點...'))
            
            selected_entries = self._select_key_entries(srt_entries, number_of_prompts)
            print(f"DEBUG: 選中 {len(selected_entries)} 個關鍵條目")
            
            # 步驟3: 建立上下文片段（模仿 React 版本的 buildContextSnippet）
            self.root.after(0, lambda: self.image_status_var.set('正在建立上下文...'))
            
            transcript_segments = []
            for entry in selected_entries:
                idx = srt_entries.index(entry)
                context_snippet = self._build_context_snippet(srt_entries, idx, context_radius)
                timestamp = entry['start_time'].split(',')[0]  # 只取時間部分，去掉毫秒
                transcript_segments.append(f"{timestamp} {context_snippet}")
            
            transcript_text = '\n'.join(transcript_segments)
            
            print(f"DEBUG: 最終 transcript 長度: {len(transcript_text)} 字符")
            print(f"DEBUG: 使用上下文範圍: {context_radius}")
            
            # 完全按照 React 版本的 systemPrompt 函數
            system_prompt = f"""// ROLE: Visual Director AI
// TASK: Convert a Chinese transcript into {number_of_prompts} distinct, high-quality, English image generation prompts with a CONSISTENT style.
// OUTPUT FORMAT: A single, valid JSON array of {number_of_prompts} objects. No other text.
// JSON Object Schema: {{ "timestamp": "string", "prompt": "string", "zh": "string" }}

// --- RULES ---
// 1. **COVERAGE & DIVERSITY (CRITICAL):**
//    - You MUST analyze the ENTIRE transcript from start to finish.
//    - The {number_of_prompts} prompts MUST represent key moments distributed across the **beginning, middle, and end** of the story.
//    - Ensure maximum **visual and thematic diversity**. Do NOT generate multiple prompts for the same scene or emotional beat.

// 2. **FAITHFULNESS TO SOURCE (CRITICAL):**
//    - The English prompt must accurately reflect the specific actions, objects, and emotions described in the corresponding Chinese transcript segment.
//    - Translate the core meaning and nuance; do not add elements not present in the source text.

// 3. PROMPT LANGUAGE: All 'prompt' values must be in English.

// 4. PROMPT STYLE (MANDATORY):
//    - Do NOT include any style keywords in the prompt itself.
//    - The application will automatically append the user-selected style "{art_style}" to the end of every prompt.
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
//   "prompt": "A young Taiwanese man standing at the edge of a cliff overlooking a vast landscape, expression of accomplishment and reflection, warm golden hour lighting, detailed facial features showing satisfaction, panoramic view with rolling hills in the distance, cinematic composition with dramatic sky, high resolution with rich textures.",
//   "zh": "一位年輕台灣男子站在懸崖邊俯瞰廣闊景觀，臉上帶著成就感和反思的表情，溫暖的黃金時刻照明，詳細的面部特徵顯示滿足感，遠處有起伏山丘的全景視野，戲劇性天空的電影構圖，高解析度豐富紋理。"
// }}

// --- START OF TASK ---
// Analyze the following transcript and generate the JSON output.

Transcript:
{transcript_text}"""
            
            print(f"DEBUG: 系統提示詞長度: {len(system_prompt)} 字符")
            
            # 步驟3: 調用 API
            payload = {
                "contents": [{
                    "role": "user",
                    "parts": [{"text": system_prompt}]
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
            
            api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{prompt_model}:generateContent?key={api_key}"
            
            print(f"DEBUG: 準備調用 API: {api_url}")
            print(f"DEBUG: Payload 大小: {len(json.dumps(payload))} 字符")
            
            response = requests.post(api_url, json=payload, timeout=60)
            
            print(f"DEBUG: API 回應狀態碼: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
                
                print(f"DEBUG: 提取的文字長度: {len(text)}")
                
                if text:
                    try:
                        parsed_prompts = json.loads(text)
                        print(f"DEBUG: 成功解析 {len(parsed_prompts)} 個提示詞")
                        
                        # 按照 React 版本添加風格後綴
                        style_suffix = self.build_style_suffix(art_style)
                        self.image_prompts = []
                        for prompt_item in parsed_prompts:
                            enhanced_prompt = {
                                'timestamp': prompt_item.get('timestamp', ''),
                                'prompt': f"{prompt_item.get('prompt', '')} {style_suffix}".strip(),
                                'zh': prompt_item.get('zh', '')
                            }
                            self.image_prompts.append(enhanced_prompt)
                        
                        print(f"DEBUG: 已添加風格後綴: {style_suffix}")
                        
                        # 更新 UI
                        self.root.after(0, self.update_image_prompts_display)
                        self.root.after(0, lambda: self.image_status_var.set(f"成功生成 {len(self.image_prompts)} 個圖像提示詞"))
                        
                    except json.JSONDecodeError as je:
                        error_msg = f"JSON 解析錯誤: {je}"
                        print(f"DEBUG: {error_msg}")
                        self.root.after(0, lambda: self.image_status_var.set(error_msg))
                else:
                    error_msg = "API 回應為空"
                    print(f"DEBUG: {error_msg}")
                    self.root.after(0, lambda: self.image_status_var.set(error_msg))
            else:
                error_msg = f"API 調用失敗: {response.status_code} - {response.text}"
                print(f"DEBUG: {error_msg}")
                self.root.after(0, lambda: self.image_status_var.set(error_msg))
                
        except Exception as e:
            error_msg = f"生成失敗: {str(e)}"
            self.root.after(0, lambda: self.image_status_var.set(error_msg))
            print(f"DEBUG: {error_msg}")
            traceback.print_exc()
        
        finally:
            # 恢復按鈕狀態
            self.root.after(0, lambda: self.image_generate_button.config(state='normal', text='🚀 生成英文圖片指令'))
    
    def _parse_srt_content(self, content: str) -> list:
        """解析 SRT 內容 - 模仿 React 版本的 parseSrt"""
        entries = []
        lines = content.strip().split('\n')
        i = 0
        
        while i < len(lines):
            # 跳過空行
            while i < len(lines) and not lines[i].strip():
                i += 1
            if i >= len(lines):
                break
                
            # 跳過序號行
            if lines[i].strip().isdigit():
                i += 1
                
            # 讀取時間戳行
            if i < len(lines) and '-->' in lines[i]:
                time_line = lines[i].strip()
                start_time, end_time = time_line.split(' --> ')
                i += 1
                
                # 讀取文字內容
                text_lines = []
                while i < len(lines) and lines[i].strip() and not lines[i].strip().isdigit():
                    text_lines.append(lines[i].strip())
                    i += 1
                
                if text_lines:
                    entries.append({
                        'start_time': start_time,
                        'end_time': end_time,
                        'text': ' '.join(text_lines)
                    })
            else:
                i += 1
                
        return entries
    
    def _select_key_entries(self, srt_entries: list, count: int) -> list:
        """選擇關鍵條目 - 模仿 React 版本的 selectKeyEntries"""
        if not srt_entries or count <= 0:
            return []
            
        if len(srt_entries) <= count:
            return srt_entries
            
        # 均勻分佈選擇
        step = len(srt_entries) / count
        selected = []
        
        for i in range(count):
            index = int(i * step)
            if index < len(srt_entries):
                selected.append(srt_entries[index])
                
        return selected
    
    def _build_context_snippet(self, srt_entries: list, idx: int, radius: int) -> str:
        """建立上下文片段 - 模仿 React 版本的 buildContextSnippet"""
        if not srt_entries or idx < 0 or idx >= len(srt_entries):
            return ""
            
        # 計算範圍
        start_idx = max(0, idx - radius)
        end_idx = min(len(srt_entries), idx + radius + 1)
        
        # 收集上下文文字
        context_texts = []
        for i in range(start_idx, end_idx):
            context_texts.append(srt_entries[i]['text'])
            
        return ' '.join(context_texts)
    
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
    
    def update_image_prompts_display(self):
        """更新提示詞顯示 - 緊湊佈局版本"""
        # 清除現有內容
        for widget in self.image_prompts_frame.winfo_children():
            widget.destroy()
        
        if not hasattr(self, 'image_prompts') or not self.image_prompts:
            return
        
        # 創建滾動區域
        canvas = tk.Canvas(self.image_prompts_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.image_prompts_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 顯示提示詞
        for i, prompt_item in enumerate(self.image_prompts):
            # 主容器
            item_frame = ttk.Frame(scrollable_frame, relief='solid', padding=8)
            item_frame.pack(fill=tk.X, pady=3, padx=5)
            
            # 標題行 - 包含編號、時間戳和按鈕
            header_frame = ttk.Frame(item_frame)
            header_frame.pack(fill=tk.X, pady=(0, 8))
            
            # 左側：編號和時間戳
            title_label = ttk.Label(header_frame, text=f"指令 {i+1} - 時間: {prompt_item['timestamp']}", 
                                   font=("Arial", 10, "bold"))
            title_label.pack(side=tk.LEFT)
            
            # 右側：按鈕組
            button_group = ttk.Frame(header_frame)
            button_group.pack(side=tk.RIGHT)
            
            copy_button = ttk.Button(button_group, text="複製", width=6,
                                   command=lambda idx=i: self.copy_image_prompt(idx))
            copy_button.pack(side=tk.LEFT, padx=(0, 5))
            
            delete_button = ttk.Button(button_group, text="刪除", width=6,
                                     command=lambda idx=i: self.delete_image_prompt(idx))
            delete_button.pack(side=tk.LEFT)
            
            # 英文提示詞區域
            prompt_label = ttk.Label(item_frame, text="英文提示詞:", font=("Arial", 9, "bold"))
            prompt_label.pack(anchor=tk.W, pady=(0, 3))
            
            prompt_text = tk.Text(item_frame, height=3, wrap=tk.WORD, font=("Arial", 9),
                                 relief='solid', borderwidth=1, bg='white', fg='black')
            prompt_text.insert(tk.END, prompt_item['prompt'])
            prompt_text.pack(fill=tk.X, pady=(0, 8))
            
            # 綁定文字變更事件
            def on_prompt_change(event, index=i):
                self.on_image_prompt_change(index, event.widget.get("1.0", tk.END).strip())
            prompt_text.bind('<KeyRelease>', on_prompt_change)
            
            # 中文說明區域
            zh_label = ttk.Label(item_frame, text="中文說明:", font=("Arial", 9, "bold"))
            zh_label.pack(anchor=tk.W, pady=(0, 3))
            
            zh_text = tk.Text(item_frame, height=2, wrap=tk.WORD, font=("Arial", 9),
                             relief='solid', borderwidth=1, fg='#333333', bg='#f8f8f8')
            zh_text.insert(tk.END, prompt_item['zh'])
            zh_text.pack(fill=tk.X)
        
        # 佈局滾動條和畫布
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 綁定滑鼠滾輪事件
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", _on_mousewheel)
        
        # 綁定畫布大小變化事件，確保內容寬度跟隨畫布
        def _on_canvas_configure(event):
            canvas.itemconfig(canvas.find_all()[0], width=event.width)
        canvas.bind('<Configure>', _on_canvas_configure)
    
    def on_image_prompt_change(self, index, new_value):
        """處理提示詞變更"""
        if hasattr(self, 'image_prompts') and 0 <= index < len(self.image_prompts):
            self.image_prompts[index]['prompt'] = new_value
    
    def delete_image_prompt(self, index):
        """刪除指定的提示詞"""
        if hasattr(self, 'image_prompts') and 0 <= index < len(self.image_prompts):
            result = messagebox.askyesno("確認刪除", f"確定要刪除指令 {index+1} 嗎？")
            if result:
                del self.image_prompts[index]
                self.update_image_prompts_display()
                self.image_status_var.set(f"已刪除指令 {index+1}，剩餘 {len(self.image_prompts)} 個指令")
    
    def copy_image_prompt(self, index):
        """複製提示詞到剪貼簿"""
        if hasattr(self, 'image_prompts') and 0 <= index < len(self.image_prompts):
            prompt_text = self.image_prompts[index]['prompt']
            self.root.clipboard_clear()
            self.root.clipboard_append(prompt_text)
            self.image_status_var.set(f"已複製指令 {index+1} 到剪貼簿")
    
    def generate_images_from_prompts(self):
        """從提示詞生成圖片"""
        if not hasattr(self, 'image_prompts') or not self.image_prompts:
            messagebox.showwarning("警告", "請先生成圖像提示詞")
            return
        
        if not self.image_api_key_var.get():
            messagebox.showwarning("警告", "請輸入 API 金鑰")
            return
        
        # 更新狀態
        self.image_status_var.set("正在生成圖片...")
        self.image_generate_images_button.config(state='disabled', text='生成中...')
        
        # 初始化結果顯示區域
        self.image_results = []
        self.init_image_results_display()
        
        # 在背景執行緒中執行生成
        threading.Thread(target=self._generate_images_from_prompts_thread, daemon=True).start()
    
    def _generate_images_from_prompts_thread(self):
        """生成圖片的背景執行緒 - 完全按照原本的實現"""
        try:
            import requests
            import base64
            import time
            from io import BytesIO
            
            # 設定參數
            api_key = self.image_api_key_var.get()
            image_model = self.image_model_var.get()
            number_of_images = int(self.image_number_of_images_var.get())
            person_generation = self.image_person_generation_var.get()
            
            self.image_results = []
            
            for i, prompt_item in enumerate(self.image_prompts):
                self.root.after(0, lambda i=i: self.image_status_var.set(f"處理指令 {i + 1} / {len(self.image_prompts)} ..."))
                
                try:
                    urls = []
                    
                    print(f"DEBUG: 使用模型 {image_model} 生成圖片 {i+1}")
                    print(f"DEBUG: 提示詞: {prompt_item['prompt'][:100]}...")
                    
                    if 'imagen-4' in image_model.lower():
                        # 使用 Google GenAI SDK (Imagen 4.0)
                        try:
                            from google import genai
                            from google.genai import types
                            from PIL import Image
                            
                            client = genai.Client(api_key=api_key)
                            
                            response = client.models.generate_images(
                                model=image_model,
                                prompt=prompt_item['prompt'],
                                config=types.GenerateImagesConfig(
                                    number_of_images=number_of_images,
                                    aspect_ratio="16:9",
                                    person_generation=person_generation
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
                    
                    elif 'imagen-3' in image_model.lower():
                        # 使用 Imagen 3.0 API
                        try:
                            payload = {
                                "instances": [{"prompt": prompt_item['prompt']}],
                                "parameters": {
                                    "sampleCount": number_of_images,
                                    "aspectRatio": "16:9",
                                    "personGeneration": person_generation
                                }
                            }
                            
                            api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{image_model}:predict?key={api_key}"
                            
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
                    
                    elif 'gemini' in image_model.lower():
                        # 使用 Gemini 多模態 API
                        try:
                            import google.generativeai as genai
                            
                            genai.configure(api_key=api_key)
                            model = genai.GenerativeModel(image_model)
                            
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
                        print(f"DEBUG: 不支援的模型: {image_model}")
                        print("DEBUG: 支援的模型: imagen-3.0-generate-002, imagen-4.0-generate-preview-06-06")
                    
                    # 根據生成結果添加到圖片列表並即時顯示
                    if urls:
                        result_item = {
                            "urls": urls,
                            "prompt_index": i,
                            "prompt_preview": prompt_item['prompt'],
                            "status": f"成功生成 {len(urls)} 張圖片"
                        }
                        self.image_results.append(result_item)
                        # 即時更新UI顯示這一個結果
                        self.root.after(0, lambda item=result_item: self.add_single_image_result(item))
                    else:
                        result_item = {
                            "urls": [],
                            "error": f"指令 {i + 1} 圖片生成失敗",
                            "prompt_index": i
                        }
                        self.image_results.append(result_item)
                        # 即時更新UI顯示這一個錯誤結果
                        self.root.after(0, lambda item=result_item: self.add_single_image_result(item))
                
                except Exception as e:
                    print(f"DEBUG: 指令 {i + 1} 生成失敗: {e}")
                    result_item = {
                        "urls": [],
                        "error": f"指令 {i + 1} 生成失敗: {str(e)}",
                        "prompt_index": i
                    }
                    self.image_results.append(result_item)
                    # 即時更新UI顯示這一個錯誤結果
                    self.root.after(0, lambda item=result_item: self.add_single_image_result(item))
                
                # 延遲避免 API 限制
                if i < len(self.image_prompts) - 1:
                    time.sleep(1.5)
            
            # 最終狀態更新
            self.root.after(0, lambda: self.image_status_var.set(f"圖片生成完成！共處理 {len(self.image_prompts)} 個指令"))
            
        except Exception as e:
            error_msg = f"圖片生成失敗: {str(e)}"
            self.root.after(0, lambda: self.image_status_var.set(error_msg))
            print(f"DEBUG: {error_msg}")
            traceback.print_exc()
        
        finally:
            # 恢復按鈕狀態
            self.root.after(0, lambda: self.image_generate_images_button.config(state='normal', text='🖼️ 開始生成圖片'))
    
    def init_image_results_display(self):
        """初始化圖片結果顯示區域"""
        # 清除現有內容
        for widget in self.image_results_frame.winfo_children():
            widget.destroy()
        
        # 標題和一鍵下載按鈕
        header_frame = ttk.Frame(self.image_results_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.results_title_label = ttk.Label(header_frame, 
                                           text="生成結果 (準備中...)",
                                           font=("Arial", 12, "bold"))
        self.results_title_label.pack(side=tk.LEFT)
        
        # 一鍵下載按鈕
        self.download_all_button = ttk.Button(header_frame, text="📥 一鍵下載全部", 
                                            command=self.download_all_generated_images,
                                            state='disabled')  # 初始為禁用狀態
        self.download_all_button.pack(side=tk.RIGHT)
        
        # 創建滾動區域用於顯示圖片
        canvas = tk.Canvas(self.image_results_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.image_results_frame, orient="vertical", command=canvas.yview)
        self.images_grid_frame = ttk.Frame(canvas)
        
        self.images_grid_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.images_grid_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 綁定滑鼠滾輪
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", _on_mousewheel)
        
        # 初始化網格變數
        self.current_row = 0
        self.current_col = 0
        self.images_per_row = 4
        
        # 配置網格列權重，讓圖片均勻分佈
        for i in range(self.images_per_row):
            self.images_grid_frame.columnconfigure(i, weight=1)
    
    def add_single_image_result(self, result):
        """添加單個圖片結果到網格顯示 - 即時顯示"""
        if result.get('error'):
            # 錯誤顯示 - 跳過，不佔用網格空間
            return
        
        urls = result.get('urls', [])
        if not urls:
            return
        
        # 為每張圖片創建網格項目
        for j, img_url in enumerate(urls):
            # 創建圖片容器
            img_container = ttk.Frame(self.images_grid_frame, relief='solid', borderwidth=1, padding=5)
            img_container.grid(row=self.current_row, column=self.current_col, 
                             padx=5, pady=5, sticky='nsew')
            
            # 設定容器固定大小
            img_container.configure(width=180, height=200)
            
            # 顯示縮圖預覽
            try:
                preview_label = self.create_image_preview(img_container, img_url, size=(160, 120))
                if preview_label:
                    preview_label.pack(pady=(0, 5))
            except Exception as e:
                print(f"預覽生成失敗: {e}")
                # 如果預覽失敗，顯示佔位符
                placeholder = ttk.Label(img_container, text=f"🖼️\n指令 {result['prompt_index']+1}\n圖片 {j+1}", 
                                      background='lightgray', width=20, anchor='center')
                placeholder.pack(pady=(0, 5))
            
            # 下載按鈕
            download_btn = ttk.Button(img_container, text="📥 下載", 
                                    command=lambda url=img_url, idx=f"{result['prompt_index']+1}_{j+1}": self.download_generated_image(url, idx))
            download_btn.pack(pady=(5, 0), fill=tk.X)
            
            # 更新網格位置
            self.current_col += 1
            if self.current_col >= self.images_per_row:
                self.current_col = 0
                self.current_row += 1
        
        # 更新標題統計
        self.update_results_title()
    
    def update_results_title(self):
        """更新結果標題統計"""
        if hasattr(self, 'image_results'):
            success_count = sum(len(img.get('urls', [])) for img in self.image_results if 'error' not in img)
            error_count = sum(1 for img in self.image_results if img.get('error'))
            self.results_title_label.config(text=f"生成結果 (成功: {success_count} 張圖片, 失敗: {error_count} 個指令)")
            
            # 啟用/禁用一鍵下載按鈕
            if hasattr(self, 'download_all_button'):
                if success_count > 0:
                    self.download_all_button.config(state='normal')
                else:
                    self.download_all_button.config(state='disabled')
    
    def download_all_generated_images(self):
        """一鍵下載所有生成的圖片"""
        if not hasattr(self, 'image_results') or not self.image_results:
            messagebox.showwarning("警告", "沒有可下載的圖片")
            return
        
        # 收集所有圖片URL
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        all_images = []
        for result in self.image_results:
            if not result.get('error') and result.get('urls'):
                for j, url in enumerate(result['urls']):
                    all_images.append({
                        'url': url,
                        'filename': f"image_{timestamp}_prompt_{result['prompt_index']+1}_{j+1}.png"
                    })
        
        if not all_images:
            messagebox.showwarning("警告", "沒有可下載的圖片")
            return
        
        # 選擇儲存資料夾
        from tkinter import filedialog
        folder_path = filedialog.askdirectory(title="選擇儲存資料夾")
        if not folder_path:
            return
        
        # 批量下載
        try:
            import base64
            import os
            
            downloaded_count = 0
            for img_info in all_images:
                try:
                    if img_info['url'].startswith('data:image/png;base64,'):
                        base64_data = img_info['url'].split(',')[1]
                        img_data = base64.b64decode(base64_data)
                        
                        file_path = os.path.join(folder_path, img_info['filename'])
                        with open(file_path, 'wb') as f:
                            f.write(img_data)
                        downloaded_count += 1
                except Exception as e:
                    print(f"下載 {img_info['filename']} 失敗: {e}")
            
            messagebox.showinfo("完成", f"成功下載 {downloaded_count} 張圖片到:\n{folder_path}")
            self.image_status_var.set(f"批量下載完成: {downloaded_count} 張圖片")
            
        except Exception as e:
            error_msg = f"批量下載失敗: {str(e)}"
            messagebox.showerror("錯誤", error_msg)
            self.image_status_var.set(error_msg)
    
    def create_image_preview(self, parent, img_url, size=(150, 150)):
        """創建圖片預覽 - 按照原本的實現"""
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
    
    def download_generated_image(self, img_url, filename):
        """下載生成的圖片 - 按照原本的實現"""
        try:
            print(f"DEBUG: 開始下載圖片 {filename}")
            print(f"DEBUG: URL 類型: {type(img_url)}")
            print(f"DEBUG: URL 開頭: {img_url[:50] if img_url else 'None'}...")
            
            if img_url and img_url.startswith('data:image/png;base64,'):
                import base64
                from tkinter import filedialog
                
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
                    self.image_status_var.set(f"圖片已儲存至: {file_path}")
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
            error_msg = f"下載失敗: {str(e)}"
            self.image_status_var.set(error_msg)
            messagebox.showerror("錯誤", error_msg)

    # SECTION 2.4: AI 媒體庫歸檔頁籤
    # ===============================================================
    def create_archive_tab(self):
        main_frame = ttk.Frame(self.archive_tab)
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(1, weight=1)
        
        settings_frame = ttk.Labelframe(main_frame, text="設定", padding=10)
        settings_frame.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        settings_frame.columnconfigure(1, weight=1)
        
        ttk.Label(settings_frame, text="API 金鑰:").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(settings_frame, textvariable=self.api_key_var, show="*").grid(row=0, column=1, columnspan=2, sticky="ew", pady=2)
        
        ttk.Label(settings_frame, text="AI 模型:").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Entry(settings_frame, textvariable=self.ai_model_var).grid(row=1, column=1, columnspan=2, sticky="ew", pady=2)
        
        ttk.Label(settings_frame, text="待處理資料夾:").grid(row=2, column=0, sticky="w", pady=2)
        ttk.Entry(settings_frame, textvariable=self.source_folder_var).grid(row=2, column=1, sticky="ew", pady=2)
        ttk.Button(settings_frame, text="瀏覽", command=lambda: self.browse_folder(self.source_folder_var)).grid(row=2, column=2, padx=(5,0))
        
        ttk.Label(settings_frame, text="已處理資料夾:").grid(row=3, column=0, sticky="w", pady=2)
        ttk.Entry(settings_frame, textvariable=self.processed_folder_var).grid(row=3, column=1, sticky="ew", pady=2)
        ttk.Button(settings_frame, text="瀏覽", command=lambda: self.browse_folder(self.processed_folder_var)).grid(row=3, column=2, padx=(5,0))
        
        control_frame = ttk.Frame(settings_frame)
        control_frame.grid(row=4, column=0, columnspan=3, pady=10)
        
        self.archive_start_btn = ttk.Button(control_frame, text="開始處理", command=self.start_archiving, style="Accent.TButton")
        self.archive_start_btn.pack(side=tk.LEFT, padx=5)
        self.archive_stop_btn = ttk.Button(control_frame, text="停止處理", command=self.stop_archiving, style="Stop.TButton", state=tk.DISABLED)
        self.archive_stop_btn.pack(side=tk.LEFT, padx=5)
        
        log_frame = ttk.Labelframe(main_frame, text="處理日誌", padding=10)
        log_frame.grid(row=0, column=1, sticky="nsew")
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        
        self.archive_log_area = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=10, font=self.fonts['console'])
        self.archive_log_area.grid(row=0, column=0, sticky="nsew")
        self.archive_log_area.config(state=tk.DISABLED)

    # ===============================================================
    # SECTION 2.5: 媒體搜尋頁籤
    # ===============================================================
    def create_search_tab(self):
        main_frame = ttk.Frame(self.search_tab)
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.rowconfigure(2, weight=1)
        main_frame.columnconfigure(0, weight=2)
        main_frame.columnconfigure(1, weight=1)
        
        search_control_frame = ttk.Frame(main_frame)
        search_control_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        search_control_frame.columnconfigure(0, weight=1)
        
        self.search_query_var = tk.StringVar()
        ttk.Entry(search_control_frame, textvariable=self.search_query_var).grid(row=0, column=0, sticky="ew")
        ttk.Button(search_control_frame, text="🔍 搜尋", command=self.perform_search).grid(row=0, column=1, padx=5)
        ttk.Button(search_control_frame, text="🧠 自然語言搜尋", command=self.perform_nl_search).grid(row=0, column=2, padx=5)
        ttk.Button(search_control_frame, text="🔄 重新整理資料", command=self.load_search_data).grid(row=0, column=3, padx=5)
        
        self.search_status_label = ttk.Label(main_frame, text="請點擊「重新整理資料」以載入媒體庫。")
        self.search_status_label.grid(row=1, column=0, columnspan=2, sticky="w")
        
        results_frame = ttk.Labelframe(main_frame, text="搜尋結果", padding=10)
        results_frame.grid(row=2, column=0, sticky="nsew", padx=(0, 10))
        results_frame.rowconfigure(0, weight=1)
        results_frame.columnconfigure(0, weight=1)
        
        self.search_tree = ttk.Treeview(results_frame, columns=("ID", "Title", "Type", "Path"), show="headings")
        self.search_tree.heading("ID", text="ID")
        self.search_tree.heading("Title", text="建議標題")
        self.search_tree.heading("Type", text="類型")
        self.search_tree.heading("Path", text="檔案名稱")
        self.search_tree.column("ID", width=60, anchor='center')
        self.search_tree.column("Title", width=250)
        self.search_tree.column("Type", width=80, anchor='center')
        self.search_tree.column("Path", width=250)
        self.search_tree.grid(row=0, column=0, sticky="nsew")
        
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.search_tree.yview)
        self.search_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        self.search_tree.bind("<<TreeviewSelect>>", self.on_search_result_select)
        
        details_frame = ttk.Labelframe(main_frame, text="詳細資訊", padding=10)
        details_frame.grid(row=2, column=1, sticky="nsew")
        details_frame.rowconfigure(1, weight=1)
        details_frame.columnconfigure(0, weight=1)
        
        self.details_image_label = ttk.Label(details_frame)
        self.details_image_label.grid(row=0, column=0, pady=5)
        
        self.details_text = scrolledtext.ScrolledText(details_frame, wrap=tk.WORD, height=10, font=self.fonts['console'])
        self.details_text.grid(row=1, column=0, sticky="nsew", pady=5)
        self.details_text.config(state=tk.DISABLED)

    # ===============================================================
    # SECTION 3: 功能實現方法
    # ===============================================================
    
    def check_required_files(self):
        log_ref = self.transcribe_log_area
        self.log_message("正在檢查必要檔案...", log_area_ref=log_ref)
        
        if not WHISPER_CPP_PATH.is_dir():
            error_msg = f"錯誤：找不到資源檔案夾 '{WHISPER_CPP_FOLDER_NAME}'"
            self.log_message(error_msg, is_error=True, log_area_ref=log_ref)
            messagebox.showerror("啟動錯誤", error_msg)
            return
            
        self.log_message("必要檔案檢查通過。", is_success=True, log_area_ref=log_ref)
    
    def select_file(self):
        filetypes = [
            ("音頻/視頻檔案", "*.mp3 *.mp4 *.m4a *.wav *.aac *.flac *.ogg *.wma *.mov *.avi *.mkv"),
            ("所有檔案", "*.*")
        ]
        selected = filedialog.askopenfilename(filetypes=filetypes)
        if selected:
            self.selected_file = selected
            self.file_label.config(text=Path(self.selected_file).name)
            self.external_srt_path = None

            self.last_srt_path = None
            self.update_ai_buttons_state()
            self.log_message(f"已選擇輸入檔案: {Path(selected).name}", log_area_ref=self.transcribe_log_area)
    

    def select_output_dir(self):
        selected = filedialog.askdirectory()
        if selected:
            self.output_dir = selected
            self.output_dir_label.config(text=self.output_dir)
            self.log_message(f"已選擇輸出目錄: {self.output_dir}", log_area_ref=self.transcribe_log_area)
    
    def start_transcription_thread(self):
        thread = threading.Thread(target=self.transcribe_audio, daemon=True)
        thread.start()
    

    
    def transcribe_audio(self):
        log_ref = self.transcribe_log_area
        if not self.selected_file:
            self.log_message("轉錄請求失敗: 未選擇檔案", is_warning=True, log_area_ref=log_ref)
            self.root.after(0, lambda: messagebox.showwarning("警告", "請選擇文件"))
            return
        
        try:
            original_file = Path(self.selected_file)
            temp_wav_file = None  # 用於追蹤臨時 WAV 檔案
            
            # 檢查檔案格式，Whisper 需要特定格式的 WAV (16kHz, 單聲道)
            if original_file.suffix.lower() != '.wav':
                self.log_message(f"檔案格式為 {original_file.suffix}，自動轉換為 WAV 格式", log_area_ref=log_ref)
                
                # 自動轉換為 WAV
                wav_file = self._convert_to_wav_for_transcription(original_file, log_ref)
                if not wav_file:
                    self.log_message("WAV 轉換失敗，轉錄中止", is_warning=True, log_area_ref=log_ref)
                    return
                
                # 使用轉換後的 WAV 檔案
                input_file = wav_file
                temp_wav_file = wav_file  # 記錄臨時檔案，稍後刪除
                self.log_message(f"已轉換為 WAV 格式: {input_file}", log_area_ref=log_ref)
            else:
                # 即使是 WAV 檔案，也需要確保格式正確 (16kHz, 單聲道)
                self.log_message(f"檔案格式為 .wav，檢查並轉換為正確格式", log_area_ref=log_ref)
                
                # 重新轉換 WAV 檔案以確保格式正確
                wav_file = self._convert_to_wav_for_transcription(original_file, log_ref)
                if not wav_file:
                    self.log_message("WAV 格式轉換失敗，轉錄中止", is_warning=True, log_area_ref=log_ref)
                    return
                
                # 使用轉換後的 WAV 檔案
                input_file = wav_file
                temp_wav_file = wav_file  # 記錄臨時檔案，稍後刪除
                self.log_message(f"已轉換為正確的 WAV 格式: {input_file}", log_area_ref=log_ref)
            
            self.log_message("開始語音轉錄...", log_area_ref=log_ref)
            output_srt = input_file.parent / f"{input_file.stem}.srt"
            
            # 直接使用 Whisper main 執行檔
            import subprocess
            from config_service import config_service
            
            whisper_main = config_service.get_whisper_main_path()
            whisper_resources = config_service.get_whisper_resources_path()
            model_file = whisper_resources / "ggml-medium.bin"
            
            if not whisper_main.exists():
                raise FileNotFoundError("找不到 Whisper main 執行檔")
            
            if not model_file.exists():
                raise FileNotFoundError("找不到 Whisper 模型檔案")
            
            # 獲取 GUI 設定
            selected_model = AVAILABLE_MODELS.get(self.selected_model_key.get(), "ggml-medium.bin")
            model_file = whisper_resources / selected_model
            language = self.selected_language.get()
            threads = "4"  # 固定使用4個線程
            temperature = "0.0"  # 固定使用0.0溫度以獲得最佳準確度
            
            # 獲取提示詞 (從 Text 元件)
            prompt_text = self.transcribe_prompt_widget.get('1.0', 'end-1c').strip()
            placeholder_text = "範例：張三 李四 王五 台積電 聯發科 機器學習 深度學習\n\n• 詞彙間用空格分隔\n• 輸入專有名詞、人名、公司名等\n• 可提高特定詞彙的識別準確度"
            if prompt_text == placeholder_text or not prompt_text:
                prompt_text = ""
            
            # Whisper 命令 - 使用 GUI 設定
            output_base = str(input_file.parent / input_file.stem)
            command = [
                str(whisper_main),
                "-f", str(input_file),
                "-m", str(model_file),
                "-l", language,
                "-t", threads,
                "--output-file", output_base,  # 指定輸出檔案基礎名稱
                "--output-srt"
            ]
            
            # 所有模型使用相同的標準參數，不做特殊處理
            command.extend(["--temperature", "0.0"])
            
            # 加入提示詞
            if prompt_text:
                command.extend(["--prompt", prompt_text])
            
            # 移除翻譯選項，因為翻譯品質不佳
            
            self.log_message(f"執行命令: {' '.join(command)}", log_area_ref=log_ref)
            self.log_message("轉錄中，請稍候...", log_area_ref=log_ref)
            
            # 在背景執行轉錄
            def run_transcription():
                try:
                    # 使用 Popen 來即時獲取輸出
                    import subprocess
                    
                    process = subprocess.Popen(
                        command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,  # 將錯誤輸出重定向到標準輸出
                        text=True,
                        bufsize=1,  # 行緩衝
                        universal_newlines=True,
                        cwd=str(input_file.parent)
                    )
                    
                    # 即時讀取並顯示輸出
                    output_lines = []
                    error_detected = False
                    while True:
                        line = process.stdout.readline()
                        if not line and process.poll() is not None:
                            break
                        if line:
                            line = line.strip()
                            output_lines.append(line)
                            # 檢測錯誤訊息
                            if "error:" in line.lower() or "unknown argument:" in line.lower():
                                error_detected = True
                            # 即時顯示到日誌
                            self.root.after(0, lambda l=line: self.log_message(l, log_area_ref=log_ref))
                    
                    # 等待進程完成
                    return_code = process.wait()
                    
                    # 如果檢測到錯誤，強制設定返回碼為非零
                    if error_detected:
                        return_code = 1
                    
                    # 創建結果對象以保持兼容性
                    class Result:
                        def __init__(self, returncode, stdout, stderr=""):
                            self.returncode = returncode
                            self.stdout = stdout
                            self.stderr = stderr
                    
                    result = Result(return_code, "\n".join(output_lines))
                    
                    self.root.after(0, lambda: self.log_message(f"Whisper 執行完成，返回碼: {result.returncode}", log_area_ref=log_ref))
                    
                    # 在主線程中更新 UI，並傳遞臨時檔案資訊
                    self.root.after(0, lambda: self._handle_transcription_result(result, output_srt, log_ref, temp_wav_file))
                    
                except subprocess.TimeoutExpired:
                    self.root.after(0, lambda: self._handle_transcription_error("轉錄超時（超過30分鐘）", log_ref, temp_wav_file))
                except Exception as e:
                    self.root.after(0, lambda: self._handle_transcription_error(f"轉錄錯誤: {str(e)}", log_ref, temp_wav_file))
            
            # 在背景線程中執行
            import threading
            thread = threading.Thread(target=run_transcription)
            thread.daemon = True
            thread.start()
                
        except FileNotFoundError as e:
            error_msg = str(e)
            self.log_message(error_msg, is_warning=True, log_area_ref=log_ref)
            messagebox.showerror("錯誤", error_msg)
        except Exception as e:
            error_msg = f"語音轉錄錯誤: {str(e)}"
            self.log_message(error_msg, is_warning=True, log_area_ref=log_ref)
            messagebox.showerror("錯誤", error_msg)
    
    def update_ai_buttons_state(self):
        """更新語音轉錄頁籤中的 AI 按鈕狀態（已移除 AI 功能區塊）"""
        # 語音轉錄頁籤中的 AI 功能已移除，此方法保留以避免錯誤
        pass
    
    def update_status_label(self, message):
        """更新狀態標籤"""
        # 這個方法用於更新狀態，目前使用日誌代替
        self.log_message(f"狀態: {message}", log_area_ref=self.transcribe_log_area)
    
    def _handle_transcription_result(self, result, output_srt, log_ref, temp_wav_file=None):
        """處理轉錄結果"""
        try:
            if result.returncode == 0:
                self.log_message("轉錄完成！", log_area_ref=log_ref)
                
                # 檢查多種可能的輸出檔案位置
                input_file = Path(self.selected_file)
                possible_outputs = [
                    output_srt,  # 原始預期位置
                    input_file.parent / f"{input_file.stem}.srt",  # 同目錄
                    Path.cwd() / f"{input_file.stem}.srt",  # 當前工作目錄
                ]
                
                found_srt = None
                for srt_path in possible_outputs:
                    if srt_path.exists():
                        found_srt = srt_path
                        break
                
                if found_srt:
                    self.log_message(f"SRT 檔案已生成: {found_srt}", log_area_ref=log_ref)
                    
                    # 移除Large-v3特殊處理，所有模型使用相同邏輯
                    
                    # 轉換簡體中文為繁體中文 (僅在選擇該選項時)
                    if self.convert_to_traditional_chinese.get():
                        try:
                            self._convert_srt_to_traditional_chinese(found_srt, log_ref)
                        except Exception as e:
                            self.log_message(f"繁體轉換警告: {str(e)}", is_warning=True, log_area_ref=log_ref)
                    
                    messagebox.showinfo("轉錄完成", f"轉錄完成！\n\nSRT 檔案: {found_srt}")
                    
                    # 自動載入 SRT 檔案
                    self.last_srt_path = str(found_srt)
                    self.update_ai_buttons_state()
                else:
                    self.log_message("警告: 轉錄完成，但未找到 SRT 檔案", is_warning=True, log_area_ref=log_ref)
                    messagebox.showwarning("轉錄完成", f"轉錄完成，但未找到 SRT 檔案\n\n可能的原因：\n1. 音訊檔案太短或無語音內容\n2. 輸出路徑問題\n\n請檢查日誌獲取更多資訊")
            else:
                error_msg = f"Whisper 錯誤 (返回碼 {result.returncode}): {result.stderr}"
                self.log_message(error_msg, is_warning=True, log_area_ref=log_ref)
                messagebox.showerror("轉錄失敗", f"轉錄失敗\n{error_msg}")
        finally:
            # 清理臨時 WAV 檔案
            self._cleanup_temp_wav_file(temp_wav_file, log_ref)
    
    def _handle_transcription_error(self, error_msg, log_ref, temp_wav_file=None):
        """處理轉錄錯誤"""
        self.log_message(error_msg, is_warning=True, log_area_ref=log_ref)
        messagebox.showerror("轉錄錯誤", error_msg)
        # 清理臨時 WAV 檔案
        self._cleanup_temp_wav_file(temp_wav_file, log_ref)
    
    def _cleanup_temp_wav_file(self, temp_wav_file, log_ref):
        """清理臨時 WAV 檔案"""
        if temp_wav_file and temp_wav_file.exists():
            try:
                temp_wav_file.unlink()  # 刪除檔案
                self.log_message(f"已清理臨時 WAV 檔案: {temp_wav_file}", log_area_ref=log_ref)
            except Exception as e:
                self.log_message(f"清理臨時檔案失敗: {str(e)}", is_warning=True, log_area_ref=log_ref)
    
    def _convert_to_wav_for_transcription(self, input_file, log_ref):
        """專門用於轉錄的 WAV 轉換方法"""
        try:
            self.log_message("開始 WAV 轉換...", log_area_ref=log_ref)
            
            # 如果原檔案就是 WAV，創建臨時檔案名稱避免衝突
            if input_file.suffix.lower() == '.wav':
                output_file = input_file.parent / f"{input_file.stem}_temp_16k.wav"
            else:
                output_file = input_file.parent / f"{input_file.stem}.wav"
            
            # 直接使用 FFmpeg 進行轉換
            import subprocess
            from config_service import config_service
            
            ffmpeg_path = config_service.get_ffmpeg_path()
            
            if not ffmpeg_path.exists():
                # 嘗試使用系統的 FFmpeg
                ffmpeg_path = "ffmpeg"
            
            # FFmpeg 命令
            command = [
                str(ffmpeg_path),
                "-i", str(input_file),
                "-vn",  # 不處理視頻流（對於視頻檔案）
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                "-y",  # 覆蓋輸出檔案
                str(output_file)
            ]
            
            self.log_message(f"執行命令: {' '.join(command)}", log_area_ref=log_ref)
            
            # 執行轉換
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300  # 5分鐘超時
            )
            
            if result.returncode == 0:
                self.log_message(f"WAV 轉換完成: {output_file}", log_area_ref=log_ref)
                return output_file
            else:
                error_msg = f"FFmpeg 錯誤: {result.stderr}"
                self.log_message(error_msg, is_warning=True, log_area_ref=log_ref)
                return None
                
        except subprocess.TimeoutExpired:
            self.log_message("WAV 轉換超時（超過5分鐘）", is_warning=True, log_area_ref=log_ref)
            return None
        except FileNotFoundError:
            self.log_message("找不到 FFmpeg，請確認已正確安裝", is_warning=True, log_area_ref=log_ref)
            return None
        except Exception as e:
            self.log_message(f"WAV 轉換錯誤: {str(e)}", is_warning=True, log_area_ref=log_ref)
            return None

    def _clean_repetitive_content(self, srt_file, log_ref):
        """清理SRT檔案中的重複內容 - 針對Large-v3模型的幻聽問題"""
        try:
            import re
            
            # 讀取 SRT 檔案
            with open(srt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 分割成字幕塊
            subtitle_blocks = re.split(r'\n\s*\n', content.strip())
            cleaned_blocks = []
            repetition_threshold = 3  # 連續重複3次以上視為異常
            
            for i, block in enumerate(subtitle_blocks):
                if not block.strip():
                    continue
                
                lines = block.strip().split('\n')
                if len(lines) < 3:  # 不是完整的字幕塊
                    cleaned_blocks.append(block)
                    continue
                
                # 提取文字內容（跳過序號和時間戳）
                text_content = '\n'.join(lines[2:]).strip()
                
                # 檢查是否與前面的內容重複
                is_repetitive = False
                if len(cleaned_blocks) >= repetition_threshold:
                    recent_texts = []
                    for j in range(max(0, len(cleaned_blocks) - repetition_threshold), len(cleaned_blocks)):
                        recent_block = cleaned_blocks[j]
                        recent_lines = recent_block.strip().split('\n')
                        if len(recent_lines) >= 3:
                            recent_text = '\n'.join(recent_lines[2:]).strip()
                            recent_texts.append(recent_text)
                    
                    # 檢查是否所有最近的文字都相同或非常相似
                    if len(recent_texts) >= repetition_threshold:
                        similarity_count = sum(1 for text in recent_texts if self._text_similarity(text, text_content) > 0.8)
                        if similarity_count >= repetition_threshold - 1:
                            is_repetitive = True
                
                if not is_repetitive:
                    cleaned_blocks.append(block)
                else:
                    # 發現重複，停止處理後續內容
                    self.log_message(f"檢測到重複內容，已清理從第 {i+1} 個字幕塊開始的重複部分", log_area_ref=log_ref)
                    break
            
            # 重新組合清理後的內容
            cleaned_content = '\n\n'.join(cleaned_blocks)
            
            # 寫回檔案
            with open(srt_file, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            
            original_count = len(subtitle_blocks)
            cleaned_count = len(cleaned_blocks)
            if cleaned_count < original_count:
                self.log_message(f"已清理重複內容：原有 {original_count} 個字幕塊，清理後 {cleaned_count} 個", log_area_ref=log_ref)
            else:
                self.log_message("未發現重複內容", log_area_ref=log_ref)
            
        except Exception as e:
            self.log_message(f"重複內容清理失敗: {str(e)}", is_warning=True, log_area_ref=log_ref)
    
    def _text_similarity(self, text1, text2):
        """計算兩個文字的相似度"""
        if not text1 or not text2:
            return 0.0
        
        # 簡單的相似度計算：基於共同詞彙
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 1.0 if text1.strip() == text2.strip() else 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0

    def _convert_srt_to_traditional_chinese(self, srt_file, log_ref):
        """將 SRT 檔案中的簡體中文轉換為繁體中文"""
        try:
            import opencc
            
            # 創建簡體轉繁體的轉換器
            converter = opencc.OpenCC('s2t')  # 簡體轉繁體
            
            # 讀取 SRT 檔案
            with open(srt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 轉換為繁體中文
            traditional_content = converter.convert(content)
            
            # 寫回檔案
            with open(srt_file, 'w', encoding='utf-8') as f:
                f.write(traditional_content)
            
            self.log_message("已轉換為繁體中文", log_area_ref=log_ref)
            
        except ImportError:
            self.log_message("OpenCC 未安裝，跳過繁體轉換", is_warning=True, log_area_ref=log_ref)
        except Exception as e:
            self.log_message(f"繁體轉換失敗: {str(e)}", is_warning=True, log_area_ref=log_ref)

    def ai_correct_srt(self):
        self.log_message("請求 AI 校正...")
        if not _GENAI_IMPORTED or not _SRT_IMPORTED: 
            err_msg = f"缺少必要的函式庫: {', '.join(lib for lib in _IMPORT_ERROR_LIBS if lib in ['google-generativeai', 'srt'])}\n請安裝後重啟程式。"
            self.log_message(err_msg, is_error=True)
            messagebox.showerror("AI 校正錯誤", err_msg)
            return
        
        api_key = self.api_key_var.get()
        if not api_key: 
            self.log_message("AI 校正錯誤: 未輸入 API 金鑰", is_warning=True)
            messagebox.showerror("AI 校正錯誤", "請先在設定區輸入您的 Google AI API 金鑰。")
            return
        
        # 優先使用 AI 頁籤的 SRT 檔案，否則使用語音轉錄的檔案
        if hasattr(self, 'ai_srt_file_path') and self.ai_srt_file_path:
            target_srt_path = self.ai_srt_file_path
            log_area_ref = self.ai_log_area
        else:
            target_srt_path = self.external_srt_path if self.external_srt_path else self.last_srt_path
            log_area_ref = self.transcribe_log_area
            
        if not target_srt_path or not os.path.exists(target_srt_path): 
            self.log_message("AI 校正錯誤: 找不到有效的 SRT 檔案", is_warning=True, log_area_ref=log_area_ref)
            messagebox.showerror("AI 校正錯誤", "找不到有效的 SRT 檔案進行校正。\n請先轉錄生成 SRT 或載入 SRT 檔案。")
            return
        
        if self.is_ai_correcting or self.is_ai_analyzing: 
            self.log_message("AI 功能正在執行中，請稍候...", is_warning=True)
            messagebox.showwarning("提示", "AI 功能正在執行中，請稍候...")
            return
        
        # 獲取使用者提示詞 (根據來源選擇正確的提示詞框)
        if hasattr(self, 'ai_srt_file_path') and self.ai_srt_file_path:
            # 使用 AI 頁籤的提示詞
            user_prompt_terms = self.ai_prompt_widget.get('1.0', 'end-1c').strip()
            ai_placeholder_text = "範例：張三 李四 王五 台積電 聯發科 機器學習 深度學習\n\n• 詞彙間用空格分隔\n• 輸入專有名詞、人名、公司名等"
            if user_prompt_terms == ai_placeholder_text:
                user_prompt_terms = ""
        else:
            # 使用語音轉錄頁籤的提示詞
            user_prompt_terms = self.transcribe_prompt_widget.get('1.0', 'end-1c').strip()
            transcribe_placeholder_text = "範例：張三 李四 王五 台積電 聯發科 機器學習 深度學習\n\n• 詞彙間用空格分隔\n• 輸入專有名詞、人名、公司名等"
            if user_prompt_terms == transcribe_placeholder_text:
                user_prompt_terms = ""
        
        self.is_ai_correcting = True
        self.update_ai_buttons_state_tab()
        self.update_status_label("準備開始 AI 校正...")
        self.log_message(f"開始 AI 校正執行緒，目標檔案: {os.path.basename(target_srt_path)}", log_area_ref=log_area_ref)
        self.root.update_idletasks()
        
        correction_thread = threading.Thread(target=self._do_ai_correction_thread, args=(api_key, target_srt_path, user_prompt_terms, log_area_ref), daemon=True)
        correction_thread.start()
    
    def _do_ai_correction_thread(self, api_key, srt_path, user_prompt_terms, log_area_ref=None):
        original_subs = []
        all_correction_data = []
        
        try:
            if log_area_ref is None:
                log_area_ref = self.transcribe_log_area
            self.log_message("AI 校正線程：正在設定 Google AI...", log_area_ref=log_area_ref)
            self.root.after(0, self.update_status_label, "正在設定 Google AI...")
            
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                model_name = self.ai_model_var.get().strip() or "gemini-2.5-flash"
                self.log_message(f"使用 AI 模型進行校正: {model_name}", log_area_ref=log_area_ref)
                model = genai.GenerativeModel(model_name)
                safety_settings = [
                    {"category": c, "threshold": "BLOCK_NONE"} 
                    for c in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]
                ]
                generation_config = genai.types.GenerationConfig(temperature=0.1)
            except Exception as config_err:
                if "API key not valid" in str(config_err): 
                    raise ValueError(f"Google AI API 金鑰無效或錯誤。") from config_err
                elif "model not found" in str(config_err).lower() or "permission denied" in str(config_err).lower() or "model_name" in str(config_err).lower(): 
                    raise ValueError(f"無法使用 AI 模型 '{model_name}'。\n請確認名稱正確、API金鑰有效且模型有權限使用。") from config_err
                else: 
                    raise Exception(f"設定 Google AI 失敗: {config_err}") from config_err
            
            self.log_message(f"正在讀取 SRT: {os.path.basename(srt_path)}")
            self.root.after(0, self.update_status_label, f"正在讀取 SRT...")
            
            try:
                import srt
                with open(srt_path, 'r', encoding='utf-8') as f: 
                    srt_content = f.read()
                original_subs = list(srt.parse(srt_content))
                if not original_subs: 
                    raise ValueError("SRT 檔案為空或無法解析。")
                self.log_message(f"成功讀取 {len(original_subs)} 條原始字幕。")
            except Exception as parse_err: 
                raise Exception(f"讀取或解析 SRT 失敗: {parse_err}") from parse_err
            
            # 使用者設定的批次大小
            try:
                chunk_size = int(self.batch_size_var.get().strip())
                if chunk_size <= 0:
                    chunk_size = 15
            except (ValueError, AttributeError):
                chunk_size = 15
            total_subs = len(original_subs)
            num_chunks = math.ceil(total_subs / chunk_size)
            self.log_message(f"將 {total_subs} 條字幕分為 {num_chunks} 個區塊處理 (每區塊最多 {chunk_size} 條)。")
            
            for i in range(num_chunks):
                start_index = i * chunk_size
                end_index = min((i + 1) * chunk_size, total_subs)
                chunk_original_subs = original_subs[start_index:end_index]
                
                if not chunk_original_subs: 
                    continue
                
                progress = int(((i + 1) / num_chunks) * 100)
                status_msg = f"AI 校正中 ({progress}%)... Chunk {i+1}/{num_chunks}"
                self.log_message(status_msg)
                self.root.after(0, self.update_status_label, status_msg)
                
                prompt_lines = [
                    "你是一位專業的繁體中文影片字幕校對編輯。",
                    "任務：請仔細檢查以下提供的「原始字幕文字」（這是自動語音辨識或斷句後的結果，可能包含聽音錯誤（同音異字、近音異字）、斷句錯誤、以及專有名詞辨識錯誤），逐行修正其中的錯別字、標點符號錯誤、語音辨識錯誤或不通順之處。",
                    "目標：讓字幕更準確、易讀、流暢，同時必須完整保留原始語意。"
                ]
                
                if user_prompt_terms: 
                    prompt_lines.append(f"重要參考：以下是使用者提供的可能正確的詞彙或專有名詞列表。如果原始文字中的某個詞語發音相似但意義不符上下文，且替換為列表中的詞彙後語意更合理，請優先進行替換。列表：'{user_prompt_terms}'。")
                
                prompt_lines.extend([
                    "重要規則：",
                    "1. 輸出：僅輸出「修正後的字幕文字」，不要包含任何原始文字、標籤、索引編號或解釋。",
                    "2. 行數：輸出的總行數必須與輸入的「原始字幕文字」總行數完全相同。",
                    "3. 對應：輸出的每一行文字，都必須是對應順序的原始文字行的修正結果。",
                    "4. 無錯誤：如果某一行原始文字沒有錯誤，請直接「原樣」輸出該行文字。",
                    "原始字幕文字如下 (每行代表一個字幕片段)：",
                    "---"
                ])
                
                current_chunk_input_lines = []
                for sub_idx, sub in enumerate(chunk_original_subs):
                    prompt_line = f"{sub.content.replace(chr(10), ' ').strip()}"
                    prompt_lines.append(prompt_line)
                    current_chunk_input_lines.append(sub.content)
                
                prompt_lines.append("---")
                prompt_lines.append(f"請嚴格遵守以上規則，開始輸出 {len(chunk_original_subs)} 行修正後的文字：")
                full_prompt = "\n".join(prompt_lines)
                
                retries = 2
                corrected_texts_str = None
                last_api_error_for_chunk = None
                
                for attempt in range(retries):
                    try:
                        self.log_message(f"  Chunk {i+1}, Attempt {attempt+1}/{retries}: 呼叫 Gemini API...")
                        response = model.generate_content(full_prompt, generation_config=generation_config, safety_settings=safety_settings)
                        
                        if hasattr(response, 'text') and response.text is not None:
                            raw_response_text = response.text
                            corrected_text_lines_raw = raw_response_text.strip().split('\n')
                            import re
                            corrected_text_lines = [re.sub(r"^\s*[\d\.\-\*:]+\s*", "", l).strip() for l in corrected_text_lines_raw]
                            
                            if len(corrected_text_lines) == len(chunk_original_subs):
                                corrected_texts_str = raw_response_text
                                self.log_message(f"  Chunk {i+1}, Attempt {attempt+1}: API 成功返回內容且行數正確。")
                                break
                            else:
                                self.log_message(f"!! 校正 Chunk {i+1}, Attempt {attempt+1} API 成功但行數不符 (收到 {len(corrected_text_lines)} 行 vs 預期 {len(chunk_original_subs)} 行)。", is_warning=True)
                                corrected_texts_str = None
                                last_api_error_for_chunk = Exception(f"行數不符 (收到 {len(corrected_text_lines)} vs 預期 {len(chunk_original_subs)})")
                                if attempt < retries - 1: 
                                    self.log_message(f"  Chunk {i+1}: 行數錯誤，嘗試重試 ({attempt+2}/{retries})。")
                                else: 
                                    self.log_message(f"!! Chunk {i+1}: 第二次嘗試後行數仍錯誤。", is_error=True)
                        else:
                            finish_reason = "未知"
                            try:
                                if response.candidates and response.candidates[0].finish_reason: 
                                    finish_reason = response.candidates[0].finish_reason.name
                            except Exception as e_fr_parse: 
                                self.log_message(f"解析 finish_reason 時出錯: {e_fr_parse}", is_warning=True)
                            
                            err_msg = f"API 未返回內容 (原因: {finish_reason})"
                            self.log_message(f"!! 校正 Chunk {i+1}, Attempt {attempt+1} {err_msg}", is_warning=True)
                            corrected_texts_str = None
                            last_api_error_for_chunk = Exception(err_msg)
                            if finish_reason == 'SAFETY' or attempt == retries - 1: 
                                break
                    except Exception as api_err:
                        self.log_message(f"!! 校正 Chunk {i+1}, Attempt {attempt+1} API 錯誤: {api_err}", is_error=True)
                        last_api_error_for_chunk = api_err
                        corrected_texts_str = None
                        if attempt == retries - 1: 
                            self.log_message(f"!! Chunk {i+1} 校正因 API 錯誤失敗 (所有嘗試用盡)。", is_error=True)
                            break
                        else: 
                            self.log_message(f"  Chunk {i+1}: API 錯誤，嘗試重試 ({attempt+2}/{retries})。")
                
                if corrected_texts_str is None:
                    self.log_message(f"!! Chunk {i+1} 校正失敗或無有效內容 (最終原因: {last_api_error_for_chunk})，將使用原始字幕。", is_warning=True)
                    for sub_idx, sub in enumerate(chunk_original_subs):
                        all_correction_data.append({
                            "index": sub.index, 
                            "start": sub.start, 
                            "end": sub.end, 
                            "original": current_chunk_input_lines[sub_idx], 
                            "corrected": current_chunk_input_lines[sub_idx], 
                            "changed": False, 
                            "ai_failed": True
                        })
                else:
                    corrected_text_lines_raw = corrected_texts_str.strip().split('\n')
                    import re
                    corrected_text_lines = [re.sub(r"^\s*[\d\.\-\*:]+\s*", "", l).strip() for l in corrected_text_lines_raw]
                    self.log_message(f"Chunk {i+1}: 校正成功，處理校正結果 ({len(corrected_text_lines)} 行)。")
                    
                    for idx, sub in enumerate(chunk_original_subs):
                        original_content = current_chunk_input_lines[idx]
                        corrected_content = corrected_text_lines[idx]
                        changed_flag = original_content.strip().replace('\n',' ') != corrected_content.strip()
                        all_correction_data.append({
                            "index": sub.index, 
                            "start": sub.start, 
                            "end": sub.end, 
                            "original": original_content, 
                            "corrected": corrected_content, 
                            "changed": changed_flag, 
                            "ai_failed": False
                        })
            
            self.log_message("所有區塊處理完成，準備顯示預覽視窗...")
            self.root.after(0, self.update_status_label, "準備顯示校正預覽...")
            all_correction_data.sort(key=lambda x: x["index"])
            self.root.after(0, self.show_correction_preview, srt_path, all_correction_data)
            
        except Exception as e:
            err_msg = f"AI 校正過程中發生錯誤: {e}"
            self.log_message(err_msg, is_error=True)
            import traceback
            self.log_message(traceback.format_exc())
            self.root.after(0, self.update_status_label, f"AI 校正錯誤: {e}")
            
            display_err_msg = f"AI 校正過程中發生錯誤:\n{e}"
            if isinstance(e, ValueError) and ("API 金鑰無效" in str(e) or "無法使用 AI 模型" in str(e)): 
                display_err_msg = str(e)
            else: 
                display_err_msg += f"\n\n(詳細資訊請見日誌)"
            
            self.root.after(0, messagebox.showerror, "AI 校正錯誤", display_err_msg)
            self.is_ai_correcting = False
            self.root.after(0, self.update_ai_buttons_state)
            self.log_message("AI 校正流程因錯誤中止。")
    
    def show_correction_preview(self, original_srt_path, correction_data):
        try:
            popup = tk.Toplevel(self.root)
            popup.title("AI 校正預覽、編輯與確認")
            popup.geometry("800x600")
            popup.configure(bg=self.colors.get("background", "#1E1E1E"))
            
            text_frame = ttk.Frame(popup, style='TFrame')
            text_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=(10,0))
            
            preview_text_bg = self.colors.get("input_bg", "#3A3A3A")
            preview_text_fg = "#CCCCCC"
            if self.style is None: 
                preview_text_bg = "SystemWindow"
                preview_text_fg = "SystemWindowText"
            
            import tkinter.scrolledtext as scrolledtext
            preview_text = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, padx=5, pady=5, font=("Arial", 11), 
                                                   bg=preview_text_bg, fg=preview_text_fg, 
                                                   insertbackground=self.colors.get("input_fg", "#00FFFF"))
            preview_text.pack(expand=True, fill=tk.BOTH)
            
            # 定義標籤顏色
            preview_text.tag_config("header", font=("Arial", 11, "bold"), spacing1=8, spacing3=2, 
                                  foreground=self.colors.get("foreground", "#00FFFF"))
            preview_text.tag_config("original", foreground="#888888")
            preview_text.tag_config("corrected_unchanged", foreground="#CCCCCC")
            preview_text.tag_config("corrected_changed", foreground=self.colors.get("accent_green", "#00FF00"), 
                                  font=("Arial", 11, "bold"))
            preview_text.tag_config("corrected_failed_ai", foreground=self.colors.get("fail_red", "red"), 
                                  font=("Arial", 11))
            
            line_count = 0
            changed_count = 0
            for item in correction_data:
                line_count += 1
                start_td = item['start']
                end_td = item['end']
                start_str = f"{int(start_td.total_seconds() // 3600):02}:{int(start_td.total_seconds() % 3600 // 60):02}:{int(start_td.total_seconds() % 60):02},{int(start_td.microseconds / 1000):03}"
                end_str = f"{int(end_td.total_seconds() // 3600):02}:{int(end_td.total_seconds() % 3600 // 60):02}:{int(end_td.total_seconds() % 60):02},{int(end_td.microseconds / 1000):03}"
                
                header = f"--- 字幕 {item['index']} ({start_str} --> {end_str}) ---"
                preview_text.insert(tk.END, header + "\n", "header")
                
                original_display = item['original'].replace('\n', ' ')
                preview_text.insert(tk.END, f"原始: {original_display}\n", "original")
                
                corrected_display = item['corrected']
                start_index_corrected = preview_text.index(tk.INSERT)
                line_content = f"校正: {corrected_display}\n\n"
                preview_text.insert(tk.END, line_content)
                end_index_corrected = preview_text.index(f"{start_index_corrected}+{len(line_content)}c")
                
                tag_name = f"correction_{item['index']}"
                preview_text.tag_add(tag_name, start_index_corrected, end_index_corrected)
                
                visual_tag = ""
                if item.get('ai_failed', False):
                    visual_tag = "corrected_failed_ai"
                elif item['changed']:
                    visual_tag = "corrected_changed"
                else:
                    visual_tag = "corrected_unchanged"
                
                preview_text.tag_add(visual_tag, start_index_corrected, end_index_corrected)
                
                if item['changed']:
                    changed_count += 1
            
            self.log_message(f"顯示 AI 校正預覽與編輯視窗，共 {line_count} 條，{changed_count} 條被 AI 成功修改。")
            
            button_frame = ttk.Frame(popup, style='TFrame')
            button_frame.pack(fill=tk.X, padx=10, pady=10)
            
            info_label = ttk.Label(button_frame, text=f"共 {line_count} 條字幕，{changed_count} 條被 AI 成功修改。(紅色表示 AI 未能處理，顯示原文)", style='TLabel')
            info_label.pack(side=tk.LEFT, padx=5)
            
            cancel_button = ttk.Button(button_frame, text="取消", 
                                     command=lambda p=popup: self._finalize_correction(p, None, None, None), 
                                     style='TButton')
            cancel_button.pack(side=tk.RIGHT, padx=5)
            
            save_button = ttk.Button(button_frame, text="儲存編輯後結果", 
                                   command=lambda p=popup, osp=original_srt_path, cd=correction_data, pt=preview_text: self._finalize_correction(p, osp, cd, pt), 
                                   style='Accent.TButton')
            save_button.pack(side=tk.RIGHT, padx=5)
            
            popup.transient(self.root)
            popup.grab_set()
            self.root.wait_window(popup)
            
        except Exception as popup_err:
            self.log_message(f"!! 顯示 AI 校正預覽/編輯彈窗時出錯: {popup_err}", is_error=True)
            import traceback
            self.log_message(traceback.format_exc())
            messagebox.showerror("彈窗錯誤", f"無法顯示 AI 校正結果預覽/編輯彈窗:\n{popup_err}")
    
    def _finalize_correction(self, popup_window, original_srt_path, correction_data, preview_text_widget):
        try:
            if original_srt_path and correction_data and preview_text_widget:
                self.log_message("使用者點擊儲存，正在讀取編輯後內容並儲存檔案...")
                self.root.after(0, self.update_status_label, "正在讀取編輯內容並儲存 SRT...")
                
                output_dir_to_use = os.path.dirname(original_srt_path)
                os.makedirs(output_dir_to_use, exist_ok=True)
                
                timestamp_str = time.strftime("%Y%m%d_%H%M%S")
                base_name = os.path.splitext(os.path.basename(original_srt_path))[0]
                if base_name.endswith("_segmented"): 
                    base_name = base_name[:-len("_segmented")]
                
                corrected_srt_path = os.path.normpath(os.path.join(output_dir_to_use, f"{base_name}_ai_edited_{timestamp_str}.srt"))
                
                try:
                    import srt
                    final_subs = []
                    parsing_errors = []
                    
                    for item in correction_data:
                        tag_name = f"correction_{item['index']}"
                        tag_ranges = preview_text_widget.tag_ranges(tag_name)
                        
                        if tag_ranges:
                            start_pos, end_pos = tag_ranges
                            edited_line = preview_text_widget.get(start_pos, end_pos).strip()
                            prefix = "校正: "
                            if edited_line.startswith(prefix): 
                                edited_content = edited_line[len(prefix):].strip()
                            else: 
                                edited_content = edited_line
                                self.log_message(f"警告：字幕 {item['index']} 的校正結果格式可能已更改，未找到 '校正: ' 前綴。", is_warning=True)
                            
                            sub = srt.Subtitle(index=item['index'], start=item['start'], end=item['end'], content=edited_content)
                            final_subs.append(sub)
                        else: 
                            parsing_errors.append(item['index'])
                            self.log_message(f"錯誤：無法在預覽視窗中找到字幕 {item['index']} 的校正內容標籤。可能已被刪除。", is_error=True)
                    
                    if parsing_errors:
                        messagebox.showerror("儲存錯誤", f"無法解析預覽視窗中以下字幕索引的編輯內容: {', '.join(map(str, parsing_errors))}\n\n請檢查您是否意外刪除了包含 '校正:' 的整行或標題行。\n\n檔案未儲存。", 
                                           parent=popup_window if popup_window and popup_window.winfo_exists() else self.root)
                        raise Exception("Parsing error prevents saving")
                    
                    final_subs.sort(key=lambda s: s.start)
                    final_subs_reindexed = []
                    for idx, sub in enumerate(final_subs): 
                        final_subs_reindexed.append(srt.Subtitle(index=idx + 1, start=sub.start, end=sub.end, content=sub.content))
                    
                    final_srt_content = srt.compose(final_subs_reindexed)
                    
                    with open(corrected_srt_path, 'w', encoding='utf-8') as f: 
                        f.write(final_srt_content)
                    
                    success_msg = f"AI 校正與編輯完成！已儲存檔案至:\n{corrected_srt_path}"
                    self.log_message(success_msg, is_success=True)
                    self.root.after(0, self.update_status_label, "AI 校正與編輯完成！")
                    self.root.after(100, messagebox.showinfo, "成功", success_msg)
                    self.last_srt_path = corrected_srt_path
                    
                except Exception as write_err:
                    if "Parsing error prevents saving" not in str(write_err):
                        err_msg = f"處理或寫入編輯後 SRT 失敗: {write_err}"
                        self.log_message(err_msg, is_error=True)
                        import traceback
                        self.log_message(traceback.format_exc())
                        self.root.after(0, self.update_status_label, f"AI 校正儲存錯誤")
                        self.root.after(0, messagebox.showerror, "儲存錯誤", err_msg)
                    self.last_srt_path = original_srt_path
                    
            elif original_srt_path is None and correction_data is None and preview_text_widget is None:
                self.log_message("使用者取消儲存.")
                self.root.after(0, self.update_status_label, "操作已取消。")
                
        finally:
            self.is_ai_correcting = False
            self.root.after(0, self.update_ai_buttons_state_tab)
            self.log_message("預覽/編輯與儲存流程結束。")
            
            try:
                if popup_window and popup_window.winfo_exists(): 
                    popup_window.destroy()
            except tk.TclError: 
                pass
    
    def ai_analyze_srt(self):
        self.log_message("請求 AI 分析...")
        if not _GENAI_IMPORTED or not _SRT_IMPORTED: 
            err_msg = f"缺少必要的函式庫: {', '.join(lib for lib in _IMPORT_ERROR_LIBS if lib in ['google-generativeai', 'srt'])}\n請安裝後重啟程式。"
            self.log_message(err_msg, is_error=True)
            messagebox.showerror("AI 分析錯誤", err_msg)
            return
        
        api_key = self.api_key_var.get()
        if not api_key: 
            self.log_message("AI 分析錯誤: 未輸入 API 金鑰", is_warning=True)
            messagebox.showerror("AI 分析錯誤", "請先在設定區輸入您的 Google AI API 金鑰。")
            return
        
        # 優先使用 AI 頁籤的 SRT 檔案，否則使用語音轉錄的檔案
        if hasattr(self, 'ai_srt_file_path') and self.ai_srt_file_path:
            target_srt_path = self.ai_srt_file_path
            log_area_ref = self.ai_log_area
        else:
            target_srt_path = self.external_srt_path if self.external_srt_path else self.last_srt_path
            log_area_ref = self.transcribe_log_area
            
        if not target_srt_path or not os.path.exists(target_srt_path): 
            self.log_message("AI 分析錯誤: 找不到有效的 SRT 檔案", is_warning=True, log_area_ref=log_area_ref)
            messagebox.showerror("AI 分析錯誤", "找不到有效的 SRT 檔案進行分析。\n請先轉錄生成 SRT 或載入 SRT 檔案。")
            return
        
        if self.is_ai_analyzing or self.is_ai_correcting: 
            self.log_message("AI 功能正在執行中，請稍候...", is_warning=True)
            messagebox.showwarning("提示", "AI 功能正在執行中，請稍候...")
            return
        
        self.is_ai_analyzing = True
        self.update_ai_buttons_state_tab()
        self.update_status_label("準備開始 AI 分析...")
        self.log_message(f"開始 AI 分析執行緒，目標檔案: {os.path.basename(target_srt_path)}", log_area_ref=log_area_ref)
        self.root.update_idletasks()
        
        analysis_thread = threading.Thread(target=self._do_ai_analysis_thread, args=(api_key, target_srt_path, log_area_ref), daemon=True)
        analysis_thread.start()
    
    def _do_ai_analysis_thread(self, api_key, srt_path, log_area_ref=None):
        summary = "(未能解析摘要)"
        keywords = "(未能解析關鍵詞)"
        correction_suggestions = "(未能解析修正建議)"
        
        try:
            self.log_message("AI 分析線程: 正在設定 Google AI...")
            self.root.after(0, self.update_status_label, "正在設定 Google AI...")
            
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                model_name = self.ai_model_var.get().strip() or "gemini-2.5-flash"
                self.log_message(f"使用 AI 模型進行分析: {model_name}")
                model = genai.GenerativeModel(model_name)
                safety_settings = [
                    {"category": c, "threshold": "BLOCK_NONE"} 
                    for c in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]
                ]
                generation_config = genai.types.GenerationConfig(temperature=0.5)
            except Exception as config_err:
                if "API key not valid" in str(config_err): 
                    raise ValueError(f"Google AI API 金鑰無效或錯誤。") from config_err
                elif "model not found" in str(config_err).lower() or "permission denied" in str(config_err).lower() or "model_name" in str(config_err).lower(): 
                    raise ValueError(f"無法使用 AI 模型 '{model_name}'。\n請確認名稱正確、API金鑰有效且模型有權限使用。") from config_err
                else: 
                    raise Exception(f"設定 Google AI 失敗: {config_err}") from config_err
            
            self.log_message(f"正在讀取 SRT 進行分析: {os.path.basename(srt_path)}")
            self.root.after(0, self.update_status_label, f"正在讀取 SRT 進行分析...")
            
            try:
                import srt
                with open(srt_path, 'r', encoding='utf-8') as f: 
                    srt_content = f.read()
                subs = list(srt.parse(srt_content))
                if not subs: 
                    raise ValueError("SRT 檔案為空或無法解析。")
                
                full_text = "\n".join([sub.content for sub in subs])
                max_chars_for_analysis = 30000
                if len(full_text) > max_chars_for_analysis: 
                    self.log_message(f"警告：SRT 文本過長 ({len(full_text)} 字元)，將截斷前 {max_chars_for_analysis} 字元進行分析。", is_warning=True)
                    full_text = full_text[:max_chars_for_analysis]
                
                self.log_message(f"讀取到 {len(subs)} 條字幕，使用 {len(full_text)} 字元進行分析。")
            except Exception as parse_err: 
                raise Exception(f"讀取或解析 SRT 失敗: {parse_err}") from parse_err
            
            analysis_prompt = f"""作為一個文本分析助手，請閱讀以下由語音辨識產生的影片字幕文字記錄。

任務：
1.  生成一個簡潔的摘要（約 3-5 句話），總結這段文字的主要內容。
2.  仔細辨識並修正文字中可能存在的語音辨識錯誤，特別注意：
    * 依據上下文判斷詞彙的正確性
    * 確保修正後的詞彙是台灣人常用的表達方式
    * 專有名詞、術語或特定領域詞彙的準確性
3.  提取文字中出現的關鍵詞與專有名詞 (請盡量提取，每行一個)

請嚴格按照以下格式輸出結果，每個區塊標題（摘要、修正建議、關鍵詞/專有名詞）後方必須緊跟一個冒號（：）和一個換行符：

摘要：
[這裡填寫摘要內容]

修正建議：
原文：[原始可能有誤的詞彙或片段]
修正：[修正後的詞彙或片段]
說明：[簡短說明為何需要修正及判斷依據]
(如果有多個修正建議，請重複以上三行格式；如果沒有建議，請輸出 "無")

關鍵詞/專有名詞：
[這裡列出詞彙，每個詞彙一行，如果沒有，請輸出 "無"]

原始文字記錄如下：
---
{full_text}
---
請開始分析並輸出結果："""
            
            self.log_message("正在呼叫 Gemini API 進行分析...")
            self.root.after(0, self.update_status_label, f"正在呼叫 AI 進行分析...")
            
            try:
                response = model.generate_content(analysis_prompt, generation_config=generation_config, safety_settings=safety_settings)
                if hasattr(response, 'text') and response.text:
                    response_text = response.text
                    self.log_message("-" * 20 + " AI 分析原始回應 " + "-" * 20)
                    self.log_message(response_text)
                    self.log_message("-" * 50)
                    
                    import re
                    summary_match = re.search(r"摘要：\s*([\s\S]*?)(?=\n\s*\n?\s*修正建議：|\n\s*\n?\s*關鍵詞/專有名詞：|$)", response_text, re.MULTILINE)
                    summary = summary_match.group(1).strip() if summary_match else "(未能解析摘要)"
                    
                    correction_suggestions_match = re.search(r"修正建議：\s*([\s\S]*?)(?=\n\s*\n?\s*關鍵詞/專有名詞：|$)", response_text, re.MULTILINE)
                    correction_suggestions = correction_suggestions_match.group(1).strip() if correction_suggestions_match else "(未能解析修正建議)"
                    if not correction_suggestions or correction_suggestions.lower() == "無": 
                        correction_suggestions = "(無修正建議)"
                    
                    keywords_match = re.search(r"關鍵詞/專有名詞：\s*([\s\S]*)", response_text, re.MULTILINE | re.IGNORECASE)
                    keywords = keywords_match.group(1).strip() if keywords_match else "(未能解析關鍵詞)"
                    if not keywords or keywords.lower() == "無": 
                        keywords = "(無關鍵詞/專有名詞)"
                    
                    self.log_message(f"解析結果: \n摘要: {summary[:100]}...\n修正建議: {correction_suggestions[:100]}...\n關鍵詞: {keywords[:100]}...")
                else:
                    finish_reason = "未知原因"
                    try:
                        if response.candidates and response.candidates[0].finish_reason: 
                            finish_reason = response.candidates[0].finish_reason.name
                    except Exception as e_fr_parse: 
                        self.log_message(f"解析 finish_reason 時出錯: {e_fr_parse}", is_warning=True)
                    
                    err_msg = f"AI 分析 API 未返回有效內容 (原因: {finish_reason})"
                    self.log_message(f"!! {err_msg}", is_error=True)
                    raise Exception(err_msg)
            except Exception as api_err: 
                raise Exception(f"AI 分析 API 呼叫失敗: {api_err}") from api_err
            
            self.root.after(0, self.show_analysis_popup, summary, correction_suggestions, keywords)
            self.root.after(0, self.update_status_label, "AI 分析完成。")
            self.log_message("AI 分析成功完成。", is_success=True)
            
        except Exception as e:
            err_msg = f"AI 分析過程中發生錯誤: {e}"
            self.log_message(err_msg, is_error=True)
            import traceback
            self.log_message(traceback.format_exc())
            self.root.after(0, self.update_status_label, f"AI 分析錯誤: {e}")
            
            if isinstance(e, ValueError): 
                self.root.after(0, messagebox.showerror, "AI 分析錯誤", f"{e}")
            else: 
                self.root.after(0, messagebox.showerror, "AI 分析錯誤", f"AI 分析過程中發生錯誤:\n{e}\n\n(詳細資訊請見日誌)")
        finally: 
            self.is_ai_analyzing = False
            self.root.after(0, self.update_ai_buttons_state_tab)
            self.log_message("AI 分析流程結束。")
    
    def show_analysis_popup(self, summary, correction_suggestions, keywords):
        try:
            popup = tk.Toplevel(self.root)
            popup.title("AI 分析結果 (摘要、修正建議、關鍵詞)")
            popup.geometry("700x550")
            popup.configure(bg=self.colors.get("background", "#1E1E1E"))
            
            text_area_bg = self.colors.get("input_bg", "#3A3A3A")
            text_area_fg = "#CCCCCC"
            if self.style is None: 
                text_area_bg = "SystemWindow"
                text_area_fg = "SystemWindowText"
            
            import tkinter.scrolledtext as scrolledtext
            text_area = scrolledtext.ScrolledText(popup, wrap=tk.WORD, padx=10, pady=10, font=("Arial", 12), 
                                                bg=text_area_bg, fg=text_area_fg, 
                                                insertbackground=self.colors.get("input_fg", "#00FFFF"))
            text_area.pack(expand=True, fill=tk.BOTH)
            
            text_area.tag_config("h2", font=("Arial", 14, "bold"), spacing1=10, spacing3=5, 
                               foreground=self.colors.get("foreground", "#00FFFF"))
            
            text_area.insert(tk.END, "摘要：\n", ("h2",))
            text_area.insert(tk.END, f"{summary}\n\n")
            text_area.insert(tk.END, "修正建議：\n", ("h2",))
            text_area.insert(tk.END, f"{correction_suggestions}\n\n")
            text_area.insert(tk.END, "關鍵詞/專有名詞：\n", ("h2",))
            text_area.insert(tk.END, f"{keywords}")
            text_area.config(state=tk.NORMAL)
            
            button_frame = ttk.Frame(popup, style='TFrame')
            button_frame.pack(fill=tk.X, pady=(5, 10))
            
            add_kw_button = ttk.Button(button_frame, text="使用編輯後的「修正」詞彙更新提示詞", 
                                     command=lambda ta=text_area, p=popup: self.update_prompt_from_analysis(ta, p), 
                                     style='Optional.TButton')
            add_kw_button.pack(side=tk.LEFT, padx=10, pady=5)
            
            close_button = ttk.Button(button_frame, text="關閉視窗", command=popup.destroy, style='TButton')
            close_button.pack(side=tk.RIGHT, padx=10, pady=5)
            
            popup.transient(self.root)
            popup.grab_set()
            self.root.wait_window(popup)
            
        except Exception as popup_err: 
            self.log_message(f"!! 顯示 AI 分析彈窗時出錯: {popup_err}", is_error=True)
            import traceback
            self.log_message(traceback.format_exc())
            messagebox.showerror("彈窗錯誤", f"無法顯示 AI 分析結果彈窗:\n{popup_err}")
    
    def update_prompt_from_analysis(self, text_area_widget, popup_window):
        try:
            full_content = text_area_widget.get("1.0", tk.END)
            extracted_terms = []
            
            import re
            corrections_section_match = re.search(r"修正建議：\s*([\s\S]*?)(?=\n\s*\n?\s*關鍵詞/專有名詞：|$)", full_content, re.MULTILINE | re.IGNORECASE)
            if corrections_section_match:
                corrections_str = corrections_section_match.group(1).strip()
                found_correction_terms = re.findall(r"^\s*修正：\s*(.*?)\s*$", corrections_str, re.MULTILINE | re.IGNORECASE)
                if found_correction_terms: 
                    extracted_terms.extend(found_correction_terms)
                    self.log_message(f"從「修正建議」區塊提取到 {'、'.join(extracted_terms)} 詞彙。")
            
            if not extracted_terms:
                self.log_message("未在「修正建議」區塊找到 '修正：' 標籤或內容，嘗試從「關鍵詞」區塊提取...", is_warning=True)
                keywords_match = re.search(r"關鍵詞/專有名詞：\s*([\s\S]*)", full_content, re.MULTILINE | re.IGNORECASE)
                if keywords_match:
                    keywords_str = keywords_match.group(1).strip()
                    if keywords_str and keywords_str != "(未能解析關鍵詞)" and keywords_str.lower() != "無" and keywords_str != "(無關鍵詞/專有名詞)":
                        extracted_terms.extend([line.strip() for line in keywords_str.split('\n') if line.strip()])
                        if extracted_terms: 
                            self.log_message(f"從「關鍵詞」區塊提取到 {'、'.join(extracted_terms)} 詞彙。")
                        else:
                            self.log_message("「關鍵詞/專有名詞」區塊無有效內容。", is_warning=True)
                elif not extracted_terms: 
                    self.log_message("在彈窗內容中找不到「關鍵詞/專有名詞：」區塊。", is_warning=True)
                    messagebox.showwarning("無法解析", "在彈窗內容中找不到「修正建議：」或「關鍵詞/專有名詞：」區塊。", parent=popup_window)
                    return
            
            if not extracted_terms: 
                messagebox.showwarning("無法解析", "在彈窗內容中找不到有效的「修正：」標籤，且「關鍵詞/專有名詞」區塊也無內容或標示為'無'。", parent=popup_window)
                return
            
            final_term_list = []
            for term_group in extracted_terms: 
                final_term_list.extend(term_group.split())
            unique_terms = sorted(list(set(t for t in final_term_list if t)))
            formatted_keywords = " ".join(unique_terms)
            
            if not formatted_keywords: 
                messagebox.showinfo("提示", "未能從編輯後的內容提取有效詞彙。", parent=popup_window)
                return
            
            # 獲取目前提示詞內容 (使用 AI 頁籤的提示詞框)
            current_prompt = self.ai_prompt_widget.get('1.0', 'end-1c').strip()
            ai_placeholder_text = "範例：張三 李四 王五 台積電 聯發科 機器學習 深度學習\n\n• 詞彙間用空格分隔\n• 輸入專有名詞、人名、公司名等"
            if current_prompt == ai_placeholder_text:
                current_prompt = ""
            
            new_keywords_list = []
            existing_terms = set(current_prompt.split())
            added_count = 0
            for kw in formatted_keywords.split():
                if kw and kw not in existing_terms: 
                    new_keywords_list.append(kw)
                    existing_terms.add(kw)
                    added_count += 1
            
            if not new_keywords_list: 
                self.log_message("所有提取的詞彙似乎已存在於提示詞中。")
                messagebox.showinfo("提示", "所有提取的詞彙似乎已存在於提示詞中。", parent=popup_window)
                popup_window.destroy()
                return
            
            new_keywords_str = " ".join(new_keywords_list)
            if current_prompt: 
                new_prompt = current_prompt + " " + new_keywords_str
            else: 
                new_prompt = new_keywords_str
            
            # 更新 AI 提示詞 Text 元件
            self.ai_prompt_widget.delete('1.0', tk.END)
            self.ai_prompt_widget.insert('1.0', new_prompt)
            self.ai_prompt_widget.config(foreground='white')
            
            self.log_message(f"已將 {added_count} 個新詞彙附加到提示詞：{new_keywords_str}")
            messagebox.showinfo("提示", f"已將 {added_count} 個新詞彙附加到主介面的提示詞欄位。", parent=popup_window)
            popup_window.destroy()
            
        except Exception as append_err: 
            self.log_message(f"!! 附加提示詞時出錯: {append_err}", is_error=True)
            import traceback
            self.log_message(traceback.format_exc())
            messagebox.showerror("錯誤", f"附加提示詞時出錯:\n{append_err}", parent=popup_window if popup_window and popup_window.winfo_exists() else self.root)
    
    # 歸檔功能
    def browse_folder(self, var):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            var.set(folder_selected)
    
    def start_archiving(self):
        self._save_config()
        if not self.source_folder_var.get() or not self.processed_folder_var.get():
            messagebox.showerror("錯誤", "請先設定待處理和已處理資料夾的路徑。")
            return
        
        messagebox.showinfo("功能提示", "AI 媒體庫歸檔功能已觸發 (此為整合版示意)。")
    
    def stop_archiving(self):
        messagebox.showinfo("功能提示", "停止歸檔功能已觸發。")
    

    
    def ai_translate_srt_placeholder(self):
        """AI翻譯功能 - 參考OkokGo實作"""
        self.log_message("請求 AI 翻譯...")
        if not _GENAI_IMPORTED or not _SRT_IMPORTED: 
            err_msg = f"缺少必要的函式庫: {', '.join(lib for lib in _IMPORT_ERROR_LIBS if lib in ['google-generativeai', 'srt'])}\n請安裝後重啟程式。"
            self.log_message(err_msg, is_error=True)
            messagebox.showerror("AI 翻譯錯誤", err_msg)
            return
        
        api_key = self.api_key_var.get()
        if not api_key: 
            self.log_message("AI 翻譯錯誤: 未輸入 API 金鑰", is_warning=True)
            messagebox.showerror("AI 翻譯錯誤", "請先在設定區輸入您的 Google AI API 金鑰。")
            return
        
        # 優先使用 AI 頁籤的 SRT 檔案，否則使用語音轉錄的檔案
        if hasattr(self, 'ai_srt_file_path') and self.ai_srt_file_path:
            target_srt_path = self.ai_srt_file_path
            log_area_ref = self.ai_log_area
        else:
            target_srt_path = self.external_srt_path if self.external_srt_path else self.last_srt_path
            log_area_ref = self.transcribe_log_area
            
        if not target_srt_path or not os.path.exists(target_srt_path): 
            self.log_message("AI 翻譯錯誤: 找不到有效的 SRT 檔案", is_warning=True, log_area_ref=log_area_ref)
            messagebox.showerror("AI 翻譯錯誤", "找不到有效的 SRT 檔案進行翻譯。\n請先轉錄生成 SRT 或載入 SRT 檔案。")
            return
        
        if self.is_ai_translating or self.is_ai_correcting or self.is_ai_analyzing: 
            self.log_message("AI 功能正在執行中，請稍候...", is_warning=True)
            messagebox.showwarning("提示", "AI 功能正在執行中，請稍候...")
            return
        
        # 直接開始翻譯，使用設定中的語言
        target_language = self.translation_language_var.get().split(' ')[0]  # 取得語言代碼
        
        # 開始翻譯處理流程
        self.is_ai_translating = True
        self.update_ai_buttons_state_tab()
        self.update_status_label("準備開始 AI 翻譯...")
        self.log_message(f"開始 AI 翻譯執行緒，目標檔案: {os.path.basename(target_srt_path)}，目標語言: {target_language}", log_area_ref=log_area_ref)
        self.root.update_idletasks()
        
        translation_thread = threading.Thread(target=self._do_ai_translation_thread, 
                                             args=(api_key, target_srt_path, target_language, log_area_ref), daemon=True)
        translation_thread.start()
    
    def _do_ai_translation_thread(self, api_key, srt_path, target_language, log_area_ref=None):
        """AI翻譯處理線程 - 參考OkokGo實作"""
        original_subs = []
        all_translation_data = []
        
        try:
            if log_area_ref is None:
                log_area_ref = self.ai_log_area
            self.log_message("AI 翻譯線程：正在設定 Google AI...", log_area_ref=log_area_ref)
            self.root.after(0, self.update_status_label, "正在設定 Google AI...")
            
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                model_name = self.ai_model_var.get().strip() or "gemini-2.5-flash"
                self.log_message(f"使用 AI 模型進行翻譯: {model_name}", log_area_ref=log_area_ref)
                model = genai.GenerativeModel(model_name)
                
                # OkokGo 的安全設定
                safety_settings = [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                ]
                generation_config = genai.types.GenerationConfig(temperature=0.3)  # 低溫度確保準確性
            except Exception as config_err:
                if "API key not valid" in str(config_err):
                    self.log_message("AI 翻譯錯誤: API 金鑰無效", is_error=True, log_area_ref=log_area_ref)
                    self.root.after(0, messagebox.showerror, "AI 翻譯錯誤", "API 金鑰無效，請檢查您的 Google AI API 金鑰。")
                else:
                    self.log_message(f"AI 翻譯錯誤: Google AI 設定失敗 - {str(config_err)}", is_error=True, log_area_ref=log_area_ref)
                    self.root.after(0, messagebox.showerror, "AI 翻譯錯誤", f"Google AI 設定失敗：{str(config_err)}")
                return
            
            self.log_message("AI 翻譯線程：正在讀取 SRT 檔案...", log_area_ref=log_area_ref)
            self.root.after(0, self.update_status_label, "正在讀取 SRT 檔案...")
            
            try:
                import srt
                with open(srt_path, 'r', encoding='utf-8') as f:
                    srt_content = f.read()
                original_subs = list(srt.parse(srt_content))
                self.log_message(f"成功讀取 {len(original_subs)} 條字幕", log_area_ref=log_area_ref)
            except Exception as read_err:
                self.log_message(f"AI 翻譯錯誤: 讀取 SRT 檔案失敗 - {str(read_err)}", is_error=True, log_area_ref=log_area_ref)
                self.root.after(0, messagebox.showerror, "AI 翻譯錯誤", f"讀取 SRT 檔案失敗：{str(read_err)}")
                return
            
            if not original_subs:
                self.log_message("AI 翻譯錯誤: SRT 檔案為空或格式錯誤", is_warning=True, log_area_ref=log_area_ref)
                self.root.after(0, messagebox.showwarning, "AI 翻譯警告", "SRT 檔案為空或格式錯誤")
                return
            
            # 分批處理 - 使用設定中的批次大小
            try:
                chunk_size = int(self.batch_size_var.get().strip())
                if chunk_size <= 0:
                    chunk_size = 15
            except (ValueError, AttributeError):
                chunk_size = 15
            chunks = [original_subs[i:i + chunk_size] for i in range(0, len(original_subs), chunk_size)]
            total_chunks = len(chunks)
            
            self.log_message(f"開始分批翻譯：共 {total_chunks} 批，每批 {chunk_size} 條字幕", log_area_ref=log_area_ref)
            
            # 處理每個批次
            for chunk_index, chunk in enumerate(chunks):
                current_progress = int((chunk_index / total_chunks) * 100)
                self.root.after(0, self.update_status_label, f"AI 翻譯中 ({current_progress}%)... Chunk {chunk_index + 1}/{total_chunks}")
                self.log_message(f"處理批次 {chunk_index + 1}/{total_chunks} ({len(chunk)} 條字幕)", log_area_ref=log_area_ref)
                
                # 提取純文字內容
                chunk_texts = [sub.content for sub in chunk]
                chunk_text = '\n'.join(chunk_texts)
                
                # OkokGo 風格的翻譯提示詞
                prompt = f"""你是一位專業的字幕翻譯專家。請將以下繁體中文字幕翻譯成 {target_language}。

翻譯要求：
1. 保持原文的語調和情感
2. 確保翻譯自然流暢，符合目標語言的表達習慣
3. 保持專有名詞的一致性
4. 如果遇到文化特定的概念，請選擇最適合的對等表達

重要規則：
1. 輸出：僅輸出翻譯後的文字，不要包含任何原始文字、標籤、索引編號或解釋
2. 行數：輸出的總行數必須與輸入的文字行數完全相同
3. 對應：輸出的每一行文字，都必須是對應順序的原始文字行的翻譯結果
4. 格式：每行一個翻譯結果，不要添加額外的格式或標記

原始字幕文字：
{chunk_text}"""
                
                # 重試機制 - 重用已鎖定功能的成功模式
                max_retries = 2
                translated_texts = None
                
                for retry in range(max_retries + 1):
                    try:
                        if retry > 0:
                            self.log_message(f"批次 {chunk_index + 1} 重試第 {retry} 次", log_area_ref=log_area_ref)
                        
                        response = model.generate_content(prompt, safety_settings=safety_settings, generation_config=generation_config)
                        translated_text = response.text.strip()
                        
                        if translated_text:
                            translated_texts = translated_text.split('\n')
                            
                            # 驗證行數是否匹配
                            if len(translated_texts) == len(chunk_texts):
                                break
                            else:
                                self.log_message(f"批次 {chunk_index + 1} 行數不匹配：原始 {len(chunk_texts)} 行，翻譯後 {len(translated_texts)} 行", is_warning=True, log_area_ref=log_area_ref)
                                if retry == max_retries:
                                    # 最後一次重試失敗，使用原始文字
                                    translated_texts = chunk_texts
                                    self.log_message(f"批次 {chunk_index + 1} 翻譯失敗，保持原始內容", is_warning=True, log_area_ref=log_area_ref)
                        else:
                            if retry == max_retries:
                                translated_texts = chunk_texts
                                self.log_message(f"批次 {chunk_index + 1} AI 回應為空，保持原始內容", is_warning=True, log_area_ref=log_area_ref)
                    
                    except Exception as ai_err:
                        self.log_message(f"批次 {chunk_index + 1} AI 處理錯誤 (重試 {retry}): {str(ai_err)}", is_warning=True, log_area_ref=log_area_ref)
                        if retry == max_retries:
                            translated_texts = chunk_texts
                            self.log_message(f"批次 {chunk_index + 1} 最終失敗，保持原始內容", is_warning=True, log_area_ref=log_area_ref)
                
                # 記錄翻譯結果
                for i, (original_sub, translated_text) in enumerate(zip(chunk, translated_texts)):
                    translation_data = {
                        'index': chunk_index * chunk_size + i,
                        'start': str(original_sub.start),
                        'end': str(original_sub.end),
                        'original': original_sub.content,
                        'translated': translated_text,
                        'changed': original_sub.content != translated_text,
                        'ai_failed_chunk': translated_texts == chunk_texts and translated_text != original_sub.content
                    }
                    all_translation_data.append(translation_data)
            
            # 完成處理
            self.root.after(0, self.update_status_label, "正在生成翻譯結果...")
            
            # 統計結果
            total_subs = len(all_translation_data)
            translated_count = sum(1 for item in all_translation_data if item['changed'])
            failed_count = sum(1 for item in all_translation_data if item['ai_failed_chunk'])
            
            self.log_message(f"翻譯統計：總共 {total_subs} 條，翻譯 {translated_count} 條，失敗 {failed_count} 條", log_area_ref=log_area_ref)
            
            # 生成翻譯後的 SRT 內容
            translated_subs = []
            for i, (original_sub, translation_data) in enumerate(zip(original_subs, all_translation_data)):
                translated_sub = srt.Subtitle(
                    index=original_sub.index,
                    start=original_sub.start,
                    end=original_sub.end,
                    content=translation_data['translated']
                )
                translated_subs.append(translated_sub)
            
            # 儲存翻譯後的檔案 - 使用時間戳命名
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = os.path.splitext(os.path.basename(srt_path))[0]
            translated_path = os.path.join(os.path.dirname(srt_path), f"{base_name}_translated_{target_language}_{timestamp}.srt")
            
            translated_content = srt.compose(translated_subs)
            with open(translated_path, 'w', encoding='utf-8') as f:
                f.write(translated_content)
            
            self.log_message(f"AI 翻譯完成！翻譯後檔案已儲存至: {translated_path}", log_area_ref=log_area_ref)
            
            # 顯示預覽視窗
            self.root.after(0, self._show_translation_preview, all_translation_data, translated_path, target_language)
                
        except Exception as e:
            self.log_message(f"AI 翻譯執行緒發生未預期錯誤: {str(e)}", is_error=True, log_area_ref=log_area_ref)
            self.root.after(0, messagebox.showerror, "AI 翻譯錯誤", f"發生未預期錯誤：{str(e)}")
        finally:
            self.is_ai_translating = False
            self.root.after(0, self.update_ai_buttons_state_tab)
            self.root.after(0, self.update_status_label, "就緒")
    
    def _show_translation_preview(self, translation_data, translated_path, target_language):
        """顯示翻譯預覽視窗 - 參考校正預覽的成功模式"""
        try:
            popup = tk.Toplevel(self.root)
            popup.title(f"AI 翻譯預覽 - {target_language}")
            popup.geometry("900x700")
            popup.configure(bg=self.colors.get("background", "#1E1E1E"))
            
            # 主框架
            main_frame = ttk.Frame(popup, style='TFrame')
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # 標題和統計
            title_frame = ttk.Frame(main_frame, style='TFrame')
            title_frame.pack(fill=tk.X, pady=(0, 10))
            
            total_count = len(translation_data)
            translated_count = sum(1 for item in translation_data if item['changed'])
            failed_count = sum(1 for item in translation_data if item['ai_failed_chunk'])
            
            title_label = ttk.Label(title_frame, 
                                  text=f"翻譯結果預覽 - 目標語言: {target_language}", 
                                  style='TLabel', font=("Arial", 14, "bold"))
            title_label.pack(side=tk.LEFT)
            
            stats_label = ttk.Label(title_frame, 
                                  text=f"總計: {total_count} 條 | 已翻譯: {translated_count} 條 | 失敗: {failed_count} 條", 
                                  style='TLabel')
            stats_label.pack(side=tk.RIGHT)
            
            # 預覽文字區域
            text_frame = ttk.Frame(main_frame, style='TFrame')
            text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            
            import tkinter.scrolledtext as scrolledtext
            preview_text = scrolledtext.ScrolledText(
                text_frame, 
                wrap=tk.WORD, 
                font=("Consolas", 10),
                bg=self.colors.get("input_bg", "#3A3A3A"),
                fg="#CCCCCC",
                insertbackground=self.colors.get("input_fg", "#00FFFF"),
                selectbackground="#4A4A4A"
            )
            preview_text.pack(fill=tk.BOTH, expand=True)
            
            # 配置標籤顏色
            preview_text.tag_config("original", foreground="#AAAAAA", font=("Consolas", 9))
            preview_text.tag_config("translated", foreground="#00FF00", font=("Consolas", 10, "bold"))
            preview_text.tag_config("failed", foreground="#FF6666", font=("Consolas", 10))
            preview_text.tag_config("unchanged", foreground="#FFFF99", font=("Consolas", 10))
            preview_text.tag_config("separator", foreground="#666666")
            
            # 填充預覽內容
            for i, item in enumerate(translation_data):
                # 時間軸
                preview_text.insert(tk.END, f"{i+1:3d}  {item['start']} --> {item['end']}\n", ("separator",))
                
                # 原始文字
                preview_text.insert(tk.END, f"原文: {item['original']}\n", ("original",))
                
                # 翻譯文字
                if item['ai_failed_chunk']:
                    preview_text.insert(tk.END, f"翻譯: {item['translated']} [翻譯失敗]\n", ("failed",))
                elif item['changed']:
                    preview_text.insert(tk.END, f"翻譯: {item['translated']}\n", ("translated",))
                else:
                    preview_text.insert(tk.END, f"翻譯: {item['translated']} [未變更]\n", ("unchanged",))
                
                preview_text.insert(tk.END, "\n", ("separator",))
            
            preview_text.config(state=tk.DISABLED)
            
            # 按鈕框架
            button_frame = ttk.Frame(main_frame, style='TFrame')
            button_frame.pack(fill=tk.X, pady=(10, 0))
            
            # 說明標籤
            info_label = ttk.Label(button_frame, 
                                 text="綠色=已翻譯 | 黃色=未變更 | 紅色=翻譯失敗", 
                                 style='TLabel', font=("Arial", 9))
            info_label.pack(side=tk.LEFT)
            
            # 按鈕
            def open_file_location():
                import subprocess
                import platform
                try:
                    if platform.system() == "Darwin":  # macOS
                        subprocess.run(["open", "-R", translated_path])
                    elif platform.system() == "Windows":
                        subprocess.run(["explorer", "/select,", translated_path])
                    else:  # Linux
                        subprocess.run(["xdg-open", os.path.dirname(translated_path)])
                except Exception as e:
                    messagebox.showerror("錯誤", f"無法開啟檔案位置：{str(e)}")
            
            ttk.Button(button_frame, text="開啟檔案位置", command=open_file_location, style='TButton').pack(side=tk.RIGHT, padx=(10, 0))
            ttk.Button(button_frame, text="關閉", command=popup.destroy, style='TButton').pack(side=tk.RIGHT)
            
            # 顯示完成訊息
            self.log_message(f"翻譯預覽視窗已開啟，共 {total_count} 條字幕，{translated_count} 條已翻譯")
            
            popup.transient(self.root)
            popup.grab_set()
            
        except Exception as preview_err:
            self.log_message(f"顯示翻譯預覽視窗時出錯: {preview_err}", is_error=True)
            import traceback
            self.log_message(traceback.format_exc())
            messagebox.showerror("預覽錯誤", f"無法顯示翻譯預覽視窗：{str(preview_err)}")
    
    def ai_generate_news_report(self):
        """AI新聞報導生成功能 - 參考OkokGo實作"""
        self.log_message("請求 AI 新聞報導生成...")
        if not _GENAI_IMPORTED or not _SRT_IMPORTED: 
            err_msg = f"缺少必要的函式庫: {', '.join(lib for lib in _IMPORT_ERROR_LIBS if lib in ['google-generativeai', 'srt'])}\n請安裝後重啟程式。"
            self.log_message(err_msg, is_error=True)
            messagebox.showerror("AI 新聞報導錯誤", err_msg)
            return
        
        api_key = self.api_key_var.get()
        if not api_key: 
            self.log_message("AI 新聞報導錯誤: 未輸入 API 金鑰", is_warning=True)
            messagebox.showerror("AI 新聞報導錯誤", "請先在設定區輸入您的 Google AI API 金鑰。")
            return
        
        # 優先使用 AI 頁籤的 SRT 檔案，否則使用語音轉錄的檔案
        if hasattr(self, 'ai_srt_file_path') and self.ai_srt_file_path:
            target_srt_path = self.ai_srt_file_path
            log_area_ref = self.ai_log_area
        else:
            target_srt_path = self.external_srt_path if self.external_srt_path else self.last_srt_path
            log_area_ref = self.transcribe_log_area
            
        if not target_srt_path or not os.path.exists(target_srt_path): 
            self.log_message("AI 新聞報導錯誤: 找不到有效的 SRT 檔案", is_warning=True, log_area_ref=log_area_ref)
            messagebox.showerror("AI 新聞報導錯誤", "找不到有效的 SRT 檔案進行新聞報導生成。\n請先轉錄生成 SRT 或載入 SRT 檔案。")
            return
        
        if self.is_ai_generating_news or self.is_ai_correcting or self.is_ai_analyzing or self.is_ai_translating: 
            self.log_message("AI 功能正在執行中，請稍候...", is_warning=True)
            messagebox.showwarning("提示", "AI 功能正在執行中，請稍候...")
            return
        
        # 開始新聞報導生成處理流程
        self.is_ai_generating_news = True
        self.update_ai_buttons_state_tab()
        self.update_status_label("準備開始 AI 新聞報導生成...")
        self.log_message(f"開始 AI 新聞報導生成執行緒，目標檔案: {os.path.basename(target_srt_path)}", log_area_ref=log_area_ref)
        self.root.update_idletasks()
        
        news_thread = threading.Thread(target=self._do_ai_news_generation_thread, 
                                       args=(api_key, target_srt_path, log_area_ref), daemon=True)
        news_thread.start()
    
    def _do_ai_news_generation_thread(self, api_key, srt_path, log_area_ref=None):
        """AI新聞報導生成處理線程 - 參考OkokGo實作"""
        try:
            if log_area_ref is None:
                log_area_ref = self.ai_log_area
            self.log_message("AI 新聞報導線程：正在設定 Google AI...", log_area_ref=log_area_ref)
            self.root.after(0, self.update_status_label, "正在設定 Google AI...")
            
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                model_name = self.ai_model_var.get().strip() or "gemini-2.5-flash"
                self.log_message(f"使用 AI 模型進行新聞報導生成: {model_name}", log_area_ref=log_area_ref)
                model = genai.GenerativeModel(model_name)
                
                # OkokGo 的安全設定
                safety_settings = [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                ]
                generation_config = genai.types.GenerationConfig(temperature=0.7)  # 較高創意性
            except Exception as config_err:
                if "API key not valid" in str(config_err):
                    self.log_message("AI 新聞報導錯誤: API 金鑰無效", is_error=True, log_area_ref=log_area_ref)
                    self.root.after(0, messagebox.showerror, "AI 新聞報導錯誤", "API 金鑰無效，請檢查您的 Google AI API 金鑰。")
                else:
                    self.log_message(f"AI 新聞報導錯誤: Google AI 設定失敗 - {str(config_err)}", is_error=True, log_area_ref=log_area_ref)
                    self.root.after(0, messagebox.showerror, "AI 新聞報導錯誤", f"Google AI 設定失敗：{str(config_err)}")
                return
            
            self.log_message("AI 新聞報導線程：正在讀取 SRT 檔案...", log_area_ref=log_area_ref)
            self.root.after(0, self.update_status_label, "正在讀取 SRT 檔案...")
            
            try:
                import srt
                with open(srt_path, 'r', encoding='utf-8') as f:
                    srt_content = f.read()
                subs = list(srt.parse(srt_content))
                if not subs:
                    raise ValueError("SRT 檔案為空或無法解析。")
                
                # 提取純文字內容
                full_text = "\n".join([sub.content for sub in subs])
                self.log_message(f"成功讀取 {len(subs)} 條字幕，共 {len(full_text)} 字元", log_area_ref=log_area_ref)
            except Exception as read_err:
                self.log_message(f"AI 新聞報導錯誤: 讀取 SRT 檔案失敗 - {str(read_err)}", is_error=True, log_area_ref=log_area_ref)
                self.root.after(0, messagebox.showerror, "AI 新聞報導錯誤", f"讀取 SRT 檔案失敗：{str(read_err)}")
                return
            
            # OkokGo 風格的新聞報導生成提示詞
            prompt = f"""你是一位專業的新聞記者和編輯。請根據以下字幕記錄內容，撰寫一篇專業的新聞報導。

要求：
1. 風格：繁體中文、正式、客觀、專業
2. 結構：包含新聞標題和完整的新聞內容
3. 內容：基於提供的記錄，不可捏造原始記錄中未提及的事實
4. 語調：保持新聞報導的客觀性和專業性

請嚴格按照以下格式輸出：

標題：
[這裡填寫新聞標題]

內容：
[這裡填寫完整的新聞報導內容]

原始字幕記錄：
---
{full_text}
---

請開始撰寫新聞報導："""
            
            self.log_message("正在呼叫 AI 進行新聞報導生成...", log_area_ref=log_area_ref)
            self.root.after(0, self.update_status_label, "正在生成新聞報導...")
            
            try:
                response = model.generate_content(prompt, safety_settings=safety_settings, generation_config=generation_config)
                
                if hasattr(response, 'text') and response.text:
                    response_text = response.text.strip()
                    self.log_message("AI 新聞報導生成成功", log_area_ref=log_area_ref)
                    
                    # 解析標題和內容
                    import re
                    title_match = re.search(r"標題：\s*(.*?)(?=\n\s*內容：|\n\s*$)", response_text, re.DOTALL)
                    content_match = re.search(r"內容：\s*(.*)", response_text, re.DOTALL)
                    
                    title = title_match.group(1).strip() if title_match else "未能解析標題"
                    content = content_match.group(1).strip() if content_match else response_text
                    
                    # 儲存新聞報導
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    base_name = os.path.splitext(os.path.basename(srt_path))[0]
                    news_path = os.path.join(os.path.dirname(srt_path), f"{base_name}_news_report_{timestamp}.txt")
                    
                    news_content = f"標題：{title}\n\n內容：\n{content}"
                    with open(news_path, 'w', encoding='utf-8') as f:
                        f.write(news_content)
                    
                    self.log_message(f"新聞報導已儲存至: {news_path}", log_area_ref=log_area_ref)
                    
                    # 顯示預覽視窗
                    self.root.after(0, self._show_news_report_preview, title, content, news_path)
                    
                else:
                    finish_reason = "未知原因"
                    try:
                        if response.candidates and response.candidates[0].finish_reason: 
                            finish_reason = response.candidates[0].finish_reason.name
                    except Exception:
                        pass
                    
                    err_msg = f"AI 新聞報導生成 API 未返回有效內容 (原因: {finish_reason})"
                    self.log_message(err_msg, is_error=True, log_area_ref=log_area_ref)
                    self.root.after(0, messagebox.showerror, "AI 新聞報導錯誤", err_msg)
                    
            except Exception as ai_err:
                self.log_message(f"AI 新聞報導生成失敗: {str(ai_err)}", is_error=True, log_area_ref=log_area_ref)
                self.root.after(0, messagebox.showerror, "AI 新聞報導錯誤", f"新聞報導生成失敗：{str(ai_err)}")
                
        except Exception as e:
            self.log_message(f"AI 新聞報導執行緒發生未預期錯誤: {str(e)}", is_error=True, log_area_ref=log_area_ref)
            self.root.after(0, messagebox.showerror, "AI 新聞報導錯誤", f"發生未預期錯誤：{str(e)}")
        finally:
            self.is_ai_generating_news = False
            self.root.after(0, self.update_ai_buttons_state_tab)
            self.root.after(0, self.update_status_label, "就緒")
    
    def _show_news_report_preview(self, title, content, news_path):
        """顯示新聞報導預覽視窗"""
        try:
            popup = tk.Toplevel(self.root)
            popup.title("AI 新聞報導預覽")
            popup.geometry("800x600")
            popup.configure(bg=self.colors.get("background", "#1E1E1E"))
            
            # 主框架
            main_frame = ttk.Frame(popup, style='TFrame')
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # 標題框架
            title_frame = ttk.Frame(main_frame, style='TFrame')
            title_frame.pack(fill=tk.X, pady=(0, 10))
            
            title_label = ttk.Label(title_frame, text="新聞報導生成結果", 
                                  style='TLabel', font=("Arial", 14, "bold"))
            title_label.pack(side=tk.LEFT)
            
            # 新聞標題顯示
            news_title_frame = ttk.LabelFrame(main_frame, text="新聞標題", style='TLabelframe')
            news_title_frame.pack(fill=tk.X, pady=(0, 10))
            
            title_text = tk.Text(news_title_frame, height=2, wrap=tk.WORD, font=("Arial", 12, "bold"),
                                bg=self.colors.get("input_bg", "#3A3A3A"), fg="#00FFFF",
                                insertbackground=self.colors.get("input_fg", "#00FFFF"))
            title_text.pack(fill=tk.X, padx=5, pady=5)
            title_text.insert('1.0', title)
            title_text.config(state=tk.NORMAL)
            
            # 新聞內容顯示
            content_frame = ttk.LabelFrame(main_frame, text="新聞內容", style='TLabelframe')
            content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            
            import tkinter.scrolledtext as scrolledtext
            content_text = scrolledtext.ScrolledText(
                content_frame, 
                wrap=tk.WORD, 
                font=("Arial", 11),
                bg=self.colors.get("input_bg", "#3A3A3A"),
                fg="#CCCCCC",
                insertbackground=self.colors.get("input_fg", "#00FFFF"),
                selectbackground="#4A4A4A"
            )
            content_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            content_text.insert('1.0', content)
            content_text.config(state=tk.NORMAL)
            
            # 按鈕框架
            button_frame = ttk.Frame(main_frame, style='TFrame')
            button_frame.pack(fill=tk.X, pady=(10, 0))
            
            # 說明標籤
            info_label = ttk.Label(button_frame, 
                                 text="您可以編輯上方內容，點擊「儲存修改」保存變更", 
                                 style='TLabel', font=("Arial", 9))
            info_label.pack(side=tk.LEFT)
            
            # 按鈕
            def save_changes():
                try:
                    new_title = title_text.get('1.0', 'end-1c').strip()
                    new_content = content_text.get('1.0', 'end-1c').strip()
                    
                    updated_news_content = f"標題：{new_title}\n\n內容：\n{new_content}"
                    with open(news_path, 'w', encoding='utf-8') as f:
                        f.write(updated_news_content)
                    
                    messagebox.showinfo("儲存成功", f"新聞報導已更新並儲存至：\n{news_path}")
                    self.log_message(f"新聞報導已更新儲存: {news_path}")
                except Exception as e:
                    messagebox.showerror("儲存錯誤", f"儲存失敗：{str(e)}")
            
            def open_file_location():
                import subprocess
                import platform
                try:
                    if platform.system() == "Darwin":  # macOS
                        subprocess.run(["open", "-R", news_path])
                    elif platform.system() == "Windows":
                        subprocess.run(["explorer", "/select,", news_path])
                    else:  # Linux
                        subprocess.run(["xdg-open", os.path.dirname(news_path)])
                except Exception as e:
                    messagebox.showerror("錯誤", f"無法開啟檔案位置：{str(e)}")
            
            ttk.Button(button_frame, text="開啟檔案位置", command=open_file_location, style='TButton').pack(side=tk.RIGHT, padx=(10, 0))
            ttk.Button(button_frame, text="儲存修改", command=save_changes, style='TButton').pack(side=tk.RIGHT, padx=(10, 0))
            ttk.Button(button_frame, text="關閉", command=popup.destroy, style='TButton').pack(side=tk.RIGHT)
            
            # 顯示完成訊息
            self.log_message(f"新聞報導預覽視窗已開啟")
            
            popup.transient(self.root)
            popup.grab_set()
            
        except Exception as preview_err:
            self.log_message(f"顯示新聞報導預覽視窗時出錯: {preview_err}", is_error=True)
            import traceback
            self.log_message(traceback.format_exc())
            messagebox.showerror("預覽錯誤", f"無法顯示新聞報導預覽視窗：{str(preview_err)}")
    
    def ai_generate_social_media(self):
        """AI社群媒體建議功能 - 參考OkokGo實作"""
        self.log_message("請求 AI 社群媒體建議生成...")
        if not _GENAI_IMPORTED or not _SRT_IMPORTED: 
            err_msg = f"缺少必要的函式庫: {', '.join(lib for lib in _IMPORT_ERROR_LIBS if lib in ['google-generativeai', 'srt'])}\n請安裝後重啟程式。"
            self.log_message(err_msg, is_error=True)
            messagebox.showerror("AI 社群媒體錯誤", err_msg)
            return
        
        api_key = self.api_key_var.get()
        if not api_key: 
            self.log_message("AI 社群媒體錯誤: 未輸入 API 金鑰", is_warning=True)
            messagebox.showerror("AI 社群媒體錯誤", "請先在設定區輸入您的 Google AI API 金鑰。")
            return
        
        # 優先使用 AI 頁籤的 SRT 檔案，否則使用語音轉錄的檔案
        if hasattr(self, 'ai_srt_file_path') and self.ai_srt_file_path:
            target_srt_path = self.ai_srt_file_path
            log_area_ref = self.ai_log_area
        else:
            target_srt_path = self.external_srt_path if self.external_srt_path else self.last_srt_path
            log_area_ref = self.transcribe_log_area
            
        if not target_srt_path or not os.path.exists(target_srt_path): 
            self.log_message("AI 社群媒體錯誤: 找不到有效的 SRT 檔案", is_warning=True, log_area_ref=log_area_ref)
            messagebox.showerror("AI 社群媒體錯誤", "找不到有效的 SRT 檔案進行社群媒體建議生成。\n請先轉錄生成 SRT 或載入 SRT 檔案。")
            return
        
        if self.is_ai_generating_social or self.is_ai_correcting or self.is_ai_analyzing or self.is_ai_translating or self.is_ai_generating_news: 
            self.log_message("AI 功能正在執行中，請稍候...", is_warning=True)
            messagebox.showwarning("提示", "AI 功能正在執行中，請稍候...")
            return
        
        # 開始社群媒體建議生成處理流程
        self.is_ai_generating_social = True
        self.update_ai_buttons_state_tab()
        self.update_status_label("準備開始 AI 社群媒體建議生成...")
        self.log_message(f"開始 AI 社群媒體建議生成執行緒，目標檔案: {os.path.basename(target_srt_path)}", log_area_ref=log_area_ref)
        self.root.update_idletasks()
        
        social_thread = threading.Thread(target=self._do_ai_social_media_thread, 
                                        args=(api_key, target_srt_path, log_area_ref), daemon=True)
        social_thread.start()
    
    def _do_ai_social_media_thread(self, api_key, srt_path, log_area_ref=None):
        """AI社群媒體建議生成處理線程 - 參考OkokGo實作"""
        try:
            if log_area_ref is None:
                log_area_ref = self.ai_log_area
            self.log_message("AI 社群媒體線程：正在設定 Google AI...", log_area_ref=log_area_ref)
            self.root.after(0, self.update_status_label, "正在設定 Google AI...")
            
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                model_name = self.ai_model_var.get().strip() or "gemini-2.5-flash"
                self.log_message(f"使用 AI 模型進行社群媒體建議生成: {model_name}", log_area_ref=log_area_ref)
                model = genai.GenerativeModel(model_name)
                
                # OkokGo 的安全設定
                safety_settings = [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                ]
                generation_config = genai.types.GenerationConfig(temperature=0.8)  # 高創意性
            except Exception as config_err:
                if "API key not valid" in str(config_err):
                    self.log_message("AI 社群媒體錯誤: API 金鑰無效", is_error=True, log_area_ref=log_area_ref)
                    self.root.after(0, messagebox.showerror, "AI 社群媒體錯誤", "API 金鑰無效，請檢查您的 Google AI API 金鑰。")
                else:
                    self.log_message(f"AI 社群媒體錯誤: Google AI 設定失敗 - {str(config_err)}", is_error=True, log_area_ref=log_area_ref)
                    self.root.after(0, messagebox.showerror, "AI 社群媒體錯誤", f"Google AI 設定失敗：{str(config_err)}")
                return
            
            self.log_message("AI 社群媒體線程：正在讀取 SRT 檔案...", log_area_ref=log_area_ref)
            self.root.after(0, self.update_status_label, "正在讀取 SRT 檔案...")
            
            try:
                import srt
                with open(srt_path, 'r', encoding='utf-8') as f:
                    srt_content = f.read()
                subs = list(srt.parse(srt_content))
                if not subs:
                    raise ValueError("SRT 檔案為空或無法解析。")
                
                # 提取純文字內容
                full_text = "\n".join([sub.content for sub in subs])
                self.log_message(f"成功讀取 {len(subs)} 條字幕，共 {len(full_text)} 字元", log_area_ref=log_area_ref)
            except Exception as read_err:
                self.log_message(f"AI 社群媒體錯誤: 讀取 SRT 檔案失敗 - {str(read_err)}", is_error=True, log_area_ref=log_area_ref)
                self.root.after(0, messagebox.showerror, "AI 社群媒體錯誤", f"讀取 SRT 檔案失敗：{str(read_err)}")
                return
            
            # 改進版：一次調用，JSON結構化輸出，參考OkokGo的高品質方法
            self.log_message("正在生成社群媒體建議...", log_area_ref=log_area_ref)
            self.root.after(0, self.update_status_label, "正在生成社群媒體建議...")
            
            # 改進版：一次調用，JSON結構化輸出，高品質提示詞 - 參考OkokGo專業方法
            prompt = f"""你是一位資深跨平台社群媒體策略專家，擁有豐富的內容行銷和數位行銷經驗。請基於以下內容，為不同社群媒體平台制定專業且具有商業價值的策略建議。

**重要指示：請嚴格按照以下JSON格式回應，不要添加任何額外的文字或說明：**

{{
  "youtube": {{
    "title": "創建一個吸引人且SEO友善的YouTube影片標題（50-60字元，包含主要關鍵字）",
    "description": "撰寫詳細的影片描述，包含：1)內容摘要 2)關鍵時間戳 3)相關關鍵字 4)觀眾互動提示 5)訂閱呼籲",
    "tags": "提供15-20個相關標籤，涵蓋主題關鍵字、長尾關鍵字、趨勢標籤，用逗號分隔"
  }},
  "podcast": {{
    "title": "設計引人入勝的Podcast節目標題（突出核心價值和聽眾收穫）",
    "description": "撰寫節目描述，強調：1)核心議題 2)專家觀點 3)實用價值 4)目標聽眾",
    "highlights": "列出3-5個節目重點摘要，每個重點都要具體且有價值，幫助聽眾快速了解收聽價值"
  }},
  "seo_keywords": "提供12-15個高價值SEO關鍵字，包含：主要關鍵字、長尾關鍵字、相關詞彙、趨勢詞彙，用逗號分隔",
  "thumbnail_suggestions": "提供具體的封面設計建議，包含：1)視覺元素建議 2)色彩搭配方案 3)文字配置策略 4)情感表達方式 5)品牌一致性考量",
  "overall_analysis": "提供專業的市場分析，包含：1)目標受眾特徵分析 2)內容潛力評估 3)跨平台推廣策略 4)具體行銷建議 5)預期效果評估 6)競爭優勢分析"
}}

**內容分析基礎：**
{full_text}

**專業要求：**
1. 所有建議必須具有實用性和可執行性
2. 重點關注商業價值和影響力提升
3. 考慮台灣市場特色和用戶習慣
4. 提供具體、可量化的建議
5. 確保跨平台內容的一致性和協同效應

請基於你的專業知識和市場洞察，為每個平台提供高品質、具有商業價值的建議。"""
            
            try:
                response = model.generate_content(prompt, safety_settings=safety_settings, generation_config=generation_config)
                
                if hasattr(response, 'text') and response.text:
                    response_text = response.text.strip()
                    self.log_message("AI 社群媒體建議生成成功，正在解析JSON...", log_area_ref=log_area_ref)
                    
                    # 改進版JSON解析：主要解析 + 備用解析，確保可靠性
                    import json
                    import re
                    
                    try:
                        # 主要解析方法：嘗試直接解析JSON
                        # 清理回應文字，移除可能的markdown標記
                        clean_response = response_text.replace('```json', '').replace('```', '').strip()
                        
                        # 尋找JSON物件
                        json_match = re.search(r'\{.*\}', clean_response, re.DOTALL)
                        if json_match:
                            json_str = json_match.group(0)
                            social_json = json.loads(json_str)
                            
                            # 安全提取各部分內容，提供預設值
                            youtube_data = social_json.get('youtube', {})
                            youtube_content = f"""【YouTube 建議】

標題：
{youtube_data.get('title', '未能生成YouTube標題')}

描述：
{youtube_data.get('description', '未能生成YouTube描述')}

標籤：
{youtube_data.get('tags', '未能生成YouTube標籤')}"""
                            
                            podcast_data = social_json.get('podcast', {})
                            podcast_content = f"""【Podcast 建議】

標題：
{podcast_data.get('title', '未能生成Podcast標題')}

描述：
{podcast_data.get('description', '未能生成Podcast描述')}

重點摘要：
{podcast_data.get('highlights', '未能生成Podcast重點摘要')}"""
                            
                            seo_keywords = f"""【SEO 關鍵字】

{social_json.get('seo_keywords', '未能生成SEO關鍵字')}"""
                            
                            thumbnail_suggestions = f"""【封面設計建議】

{social_json.get('thumbnail_suggestions', '未能生成封面建議')}"""
                            
                            overall_analysis = f"""【整體市場分析】

{social_json.get('overall_analysis', '未能生成整體分析')}"""
                            
                            self.log_message("JSON解析成功", log_area_ref=log_area_ref)
                            
                        else:
                            raise ValueError("未找到有效的JSON格式")
                            
                    except (json.JSONDecodeError, ValueError) as json_err:
                        self.log_message(f"JSON解析失敗，使用備用解析方法: {str(json_err)}", is_warning=True, log_area_ref=log_area_ref)
                        
                        # 備用解析方法：基於關鍵字的智能內容分割
                        lines = response_text.split('\n')
                        current_section = None
                        sections = {
                            'youtube': [],
                            'podcast': [],
                            'seo': [],
                            'thumbnail': [],
                            'analysis': []
                        }
                        
                        for line in lines:
                            line = line.strip()
                            if not line or line.startswith(('```', '{', '}', '"')):
                                continue
                            
                            # 智能識別區塊
                            line_lower = line.lower()
                            if any(keyword in line_lower for keyword in ['youtube', '影片', 'video', '標題']):
                                current_section = 'youtube'
                                continue
                            elif any(keyword in line_lower for keyword in ['podcast', '節目', '播客', 'audio']):
                                current_section = 'podcast'
                                continue
                            elif any(keyword in line_lower for keyword in ['seo', '關鍵字', 'keyword', '搜尋']):
                                current_section = 'seo'
                                continue
                            elif any(keyword in line_lower for keyword in ['封面', '縮圖', 'thumbnail', '設計']):
                                current_section = 'thumbnail'
                                continue
                            elif any(keyword in line_lower for keyword in ['分析', '策略', 'analysis', '市場']):
                                current_section = 'analysis'
                                continue
                            elif current_section:
                                sections[current_section].append(line)
                        
                        # 格式化備用解析結果
                        youtube_content = f"""【YouTube 建議】

{chr(10).join(sections['youtube']) if sections['youtube'] else "備用解析：YouTube建議生成失敗"}"""
                        
                        podcast_content = f"""【Podcast 建議】

{chr(10).join(sections['podcast']) if sections['podcast'] else "備用解析：Podcast建議生成失敗"}"""
                        
                        seo_keywords = f"""【SEO 關鍵字】

{chr(10).join(sections['seo']) if sections['seo'] else "備用解析：SEO關鍵字生成失敗"}"""
                        
                        thumbnail_suggestions = f"""【封面設計建議】

{chr(10).join(sections['thumbnail']) if sections['thumbnail'] else "備用解析：封面建議生成失敗"}"""
                        
                        overall_analysis = f"""【整體市場分析】

{chr(10).join(sections['analysis']) if sections['analysis'] else "備用解析：整體分析生成失敗"}"""
                
                else:
                    # 如果AI沒有回應，提供預設內容
                    youtube_content = "AI未能生成YouTube建議"
                    podcast_content = "AI未能生成Podcast建議"
                    seo_keywords = "AI未能生成SEO關鍵字"
                    thumbnail_suggestions = "AI未能生成封面建議"
                    overall_analysis = "AI未能生成整體分析"
                    
            except Exception as ai_err:
                self.log_message(f"AI 社群媒體建議生成失敗: {str(ai_err)}", is_error=True, log_area_ref=log_area_ref)
                # 提供錯誤回饋
                error_msg = f"生成失敗：{str(ai_err)}"
                youtube_content = error_msg
                podcast_content = error_msg
                seo_keywords = error_msg
                thumbnail_suggestions = error_msg
                overall_analysis = error_msg
            
            # 儲存社群媒體建議
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = os.path.splitext(os.path.basename(srt_path))[0]
            social_path = os.path.join(os.path.dirname(srt_path), f"{base_name}_social_media_{timestamp}.txt")
            
            social_content = f"""社群媒體建議報告

YouTube建議：
{youtube_content}

Podcast建議：
{podcast_content}

SEO關鍵字：
{seo_keywords}

封面建議：
{thumbnail_suggestions}

整體分析：
{overall_analysis}"""
            
            with open(social_path, 'w', encoding='utf-8') as f:
                f.write(social_content)
            
            self.log_message(f"社群媒體建議已儲存至: {social_path}", log_area_ref=log_area_ref)
            
            # 顯示預覽視窗
            social_data = {
                'youtube': youtube_content,
                'podcast': podcast_content,
                'seo_keywords': seo_keywords,
                'thumbnail': thumbnail_suggestions,
                'analysis': overall_analysis
            }
            self.root.after(0, self._show_social_media_preview, social_data, social_path)
                
        except Exception as e:
            self.log_message(f"AI 社群媒體執行緒發生未預期錯誤: {str(e)}", is_error=True, log_area_ref=log_area_ref)
            self.root.after(0, messagebox.showerror, "AI 社群媒體錯誤", f"發生未預期錯誤：{str(e)}")
        finally:
            self.is_ai_generating_social = False
            self.root.after(0, self.update_ai_buttons_state_tab)
            self.root.after(0, self.update_status_label, "就緒")
    
    def _show_social_media_preview(self, social_data, social_path):
        """顯示社群媒體建議預覽視窗"""
        try:
            popup = tk.Toplevel(self.root)
            popup.title("AI 社群媒體建議預覽")
            popup.geometry("900x700")
            popup.configure(bg=self.colors.get("background", "#1E1E1E"))
            
            # 主框架
            main_frame = ttk.Frame(popup, style='TFrame')
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # 標題框架
            title_frame = ttk.Frame(main_frame, style='TFrame')
            title_frame.pack(fill=tk.X, pady=(0, 10))
            
            title_label = ttk.Label(title_frame, text="社群媒體建議生成結果", 
                                  style='TLabel', font=("Arial", 14, "bold"))
            title_label.pack(side=tk.LEFT)
            
            # 創建筆記本頁籤
            notebook = ttk.Notebook(main_frame, style='TNotebook')
            notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            
            # YouTube頁籤
            youtube_frame = ttk.Frame(notebook, style='TFrame')
            notebook.add(youtube_frame, text="YouTube")
            
            youtube_text = tk.Text(youtube_frame, wrap=tk.WORD, font=("Arial", 11),
                                  bg=self.colors.get("input_bg", "#3A3A3A"), fg="#CCCCCC",
                                  insertbackground=self.colors.get("input_fg", "#00FFFF"))
            youtube_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            youtube_text.insert('1.0', social_data['youtube'])
            
            # Podcast頁籤
            podcast_frame = ttk.Frame(notebook, style='TFrame')
            notebook.add(podcast_frame, text="Podcast")
            
            podcast_text = tk.Text(podcast_frame, wrap=tk.WORD, font=("Arial", 11),
                                  bg=self.colors.get("input_bg", "#3A3A3A"), fg="#CCCCCC",
                                  insertbackground=self.colors.get("input_fg", "#00FFFF"))
            podcast_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            podcast_text.insert('1.0', social_data['podcast'])
            
            # SEO關鍵字頁籤
            seo_frame = ttk.Frame(notebook, style='TFrame')
            notebook.add(seo_frame, text="SEO關鍵字")
            
            seo_text = tk.Text(seo_frame, wrap=tk.WORD, font=("Arial", 11),
                              bg=self.colors.get("input_bg", "#3A3A3A"), fg="#00FF00",
                              insertbackground=self.colors.get("input_fg", "#00FFFF"))
            seo_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            seo_text.insert('1.0', social_data['seo_keywords'])
            
            # 封面建議頁籤
            thumbnail_frame = ttk.Frame(notebook, style='TFrame')
            notebook.add(thumbnail_frame, text="封面建議")
            
            thumbnail_text = tk.Text(thumbnail_frame, wrap=tk.WORD, font=("Arial", 11),
                                    bg=self.colors.get("input_bg", "#3A3A3A"), fg="#CCCCCC",
                                    insertbackground=self.colors.get("input_fg", "#00FFFF"))
            thumbnail_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            thumbnail_text.insert('1.0', social_data['thumbnail'])
            
            # 整體分析頁籤
            analysis_frame = ttk.Frame(notebook, style='TFrame')
            notebook.add(analysis_frame, text="整體分析")
            
            analysis_text = tk.Text(analysis_frame, wrap=tk.WORD, font=("Arial", 11),
                                   bg=self.colors.get("input_bg", "#3A3A3A"), fg="#CCCCCC",
                                   insertbackground=self.colors.get("input_fg", "#00FFFF"))
            analysis_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            analysis_text.insert('1.0', social_data['analysis'])
            
            # 按鈕框架
            button_frame = ttk.Frame(main_frame, style='TFrame')
            button_frame.pack(fill=tk.X, pady=(10, 0))
            
            # 說明標籤
            info_label = ttk.Label(button_frame, 
                                 text="您可以編輯各頁籤內容，點擊「儲存修改」保存變更", 
                                 style='TLabel', font=("Arial", 9))
            info_label.pack(side=tk.LEFT)
            
            # 按鈕
            def save_changes():
                try:
                    updated_content = f"""社群媒體建議報告

YouTube建議：
{youtube_text.get('1.0', 'end-1c').strip()}

Podcast建議：
{podcast_text.get('1.0', 'end-1c').strip()}

SEO關鍵字：
{seo_text.get('1.0', 'end-1c').strip()}

封面建議：
{thumbnail_text.get('1.0', 'end-1c').strip()}

整體分析：
{analysis_text.get('1.0', 'end-1c').strip()}"""
                    
                    with open(social_path, 'w', encoding='utf-8') as f:
                        f.write(updated_content)
                    
                    messagebox.showinfo("儲存成功", f"社群媒體建議已更新並儲存至：\n{social_path}")
                    self.log_message(f"社群媒體建議已更新儲存: {social_path}")
                except Exception as e:
                    messagebox.showerror("儲存錯誤", f"儲存失敗：{str(e)}")
            
            def open_file_location():
                import subprocess
                import platform
                try:
                    if platform.system() == "Darwin":  # macOS
                        subprocess.run(["open", "-R", social_path])
                    elif platform.system() == "Windows":
                        subprocess.run(["explorer", "/select,", social_path])
                    else:  # Linux
                        subprocess.run(["xdg-open", os.path.dirname(social_path)])
                except Exception as e:
                    messagebox.showerror("錯誤", f"無法開啟檔案位置：{str(e)}")
            
            ttk.Button(button_frame, text="開啟檔案位置", command=open_file_location, style='TButton').pack(side=tk.RIGHT, padx=(10, 0))
            ttk.Button(button_frame, text="儲存修改", command=save_changes, style='TButton').pack(side=tk.RIGHT, padx=(10, 0))
            ttk.Button(button_frame, text="關閉", command=popup.destroy, style='TButton').pack(side=tk.RIGHT)
            
            # 顯示完成訊息
            self.log_message(f"社群媒體建議預覽視窗已開啟")
            
            popup.transient(self.root)
            popup.grab_set()
            
        except Exception as preview_err:
            self.log_message(f"顯示社群媒體建議預覽視窗時出錯: {preview_err}", is_error=True)
            import traceback
            self.log_message(traceback.format_exc())
            messagebox.showerror("預覽錯誤", f"無法顯示社群媒體建議預覽視窗：{str(preview_err)}")
    
    # 搜尋功能
    def load_search_data(self):
        try:
            # 檢查是否設定了處理資料夾
            processed_folder = self.processed_folder_var.get()
            if not processed_folder:
                self.search_status_label.config(text="✗ 請先在『AI媒體庫歸檔』標籤頁設定已處理資料夾路徑")
                return
            
            # 更新搜尋管理器的配置
            self.search_manager.config.processed_folder = processed_folder
            
            # 重新載入資料
            self.search_manager.reload_data()
            
            # 檢查載入的資料數量
            if hasattr(self.search_manager, 'media_data') and self.search_manager.media_data:
                count = len(self.search_manager.media_data)
                self.search_status_label.config(text=f"✅ 已成功載入 {count} 筆媒體資料")
            else:
                self.search_status_label.config(text="⚠️ 資料載入完成，但未找到媒體資料")
                
        except Exception as e:
            self.search_status_label.config(text=f"✗ 載入資料時發生錯誤: {e}")
    
    def perform_search(self):
        query = self.search_query_var.get().strip()
        if not query:
            messagebox.showwarning("警告", "請輸入搜尋關鍵字")
            return
        
        try:
            # 確保配置已更新
            processed_folder = self.processed_folder_var.get()
            if not processed_folder:
                self.search_status_label.config(text="✗ 請先載入搜尋資料")
                return
            
            self.search_manager.config.processed_folder = processed_folder
            results = self.search_manager.search(query)
            self.display_search_results(results)
            
            count = len(results.results) if hasattr(results, 'results') else 0
            self.search_status_label.config(text=f"找到 {count} 筆與「{query}」相關的資料。")
        except Exception as e:
            self.search_status_label.config(text=f"✗ 搜尋時發生錯誤: {e}")
    
    def perform_nl_search(self):
        query = self.search_query_var.get().strip()
        if not query:
            messagebox.showwarning("警告", "請輸入搜尋查詢")
            return
        
        try:
            # 確保配置已更新
            processed_folder = self.processed_folder_var.get()
            if not processed_folder:
                self.search_status_label.config(text="✗ 請先載入搜尋資料")
                return
            
            self.search_manager.config.processed_folder = processed_folder
            
            # 解析自然語言查詢
            criteria = self.nl_search.parse_query(query)
            
            # 將解析的條件轉換為搜尋字串
            search_terms = []
            if criteria.keywords:
                search_terms.extend(criteria.keywords)
            if criteria.emotions:
                search_terms.extend(criteria.emotions)
            if criteria.file_types:
                search_terms.extend(criteria.file_types)
            if criteria.categories:
                search_terms.extend(criteria.categories)
            
            # 如果沒有解析出任何條件，使用原始查詢
            if not search_terms:
                search_terms = [query]
            
            # 執行搜尋
            search_query = " ".join(search_terms)
            results = self.search_manager.search(search_query)
            self.display_search_results(results)
            
            count = len(results.results) if hasattr(results, 'results') else 0
            self.search_status_label.config(text=f"自然語言搜尋完成，找到 {count} 筆結果。")
            
        except Exception as e:
            self.search_status_label.config(text=f"✗ 自然語言搜尋時發生錯誤: {e}")
    
    def display_search_results(self, results):
        """顯示搜尋結果到樹狀檢視"""
        # 清除現有結果
        for item in self.search_tree.get_children():
            self.search_tree.delete(item)
        
        if hasattr(results, 'results') and results.results:
            for result in results.results:
                # 根據檔案類型選擇圖示
                file_type = result.file_type if hasattr(result, 'file_type') else '未知'
                if "圖片" in str(file_type):
                    icon = "🖼️"
                elif "影片" in str(file_type):
                    icon = "🎬"
                elif "音訊" in str(file_type):
                    icon = "🎵"
                else:
                    icon = "📄"
                
                # 插入結果到樹狀檢視
                self.search_tree.insert("", tk.END,
                                       text=icon,
                                       values=(
                                           result.file_id if hasattr(result, 'file_id') else '未知ID',
                                           result.title if hasattr(result, 'title') else '未知標題',
                                           file_type,
                                           result.file_path if hasattr(result, 'file_path') else '未知路徑'
                                       ))
        
        # 更新搜尋結果資料供詳細資訊顯示使用
        self.search_results_data = results.results if hasattr(results, 'results') else []

    def on_search_result_select(self, event):
        """處理搜尋結果選擇事件"""
        selected_items = self.search_tree.selection()
        if not selected_items:
            return
            
        try:
            # 獲取選中項目的索引
            selected_index = self.search_tree.index(selected_items[0])
            
            # 檢查是否有搜尋結果資料
            if not hasattr(self, 'search_results_data') or not self.search_results_data:
                self.details_text.config(state=tk.NORMAL)
                self.details_text.delete('1.0', tk.END)
                self.details_text.insert('1.0', "沒有可用的詳細資訊")
                self.details_text.config(state=tk.DISABLED)
                return
            
            # 檢查索引是否有效
            if selected_index >= len(self.search_results_data):
                return
                
            # 獲取選中的搜尋結果
            result = self.search_results_data[selected_index]
            
            # 構建詳細資訊文字
            info_lines = []
            info_lines.append(f"標題: {result.title}")
            info_lines.append(f"ID: {result.file_id}")
            info_lines.append(f"檔案類型: {result.file_type}")
            info_lines.append(f"檔案路徑: {result.file_path}")
            info_lines.append(f"相關性分數: {result.relevance_score:.2f}")
            info_lines.append(f"匹配欄位: {', '.join(result.matched_fields)}")
            info_lines.append("--------------------")
            
            # 顯示元數據
            if result.metadata:
                info_lines.append("詳細資訊:")
                for key, value in result.metadata.items():
                    if key and value:
                        info_lines.append(f"{key}: {value}")
            
            info_text = "\
n".join(info_lines)
            
            # 更新詳細資訊文字區域
            self.details_text.config(state=tk.NORMAL)
            self.details_text.delete('1.0', tk.END)
            self.details_text.insert('1.0', info_text)
            self.details_text.config(state=tk.DISABLED)
            
            # 如果是圖片檔案，嘗試顯示縮圖
            if result.file_type == "圖片" and result.file_path:
                self.display_image_thumbnail(result.file_path)
            else:
                # 清除圖片顯示
                self.details_image_label.config(image=None, text="")
                
        except Exception as e:
            # 發生錯誤時顯示錯誤資訊
            self.details_text.config(state=tk.NORMAL)
            self.details_text.delete('1.0', tk.END)
            self.details_text.insert('1.0', f"顯示詳細資訊時發生錯誤: {e}")
            self.details_text.config(state=tk.DISABLED)

    def display_image_thumbnail(self, image_path):
        """顯示圖片縮圖"""
        try:
            if not _PIL_IMPORTED:
                self.details_image_label.config(image=None, text="無法顯示圖片 (PIL未安裝)")
                return
                
            # 檢查檔案是否存在
            if not os.path.exists(image_path):
                self.details_image_label.config(image=None, text="圖片檔案不存在")
                return
            
            # 載入並調整圖片大小
            img = Image.open(image_path)
            img.thumbnail((250, 250))
            photo = ImageTk.PhotoImage(img)
            
            # 顯示圖片
            self.details_image_label.config(image=photo, text="")
            self.details_image_label.image = photo  # 保持引用避免被垃圾回收
            
        except Exception as e:
            self.details_image_label.config(image=None, text=f"無法顯示圖片: {e}")

    def create_monitoring_tab(self):
        """建立監控標籤頁"""
        # 主框架
        main_frame = ttk.Frame(self.monitoring_tab)
        main_frame.pack(fill='both', expand=True)
        
        # 左側控制面板
        control_frame = ttk.LabelFrame(main_frame, text="監控控制", padding=10)
        control_frame.pack(side='left', fill='y', padx=(0, 10))
        
        # 監控開關
        self.monitoring_enabled_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(control_frame, text="啟用即時監控", 
                       variable=self.monitoring_enabled_var,
                       command=self.toggle_monitoring).pack(anchor='w', pady=2)
        
        # 更新間隔設定
        ttk.Label(control_frame, text="更新間隔 (秒):").pack(anchor='w', pady=(10, 0))
        self.monitoring_interval_var = tk.StringVar(value="5")
        interval_spinbox = ttk.Spinbox(control_frame, from_=1, to=60, 
                                      textvariable=self.monitoring_interval_var,
                                      width=10)
        interval_spinbox.pack(anchor='w', pady=2)
        
        # 分隔線
        ttk.Separator(control_frame, orient='horizontal').pack(fill='x', pady=10)
        
        # 資料夾監控設定
        ttk.Label(control_frame, text="資料夾監控", style='Subtitle.TLabel').pack(anchor='w')
        
        self.folder_monitoring_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(control_frame, text="啟用資料夾監控", 
                       variable=self.folder_monitoring_var,
                       command=self.toggle_folder_monitoring).pack(anchor='w', pady=2)
        
        ttk.Button(control_frame, text="設定監控資料夾", 
                  command=self.configure_monitoring_folders).pack(fill='x', pady=2)
        
        # 分隔線
        ttk.Separator(control_frame, orient='horizontal').pack(fill='x', pady=10)
        
        # 效能最佳化
        ttk.Label(control_frame, text="效能最佳化", style='Subtitle.TLabel').pack(anchor='w')
        
        ttk.Button(control_frame, text="記憶體清理", 
                  command=self.cleanup_memory).pack(fill='x', pady=2)
        
        ttk.Button(control_frame, text="效能報告", 
                  command=self.generate_performance_report).pack(fill='x', pady=2)
        
        # 右側監控顯示區域
        display_frame = ttk.Frame(main_frame)
        display_frame.pack(side='right', fill='both', expand=True)
        
        # 建立監控顯示的筆記本
        self.monitoring_notebook = ttk.Notebook(display_frame)
        self.monitoring_notebook.pack(fill='both', expand=True)
        
        # 系統資源標籤頁
        self.resource_frame = ttk.Frame(self.monitoring_notebook, padding=10)
        self.monitoring_notebook.add(self.resource_frame, text="系統資源")
        
        # 資料夾監控標籤頁
        self.folder_monitor_frame = ttk.Frame(self.monitoring_notebook, padding=10)
        self.monitoring_notebook.add(self.folder_monitor_frame, text="資料夾監控")
        
        # 效能歷史標籤頁
        self.performance_frame = ttk.Frame(self.monitoring_notebook, padding=10)
        self.monitoring_notebook.add(self.performance_frame, text="效能歷史")
        
        # 建立系統資源監控介面
        self.create_resource_monitoring_ui()
        
        # 建立資料夾監控介面
        self.create_folder_monitoring_ui()
        
        # 建立效能歷史介面
        self.create_performance_history_ui()
        
        # 初始化監控變數
        self.monitoring_thread = None
        self.monitoring_running = False
    
    def create_resource_monitoring_ui(self):
        """建立系統資源監控介面"""
        # CPU 使用率
        cpu_frame = ttk.LabelFrame(self.resource_frame, text="CPU 使用率", padding=5)
        cpu_frame.pack(fill='x', pady=5)
        
        self.cpu_var = tk.StringVar(value="0.0%")
        ttk.Label(cpu_frame, textvariable=self.cpu_var, style='Large.TLabel').pack(side='left')
        
        self.cpu_progress = ttk.Progressbar(cpu_frame, length=200, mode='determinate')
        self.cpu_progress.pack(side='right', padx=(10, 0))
        
        # 記憶體使用率
        memory_frame = ttk.LabelFrame(self.resource_frame, text="記憶體使用率", padding=5)
        memory_frame.pack(fill='x', pady=5)
        
        self.memory_var = tk.StringVar(value="0.0%")
        ttk.Label(memory_frame, textvariable=self.memory_var, style='Large.TLabel').pack(side='left')
        
        self.memory_progress = ttk.Progressbar(memory_frame, length=200, mode='determinate')
        self.memory_progress.pack(side='right', padx=(10, 0))
        
        # 磁碟使用率
        disk_frame = ttk.LabelFrame(self.resource_frame, text="磁碟使用率", padding=5)
        disk_frame.pack(fill='x', pady=5)
        
        self.disk_var = tk.StringVar(value="0.0%")
        ttk.Label(disk_frame, textvariable=self.disk_var, style='Large.TLabel').pack(side='left')
        
        self.disk_progress = ttk.Progressbar(disk_frame, length=200, mode='determinate')
        self.disk_progress.pack(side='right', padx=(10, 0))
        
        # 系統資訊
        info_frame = ttk.LabelFrame(self.resource_frame, text="系統資訊", padding=5)
        info_frame.pack(fill='both', expand=True, pady=5)
        
        self.system_info_text = scrolledtext.ScrolledText(info_frame, height=8, font=self.fonts['console'])
        self.system_info_text.pack(fill='both', expand=True)
        
        # 初始化系統資訊
        self.update_system_info()
    
    def create_folder_monitoring_ui(self):
        """建立資料夾監控介面"""
        # 監控狀態
        status_frame = ttk.LabelFrame(self.folder_monitor_frame, text="監控狀態", padding=5)
        status_frame.pack(fill='x', pady=5)
        
        self.folder_monitor_status_var = tk.StringVar(value="未啟用")
        ttk.Label(status_frame, text="狀態:").pack(side='left')
        ttk.Label(status_frame, textvariable=self.folder_monitor_status_var, 
                 style='Bold.TLabel').pack(side='left', padx=(5, 0))
        
        # 監控的資料夾清單
        folders_frame = ttk.LabelFrame(self.folder_monitor_frame, text="監控資料夾", padding=5)
        folders_frame.pack(fill='x', pady=5)
        
        # 建立樹狀檢視來顯示監控的資料夾
        self.folder_tree = ttk.Treeview(folders_frame, columns=('path', 'status'), show='tree headings', height=6)
        self.folder_tree.heading('#0', text='資料夾名稱')
        self.folder_tree.heading('path', text='路徑')
        self.folder_tree.heading('status', text='狀態')
        
        self.folder_tree.column('#0', width=150)
        self.folder_tree.column('path', width=300)
        self.folder_tree.column('status', width=100)
        
        folder_scrollbar = ttk.Scrollbar(folders_frame, orient='vertical', command=self.folder_tree.yview)
        self.folder_tree.configure(yscrollcommand=folder_scrollbar.set)
        
        self.folder_tree.pack(side='left', fill='both', expand=True)
        folder_scrollbar.pack(side='right', fill='y')
        
        # 監控活動日誌
        activity_frame = ttk.LabelFrame(self.folder_monitor_frame, text="監控活動", padding=5)
        activity_frame.pack(fill='both', expand=True, pady=5)
        
        self.folder_activity_text = scrolledtext.ScrolledText(activity_frame, height=8, font=self.fonts['console'])
        self.folder_activity_text.pack(fill='both', expand=True)
    
    def create_performance_history_ui(self):
        """建立效能歷史介面"""
        # 效能統計
        stats_frame = ttk.LabelFrame(self.performance_frame, text="效能統計", padding=5)
        stats_frame.pack(fill='x', pady=5)
        
        # 統計資訊顯示
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill='x')
        
        # 平均值
        ttk.Label(stats_grid, text="平均 CPU:").grid(row=0, column=0, sticky='w', padx=5)
        self.avg_cpu_var = tk.StringVar(value="0.0%")
        ttk.Label(stats_grid, textvariable=self.avg_cpu_var).grid(row=0, column=1, sticky='w', padx=5)
        
        ttk.Label(stats_grid, text="平均記憶體:").grid(row=0, column=2, sticky='w', padx=5)
        self.avg_memory_var = tk.StringVar(value="0.0%")
        ttk.Label(stats_grid, textvariable=self.avg_memory_var).grid(row=0, column=3, sticky='w', padx=5)
        
        # 峰值
        ttk.Label(stats_grid, text="峰值 CPU:").grid(row=1, column=0, sticky='w', padx=5)
        self.peak_cpu_var = tk.StringVar(value="0.0%")
        ttk.Label(stats_grid, textvariable=self.peak_cpu_var).grid(row=1, column=1, sticky='w', padx=5)
        
        ttk.Label(stats_grid, text="峰值記憶體:").grid(row=1, column=2, sticky='w', padx=5)
        self.peak_memory_var = tk.StringVar(value="0.0%")
        ttk.Label(stats_grid, textvariable=self.peak_memory_var).grid(row=1, column=3, sticky='w', padx=5)
        
        # 效能歷史記錄
        history_frame = ttk.LabelFrame(self.performance_frame, text="效能歷史記錄", padding=5)
        history_frame.pack(fill='both', expand=True, pady=5)
        
        # 建立樹狀檢視來顯示效能歷史
        self.performance_tree = ttk.Treeview(history_frame, 
                                           columns=('time', 'cpu', 'memory', 'disk'), 
                                           show='headings', height=10)
        
        self.performance_tree.heading('time', text='時間')
        self.performance_tree.heading('cpu', text='CPU (%)')
        self.performance_tree.heading('memory', text='記憶體 (%)')
        self.performance_tree.heading('disk', text='磁碟 (%)')
        
        self.performance_tree.column('time', width=150)
        self.performance_tree.column('cpu', width=80)
        self.performance_tree.column('memory', width=80)
        self.performance_tree.column('disk', width=80)
        
        perf_scrollbar = ttk.Scrollbar(history_frame, orient='vertical', command=self.performance_tree.yview)
        self.performance_tree.configure(yscrollcommand=perf_scrollbar.set)
        
        self.performance_tree.pack(side='left', fill='both', expand=True)
        perf_scrollbar.pack(side='right', fill='y')
        
        # 初始化效能歷史變數
        self.performance_history = []
        self.max_history_size = 100
    
    def toggle_monitoring(self):
        """切換監控狀態"""
        if self.monitoring_enabled_var.get():
            self.start_monitoring()
        else:
            self.stop_monitoring()
    
    def start_monitoring(self):
        """開始監控"""
        if self.monitoring_running:
            return
        
        self.monitoring_running = True
        
        def monitoring_loop():
            while self.monitoring_running:
                try:
                    self.update_resource_monitoring()
                    interval = int(self.monitoring_interval_var.get())
                    time.sleep(interval)
                except Exception as e:
                    logging_service.error(f"監控更新錯誤: {e}")
                    time.sleep(5)  # 錯誤時等待5秒再重試
        
        self.monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        logging_service.info("系統監控已啟動")
    
    def stop_monitoring(self):
        """停止監控"""
        self.monitoring_running = False
        if self.monitoring_thread:
            self.monitoring_thread = None
        
        logging_service.info("系統監控已停止")
    
    def update_resource_monitoring(self):
        """更新資源監控資料"""
        try:
            import psutil
            
            # 取得系統資源資訊
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/' if os.name != 'nt' else 'C:')
            
            # 在主線程中更新 GUI
            self.root.after(0, lambda: self._update_resource_display(cpu_percent, memory.percent, 
                                                                    (disk.used / disk.total) * 100))
            
            # 記錄效能歷史
            timestamp = time.strftime('%H:%M:%S')
            self.performance_history.append({
                'time': timestamp,
                'cpu': cpu_percent,
                'memory': memory.percent,
                'disk': (disk.used / disk.total) * 100
            })
            
            # 限制歷史記錄大小
            if len(self.performance_history) > self.max_history_size:
                self.performance_history = self.performance_history[-self.max_history_size:]
            
            # 更新效能歷史顯示
            self.root.after(0, self._update_performance_history)
            
        except Exception as e:
            logging_service.error(f"更新資源監控失敗: {e}")
    
    def _update_resource_display(self, cpu_percent, memory_percent, disk_percent):
        """更新資源顯示"""
        self.cpu_var.set(f"{cpu_percent:.1f}%")
        self.cpu_progress['value'] = cpu_percent
        
        self.memory_var.set(f"{memory_percent:.1f}%")
        self.memory_progress['value'] = memory_percent
        
        self.disk_var.set(f"{disk_percent:.1f}%")
        self.disk_progress['value'] = disk_percent
    
    def _update_performance_history(self):
        """更新效能歷史顯示"""
        # 清除現有項目
        for item in self.performance_tree.get_children():
            self.performance_tree.delete(item)
        
        # 添加最近的記錄
        recent_history = self.performance_history[-20:]  # 顯示最近20筆記錄
        for record in recent_history:
            self.performance_tree.insert('', 'end', values=(
                record['time'],
                f"{record['cpu']:.1f}",
                f"{record['memory']:.1f}",
                f"{record['disk']:.1f}"
            ))
        
        # 更新統計資訊
        if self.performance_history:
            cpu_values = [r['cpu'] for r in self.performance_history]
            memory_values = [r['memory'] for r in self.performance_history]
            
            avg_cpu = sum(cpu_values) / len(cpu_values)
            avg_memory = sum(memory_values) / len(memory_values)
            peak_cpu = max(cpu_values)
            peak_memory = max(memory_values)
            
            self.avg_cpu_var.set(f"{avg_cpu:.1f}%")
            self.avg_memory_var.set(f"{avg_memory:.1f}%")
            self.peak_cpu_var.set(f"{peak_cpu:.1f}%")
            self.peak_memory_var.set(f"{peak_memory:.1f}%")
    
    def update_system_info(self):
        """更新系統資訊"""
        try:
            system_info = platform_adapter.get_system_info()
            
            info_text = "系統資訊:\n"
            info_text += f"作業系統: {system_info.get('system', 'Unknown')} {system_info.get('release', '')}\n"
            info_text += f"處理器: {system_info.get('processor', 'Unknown')}\n"
            info_text += f"Python 版本: {system_info.get('python_version', 'Unknown')}\n"
            info_text += f"平台: {system_info.get('platform', 'Unknown')}\n"
            info_text += f"機器類型: {system_info.get('machine', 'Unknown')}\n"
            info_text += f"基礎路徑: {system_info.get('base_path', 'Unknown')}\n"
            
            # 添加記憶體資訊
            try:
                import psutil
                memory = psutil.virtual_memory()
                info_text += f"\n記憶體資訊:\n"
                info_text += f"總記憶體: {memory.total // (1024**3)} GB\n"
                info_text += f"可用記憶體: {memory.available // (1024**3)} GB\n"
                info_text += f"已使用: {memory.used // (1024**3)} GB\n"
                
                # CPU 資訊
                info_text += f"\nCPU 資訊:\n"
                info_text += f"CPU 核心數: {psutil.cpu_count(logical=False)}\n"
                info_text += f"邏輯處理器: {psutil.cpu_count(logical=True)}\n"
                
            except ImportError:
                info_text += "\n無法取得詳細系統資訊 (需要 psutil)"
            
            self.system_info_text.delete(1.0, tk.END)
            self.system_info_text.insert(tk.END, info_text)
            
        except Exception as e:
            error_text = f"取得系統資訊失敗: {str(e)}"
            self.system_info_text.delete(1.0, tk.END)
            self.system_info_text.insert(tk.END, error_text)
    
    def toggle_folder_monitoring(self):
        """切換資料夾監控"""
        if self.folder_monitoring_var.get():
            self.start_folder_monitoring()
        else:
            self.stop_folder_monitoring()
    
    def start_folder_monitoring(self):
        """開始資料夾監控"""
        try:
            monitoring_manager.start_monitoring()
            self.folder_monitor_status_var.set("監控中")
            self.update_folder_monitoring_display()
            logging_service.info("資料夾監控已啟動")
        except Exception as e:
            self.folder_monitor_status_var.set("啟動失敗")
            logging_service.error(f"啟動資料夾監控失敗: {e}")
            messagebox.showerror("錯誤", f"啟動資料夾監控失敗: {e}")
    
    def stop_folder_monitoring(self):
        """停止資料夾監控"""
        try:
            monitoring_manager.stop_monitoring()
            self.folder_monitor_status_var.set("已停止")
            logging_service.info("資料夾監控已停止")
        except Exception as e:
            logging_service.error(f"停止資料夾監控失敗: {e}")
    
    def configure_monitoring_folders(self):
        """設定監控資料夾"""
        # 這裡可以開啟一個對話框來設定監控資料夾
        messagebox.showinfo("資訊", "資料夾監控設定功能將在後續版本中實現")
    
    def update_folder_monitoring_display(self):
        """更新資料夾監控顯示"""
        # 清除現有項目
        for item in self.folder_tree.get_children():
            self.folder_tree.delete(item)
        
        # 添加監控的資料夾（示例）
        config = config_service.get_config()
        if config.source_folder:
            self.folder_tree.insert('', 'end', text='來源資料夾', 
                                   values=(config.source_folder, '監控中'))
        
        if config.processed_folder:
            self.folder_tree.insert('', 'end', text='處理資料夾', 
                                   values=(config.processed_folder, '監控中'))
    
    def cleanup_memory(self):
        """記憶體清理"""
        try:
            import gc
            gc.collect()
            
            # 記錄清理前後的記憶體使用情況
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            result_text = f"記憶體清理完成！\n\n"
            result_text += f"當前記憶體使用: {memory_info.rss // (1024*1024)} MB\n"
            result_text += f"虛擬記憶體: {memory_info.vms // (1024*1024)} MB\n"
            
            messagebox.showinfo("記憶體清理", result_text)
            logging_service.info("執行記憶體清理")
            
        except Exception as e:
            error_msg = f"記憶體清理失敗: {str(e)}"
            messagebox.showerror("錯誤", error_msg)
            logging_service.error(error_msg)
    
    def generate_performance_report(self):
        """生成效能報告"""
        try:
            if not self.performance_history:
                messagebox.showwarning("警告", "沒有效能歷史資料")
                return
            
            # 計算統計資料
            cpu_values = [r['cpu'] for r in self.performance_history]
            memory_values = [r['memory'] for r in self.performance_history]
            disk_values = [r['disk'] for r in self.performance_history]
            
            report = f"=== 效能報告 ===\n"
            report += f"資料收集時間: {len(self.performance_history)} 個時間點\n\n"
            
            report += f"CPU 使用率:\n"
            report += f"  平均: {sum(cpu_values) / len(cpu_values):.1f}%\n"
            report += f"  最高: {max(cpu_values):.1f}%\n"
            report += f"  最低: {min(cpu_values):.1f}%\n\n"
            
            report += f"記憶體使用率:\n"
            report += f"  平均: {sum(memory_values) / len(memory_values):.1f}%\n"
            report += f"  最高: {max(memory_values):.1f}%\n"
            report += f"  最低: {min(memory_values):.1f}%\n\n"
            
            report += f"磁碟使用率:\n"
            report += f"  平均: {sum(disk_values) / len(disk_values):.1f}%\n"
            report += f"  最高: {max(disk_values):.1f}%\n"
            report += f"  最低: {min(disk_values):.1f}%\n\n"
            
            # 效能建議
            avg_cpu = sum(cpu_values) / len(cpu_values)
            avg_memory = sum(memory_values) / len(memory_values)
            
            report += f"效能建議:\n"
            if avg_cpu > 70:
                report += f"  • CPU 使用率偏高，建議關閉不必要的程式\n"
            if avg_memory > 80:
                report += f"  • 記憶體使用率偏高，建議重啟程式或增加記憶體\n"
            if max(cpu_values) > 90:
                report += f"  • 曾出現 CPU 使用率過高的情況\n"
            if max(memory_values) > 90:
                report += f"  • 曾出現記憶體使用率過高的情況\n"
            
            if avg_cpu < 50 and avg_memory < 60:
                report += f"  • 系統效能良好，無需特別調整\n"
            
            # 顯示報告
            report_window = tk.Toplevel(self.root)
            report_window.title("效能報告")
            report_window.geometry("500x400")
            
            report_text = scrolledtext.ScrolledText(report_window, wrap=tk.WORD, font=self.fonts['console'])
            report_text.pack(fill='both', expand=True, padx=10, pady=10)
            report_text.insert(tk.END, report)
            report_text.config(state='disabled')
            
            logging_service.info("生成效能報告")
            
        except Exception as e:
            error_msg = f"生成效能報告失敗: {str(e)}"
            messagebox.showerror("錯誤", error_msg)
            logging_service.error(error_msg)

    def create_diagnostic_tab(self):
        """建立診斷標籤頁"""
        # 主框架
        main_frame = ttk.Frame(self.diagnostic_tab)
        main_frame.pack(fill='both', expand=True)
        
        # 左側控制面板
        control_frame = ttk.LabelFrame(main_frame, text="診斷控制", padding=10)
        control_frame.pack(side='left', fill='y', padx=(0, 10))
        
        # 快速健康檢查按鈕
        ttk.Button(control_frame, text="快速健康檢查", 
                  command=self.run_quick_health_check).pack(fill='x', pady=2)
        
        # 完整系統診斷按鈕
        ttk.Button(control_frame, text="完整系統診斷", 
                  command=self.run_full_diagnostics).pack(fill='x', pady=2)
        
        # 匯出診斷報告按鈕
        ttk.Button(control_frame, text="匯出診斷套件", 
                  command=self.export_diagnostic_package).pack(fill='x', pady=2)
        
        # 分隔線
        ttk.Separator(control_frame, orient='horizontal').pack(fill='x', pady=10)
        
        # 日誌管理
        ttk.Label(control_frame, text="日誌管理", style='Subtitle.TLabel').pack(anchor='w')
        
        # 日誌搜尋
        ttk.Label(control_frame, text="搜尋關鍵字:").pack(anchor='w', pady=(5, 0))
        self.log_search_var = tk.StringVar()
        ttk.Entry(control_frame, textvariable=self.log_search_var).pack(fill='x', pady=2)
        
        ttk.Button(control_frame, text="搜尋日誌", 
                  command=self.search_logs).pack(fill='x', pady=2)
        
        # 日誌等級過濾
        ttk.Label(control_frame, text="日誌等級:").pack(anchor='w', pady=(5, 0))
        self.log_level_var = tk.StringVar(value="ERROR")
        log_level_combo = ttk.Combobox(control_frame, textvariable=self.log_level_var,
                                      values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                                      state="readonly")
        log_level_combo.pack(fill='x', pady=2)
        
        ttk.Button(control_frame, text="過濾日誌", 
                  command=self.filter_logs_by_level).pack(fill='x', pady=2)
        
        # 清理日誌
        ttk.Button(control_frame, text="清理舊日誌", 
                  command=self.cleanup_old_logs).pack(fill='x', pady=2)
        
        # 右側結果顯示區域
        result_frame = ttk.Frame(main_frame)
        result_frame.pack(side='right', fill='both', expand=True)
        
        # 結果顯示區域
        ttk.Label(result_frame, text="診斷結果", style='Subtitle.TLabel').pack(anchor='w')
        
        # 建立帶滾動條的文字區域
        text_frame = ttk.Frame(result_frame)
        text_frame.pack(fill='both', expand=True, pady=5)
        
        self.diagnostic_result_area = scrolledtext.ScrolledText(
            text_frame, 
            wrap=tk.WORD, 
            height=25,
            font=self.fonts['console']
        )
        self.diagnostic_result_area.pack(fill='both', expand=True)
        
        # 狀態列
        self.diagnostic_status_var = tk.StringVar(value="就緒")
        status_frame = ttk.Frame(result_frame)
        status_frame.pack(fill='x', pady=(5, 0))
        
        ttk.Label(status_frame, text="狀態:").pack(side='left')
        ttk.Label(status_frame, textvariable=self.diagnostic_status_var).pack(side='left', padx=(5, 0))
        
        # 初始化時顯示歡迎訊息
        welcome_msg = """歡迎使用系統診斷功能！

可用功能：
• 快速健康檢查 - 檢查系統基本狀態
• 完整系統診斷 - 詳細的系統分析報告
• 匯出診斷套件 - 生成完整的診斷資料包
• 日誌搜尋和過濾 - 查找特定的日誌記錄
• 清理舊日誌 - 清理過期的日誌檔案

點擊上方按鈕開始診斷...
"""
        self.diagnostic_result_area.insert(tk.END, welcome_msg)
    
    def run_quick_health_check(self):
        """執行快速健康檢查"""
        self.diagnostic_status_var.set("執行快速健康檢查...")
        self.diagnostic_result_area.delete(1.0, tk.END)
        
        def health_check_thread():
            try:
                health_status = diagnostics_manager.quick_health_check()
                
                # 格式化結果
                result = f"=== 快速健康檢查結果 ===\n"
                result += f"檢查時間: {health_status['timestamp']}\n"
                result += f"整體狀態: {health_status['overall_status']}\n\n"
                
                result += "各項檢查結果:\n"
                for check_name, status in health_status.get('checks', {}).items():
                    status_icon = "✓" if status == "ok" else "⚠" if status == "warning" else "✗"
                    result += f"  {status_icon} {check_name}: {status}\n"
                
                if health_status.get('metrics'):
                    result += f"\n效能指標:\n"
                    metrics = health_status['metrics']
                    result += f"  CPU 使用率: {metrics.get('cpu_usage', 0):.1f}%\n"
                    result += f"  記憶體使用率: {metrics.get('memory_usage', 0):.1f}%\n"
                    result += f"  磁碟使用率: {metrics.get('disk_usage', 0):.1f}%\n"
                    result += f"  錯誤數量: {metrics.get('error_count', 0)}\n"
                
                if health_status.get('issues'):
                    result += f"\n發現的問題:\n"
                    for issue in health_status['issues']:
                        result += f"  • {issue}\n"
                
                # 在主線程中更新 GUI
                self.root.after(0, lambda: self._update_diagnostic_result(result, "快速健康檢查完成"))
                
            except Exception as e:
                error_msg = f"快速健康檢查失敗: {str(e)}"
                self.root.after(0, lambda: self._update_diagnostic_result(error_msg, "檢查失敗"))
        
        # 在背景線程中執行
        threading.Thread(target=health_check_thread, daemon=True).start()
    
    def run_full_diagnostics(self):
        """執行完整系統診斷"""
        self.diagnostic_status_var.set("執行完整系統診斷...")
        self.diagnostic_result_area.delete(1.0, tk.END)
        self.diagnostic_result_area.insert(tk.END, "正在執行完整系統診斷，請稍候...\n")
        
        def full_diagnostic_thread():
            try:
                diagnostic_info = diagnostics_manager.run_full_diagnostics()
                report = diagnostics_manager.generate_diagnostic_report(diagnostic_info)
                
                # 在主線程中更新 GUI
                self.root.after(0, lambda: self._update_diagnostic_result(report, "完整系統診斷完成"))
                
            except Exception as e:
                error_msg = f"完整系統診斷失敗: {str(e)}\n\n詳細錯誤:\n{traceback.format_exc()}"
                self.root.after(0, lambda: self._update_diagnostic_result(error_msg, "診斷失敗"))
        
        # 在背景線程中執行
        threading.Thread(target=full_diagnostic_thread, daemon=True).start()
    
    def export_diagnostic_package(self):
        """匯出診斷套件"""
        self.diagnostic_status_var.set("匯出診斷套件...")
        
        def export_thread():
            try:
                diagnostic_info = diagnostics_manager.run_full_diagnostics()
                package_path = diagnostics_manager.export_diagnostic_package(diagnostic_info)
                
                result = f"診斷套件已成功匯出！\n\n"
                result += f"檔案位置: {package_path}\n\n"
                result += f"套件內容:\n"
                result += f"• diagnostic_report.txt - 診斷報告\n"
                result += f"• diagnostic_data.json - 原始診斷資料\n"
                result += f"• logs/ - 日誌檔案\n"
                result += f"• config.json - 配置檔案\n\n"
                result += f"您可以將此檔案提供給技術支援人員進行問題分析。"
                
                self.root.after(0, lambda: self._update_diagnostic_result(result, "診斷套件匯出完成"))
                
            except Exception as e:
                error_msg = f"匯出診斷套件失敗: {str(e)}"
                self.root.after(0, lambda: self._update_diagnostic_result(error_msg, "匯出失敗"))
        
        # 在背景線程中執行
        threading.Thread(target=export_thread, daemon=True).start()
    
    def search_logs(self):
        """搜尋日誌"""
        query = self.log_search_var.get().strip()
        if not query:
            messagebox.showwarning("警告", "請輸入搜尋關鍵字")
            return
        
        self.diagnostic_status_var.set(f"搜尋日誌: {query}")
        
        try:
            results = logging_service.search_logs(query, max_results=50)
            
            if results:
                result_text = f"=== 日誌搜尋結果 ===\n"
                result_text += f"搜尋關鍵字: {query}\n"
                result_text += f"找到 {len(results)} 筆記錄\n\n"
                
                for i, result in enumerate(results, 1):
                    result_text += f"{i}. 行 {result['line_number']}: {result['content']}\n"
                    if result.get('timestamp'):
                        result_text += f"   時間: {result['timestamp']}\n"
                    result_text += "\n"
            else:
                result_text = f"未找到包含 '{query}' 的日誌記錄"
            
            self._update_diagnostic_result(result_text, "日誌搜尋完成")
            
        except Exception as e:
            error_msg = f"搜尋日誌失敗: {str(e)}"
            self._update_diagnostic_result(error_msg, "搜尋失敗")
    
    def filter_logs_by_level(self):
        """依等級過濾日誌"""
        level = self.log_level_var.get()
        self.diagnostic_status_var.set(f"過濾 {level} 等級日誌")
        
        try:
            results = logging_service.filter_logs_by_level(level, max_results=50)
            
            if results:
                result_text = f"=== {level} 等級日誌 ===\n"
                result_text += f"找到 {len(results)} 筆記錄\n\n"
                
                for i, result in enumerate(results, 1):
                    result_text += f"{i}. 行 {result['line_number']}: {result['content']}\n"
                    if result.get('timestamp'):
                        result_text += f"   時間: {result['timestamp']}\n"
                    result_text += "\n"
            else:
                result_text = f"未找到 {level} 等級的日誌記錄"
            
            self._update_diagnostic_result(result_text, "日誌過濾完成")
            
        except Exception as e:
            error_msg = f"過濾日誌失敗: {str(e)}"
            self._update_diagnostic_result(error_msg, "過濾失敗")
    
    def cleanup_old_logs(self):
        """清理舊日誌"""
        result = messagebox.askyesno("確認", "確定要清理30天前的舊日誌檔案嗎？")
        if not result:
            return
        
        self.diagnostic_status_var.set("清理舊日誌...")
        
        try:
            logging_service.cleanup_old_logs(days_to_keep=30)
            
            result_text = "舊日誌清理完成！\n\n"
            result_text += "已刪除30天前的日誌檔案。\n"
            result_text += "如需查看清理詳情，請檢查主日誌檔案。"
            
            self._update_diagnostic_result(result_text, "日誌清理完成")
            
        except Exception as e:
            error_msg = f"清理舊日誌失敗: {str(e)}"
            self._update_diagnostic_result(error_msg, "清理失敗")
    
    def _update_diagnostic_result(self, text, status):
        """更新診斷結果顯示"""
        self.diagnostic_result_area.delete(1.0, tk.END)
        self.diagnostic_result_area.insert(tk.END, text)
        self.diagnostic_status_var.set(status)
    
    def create_settings_tab(self):
        """建立設定標籤頁"""
        # 主框架
        main_frame = ttk.Frame(self.settings_tab)
        main_frame.pack(fill='both', expand=True)
        
        # 左側設定選項
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # 外觀設定
        appearance_frame = ttk.LabelFrame(left_frame, text="外觀設定", padding=10)
        appearance_frame.pack(fill='x', pady=5)
        
        # 主題選擇
        ttk.Label(appearance_frame, text="主題:").grid(row=0, column=0, sticky='w', pady=2)
        self.theme_var = tk.StringVar(value=self.style.theme_use())
        theme_combo = ttk.Combobox(appearance_frame, textvariable=self.theme_var,
                                  values=list(self.style.theme_names()),
                                  state="readonly")
        theme_combo.grid(row=0, column=1, sticky='ew', padx=(5, 0), pady=2)
        theme_combo.bind('<<ComboboxSelected>>', self.change_theme)
        
        # 字體大小
        ttk.Label(appearance_frame, text="字體大小:").grid(row=1, column=0, sticky='w', pady=2)
        self.font_size_var = tk.StringVar(value="10")
        font_size_spinbox = ttk.Spinbox(appearance_frame, from_=8, to=20, 
                                       textvariable=self.font_size_var,
                                       command=self.change_font_size)
        font_size_spinbox.grid(row=1, column=1, sticky='ew', padx=(5, 0), pady=2)
        
        # 視窗透明度（僅 Windows）
        if platform_adapter.is_windows():
            ttk.Label(appearance_frame, text="視窗透明度:").grid(row=2, column=0, sticky='w', pady=2)
            self.transparency_var = tk.DoubleVar(value=1.0)
            transparency_scale = ttk.Scale(appearance_frame, from_=0.7, to=1.0,
                                         variable=self.transparency_var,
                                         command=self.change_transparency)
            transparency_scale.grid(row=2, column=1, sticky='ew', padx=(5, 0), pady=2)
        
        appearance_frame.columnconfigure(1, weight=1)
        
        # 功能設定
        function_frame = ttk.LabelFrame(left_frame, text="功能設定", padding=10)
        function_frame.pack(fill='x', pady=5)
        
        # 自動儲存設定
        self.auto_save_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(function_frame, text="自動儲存設定", 
                       variable=self.auto_save_var).pack(anchor='w', pady=2)
        
        # 啟動時檢查更新
        self.check_updates_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(function_frame, text="啟動時檢查更新", 
                       variable=self.check_updates_var).pack(anchor='w', pady=2)
        
        # 最小化到系統托盤
        self.minimize_to_tray_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(function_frame, text="最小化到系統托盤", 
                       variable=self.minimize_to_tray_var).pack(anchor='w', pady=2)
        
        # 記住視窗位置
        self.remember_window_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(function_frame, text="記住視窗位置和大小", 
                       variable=self.remember_window_var).pack(anchor='w', pady=2)
        
        # 效能設定
        performance_frame = ttk.LabelFrame(left_frame, text="效能設定", padding=10)
        performance_frame.pack(fill='x', pady=5)
        
        # 最大記憶體使用量
        ttk.Label(performance_frame, text="最大記憶體使用量 (MB):").grid(row=0, column=0, sticky='w', pady=2)
        self.max_memory_var = tk.StringVar(value="1024")
        ttk.Entry(performance_frame, textvariable=self.max_memory_var, width=10).grid(row=0, column=1, sticky='w', padx=(5, 0), pady=2)
        
        # 背景處理線程數
        ttk.Label(performance_frame, text="背景處理線程數:").grid(row=1, column=0, sticky='w', pady=2)
        self.thread_count_var = tk.StringVar(value="4")
        thread_spinbox = ttk.Spinbox(performance_frame, from_=1, to=8, 
                                    textvariable=self.thread_count_var, width=10)
        thread_spinbox.grid(row=1, column=1, sticky='w', padx=(5, 0), pady=2)
        
        # 右側預覽和控制
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side='right', fill='both', expand=True)
        
        # 預覽區域
        preview_frame = ttk.LabelFrame(right_frame, text="預覽", padding=10)
        preview_frame.pack(fill='both', expand=True, pady=5)
        
        # 建立一個示例界面來預覽主題效果
        preview_notebook = ttk.Notebook(preview_frame)
        preview_notebook.pack(fill='both', expand=True)
        
        preview_tab = ttk.Frame(preview_notebook, padding=10)
        preview_notebook.add(preview_tab, text="預覽")
        
        ttk.Label(preview_tab, text="這是主題預覽", style='Subtitle.TLabel').pack(pady=5)
        ttk.Button(preview_tab, text="示例按鈕").pack(pady=5)
        
        preview_entry = ttk.Entry(preview_tab)
        preview_entry.pack(pady=5, fill='x')
        preview_entry.insert(0, "示例文字輸入")
        
        preview_progress = ttk.Progressbar(preview_tab, value=50)
        preview_progress.pack(pady=5, fill='x')
        
        # 控制按鈕
        control_frame = ttk.Frame(right_frame)
        control_frame.pack(fill='x', pady=5)
        
        ttk.Button(control_frame, text="套用設定", 
                  command=self.apply_settings).pack(side='left', padx=5)
        ttk.Button(control_frame, text="重設為預設值", 
                  command=self.reset_settings).pack(side='left', padx=5)
        ttk.Button(control_frame, text="匯出設定", 
                  command=self.export_settings).pack(side='left', padx=5)
        ttk.Button(control_frame, text="匯入設定", 
                  command=self.import_settings).pack(side='left', padx=5)
    
    def change_theme(self, event=None):
        """變更主題"""
        try:
            new_theme = self.theme_var.get()
            self.style.theme_use(new_theme)
            logging_service.info(f"主題已變更為: {new_theme}")
        except Exception as e:
            logging_service.error(f"變更主題失敗: {e}")
            messagebox.showerror("錯誤", f"變更主題失敗: {e}")
    
    def change_font_size(self):
        """變更字體大小"""
        try:
            size = int(self.font_size_var.get())
            # 使用統一的字型系統更新所有字型
            self.update_font_size(size)
            logging_service.info(f"字體大小已變更為: {size}")
        except Exception as e:
            logging_service.error(f"變更字體大小失敗: {e}")
    
    def change_transparency(self, value):
        """變更視窗透明度（僅 Windows）"""
        try:
            if platform_adapter.is_windows():
                transparency = float(value)
                self.root.attributes('-alpha', transparency)
                logging_service.info(f"視窗透明度已變更為: {transparency}")
        except Exception as e:
            logging_service.error(f"變更透明度失敗: {e}")
    
    def apply_settings(self):
        """套用設定"""
        try:
            # 儲存設定到配置服務
            settings = {
                'theme': self.theme_var.get(),
                'font_size': self.font_size_var.get(),
                'auto_save': self.auto_save_var.get(),
                'check_updates': self.check_updates_var.get(),
                'minimize_to_tray': self.minimize_to_tray_var.get(),
                'remember_window': self.remember_window_var.get(),
                'max_memory': self.max_memory_var.get(),
                'thread_count': self.thread_count_var.get()
            }
            
            if platform_adapter.is_windows():
                settings['transparency'] = self.transparency_var.get()
            
            # 這裡可以將設定儲存到配置檔案
            logging_service.info("設定已套用")
            messagebox.showinfo("成功", "設定已成功套用！")
            
        except Exception as e:
            logging_service.error(f"套用設定失敗: {e}")
            messagebox.showerror("錯誤", f"套用設定失敗: {e}")
    
    def reset_settings(self):
        """重設為預設值"""
        try:
            # 重設所有設定為預設值
            self.theme_var.set('clam' if 'clam' in self.style.theme_names() else 'default')
            self.font_size_var.set("10")
            self.auto_save_var.set(True)
            self.check_updates_var.set(False)
            self.minimize_to_tray_var.set(False)
            self.remember_window_var.set(True)
            self.max_memory_var.set("1024")
            self.thread_count_var.set("4")
            
            if platform_adapter.is_windows():
                self.transparency_var.set(1.0)
            
            # 套用預設主題
            self.change_theme()
            self.change_font_size()
            
            if platform_adapter.is_windows():
                self.change_transparency(1.0)
            
            logging_service.info("設定已重設為預設值")
            messagebox.showinfo("成功", "設定已重設為預設值！")
            
        except Exception as e:
            logging_service.error(f"重設設定失敗: {e}")
            messagebox.showerror("錯誤", f"重設設定失敗: {e}")
    
    def export_settings(self):
        """匯出設定"""
        try:
            settings = {
                'theme': self.theme_var.get(),
                'font_size': self.font_size_var.get(),
                'auto_save': self.auto_save_var.get(),
                'check_updates': self.check_updates_var.get(),
                'minimize_to_tray': self.minimize_to_tray_var.get(),
                'remember_window': self.remember_window_var.get(),
                'max_memory': self.max_memory_var.get(),
                'thread_count': self.thread_count_var.get()
            }
            
            if platform_adapter.is_windows():
                settings['transparency'] = self.transparency_var.get()
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON 檔案", "*.json"), ("所有檔案", "*.*")],
                title="匯出設定檔案"
            )
            
            if file_path:
                import json
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, indent=2, ensure_ascii=False)
                
                logging_service.info(f"設定已匯出到: {file_path}")
                messagebox.showinfo("成功", f"設定已成功匯出到:\n{file_path}")
            
        except Exception as e:
            logging_service.error(f"匯出設定失敗: {e}")
            messagebox.showerror("錯誤", f"匯出設定失敗: {e}")
    
    def import_settings(self):
        """匯入設定"""
        try:
            file_path = filedialog.askopenfilename(
                filetypes=[("JSON 檔案", "*.json"), ("所有檔案", "*.*")],
                title="匯入設定檔案"
            )
            
            if file_path:
                import json
                with open(file_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                # 套用匯入的設定
                if 'theme' in settings:
                    self.theme_var.set(settings['theme'])
                if 'font_size' in settings:
                    self.font_size_var.set(settings['font_size'])
                if 'auto_save' in settings:
                    self.auto_save_var.set(settings['auto_save'])
                if 'check_updates' in settings:
                    self.check_updates_var.set(settings['check_updates'])
                if 'minimize_to_tray' in settings:
                    self.minimize_to_tray_var.set(settings['minimize_to_tray'])
                if 'remember_window' in settings:
                    self.remember_window_var.set(settings['remember_window'])
                if 'max_memory' in settings:
                    self.max_memory_var.set(settings['max_memory'])
                if 'thread_count' in settings:
                    self.thread_count_var.set(settings['thread_count'])
                
                if platform_adapter.is_windows() and 'transparency' in settings:
                    self.transparency_var.set(settings['transparency'])
                
                # 套用設定
                self.change_theme()
                self.change_font_size()
                
                if platform_adapter.is_windows() and 'transparency' in settings:
                    self.change_transparency(settings['transparency'])
                
                logging_service.info(f"設定已從 {file_path} 匯入")
                messagebox.showinfo("成功", f"設定已成功從以下檔案匯入:\n{file_path}")
            
        except Exception as e:
            logging_service.error(f"匯入設定失敗: {e}")
            messagebox.showerror("錯誤", f"匯入設定失敗: {e}")

# ===============================================================
# SECTION 4: 應用程式啟動
# ===============================================================
def main():
    """主程式入口"""
    if _IMPORT_ERROR_LIBS:
        messagebox.showerror("缺少必要函式庫", 
                           f"缺少函式庫: {', '.join(_IMPORT_ERROR_LIBS)}\n請執行 'pip install {' '.join(_IMPORT_ERROR_LIBS)}'")
        if "google-generativeai" in _IMPORT_ERROR_LIBS or "pandas" in _IMPORT_ERROR_LIBS:
            sys.exit(1)
    
    root = tk.Tk()
    app = AIWorkstationApp(root)
    
    # 確保字型系統在所有元件創建後再次應用
    root.after(100, lambda: app.apply_fonts_to_styles())
    root.after(200, lambda: app.update_text_widgets_font())
    
    root.mainloop()

if __name__ == "__main__":
    main()    

    def _start_translation_process(self, api_key, srt_path, target_language, log_area_ref):
        """開始翻譯處理流程"""
        self.is_ai_translating = True
        self.update_ai_buttons_state_tab()
        self.update_status_label("準備開始 AI 翻譯...")
        self.log_message(f"開始 AI 翻譯執行緒，目標檔案: {os.path.basename(srt_path)}，目標語言: {target_language}", log_area_ref=log_area_ref)
        self.root.update_idletasks()
        
        translation_thread = threading.Thread(target=self._do_ai_translation_thread, 
                                             args=(api_key, srt_path, target_language, log_area_ref), daemon=True)
        translation_thread.start()
    
    def _do_ai_translation_thread(self, api_key, srt_path, target_language, log_area_ref=None):
        """AI翻譯處理線程 - 參考OkokGo實作"""
        original_subs = []
        all_translation_data = []
        
        try:
            if log_area_ref is None:
                log_area_ref = self.ai_log_area
            self.log_message("AI 翻譯線程：正在設定 Google AI...", log_area_ref=log_area_ref)
            self.root.after(0, self.update_status_label, "正在設定 Google AI...")
            
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                model_name = self.ai_model_var.get().strip() or "gemini-2.5-flash"
                self.log_message(f"使用 AI 模型進行翻譯: {model_name}", log_area_ref=log_area_ref)
                model = genai.GenerativeModel(model_name)
                
                # OkokGo 的安全設定
                safety_settings = [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                ]
                generation_config = genai.types.GenerationConfig(temperature=0.3)  # 低溫度確保準確性
            except Exception as config_err:
                if "API key not valid" in str(config_err):
                    self.log_message("AI 翻譯錯誤: API 金鑰無效", is_error=True, log_area_ref=log_area_ref)
                    self.root.after(0, messagebox.showerror, "AI 翻譯錯誤", "API 金鑰無效，請檢查您的 Google AI API 金鑰。")
                else:
                    self.log_message(f"AI 翻譯錯誤: Google AI 設定失敗 - {str(config_err)}", is_error=True, log_area_ref=log_area_ref)
                    self.root.after(0, messagebox.showerror, "AI 翻譯錯誤", f"Google AI 設定失敗：{str(config_err)}")
                return
            
            self.log_message("AI 翻譯線程：正在讀取 SRT 檔案...", log_area_ref=log_area_ref)
            self.root.after(0, self.update_status_label, "正在讀取 SRT 檔案...")
            
            try:
                import srt
                with open(srt_path, 'r', encoding='utf-8') as f:
                    srt_content = f.read()
                original_subs = list(srt.parse(srt_content))
                self.log_message(f"成功讀取 {len(original_subs)} 條字幕", log_area_ref=log_area_ref)
            except Exception as read_err:
                self.log_message(f"AI 翻譯錯誤: 讀取 SRT 檔案失敗 - {str(read_err)}", is_error=True, log_area_ref=log_area_ref)
                self.root.after(0, messagebox.showerror, "AI 翻譯錯誤", f"讀取 SRT 檔案失敗：{str(read_err)}")
                return
            
            if not original_subs:
                self.log_message("AI 翻譯錯誤: SRT 檔案為空或格式錯誤", is_warning=True, log_area_ref=log_area_ref)
                self.root.after(0, messagebox.showwarning, "AI 翻譯警告", "SRT 檔案為空或格式錯誤")
                return
            
            # 分批處理 - 使用設定中的批次大小
            try:
                chunk_size = int(self.batch_size_var.get().strip())
                if chunk_size <= 0:
                    chunk_size = 15
            except (ValueError, AttributeError):
                chunk_size = 15
            chunks = [original_subs[i:i + chunk_size] for i in range(0, len(original_subs), chunk_size)]
            total_chunks = len(chunks)
            
            self.log_message(f"開始分批翻譯：共 {total_chunks} 批，每批 {chunk_size} 條字幕", log_area_ref=log_area_ref)
            
            # 處理每個批次
            for chunk_index, chunk in enumerate(chunks):
                current_progress = int((chunk_index / total_chunks) * 100)
                self.root.after(0, self.update_status_label, f"AI 翻譯中 ({current_progress}%)... Chunk {chunk_index + 1}/{total_chunks}")
                self.log_message(f"處理批次 {chunk_index + 1}/{total_chunks} ({len(chunk)} 條字幕)", log_area_ref=log_area_ref)
                
                # 提取純文字內容
                chunk_texts = [sub.content for sub in chunk]
                chunk_text = '\n'.join(chunk_texts)
                
                # OkokGo 風格的翻譯提示詞
                prompt = f"""你是一位專業的字幕翻譯專家。請將以下繁體中文字幕翻譯成 {target_language}。

翻譯要求：
1. 保持原文的語調和情感
2. 確保翻譯自然流暢，符合目標語言的表達習慣
3. 保持專有名詞的一致性
4. 如果遇到文化特定的概念，請選擇最適合的對等表達

重要規則：
1. 輸出：僅輸出翻譯後的文字，不要包含任何原始文字、標籤、索引編號或解釋
2. 行數：輸出的總行數必須與輸入的文字行數完全相同
3. 對應：輸出的每一行文字，都必須是對應順序的原始文字行的翻譯結果
4. 格式：每行一個翻譯結果，不要添加額外的格式或標記

原始字幕文字：
{chunk_text}"""
                
                # 重試機制 - 重用已鎖定功能的成功模式
                max_retries = 2
                translated_texts = None
                
                for retry in range(max_retries + 1):
                    try:
                        if retry > 0:
                            self.log_message(f"批次 {chunk_index + 1} 重試第 {retry} 次", log_area_ref=log_area_ref)
                        
                        response = model.generate_content(prompt, safety_settings=safety_settings, generation_config=generation_config)
                        translated_text = response.text.strip()
                        
                        if translated_text:
                            translated_texts = translated_text.split('\n')
                            
                            # 驗證行數是否匹配
                            if len(translated_texts) == len(chunk_texts):
                                break
                            else:
                                self.log_message(f"批次 {chunk_index + 1} 行數不匹配：原始 {len(chunk_texts)} 行，翻譯後 {len(translated_texts)} 行", is_warning=True, log_area_ref=log_area_ref)
                                if retry == max_retries:
                                    # 最後一次重試失敗，使用原始文字
                                    translated_texts = chunk_texts
                                    self.log_message(f"批次 {chunk_index + 1} 翻譯失敗，保持原始內容", is_warning=True, log_area_ref=log_area_ref)
                        else:
                            if retry == max_retries:
                                translated_texts = chunk_texts
                                self.log_message(f"批次 {chunk_index + 1} AI 回應為空，保持原始內容", is_warning=True, log_area_ref=log_area_ref)
                    
                    except Exception as ai_err:
                        self.log_message(f"批次 {chunk_index + 1} AI 處理錯誤 (重試 {retry}): {str(ai_err)}", is_warning=True, log_area_ref=log_area_ref)
                        if retry == max_retries:
                            translated_texts = chunk_texts
                            self.log_message(f"批次 {chunk_index + 1} 最終失敗，保持原始內容", is_warning=True, log_area_ref=log_area_ref)
                
                # 記錄翻譯結果
                for i, (original_sub, translated_text) in enumerate(zip(chunk, translated_texts)):
                    translation_data = {
                        'index': chunk_index * chunk_size + i,
                        'start': str(original_sub.start),
                        'end': str(original_sub.end),
                        'original': original_sub.content,
                        'translated': translated_text,
                        'changed': original_sub.content != translated_text,
                        'ai_failed_chunk': translated_texts == chunk_texts and translated_text != original_sub.content
                    }
                    all_translation_data.append(translation_data)
            
            # 完成處理
            self.root.after(0, self.update_status_label, "正在生成翻譯結果...")
            
            # 統計結果
            total_subs = len(all_translation_data)
            translated_count = sum(1 for item in all_translation_data if item['changed'])
            failed_count = sum(1 for item in all_translation_data if item['ai_failed_chunk'])
            
            self.log_message(f"翻譯統計：總共 {total_subs} 條，翻譯 {translated_count} 條，失敗 {failed_count} 條", log_area_ref=log_area_ref)
            
            # 生成翻譯後的 SRT 內容
            translated_subs = []
            for i, (original_sub, translation_data) in enumerate(zip(original_subs, all_translation_data)):
                translated_sub = srt.Subtitle(
                    index=original_sub.index,
                    start=original_sub.start,
                    end=original_sub.end,
                    content=translation_data['translated']
                )
                translated_subs.append(translated_sub)
            
            # 儲存翻譯後的檔案 - 使用時間戳命名
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = os.path.splitext(os.path.basename(srt_path))[0]
            translated_path = os.path.join(os.path.dirname(srt_path), f"{base_name}_translated_{target_language}_{timestamp}.srt")
            
            translated_content = srt.compose(translated_subs)
            with open(translated_path, 'w', encoding='utf-8') as f:
                f.write(translated_content)
            
            self.log_message(f"AI 翻譯完成！翻譯後檔案已儲存至: {translated_path}", log_area_ref=log_area_ref)
            
            # 顯示預覽視窗
            self.root.after(0, self._show_translation_preview, all_translation_data, translated_path, target_language)
                
        except Exception as e:
            self.log_message(f"AI 翻譯執行緒發生未預期錯誤: {str(e)}", is_error=True, log_area_ref=log_area_ref)
            self.root.after(0, messagebox.showerror, "AI 翻譯錯誤", f"發生未預期錯誤：{str(e)}")
        finally:
            self.is_ai_translating = False
            self.root.after(0, self.update_ai_buttons_state_tab)
            self.root.after(0, self.update_status_label, "就緒") 
   
    def _show_translation_preview(self, translation_data, translated_path, target_language):
        """顯示翻譯預覽視窗 - 參考校正預覽的成功模式"""
        try:
            popup = tk.Toplevel(self.root)
            popup.title(f"AI 翻譯預覽 - {target_language}")
            popup.geometry("900x700")
            popup.configure(bg=self.colors.get("background", "#1E1E1E"))
            
            # 主框架
            main_frame = ttk.Frame(popup, style='TFrame')
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # 標題和統計
            title_frame = ttk.Frame(main_frame, style='TFrame')
            title_frame.pack(fill=tk.X, pady=(0, 10))
            
            total_count = len(translation_data)
            translated_count = sum(1 for item in translation_data if item['changed'])
            failed_count = sum(1 for item in translation_data if item['ai_failed_chunk'])
            
            title_label = ttk.Label(title_frame, 
                                  text=f"翻譯結果預覽 - 目標語言: {target_language}", 
                                  style='TLabel', font=("Arial", 14, "bold"))
            title_label.pack(side=tk.LEFT)
            
            stats_label = ttk.Label(title_frame, 
                                  text=f"總計: {total_count} 條 | 已翻譯: {translated_count} 條 | 失敗: {failed_count} 條", 
                                  style='TLabel')
            stats_label.pack(side=tk.RIGHT)
            
            # 預覽文字區域
            text_frame = ttk.Frame(main_frame, style='TFrame')
            text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            
            import tkinter.scrolledtext as scrolledtext
            preview_text = scrolledtext.ScrolledText(
                text_frame, 
                wrap=tk.WORD, 
                font=("Consolas", 10),
                bg=self.colors.get("input_bg", "#3A3A3A"),
                fg="#CCCCCC",
                insertbackground=self.colors.get("input_fg", "#00FFFF"),
                selectbackground="#4A4A4A"
            )
            preview_text.pack(fill=tk.BOTH, expand=True)
            
            # 配置標籤顏色
            preview_text.tag_config("original", foreground="#AAAAAA", font=("Consolas", 9))
            preview_text.tag_config("translated", foreground="#00FF00", font=("Consolas", 10, "bold"))
            preview_text.tag_config("failed", foreground="#FF6666", font=("Consolas", 10))
            preview_text.tag_config("unchanged", foreground="#FFFF99", font=("Consolas", 10))
            preview_text.tag_config("separator", foreground="#666666")
            
            # 填充預覽內容
            for i, item in enumerate(translation_data):
                # 時間軸
                preview_text.insert(tk.END, f"{i+1:3d}  {item['start']} --> {item['end']}\n", ("separator",))
                
                # 原始文字
                preview_text.insert(tk.END, f"原文: {item['original']}\n", ("original",))
                
                # 翻譯文字
                if item['ai_failed_chunk']:
                    preview_text.insert(tk.END, f"翻譯: {item['translated']} [翻譯失敗]\n", ("failed",))
                elif item['changed']:
                    preview_text.insert(tk.END, f"翻譯: {item['translated']}\n", ("translated",))
                else:
                    preview_text.insert(tk.END, f"翻譯: {item['translated']} [未變更]\n", ("unchanged",))
                
                preview_text.insert(tk.END, "\n", ("separator",))
            
            preview_text.config(state=tk.DISABLED)
            
            # 按鈕框架
            button_frame = ttk.Frame(main_frame, style='TFrame')
            button_frame.pack(fill=tk.X, pady=(10, 0))
            
            # 說明標籤
            info_label = ttk.Label(button_frame, 
                                 text="綠色=已翻譯 | 黃色=未變更 | 紅色=翻譯失敗", 
                                 style='TLabel', font=("Arial", 9))
            info_label.pack(side=tk.LEFT)
            
            # 按鈕
            def open_file_location():
                import subprocess
                import platform
                try:
                    if platform.system() == "Darwin":  # macOS
                        subprocess.run(["open", "-R", translated_path])
                    elif platform.system() == "Windows":
                        subprocess.run(["explorer", "/select,", translated_path])
                    else:  # Linux
                        subprocess.run(["xdg-open", os.path.dirname(translated_path)])
                except Exception as e:
                    messagebox.showerror("錯誤", f"無法開啟檔案位置：{str(e)}")
            
            ttk.Button(button_frame, text="開啟檔案位置", command=open_file_location, style='TButton').pack(side=tk.RIGHT, padx=(10, 0))
            ttk.Button(button_frame, text="關閉", command=popup.destroy, style='TButton').pack(side=tk.RIGHT)
            
            # 顯示完成訊息
            self.log_message(f"翻譯預覽視窗已開啟，共 {total_count} 條字幕，{translated_count} 條已翻譯")
            
            popup.transient(self.root)
            popup.grab_set()
            
        except Exception as preview_err:
            self.log_message(f"顯示翻譯預覽視窗時出錯: {preview_err}", is_error=True)
            import traceback
            self.log_message(traceback.format_exc())
            messagebox.showerror("預覽錯誤", f"無法顯示翻譯預覽視窗：{str(preview_err)}")