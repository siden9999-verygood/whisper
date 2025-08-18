"""
轉錄管理器模組
處理語音轉錄功能，整合 Whisper.cpp 和相關工具
"""

import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum

from platform_adapter import platform_adapter, file_manager, CrossPlatformError
from config_service import config_service
from logging_service import logging_service, TaskLogger


class TranscriptionStatus(Enum):
    """轉錄狀態枚舉"""
    PENDING = "pending"
    PREPARING = "preparing"
    TRANSCRIBING = "transcribing"
    POST_PROCESSING = "post_processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TranscriptionOptions:
    """轉錄選項配置"""
    model: str = "ggml-medium.bin"
    language: str = "zh"
    threads: int = 4
    temperature: float = 0.0
    translate_to_english: bool = False
    
    # 輸出格式
    output_srt: bool = True
    output_txt: bool = False
    output_vtt: bool = False
    output_lrc: bool = False
    output_csv: bool = False
    output_json: bool = False
    output_json_full: bool = False
    
    # 後處理選項
    enable_segmentation: bool = False
    remove_punctuation: bool = False
    convert_to_traditional_chinese: bool = False
    
    # 進階選項
    prompt: str = ""
    max_len: int = 0
    word_thold: float = 0.01
    entropy_thold: float = 2.40
    logprob_thold: float = -1.00


@dataclass
class TranscriptionResult:
    """轉錄結果"""
    task_id: str
    status: TranscriptionStatus
    input_file: str
    output_files: List[str]
    transcription_text: str
    execution_time: float
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class TranscriptionTask:
    """轉錄任務類別"""
    
    def __init__(self, task_id: str, input_file: str, output_dir: str, 
                 options: TranscriptionOptions):
        self.task_id = task_id
        self.input_file = input_file
        self.output_dir = output_dir
        self.options = options
        self.status = TranscriptionStatus.PENDING
        self.progress = 0.0
        self.start_time = None
        self.end_time = None
        self.result = None
        self.error_message = None
        self.logger = None
    
    def get_duration(self) -> float:
        """取得任務執行時間"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        elif self.start_time:
            return time.time() - self.start_time
        return 0.0


@dataclass
class BatchTranscriptionTask:
    """批次轉錄任務"""
    batch_task_id: str
    sub_task_ids: List[str]
    total_files: int
    input_files: List[str]
    status: TranscriptionStatus = TranscriptionStatus.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    completed_tasks: List[str] = None
    failed_tasks: List[str] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.completed_tasks is None:
            self.completed_tasks = []
        if self.failed_tasks is None:
            self.failed_tasks = []
    
    def get_duration(self) -> float:
        """取得批次任務執行時間"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        elif self.start_time:
            return time.time() - self.start_time
        return 0.0
    
    def get_progress(self) -> float:
        """取得批次任務進度"""
        if self.total_files == 0:
            return 0.0
        completed_count = len(self.completed_tasks) + len(self.failed_tasks)
        return (completed_count / self.total_files) * 100


class TranscriptionManager:
    """轉錄管理器"""
    
    # 支援的音頻格式
    SUPPORTED_AUDIO_FORMATS = {
        '.wav', '.mp3', '.m4a', '.flac', '.ogg', '.aac'
    }
    
    # 支援的影片格式
    SUPPORTED_VIDEO_FORMATS = {
        '.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv'
    }
    
    # 可用模型
    AVAILABLE_MODELS = {
        "Tiny": "ggml-tiny.bin",
        "Tiny (English)": "ggml-tiny.en.bin",
        "Base": "ggml-base.bin",
        "Base (English)": "ggml-base.en.bin",
        "Small": "ggml-small.bin",
        "Small (English)": "ggml-small.en.bin",
        "Medium": "ggml-medium.bin",
        "Medium (English)": "ggml-medium.en.bin",
        "Large-v2": "ggml-large-v2.bin",
        "Large-v3": "ggml-large-v3.bin",
        "Large-v3-Turbo": "ggml-large-v3-turbo.bin"
    }
    
    def __init__(self):
        self.config = config_service.get_config()
        self.logger = logging_service.get_logger("TranscriptionManager")
        
        # 路徑設定
        self.whisper_resources_path = config_service.get_whisper_resources_path()
        self.whisper_main_path = config_service.get_whisper_main_path()
        self.ffmpeg_path = config_service.get_ffmpeg_path()
        
        # 任務管理
        self.active_tasks: Dict[str, TranscriptionTask] = {}
        self.batch_tasks: Dict[str, BatchTranscriptionTask] = {}
        self.task_counter = 0
        
        # 初始化檢查
        self._validate_dependencies()
    
    def _validate_dependencies(self) -> None:
        """驗證相依性"""
        missing_deps = config_service.get_missing_dependencies()
        if missing_deps:
            self.logger.warning(f"缺少相依性: {', '.join(missing_deps)}")
        
        # 檢查模型檔案
        available_models = self.get_available_models()
        if not available_models:
            self.logger.warning("未找到任何 Whisper 模型檔案")
    
    def get_available_models(self) -> List[str]:
        """取得可用的模型清單"""
        available = []
        models_path = self.whisper_resources_path
        
        for model_name, model_file in self.AVAILABLE_MODELS.items():
            model_path = models_path / model_file
            if model_path.exists():
                available.append(model_name)
        
        return available
    
    def is_supported_format(self, file_path: str) -> bool:
        """檢查檔案格式是否支援"""
        suffix = Path(file_path).suffix.lower()
        return (suffix in self.SUPPORTED_AUDIO_FORMATS or 
                suffix in self.SUPPORTED_VIDEO_FORMATS)
    
    def create_transcription_task(self, input_file: str, output_dir: str = None,
                                options: TranscriptionOptions = None) -> str:
        """建立轉錄任務"""
        # 驗證輸入檔案
        if not Path(input_file).exists():
            raise TranscriptionError(f"輸入檔案不存在: {input_file}")
        
        if not self.is_supported_format(input_file):
            raise TranscriptionError(f"不支援的檔案格式: {input_file}")
        
        # 設定輸出目錄
        if output_dir is None:
            output_dir = str(Path(input_file).parent)
        
        # 設定預設選項
        if options is None:
            options = TranscriptionOptions()
        
        # 建立任務
        self.task_counter += 1
        task_id = f"transcription_{self.task_counter}_{int(time.time())}"
        
        task = TranscriptionTask(task_id, input_file, output_dir, options)
        self.active_tasks[task_id] = task
        
        self.logger.info(f"建立轉錄任務: {task_id}")
        return task_id
    
    def start_transcription(self, task_id: str, 
                          progress_callback: Optional[Callable] = None) -> None:
        """開始轉錄任務"""
        if task_id not in self.active_tasks:
            raise TranscriptionError(f"找不到任務: {task_id}")
        
        task = self.active_tasks[task_id]
        
        # 在背景執行緒中執行轉錄
        thread = threading.Thread(
            target=self._execute_transcription,
            args=(task, progress_callback)
        )
        thread.daemon = True
        thread.start()
    
    def _execute_transcription(self, task: TranscriptionTask, 
                             progress_callback: Optional[Callable] = None) -> None:
        """執行轉錄任務"""
        task.logger = TaskLogger(f"Transcription_{task.task_id}", logging_service)
        task.start_time = time.time()
        
        try:
            # 更新狀態
            task.status = TranscriptionStatus.PREPARING
            if progress_callback:
                progress_callback(task.task_id, 10, "準備轉錄")
            
            # 準備音頻檔案
            audio_file = self._prepare_audio_file(task)
            
            # 執行轉錄
            task.status = TranscriptionStatus.TRANSCRIBING
            if progress_callback:
                progress_callback(task.task_id, 30, "執行轉錄")
            
            transcription_result = self._run_whisper(task, audio_file)
            
            # 後處理
            task.status = TranscriptionStatus.POST_PROCESSING
            if progress_callback:
                progress_callback(task.task_id, 80, "後處理")
            
            output_files = self._post_process_results(task, transcription_result)
            
            # 完成
            task.status = TranscriptionStatus.COMPLETED
            task.end_time = time.time()
            
            task.result = TranscriptionResult(
                task_id=task.task_id,
                status=task.status,
                input_file=task.input_file,
                output_files=output_files,
                transcription_text=transcription_result,
                execution_time=task.get_duration()
            )
            
            if progress_callback:
                progress_callback(task.task_id, 100, "轉錄完成")
            
            task.logger.log_completion(True, f"轉錄完成，輸出檔案: {len(output_files)} 個")
            
        except Exception as e:
            task.status = TranscriptionStatus.FAILED
            task.end_time = time.time()
            task.error_message = str(e)
            
            task.result = TranscriptionResult(
                task_id=task.task_id,
                status=task.status,
                input_file=task.input_file,
                output_files=[],
                transcription_text="",
                execution_time=task.get_duration(),
                error_message=task.error_message
            )
            
            if progress_callback:
                progress_callback(task.task_id, -1, f"轉錄失敗: {str(e)}")
            
            task.logger.log_error(f"轉錄失敗: {str(e)}", e)
    
    def _prepare_audio_file(self, task: TranscriptionTask) -> str:
        """準備音頻檔案"""
        input_path = Path(task.input_file)
        
        # 如果是影片檔案或需要轉換格式，使用 FFmpeg
        if (input_path.suffix.lower() in self.SUPPORTED_VIDEO_FORMATS or
            input_path.suffix.lower() != '.wav'):
            
            task.logger.log_step("音頻轉換", f"轉換 {input_path.name} 為 WAV 格式")
            
            # 建立臨時 WAV 檔案
            temp_wav = platform_adapter.get_temp_dir() / f"{task.task_id}.wav"
            
            # 使用 FFmpeg 轉換
            self._convert_to_wav(str(input_path), str(temp_wav))
            
            return str(temp_wav)
        
        return task.input_file
    
    def _convert_to_wav(self, input_file: str, output_file: str) -> None:
        """使用 FFmpeg 轉換音頻格式"""
        if not self.ffmpeg_path.exists():
            raise TranscriptionError("FFmpeg 執行檔不存在")
        
        command = [
            str(self.ffmpeg_path),
            "-i", input_file,
            "-ar", "16000",  # 16kHz 採樣率
            "-ac", "1",      # 單聲道
            "-c:a", "pcm_s16le",  # 16-bit PCM
            "-y",            # 覆蓋輸出檔案
            output_file
        ]
        
        try:
            result = platform_adapter.run_command(command)
            if result.returncode != 0:
                raise TranscriptionError(f"FFmpeg 轉換失敗: {result.stderr}")
        except Exception as e:
            raise TranscriptionError(f"音頻轉換失敗: {str(e)}") from e
    
    def _run_whisper(self, task: TranscriptionTask, audio_file: str) -> str:
        """執行 Whisper 轉錄"""
        if not self.whisper_main_path.exists():
            raise TranscriptionError("Whisper 主程式不存在")
        
        # 建立命令
        command = [str(self.whisper_main_path)]
        
        # 基本參數
        command.extend(["-f", audio_file])
        command.extend(["-m", str(self.whisper_resources_path / task.options.model)])
        command.extend(["-l", task.options.language])
        command.extend(["-t", str(task.options.threads)])
        command.extend(["--temperature", str(task.options.temperature)])
        
        # 輸出格式
        output_base = str(Path(task.output_dir) / Path(task.input_file).stem)
        command.extend(["-of", output_base])
        
        if task.options.output_srt:
            command.append("--output-srt")
        if task.options.output_txt:
            command.append("--output-txt")
        if task.options.output_vtt:
            command.append("--output-vtt")
        if task.options.output_lrc:
            command.append("--output-lrc")
        if task.options.output_csv:
            command.append("--output-csv")
        if task.options.output_json:
            command.append("--output-json")
        if task.options.output_json_full:
            command.append("--output-json-full")
        
        # 其他選項
        if task.options.translate_to_english:
            command.append("--translate")
        
        if task.options.prompt:
            command.extend(["--prompt", task.options.prompt])
        
        if task.options.max_len > 0:
            command.extend(["-ml", str(task.options.max_len)])
        
        task.logger.log_step("執行 Whisper", f"命令: {' '.join(command)}")
        
        try:
            # 設定較長的超時時間（1小時）
            result = platform_adapter.run_command(command, timeout=3600)
            if result.returncode != 0:
                error_msg = result.stderr if result.stderr else "未知錯誤"
                raise TranscriptionError(f"Whisper 執行失敗: {error_msg}")
            
            return result.stdout
            
        except Exception as e:
            raise TranscriptionError(f"轉錄執行失敗: {str(e)}") from e
    
    def _post_process_results(self, task: TranscriptionTask, 
                            transcription_result: str) -> List[str]:
        """後處理轉錄結果"""
        output_files = []
        base_name = Path(task.input_file).stem
        
        # 尋找生成的輸出檔案
        output_dir = Path(task.output_dir)
        for file_path in output_dir.glob(f"{base_name}.*"):
            if file_path.suffix in ['.srt', '.txt', '.vtt', '.lrc', '.csv', '.json']:
                output_files.append(str(file_path))
        
        # 應用後處理選項
        if (task.options.convert_to_traditional_chinese or 
            task.options.remove_punctuation or 
            task.options.enable_segmentation):
            
            self._apply_post_processing(task, output_files)
        
        return output_files
    
    def _apply_post_processing(self, task: TranscriptionTask, 
                             output_files: List[str]) -> None:
        """應用後處理選項"""
        task.logger.log_step("後處理", "應用文字處理選項")
        
        for file_path in output_files:
            if Path(file_path).suffix in ['.srt', '.txt', '.vtt']:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 繁體中文轉換
                    if task.options.convert_to_traditional_chinese:
                        content = self._convert_to_traditional_chinese(content)
                    
                    # 移除標點符號
                    if task.options.remove_punctuation:
                        content = self._remove_punctuation(content)
                    
                    # 智能斷句
                    if task.options.enable_segmentation:
                        content = self._apply_segmentation(content)
                    
                    # 寫回檔案
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                        
                except Exception as e:
                    task.logger.log_error(f"後處理檔案 {file_path} 失敗: {str(e)}")
    
    def _convert_to_traditional_chinese(self, text: str) -> str:
        """轉換為繁體中文"""
        try:
            import opencc
            converter = opencc.OpenCC('s2t')
            return converter.convert(text)
        except ImportError:
            self.logger.warning("OpenCC 未安裝，跳過繁體中文轉換")
            return text
        except Exception as e:
            self.logger.error(f"繁體中文轉換失敗: {str(e)}")
            return text
    
    def _remove_punctuation(self, text: str) -> str:
        """移除標點符號"""
        import string
        import re
        
        # 移除英文標點符號
        text = text.translate(str.maketrans('', '', string.punctuation))
        
        # 移除中文標點符號
        chinese_punctuation = '，。！？；：「」『』（）【】《》〈〉'
        text = re.sub(f'[{chinese_punctuation}]', '', text)
        
        return text
    
    def _apply_segmentation(self, text: str) -> str:
        """應用智能斷句"""
        # 這裡可以實現更複雜的斷句邏輯
        # 目前只是簡單的處理
        import re
        
        # 在句號、問號、驚嘆號後添加換行
        text = re.sub(r'([。！？])', r'\1\n', text)
        
        # 移除多餘的空行
        text = re.sub(r'\n+', '\n', text)
        
        return text.strip()
    
    def get_task_status(self, task_id: str) -> Optional[TranscriptionTask]:
        """取得任務狀態"""
        return self.active_tasks.get(task_id)
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任務"""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            if task.status in [TranscriptionStatus.PENDING, 
                             TranscriptionStatus.PREPARING]:
                task.status = TranscriptionStatus.CANCELLED
                return True
        return False
    
    def cleanup_completed_tasks(self) -> None:
        """清理已完成的任務"""
        completed_tasks = [
            task_id for task_id, task in self.active_tasks.items()
            if task.status in [TranscriptionStatus.COMPLETED, 
                             TranscriptionStatus.FAILED,
                             TranscriptionStatus.CANCELLED]
        ]
        
        for task_id in completed_tasks:
            del self.active_tasks[task_id]
        
        self.logger.info(f"清理了 {len(completed_tasks)} 個已完成的任務")
    
    def create_batch_transcription_task(self, input_files: List[str], 
                                      output_dir: str = None,
                                      options: TranscriptionOptions = None) -> str:
        """建立批次轉錄任務"""
        # 驗證輸入檔案
        valid_files = []
        for file_path in input_files:
            if Path(file_path).exists() and self.is_supported_format(file_path):
                valid_files.append(file_path)
            else:
                self.logger.warning(f"跳過無效檔案: {file_path}")
        
        if not valid_files:
            raise TranscriptionError("沒有有效的輸入檔案")
        
        # 建立批次任務
        self.task_counter += 1
        batch_task_id = f"batch_transcription_{self.task_counter}_{int(time.time())}"
        
        # 為每個檔案建立子任務
        sub_task_ids = []
        for file_path in valid_files:
            sub_task_id = self.create_transcription_task(file_path, output_dir, options)
            sub_task_ids.append(sub_task_id)
        
        # 建立批次任務記錄
        batch_task = BatchTranscriptionTask(
            batch_task_id=batch_task_id,
            sub_task_ids=sub_task_ids,
            total_files=len(valid_files),
            input_files=valid_files
        )
        
        self.batch_tasks[batch_task_id] = batch_task
        
        self.logger.info(f"建立批次轉錄任務: {batch_task_id} ({len(valid_files)} 個檔案)")
        return batch_task_id
    
    def start_batch_transcription(self, batch_task_id: str, 
                                progress_callback: Optional[Callable] = None) -> None:
        """開始批次轉錄任務"""
        if batch_task_id not in self.batch_tasks:
            raise TranscriptionError(f"找不到批次任務: {batch_task_id}")
        
        batch_task = self.batch_tasks[batch_task_id]
        batch_task.start_time = time.time()
        batch_task.status = TranscriptionStatus.PREPARING
        
        # 建立批次處理執行緒
        thread = threading.Thread(
            target=self._execute_batch_transcription,
            args=(batch_task, progress_callback)
        )
        thread.daemon = True
        thread.start()
    
    def _execute_batch_transcription(self, batch_task, progress_callback: Optional[Callable] = None):
        """執行批次轉錄任務"""
        try:
            batch_task.status = TranscriptionStatus.TRANSCRIBING
            
            # 並發執行子任務
            max_concurrent = min(3, len(batch_task.sub_task_ids))  # 最多3個並發
            active_tasks = []
            completed_count = 0
            
            def task_completed_callback(task_id, progress, message):
                nonlocal completed_count
                if progress == 100:
                    completed_count += 1
                    batch_progress = (completed_count / batch_task.total_files) * 100
                    
                    if progress_callback:
                        progress_callback(batch_task.batch_task_id, batch_progress, 
                                        f"已完成 {completed_count}/{batch_task.total_files} 個檔案")
            
            # 啟動子任務
            for i, sub_task_id in enumerate(batch_task.sub_task_ids):
                if len(active_tasks) >= max_concurrent:
                    # 等待一個任務完成
                    while len(active_tasks) >= max_concurrent:
                        time.sleep(1)
                        active_tasks = [tid for tid in active_tasks 
                                      if self.get_task_status(tid).status in [
                                          TranscriptionStatus.PENDING,
                                          TranscriptionStatus.PREPARING,
                                          TranscriptionStatus.TRANSCRIBING,
                                          TranscriptionStatus.POST_PROCESSING
                                      ]]
                
                self.start_transcription(sub_task_id, task_completed_callback)
                active_tasks.append(sub_task_id)
            
            # 等待所有任務完成
            while active_tasks:
                time.sleep(1)
                active_tasks = [tid for tid in active_tasks 
                              if self.get_task_status(tid).status in [
                                  TranscriptionStatus.PENDING,
                                  TranscriptionStatus.PREPARING,
                                  TranscriptionStatus.TRANSCRIBING,
                                  TranscriptionStatus.POST_PROCESSING
                              ]]
            
            # 收集結果
            batch_task.completed_tasks = []
            batch_task.failed_tasks = []
            
            for sub_task_id in batch_task.sub_task_ids:
                task = self.get_task_status(sub_task_id)
                if task.status == TranscriptionStatus.COMPLETED:
                    batch_task.completed_tasks.append(sub_task_id)
                else:
                    batch_task.failed_tasks.append(sub_task_id)
            
            batch_task.end_time = time.time()
            batch_task.status = TranscriptionStatus.COMPLETED
            
            if progress_callback:
                success_rate = len(batch_task.completed_tasks) / batch_task.total_files * 100
                progress_callback(batch_task.batch_task_id, 100, 
                                f"批次轉錄完成 (成功率: {success_rate:.1f}%)")
            
            self.logger.info(f"批次轉錄完成: {batch_task.batch_task_id}")
            
        except Exception as e:
            batch_task.status = TranscriptionStatus.FAILED
            batch_task.error_message = str(e)
            
            if progress_callback:
                progress_callback(batch_task.batch_task_id, -1, f"批次轉錄失敗: {str(e)}")
            
            self.logger.error(f"批次轉錄失敗: {str(e)}")
    
    def get_batch_task_status(self, batch_task_id: str) -> Optional['BatchTranscriptionTask']:
        """取得批次任務狀態"""
        return self.batch_tasks.get(batch_task_id)
    
    def get_transcription_preview(self, task_id: str, max_lines: int = 10) -> Optional[str]:
        """取得轉錄預覽（前幾行）"""
        task = self.get_task_status(task_id)
        if not task or not task.result:
            return None
        
        try:
            # 如果有SRT輸出檔案，讀取前幾行
            for output_file in task.result.output_files:
                if output_file.endswith('.srt'):
                    with open(output_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        preview_lines = lines[:max_lines * 4]  # SRT每個字幕4行
                        return ''.join(preview_lines)
            
            # 如果有TXT輸出檔案
            for output_file in task.result.output_files:
                if output_file.endswith('.txt'):
                    with open(output_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        preview_lines = lines[:max_lines]
                        return ''.join(preview_lines)
            
            # 使用轉錄文字
            if task.result.transcription_text:
                lines = task.result.transcription_text.split('\n')
                preview_lines = lines[:max_lines]
                return '\n'.join(preview_lines)
            
        except Exception as e:
            self.logger.error(f"取得轉錄預覽失敗: {str(e)}")
        
        return None
    
    def apply_ai_correction(self, task_id: str, api_key: str) -> bool:
        """對轉錄結果應用AI校正"""
        task = self.get_task_status(task_id)
        if not task or not task.result:
            return False
        
        try:
            # 找到SRT檔案
            srt_file = None
            for output_file in task.result.output_files:
                if output_file.endswith('.srt'):
                    srt_file = output_file
                    break
            
            if not srt_file:
                self.logger.warning("找不到SRT檔案進行AI校正")
                return False
            
            # 讀取SRT內容
            with open(srt_file, 'r', encoding='utf-8') as f:
                srt_content = f.read()
            
            # 使用Google Gemini進行校正
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            
            model = genai.GenerativeModel('gemini-1.5-pro-latest')
            
            prompt = f"""
請校正以下SRT字幕檔案的內容，修正語法錯誤、標點符號和用詞，但保持時間軸不變：

{srt_content}

請返回校正後的完整SRT內容。
"""
            
            response = model.generate_content(prompt)
            corrected_content = response.text.strip()
            
            # 儲存校正後的內容
            corrected_file = srt_file.replace('.srt', '_corrected.srt')
            with open(corrected_file, 'w', encoding='utf-8') as f:
                f.write(corrected_content)
            
            # 更新任務結果
            task.result.output_files.append(corrected_file)
            
            self.logger.info(f"AI校正完成: {corrected_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"AI校正失敗: {str(e)}")
            return False
    
    def convert_to_wav(self, input_file: str, output_file: str) -> bool:
        """將音訊檔案轉換為 WAV 格式"""
        try:
            self.logger.info(f"開始 WAV 轉換: {input_file} -> {output_file}")
            
            # 檢查 FFmpeg 是否可用
            if not self.ffmpeg_path.exists():
                self.logger.error("FFmpeg 不可用")
                return False
            
            # 構建 FFmpeg 命令
            command = [
                str(self.ffmpeg_path),
                "-i", input_file,
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                "-y",  # 覆蓋輸出檔案
                output_file
            ]
            
            # 執行轉換
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300  # 5分鐘超時
            )
            
            if result.returncode == 0:
                self.logger.info(f"WAV 轉換成功: {output_file}")
                return True
            else:
                self.logger.error(f"WAV 轉換失敗: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("WAV 轉換超時")
            return False
        except Exception as e:
            self.logger.error(f"WAV 轉換錯誤: {str(e)}")
            return False


# 自定義例外類別
class TranscriptionError(CrossPlatformError):
    """轉錄相關錯誤"""
    pass


# 全域轉錄管理器實例
transcription_manager = TranscriptionManager()


if __name__ == "__main__":
    # 測試程式
    print("=== 轉錄管理器測試 ===")
    
    print(f"可用模型: {transcription_manager.get_available_models()}")
    print(f"Whisper 路徑: {transcription_manager.whisper_main_path}")
    print(f"FFmpeg 路徑: {transcription_manager.ffmpeg_path}")
    
    # 測試檔案格式檢查
    test_files = ["test.wav", "test.mp3", "test.mp4", "test.txt"]
    for file in test_files:
        supported = transcription_manager.is_supported_format(file)
        print(f"{file}: {'支援' if supported else '不支援'}")