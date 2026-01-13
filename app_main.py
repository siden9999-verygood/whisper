#!/usr/bin/env python3
"""
免費語音轉錄工具
使用 Whisper large-v2 模型進行高精度語音轉文字
"""

import os
import sys
import threading
from pathlib import Path
from typing import Optional

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
    print("錯誤：請先安裝 customtkinter")
    sys.exit(1)

# 導入本地模組
from model_downloader import ModelDownloader
from transcription_core import TranscriptionCore

# 常數
APP_NAME = "語音轉錄工具"
APP_VERSION = "1.0.0"


class VoiceTranscriberApp(ctk.CTk):
    """主應用程式"""
    
    def __init__(self):
        super().__init__()
        
        # 視窗設定 - 稍微加高以顯示底部文字
        self.title(f"{APP_NAME}")
        self.geometry("500x430")
        self.minsize(500, 430)
        
        # 深色主題
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # 初始化
        self.selected_file: Optional[str] = None
        self.is_transcribing = False
        self.transcription_core = TranscriptionCore()
        self.model_downloader = ModelDownloader()
        
        # 選項
        self.output_srt = ctk.BooleanVar(value=True)
        self.output_txt = ctk.BooleanVar(value=False)
        self.convert_traditional = ctk.BooleanVar(value=True)
        self.language_var = ctk.StringVar(value="zh")
        
        self._build_ui()
        self.after(300, self._check_model)
    
    def _build_ui(self):
        """建立介面"""
        # 配置主視窗
        self.configure(fg_color="#1a1a2e")
        
        # 標題
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill="x", pady=(20, 5))
        
        ctk.CTkLabel(
            title_frame, 
            text=APP_NAME,
            font=ctk.CTkFont(family="Helvetica", size=22, weight="bold"),
            text_color="#e0e0e0"
        ).pack()
        
        ctk.CTkLabel(
            title_frame,
            text="Whisper AI 高精度語音辨識",
            font=ctk.CTkFont(size=11),
            text_color="#888888"
        ).pack()
        
        # 內容區
        content = ctk.CTkFrame(self, fg_color="#16213e", corner_radius=12)
        content.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 檔案選擇
        self.file_btn = ctk.CTkButton(
            content,
            text="選擇音訊或影片檔案",
            font=ctk.CTkFont(size=13),
            height=40,
            fg_color="#0f3460",
            hover_color="#1a4a7a",
            corner_radius=8,
            command=self._select_file
        )
        self.file_btn.pack(fill="x", padx=15, pady=(15, 5))
        
        self.file_label = ctk.CTkLabel(
            content, text="尚未選擇檔案", 
            font=ctk.CTkFont(size=10), text_color="#666666"
        )
        self.file_label.pack(pady=(0, 10))
        
        # 選項列
        opts = ctk.CTkFrame(content, fg_color="transparent")
        opts.pack(fill="x", padx=15)
        
        # 左側：音訊語言
        lang_frame = ctk.CTkFrame(opts, fg_color="transparent")
        lang_frame.pack(side="left")
        ctk.CTkLabel(lang_frame, text="音訊語言", font=ctk.CTkFont(size=11)).pack(side="left", padx=(0,5))
        self.lang_menu = ctk.CTkOptionMenu(
            lang_frame, values=["中文", "英文", "日文", "自動偵測"],
            width=90, height=28, font=ctk.CTkFont(size=11),
            fg_color="#0f3460", button_color="#1a4a7a",
            command=self._on_lang_change
        )
        self.lang_menu.set("中文")
        self.lang_menu.pack(side="left")
        
        # 右側：格式
        fmt_frame = ctk.CTkFrame(opts, fg_color="transparent")
        fmt_frame.pack(side="right")
        ctk.CTkCheckBox(fmt_frame, text="SRT", variable=self.output_srt, 
                       width=50, font=ctk.CTkFont(size=11)).pack(side="left", padx=3)
        ctk.CTkCheckBox(fmt_frame, text="TXT", variable=self.output_txt,
                       width=50, font=ctk.CTkFont(size=11)).pack(side="left", padx=3)
        
        # 繁體選項
        ctk.CTkCheckBox(
            content, text="簡體→繁體（僅中文音訊）", variable=self.convert_traditional,
            font=ctk.CTkFont(size=11)
        ).pack(anchor="w", padx=15, pady=8)
        
        # 進度
        self.progress = ctk.CTkProgressBar(content, height=8, corner_radius=4)
        self.progress.pack(fill="x", padx=15, pady=(5, 3))
        self.progress.set(0)
        
        self.status = ctk.CTkLabel(
            content, text="準備就緒",
            font=ctk.CTkFont(size=10), text_color="#888888"
        )
        self.status.pack(pady=(0, 10))
        
        # 按鈕
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(pady=(0, 15))
        
        self.start_btn = ctk.CTkButton(
            btn_frame, text="開始轉錄", width=120, height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#e94560", hover_color="#ff6b6b",
            corner_radius=8, command=self._start
        )
        self.start_btn.pack(side="left", padx=5)
        
        self.cancel_btn = ctk.CTkButton(
            btn_frame, text="取消", width=70, height=36,
            font=ctk.CTkFont(size=12),
            fg_color="#444444", hover_color="#555555",
            corner_radius=8, command=self._cancel, state="disabled"
        )
        self.cancel_btn.pack(side="left", padx=5)
        
        # 底部狀態 - 放置在最下方
        self.model_label = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=10), text_color="#555555"
        )
        self.model_label.pack(side="bottom", pady=5)
    
    def _select_file(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            filetypes=[("媒體檔案", "*.mp3 *.wav *.m4a *.mp4 *.mov *.mkv *.avi"), ("所有", "*.*")]
        )
        if path:
            self.selected_file = path
            name = Path(path).name
            self.file_label.configure(text=name[:45] + "..." if len(name) > 45 else name, text_color="#4CAF50")
    
    def _on_lang_change(self, choice):
        self.language_var.set({"中文": "zh", "英文": "en", "日文": "ja", "自動偵測": "auto"}.get(choice, "zh"))
    
    def _check_model(self):
        if self.model_downloader.is_model_available():
            self.model_label.configure(text="模型就緒 (large-v2)")
        else:
            self.model_label.configure(text="首次使用將下載模型 (~3GB)")
    
    def _start(self):
        if not self.selected_file:
            from tkinter import messagebox
            messagebox.showwarning("提示", "請先選擇檔案")
            return
        if self.is_transcribing:
            return
        
        self.is_transcribing = True
        self._max_progress = 0  # 追蹤最大進度，防止倒退
        self.start_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.file_btn.configure(state="disabled")
        self.progress.set(0)
        self.status.configure(text="處理中...")
        
        threading.Thread(target=self._transcribe, daemon=True).start()
    
    def _transcribe(self):
        try:
            if not self.model_downloader.is_model_available():
                self._set_status(0.05, "下載模型中...")
                self.model_downloader.download_model(
                    progress_callback=lambda p: self._set_status(p * 0.3, f"下載 {int(p*100)}%")
                )
            
            self._set_status(0.30, "轉錄中，請稍候...")
            
            result = self.transcription_core.transcribe(
                input_file=self.selected_file,
                language=self.language_var.get(),
                output_srt=self.output_srt.get(),
                output_txt=self.output_txt.get(),
                output_vtt=False,
                convert_traditional=self.convert_traditional.get(),
                # 音訊轉換部分已經沒有進度回報，所以從 0.1 開始轉錄
                progress_callback=lambda p: self._set_status(0.1 + p * 0.9, f"轉錄中 {int((0.1+p*0.9)*100)}%")
            )
            
            if result.success:
                self._set_status(1.0, "完成！")
                self.after(100, lambda: self._done(result.output_file))
            else:
                self._set_status(0, f"錯誤：{result.error_message}")
        except Exception as e:
            self._set_status(0, f"錯誤：{e}")
        finally:
            self.is_transcribing = False
            self.after(100, self._reset)
    
    def _set_status(self, p, t):
        # 進度只能前進，不能倒退（除非是錯誤重置到0）
        if p > 0 and hasattr(self, '_max_progress'):
            if p < self._max_progress:
                return  # 忽略較小的進度值
            self._max_progress = p
        self.after(0, lambda: self.progress.set(p))
        self.after(0, lambda: self.status.configure(text=t))
    
    def _done(self, path):
        from tkinter import messagebox
        messagebox.showinfo("完成", f"輸出：\n{path}")
    
    def _reset(self):
        self.start_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")
        self.file_btn.configure(state="normal")
    
    def _cancel(self):
        if self.is_transcribing:
            self.transcription_core.cancel()
            self.is_transcribing = False
            self.status.configure(text="已取消")
            self._reset()


if __name__ == "__main__":
    VoiceTranscriberApp().mainloop()
