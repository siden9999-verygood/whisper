#!/usr/bin/env python3
"""
免費語音轉錄工具
使用 Whisper large-v2 模型進行高精度語音轉文字

作者: siden9999-verygood
授權: MIT License
"""

import os
import sys
import threading
from pathlib import Path
from typing import Optional, Callable
import tkinter as tk

# 確保可以導入本地模組
if getattr(sys, 'frozen', False):
    BASE_PATH = Path(sys.executable).parent
else:
    BASE_PATH = Path(__file__).parent
sys.path.insert(0, str(BASE_PATH))

# 導入 CustomTkinter
try:
    import customtkinter as ctk
except ImportError:
    print("正在安裝 CustomTkinter...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "customtkinter"])
    import customtkinter as ctk

# 導入本地模組
from model_downloader import ModelDownloader
from transcription_core import TranscriptionCore

# 應用程式常數
APP_NAME = "語音轉錄工具"
APP_VERSION = "1.0.0"
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600


class VoiceTranscriberApp(ctk.CTk):
    """主應用程式類別"""
    
    def __init__(self):
        super().__init__()
        
        # 設定視窗
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(600, 500)
        
        # 設定外觀
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")
        
        # 初始化變數
        self.selected_file: Optional[str] = None
        self.output_dir: Optional[str] = None
        self.is_transcribing = False
        self.transcription_core = TranscriptionCore()
        self.model_downloader = ModelDownloader()
        
        # 輸出格式選項
        self.output_srt = ctk.BooleanVar(value=True)
        self.output_txt = ctk.BooleanVar(value=False)
        self.output_vtt = ctk.BooleanVar(value=False)
        self.convert_traditional = ctk.BooleanVar(value=True)
        
        # 語言選項
        self.language_var = ctk.StringVar(value="zh")
        
        # 建立 UI
        self.create_ui()
        
        # 檢查模型
        self.after(500, self.check_model_status)
    
    def create_ui(self):
        """建立使用者介面"""
        # 主容器
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 標題
        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text=f"🎙️ {APP_NAME}",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        self.title_label.pack(pady=(10, 5))
        
        # 副標題
        self.subtitle_label = ctk.CTkLabel(
            self.main_frame,
            text="使用 Whisper AI 進行高精度語音轉文字",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        self.subtitle_label.pack(pady=(0, 20))
        
        # 檔案選擇區域
        self.create_file_section()
        
        # 設定區域
        self.create_settings_section()
        
        # 進度區域
        self.create_progress_section()
        
        # 按鈕區域
        self.create_button_section()
        
        # 狀態列
        self.create_status_bar()
    
    def create_file_section(self):
        """建立檔案選擇區域"""
        self.file_frame = ctk.CTkFrame(self.main_frame)
        self.file_frame.pack(fill="x", pady=10)
        
        # 拖放區域（使用按鈕模擬）
        self.drop_area = ctk.CTkButton(
            self.file_frame,
            text="📂 點擊選擇音訊或影片檔案\n\n支援格式：MP3, WAV, M4A, MP4, MOV 等",
            font=ctk.CTkFont(size=16),
            height=120,
            corner_radius=15,
            fg_color=("gray90", "gray20"),
            hover_color=("gray80", "gray30"),
            text_color=("gray40", "gray60"),
            command=self.select_file
        )
        self.drop_area.pack(fill="x", padx=20, pady=15)
        
        # 已選擇檔案顯示
        self.file_label = ctk.CTkLabel(
            self.file_frame,
            text="尚未選擇檔案",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.file_label.pack(pady=(0, 10))
    
    def create_settings_section(self):
        """建立設定區域"""
        self.settings_frame = ctk.CTkFrame(self.main_frame)
        self.settings_frame.pack(fill="x", pady=10, padx=20)
        
        # 設定標題
        settings_title = ctk.CTkLabel(
            self.settings_frame,
            text="⚙️ 設定",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        settings_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        # 設定內容框架
        settings_content = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        settings_content.pack(fill="x", padx=15, pady=(0, 15))
        
        # 左側：語言選擇
        left_frame = ctk.CTkFrame(settings_content, fg_color="transparent")
        left_frame.pack(side="left", fill="x", expand=True)
        
        lang_label = ctk.CTkLabel(left_frame, text="語言：")
        lang_label.pack(side="left", padx=(0, 5))
        
        self.lang_menu = ctk.CTkOptionMenu(
            left_frame,
            values=["中文", "英文", "日文", "韓文", "自動偵測"],
            variable=self.language_var,
            command=self.on_language_change,
            width=120
        )
        self.lang_menu.set("中文")
        self.lang_menu.pack(side="left")
        
        # 右側：輸出格式
        right_frame = ctk.CTkFrame(settings_content, fg_color="transparent")
        right_frame.pack(side="right")
        
        format_label = ctk.CTkLabel(right_frame, text="輸出格式：")
        format_label.pack(side="left", padx=(0, 5))
        
        self.srt_check = ctk.CTkCheckBox(
            right_frame, text="SRT", variable=self.output_srt, width=60
        )
        self.srt_check.pack(side="left", padx=5)
        
        self.txt_check = ctk.CTkCheckBox(
            right_frame, text="TXT", variable=self.output_txt, width=60
        )
        self.txt_check.pack(side="left", padx=5)
        
        self.vtt_check = ctk.CTkCheckBox(
            right_frame, text="VTT", variable=self.output_vtt, width=60
        )
        self.vtt_check.pack(side="left", padx=5)
        
        # 繁體中文轉換選項
        self.traditional_check = ctk.CTkCheckBox(
            self.settings_frame,
            text="轉換為繁體中文",
            variable=self.convert_traditional
        )
        self.traditional_check.pack(anchor="w", padx=15, pady=(0, 15))
    
    def create_progress_section(self):
        """建立進度區域"""
        self.progress_frame = ctk.CTkFrame(self.main_frame)
        self.progress_frame.pack(fill="x", pady=10, padx=20)
        
        # 進度條
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, height=20)
        self.progress_bar.pack(fill="x", padx=15, pady=15)
        self.progress_bar.set(0)
        
        # 進度文字
        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="準備就緒",
            font=ctk.CTkFont(size=12)
        )
        self.progress_label.pack(pady=(0, 15))
    
    def create_button_section(self):
        """建立按鈕區域"""
        self.button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.button_frame.pack(fill="x", pady=20)
        
        # 開始按鈕
        self.start_button = ctk.CTkButton(
            self.button_frame,
            text="🚀 開始轉錄",
            font=ctk.CTkFont(size=18, weight="bold"),
            height=50,
            corner_radius=25,
            command=self.start_transcription
        )
        self.start_button.pack(side="left", expand=True, padx=10)
        
        # 取消按鈕
        self.cancel_button = ctk.CTkButton(
            self.button_frame,
            text="取消",
            font=ctk.CTkFont(size=16),
            height=50,
            corner_radius=25,
            fg_color="gray",
            hover_color="darkgray",
            command=self.cancel_transcription,
            state="disabled"
        )
        self.cancel_button.pack(side="left", padx=10)
    
    def create_status_bar(self):
        """建立狀態列"""
        self.status_bar = ctk.CTkLabel(
            self,
            text="模型狀態：檢查中...",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.status_bar.pack(side="bottom", fill="x", pady=5)
    
    def select_file(self):
        """選擇檔案"""
        from tkinter import filedialog
        
        filetypes = [
            ("音訊檔案", "*.mp3 *.wav *.m4a *.flac *.ogg *.aac"),
            ("影片檔案", "*.mp4 *.mov *.avi *.mkv *.wmv"),
            ("所有檔案", "*.*")
        ]
        
        file_path = filedialog.askopenfilename(
            title="選擇音訊或影片檔案",
            filetypes=filetypes
        )
        
        if file_path:
            self.selected_file = file_path
            filename = Path(file_path).name
            self.file_label.configure(text=f"✅ 已選擇：{filename}")
            self.drop_area.configure(
                text=f"📂 {filename}\n\n點擊更換檔案",
                text_color=("gray20", "gray80")
            )
    
    def on_language_change(self, choice):
        """語言選擇變更"""
        lang_map = {
            "中文": "zh",
            "英文": "en",
            "日文": "ja",
            "韓文": "ko",
            "自動偵測": "auto"
        }
        self.language_var.set(lang_map.get(choice, "zh"))
    
    def check_model_status(self):
        """檢查模型狀態"""
        if self.model_downloader.is_model_available():
            self.status_bar.configure(text="✅ 模型已就緒 (large-v2)")
        else:
            self.status_bar.configure(text="⚠️ 模型未下載，首次轉錄時將自動下載 (~3GB)")
    
    def start_transcription(self):
        """開始轉錄"""
        if not self.selected_file:
            self.show_message("請先選擇檔案", "warning")
            return
        
        if self.is_transcribing:
            return
        
        self.is_transcribing = True
        self.start_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.progress_bar.set(0)
        self.progress_label.configure(text="準備中...")
        
        # 在背景執行轉錄
        thread = threading.Thread(target=self._run_transcription, daemon=True)
        thread.start()
    
    def _run_transcription(self):
        """執行轉錄（背景執行緒）"""
        try:
            # 檢查並下載模型
            if not self.model_downloader.is_model_available():
                self.update_progress(0.05, "正在下載 Whisper 模型...")
                self.model_downloader.download_model(
                    progress_callback=lambda p: self.update_progress(p * 0.3, f"下載模型中... {int(p*100)}%")
                )
            
            self.update_progress(0.35, "正在轉錄...")
            
            # 執行轉錄
            result = self.transcription_core.transcribe(
                input_file=self.selected_file,
                language=self.language_var.get(),
                output_srt=self.output_srt.get(),
                output_txt=self.output_txt.get(),
                output_vtt=self.output_vtt.get(),
                convert_traditional=self.convert_traditional.get(),
                progress_callback=lambda p: self.update_progress(0.35 + p * 0.6, f"轉錄中... {int(p*100)}%")
            )
            
            self.update_progress(1.0, "✅ 轉錄完成！")
            self.after(100, lambda: self.show_message(f"轉錄完成！\n輸出檔案：{result['output_file']}", "success"))
            
        except Exception as e:
            self.update_progress(0, f"❌ 錯誤：{str(e)}")
            self.after(100, lambda: self.show_message(f"轉錄失敗：{str(e)}", "error"))
        
        finally:
            self.is_transcribing = False
            self.after(100, self._reset_buttons)
    
    def _reset_buttons(self):
        """重置按鈕狀態"""
        self.start_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")
    
    def update_progress(self, value: float, text: str):
        """更新進度（執行緒安全）"""
        self.after(0, lambda: self._update_progress_ui(value, text))
    
    def _update_progress_ui(self, value: float, text: str):
        """更新進度 UI"""
        self.progress_bar.set(value)
        self.progress_label.configure(text=text)
    
    def cancel_transcription(self):
        """取消轉錄"""
        if self.is_transcribing:
            self.transcription_core.cancel()
            self.is_transcribing = False
            self.progress_label.configure(text="已取消")
            self._reset_buttons()
    
    def show_message(self, message: str, msg_type: str = "info"):
        """顯示訊息"""
        from tkinter import messagebox
        
        if msg_type == "error":
            messagebox.showerror("錯誤", message)
        elif msg_type == "warning":
            messagebox.showwarning("警告", message)
        elif msg_type == "success":
            messagebox.showinfo("成功", message)
        else:
            messagebox.showinfo("訊息", message)


def main():
    """主程式進入點"""
    app = VoiceTranscriberApp()
    app.mainloop()


if __name__ == "__main__":
    main()
