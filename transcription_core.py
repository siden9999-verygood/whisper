"""
轉錄核心模組
處理語音轉錄功能，整合 Whisper.cpp
"""

import os
import sys
import subprocess
import threading
import tempfile
from pathlib import Path
from typing import Dict, Optional, Callable, List
from dataclasses import dataclass

# OpenCC 用於簡繁轉換
try:
    import opencc
    OPENCC_AVAILABLE = True
except ImportError:
    OPENCC_AVAILABLE = False

# SRT 處理
try:
    import srt
    SRT_AVAILABLE = True
except ImportError:
    SRT_AVAILABLE = False


@dataclass
class TranscriptionResult:
    """轉錄結果"""
    success: bool
    output_file: str
    transcript_text: str
    error_message: Optional[str] = None


class TranscriptionCore:
    """語音轉錄核心"""
    
    # 支援的音訊格式
    SUPPORTED_AUDIO_FORMATS = {'.wav', '.mp3', '.m4a', '.flac', '.ogg', '.aac'}
    SUPPORTED_VIDEO_FORMATS = {'.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm'}
    
    def __init__(self):
        """初始化轉錄核心"""
        # 確定基礎路徑
        if getattr(sys, 'frozen', False):
            # PyInstaller 打包後
            # 打包的二進位檔案在 _MEIPASS
            if hasattr(sys, '_MEIPASS'):
                self.bundled_path = Path(sys._MEIPASS)
            else:
                self.bundled_path = Path(sys.executable).parent
            
            # 用戶數據（下載的模型）
            if sys.platform == "darwin":
                # macOS: 使用標準 Application Support 目錄
                self.user_resources_dir = Path.home() / "Library" / "Application Support" / "VoiceTranscriber"
            else:
                # Windows: 使用 exe 同目錄
                self.user_resources_dir = Path(sys.executable).parent / "whisper_resources"
        else:
            # 開發模式
            self.bundled_path = Path(__file__).parent
            self.user_resources_dir = Path(__file__).parent / "whisper_resources"
        
        # 打包的資源目錄（main, ffmpeg, DLLs）
        self.resources_dir = self.bundled_path / "whisper_resources"
        # 模型路徑
        self.model_path = self.user_resources_dir / "ggml-large-v2.bin"
        
        # 確定 whisper.cpp 執行檔路徑
        if sys.platform == "win32":
            self.whisper_executable = self.resources_dir / "main.exe"
            self.ffmpeg_executable = self.resources_dir / "ffmpeg.exe"
        else:
            self.whisper_executable = self.resources_dir / "main"
            self.ffmpeg_executable = self.resources_dir / "ffmpeg"
        
        # Debug: 顯示路徑資訊
        print(f"[DEBUG] 打包資源目錄: {self.resources_dir}")
        print(f"[DEBUG] 用戶資源目錄: {self.user_resources_dir}")
        print(f"[DEBUG] 模型路徑: {self.model_path} (存在: {self.model_path.exists()})")
        print(f"[DEBUG] Whisper執行檔: {self.whisper_executable} (存在: {self.whisper_executable.exists()})")
        print(f"[DEBUG] FFmpeg: {self.ffmpeg_executable} (存在: {self.ffmpeg_executable.exists()})")
        
        # 取消標記
        self._cancelled = False
        self._process: Optional[subprocess.Popen] = None
        
        # OpenCC 轉換器
        self._opencc_converter = None
        if OPENCC_AVAILABLE:
            try:
                self._opencc_converter = opencc.OpenCC('s2t')  # 簡體轉繁體
            except Exception:
                pass
    
    def transcribe(
        self,
        input_file: str,
        language: str = "zh",
        prompt: str = "",  # 自訂詞彙
        output_srt: bool = True,
        output_txt: bool = False,
        output_vtt: bool = False,
        convert_traditional: bool = True,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> TranscriptionResult:
        """
        執行轉錄
        
        Args:
            input_file: 輸入檔案路徑
            language: 語言代碼 (zh, en, ja, ko, auto)
            output_srt: 是否輸出 SRT 檔案
            output_txt: 是否輸出 TXT 檔案
            output_vtt: 是否輸出 VTT 檔案
            convert_traditional: 是否轉換為繁體中文
            progress_callback: 進度回調函數
            
        Returns:
            TranscriptionResult
        """
        self._cancelled = False
        input_path = Path(input_file)
        
        # 驗證輸入檔案
        if not input_path.exists():
            return TranscriptionResult(
                success=False,
                output_file="",
                transcript_text="",
                error_message=f"檔案不存在：{input_file}"
            )
        
        # 驗證模型
        if not self.model_path.exists():
            return TranscriptionResult(
                success=False,
                output_file="",
                transcript_text="",
                error_message="Whisper 模型未下載"
            )
        
        # 驗證 whisper 執行檔
        if not self.whisper_executable.exists():
            return TranscriptionResult(
                success=False,
                output_file="",
                transcript_text="",
                error_message=f"找不到 Whisper 執行檔：{self.whisper_executable}"
            )
        
        audio_file = None  # 初始化，供 finally 清理使用
        try:
            # 準備音訊檔案（如果是影片則提取音訊）
            # 不傳入 progress_callback 以免進度條亂跳 (例如從 40% 跳回 0%)
            audio_file = self._prepare_audio(input_path, None)
            
            if self._cancelled:
                return TranscriptionResult(
                    success=False,
                    output_file="",
                    transcript_text="",
                    error_message="已取消"
                )
            
            # 獲取媒體總時長（秒）
            total_duration = self._get_media_duration(input_path)
            print(f"[DEBUG] 媒體總時長: {total_duration} 秒")
            
            # 執行 Whisper 轉錄
            if progress_callback:
                progress_callback(0.0)  # 轉錄開始 (0%)
            
            transcript_text, output_file = self._run_whisper(
                audio_file,
                input_path,
                language,
                output_srt,
                output_txt,
                output_vtt,
                progress_callback,
                total_duration,  # 傳入總時長
                prompt  # 自訂詞彙
            )
            
            if self._cancelled:
                return TranscriptionResult(
                    success=False,
                    output_file="",
                    transcript_text="",
                    error_message="已取消"
                )
            
            # 簡繁轉換
            if convert_traditional and language in ["zh", "auto"]:
                transcript_text = self._convert_to_traditional(transcript_text)
                if output_file and Path(output_file).exists():
                    self._convert_file_to_traditional(output_file)
            
            if progress_callback:
                progress_callback(1.0)
            
            return TranscriptionResult(
                success=True,
                output_file=output_file,
                transcript_text=transcript_text
            )
            
        except Exception as e:
            return TranscriptionResult(
                success=False,
                output_file="",
                transcript_text="",
                error_message=str(e)
            )
        finally:
            # 清理暫存的 WAV 檔案
            if audio_file and audio_file != input_path:
                try:
                    if audio_file.exists():
                        audio_file.unlink()
                        print(f"[DEBUG] 已清理暫存檔: {audio_file}")
                except Exception:
                    pass  # 忽略清理失敗

    def _prepare_audio(
        self,
        input_path: Path,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> Path:
        """準備音訊檔案"""
        suffix = input_path.suffix.lower()
        
        # 如果是 WAV 16kHz，直接使用
        if suffix == '.wav':
            return input_path
        
        # 需要使用 FFmpeg 轉換
        if not self.ffmpeg_executable.exists():
            # 嘗試使用系統 FFmpeg
            import shutil
            system_ffmpeg = shutil.which('ffmpeg')
            if system_ffmpeg:
                self.ffmpeg_executable = Path(system_ffmpeg)
            else:
                raise RuntimeError("找不到 FFmpeg，無法處理此檔案格式")
        
        if progress_callback:
            progress_callback(0.1)
        
        # 轉換為 WAV 16kHz
        output_wav = input_path.with_suffix('.whisper.wav')
        
        cmd = [
            str(self.ffmpeg_executable),
            '-i', str(input_path),
            '-ar', '16000',
            '-ac', '1',
            '-c:a', 'pcm_s16le',
            '-y',
            str(output_wav)
        ]
        
        # Windows 隱藏終端機視窗
        kwargs = {}
        if sys.platform == "win32":
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=600,  # 10 分鐘超時
                **kwargs
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg 轉換失敗：{result.stderr}")
            
            if progress_callback:
                progress_callback(0.2)
            
            return output_wav
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("FFmpeg 轉換超時")

    def _get_media_duration(self, file_path: Path) -> float:
        """獲取媒體檔案的總時長（秒）"""
        # Windows 隱藏終端機視窗
        kwargs = {}
        if sys.platform == "win32":
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
        
        try:
            # 使用 ffmpeg -i 讀取資訊
            cmd = [str(self.ffmpeg_executable), '-i', str(file_path)]
            result = subprocess.run(cmd, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore', **kwargs)
            
            # 從輸出中尋找 Duration: 00:00:00.00
            import re
            match = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', result.stderr)
            if match:
                h, m, s = int(match.group(1)), int(match.group(2)), float(match.group(3))
                return h * 3600 + m * 60 + s
        except Exception as e:
            print(f"[ERROR] 無法獲取時長: {e}")
        
        return 3600.0  # 如果失敗，預設回退到 1 小時

    def _run_whisper(
        self,
        audio_file: Path,
        original_file: Path,
        language: str,
        output_srt: bool,
        output_txt: bool,
        output_vtt: bool,
        progress_callback: Optional[Callable[[float], None]] = None,
        total_duration: float = 3600.0,
        prompt: str = ""  # 自訂詞彙
    ) -> tuple:
        """執行 Whisper 轉錄"""
        # 建立輸出檔案路徑 (whisper.cpp 會自動加上副檔名)
        output_base = original_file.with_suffix('')
        
        # 建構命令 - whisper.cpp 使用短標誌格式
        cmd = [
            str(self.whisper_executable),
            '-m', str(self.model_path),      # 模型路徑
            '-l', language if language != "auto" else "auto",  # 語言
            '-t', '4',                        # 執行緒數
            '-of', str(output_base),          # 輸出檔案基礎名稱
        ]
        
        # 自訂詞彙
        if prompt and prompt.strip():
            # 逗號分隔轉換為空格分隔
            cleaned_prompt = ' '.join([w.strip() for w in prompt.split(',') if w.strip()])
            cmd.extend(['--prompt', cleaned_prompt])
        
        # 輸出格式標誌
        if output_srt:
            cmd.append('-osrt')
        if output_txt:
            cmd.append('-otxt')
        if output_vtt:
            cmd.append('-ovtt')
        
        # 音訊檔案放在最後
        cmd.extend(['-f', str(audio_file)])
        
        print(f"[DEBUG] 執行 Whisper 命令: {' '.join(cmd)}")
        
        # Windows 隱藏終端機視窗
        kwargs = {}
        if sys.platform == "win32":
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
        
        # 執行
        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # 合併 stderr 到 stdout
                text=True,
                encoding='utf-8',  # 明確指定 UTF-8 編碼
                errors='replace',  # 無法解碼時用替代字元
                bufsize=1,  # 行緩衝
                **kwargs
            )
            
            transcript_lines = []
            
            # 讀取輸出並解析進度
            for line in iter(self._process.stdout.readline, ''):
                if self._cancelled:
                    self._process.terminate()
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                # print(f"[WHISPER] {line}")  # 減少 Debug 輸出以免洗版
                transcript_lines.append(line)
                
                # 解析時間戳來估計進度 [00:00:00.000 --> 00:00:05.000]
                if '-->' in line and progress_callback and total_duration > 0:
                    try:
                        # 提取結束時間
                        import re
                        match = re.search(r'\[(\d+):(\d+):(\d+)', line)
                        if match:
                            h, m, s = int(match.group(1)), int(match.group(2)), int(match.group(3))
                            current_seconds = h * 3600 + m * 60 + s
                            
                            # 精確計算進度
                            progress = min(current_seconds / total_duration, 0.99)
                            progress_callback(progress)
                    except:
                        pass
                
                # 如果看到 whisper_print_timings，表示快完成了
                if 'whisper_print_timings' in line and progress_callback:
                    progress_callback(1.0)
            
            self._process.wait()
            
            if self._process.returncode != 0:
                raise RuntimeError(f"Whisper 返回錯誤碼：{self._process.returncode}")
            
            # 讀取輸出檔案
            transcript_text = ""
            output_file = ""
            
            srt_file = Path(str(output_base) + ".srt")
            txt_file = Path(str(output_base) + ".txt")
            
            if srt_file.exists():
                output_file = str(srt_file)
                transcript_text = srt_file.read_text(encoding='utf-8')
            elif txt_file.exists():
                output_file = str(txt_file)
                transcript_text = txt_file.read_text(encoding='utf-8')
            
            return transcript_text, output_file
            
        except subprocess.TimeoutExpired:
            if self._process:
                self._process.terminate()
            raise RuntimeError("Whisper 轉錄超時")
        
        finally:
            self._process = None
    
    def _convert_to_traditional(self, text: str) -> str:
        """將文字轉換為繁體中文"""
        if not self._opencc_converter or not text:
            return text
        
        try:
            return self._opencc_converter.convert(text)
        except Exception:
            return text
    
    def _convert_file_to_traditional(self, file_path: str):
        """將檔案內容轉換為繁體中文"""
        if not self._opencc_converter:
            return
        
        try:
            path = Path(file_path)
            content = path.read_text(encoding='utf-8')
            converted = self._opencc_converter.convert(content)
            path.write_text(converted, encoding='utf-8')
        except Exception:
            pass
    
    def cancel(self):
        """取消轉錄"""
        self._cancelled = True
        if self._process:
            self._process.terminate()
    
    def is_supported_format(self, file_path: str) -> bool:
        """檢查檔案格式是否支援"""
        suffix = Path(file_path).suffix.lower()
        return suffix in self.SUPPORTED_AUDIO_FORMATS or suffix in self.SUPPORTED_VIDEO_FORMATS


# 測試
if __name__ == "__main__":
    core = TranscriptionCore()
    
    print(f"Whisper 執行檔：{core.whisper_executable}")
    print(f"模型路徑：{core.model_path}")
    print(f"模型存在：{core.model_path.exists()}")
    print(f"Whisper 存在：{core.whisper_executable.exists()}")
