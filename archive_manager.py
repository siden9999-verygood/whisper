"""
歸檔管理器模組
處理媒體檔案的 AI 分析和自動歸檔功能
"""

import os
import json
import time
import shutil
import threading
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
# 嘗試導入 pandas，如果沒有則使用替代方案
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None

from platform_adapter import platform_adapter, file_manager, CrossPlatformError
from config_service import config_service
from logging_service import logging_service, TaskLogger


class ArchiveStatus(Enum):
    """歸檔狀態枚舉"""
    PENDING = "pending"
    ANALYZING = "analyzing"
    PROCESSING = "processing"
    ORGANIZING = "organizing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class MediaMetadata:
    """媒體元數據"""
    file_id: str
    suggested_title: str
    labels: List[str]
    description: str
    keywords: List[str]
    mood: str
    category: Dict[str, str]  # main_category, sub_category
    technical_analysis: Dict[str, Any]
    processing_date: str
    original_path: str
    new_path: str


@dataclass
class ArchiveOptions:
    """歸檔選項配置"""
    api_key: str
    ai_model: str = "gemini-1.5-pro-latest"
    source_folder: str = ""
    processed_folder: str = ""
    
    # 處理選項
    include_subdirectories: bool = True
    overwrite_existing: bool = False
    create_backup: bool = True
    
    # AI 分析選項
    max_retries: int = 3
    retry_delay: float = 5.0
    timeout: int = 300  # 5 minutes
    
    # 檔案組織選項
    organize_by_category: bool = True
    organize_by_date: bool = False
    preserve_original_name: bool = False


class ArchiveTask:
    """歸檔任務類別"""
    
    def __init__(self, task_id: str, options: ArchiveOptions):
        self.task_id = task_id
        self.options = options
        self.status = ArchiveStatus.PENDING
        self.progress = 0.0
        self.current_file = ""
        self.processed_count = 0
        self.total_count = 0
        self.start_time = None
        self.end_time = None
        self.results: List[MediaMetadata] = []
        self.errors: List[str] = []
        self.logger = None
        self.is_cancelled = False
    
    def get_duration(self) -> float:
        """取得任務執行時間"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        elif self.start_time:
            return time.time() - self.start_time
        return 0.0


class ArchiveManager:
    """歸檔管理器"""
    
    # 支援的媒體格式
    SUPPORTED_IMAGE_FORMATS = {
        '.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif', '.tiff', '.tif'
    }
    
    SUPPORTED_VIDEO_FORMATS = {
        '.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm'
    }
    
    SUPPORTED_AUDIO_FORMATS = {
        '.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac'
    }
    
    def __init__(self):
        self.config = config_service.get_config()
        self.logger = logging_service.get_logger("ArchiveManager")
        
        # AI 服務
        self.genai = None
        self._initialize_ai_service()
        
        # 任務管理
        self.active_tasks: Dict[str, ArchiveTask] = {}
        self.task_counter = 0
        
        # 檔案 ID 計數器
        self.current_id = 1
    
    def _initialize_ai_service(self) -> None:
        """初始化 AI 服務"""
        try:
            import google.generativeai as genai
            self.genai = genai
            
            if self.config.api_key and self.config.api_key != "請在此貼上您的 Google Cloud API 金鑰":
                genai.configure(api_key=self.config.api_key)
                self.logger.info("Google Gemini AI 服務已初始化")
            else:
                self.logger.warning("未設定 Google AI API 金鑰")
                
        except ImportError:
            self.logger.error("Google Generative AI 套件未安裝")
            self.genai = None
    
    def is_ai_available(self) -> bool:
        """檢查 AI 服務是否可用"""
        return (self.genai is not None and 
                self.config.api_key and 
                self.config.api_key != "請在此貼上您的 Google Cloud API 金鑰")
    
    def get_supported_formats(self) -> List[str]:
        """取得支援的檔案格式"""
        return list(self.SUPPORTED_IMAGE_FORMATS | 
                   self.SUPPORTED_VIDEO_FORMATS | 
                   self.SUPPORTED_AUDIO_FORMATS)
    
    def is_supported_format(self, file_path: str) -> bool:
        """檢查檔案格式是否支援"""
        suffix = Path(file_path).suffix.lower()
        return (suffix in self.SUPPORTED_IMAGE_FORMATS or
                suffix in self.SUPPORTED_VIDEO_FORMATS or
                suffix in self.SUPPORTED_AUDIO_FORMATS)
    
    def get_file_type(self, file_path: str) -> Optional[str]:
        """取得檔案類型"""
        suffix = Path(file_path).suffix.lower()
        
        if suffix in self.SUPPORTED_IMAGE_FORMATS:
            return "圖片"
        elif suffix in self.SUPPORTED_VIDEO_FORMATS:
            return "影片"
        elif suffix in self.SUPPORTED_AUDIO_FORMATS:
            return "音訊"
        
        return None
    
    def create_archive_task(self, options: ArchiveOptions) -> str:
        """建立歸檔任務"""
        # 驗證選項
        if not options.source_folder or not Path(options.source_folder).exists():
            raise ArchiveError("來源資料夾不存在或未指定")
        
        if not options.processed_folder:
            raise ArchiveError("目標資料夾未指定")
        
        if not self.is_ai_available():
            raise ArchiveError("AI 服務不可用，請檢查 API 金鑰設定")
        
        # 建立目標資料夾
        Path(options.processed_folder).mkdir(parents=True, exist_ok=True)
        
        # 建立任務
        self.task_counter += 1
        task_id = f"archive_{self.task_counter}_{int(time.time())}"
        
        task = ArchiveTask(task_id, options)
        self.active_tasks[task_id] = task
        
        self.logger.info(f"建立歸檔任務: {task_id}")
        return task_id
    
    def start_archive_task(self, task_id: str, 
                          progress_callback: Optional[Callable] = None) -> None:
        """開始歸檔任務"""
        if task_id not in self.active_tasks:
            raise ArchiveError(f"找不到任務: {task_id}")
        
        task = self.active_tasks[task_id]
        
        # 在背景執行緒中執行歸檔
        thread = threading.Thread(
            target=self._execute_archive_task,
            args=(task, progress_callback)
        )
        thread.daemon = True
        thread.start()
    
    def _execute_archive_task(self, task: ArchiveTask, 
                            progress_callback: Optional[Callable] = None) -> None:
        """執行歸檔任務"""
        task.logger = TaskLogger(f"Archive_{task.task_id}", logging_service)
        task.start_time = time.time()
        
        try:
            # 初始化檔案 ID
            self._initialize_file_id(task)
            
            # 掃描檔案
            task.status = ArchiveStatus.ANALYZING
            if progress_callback:
                progress_callback(task.task_id, 5, "掃描檔案")
            
            files_to_process = self._scan_files(task)
            task.total_count = len(files_to_process)
            
            if task.total_count == 0:
                task.logger.log_completion(True, "沒有找到需要處理的檔案")
                task.status = ArchiveStatus.COMPLETED
                return
            
            task.logger.log_step("檔案掃描", f"找到 {task.total_count} 個檔案需要處理")
            
            # 處理檔案
            task.status = ArchiveStatus.PROCESSING
            
            for i, file_path in enumerate(files_to_process):
                if task.is_cancelled:
                    task.status = ArchiveStatus.CANCELLED
                    break
                
                task.current_file = str(file_path)
                progress = 10 + (i / task.total_count) * 80
                
                if progress_callback:
                    progress_callback(task.task_id, progress, 
                                    f"處理 {file_path.name}")
                
                try:
                    metadata = self._process_single_file(task, file_path)
                    if metadata:
                        task.results.append(metadata)
                        task.processed_count += 1
                        
                except Exception as e:
                    error_msg = f"處理檔案 {file_path.name} 失敗: {str(e)}"
                    task.errors.append(error_msg)
                    task.logger.log_error(error_msg, e)
            
            # 組織檔案
            if not task.is_cancelled and task.results:
                task.status = ArchiveStatus.ORGANIZING
                if progress_callback:
                    progress_callback(task.task_id, 90, "整理檔案")
                
                self._organize_files(task)
            
            # 生成報告
            if not task.is_cancelled:
                self._generate_report(task)
                task.status = ArchiveStatus.COMPLETED
                
                if progress_callback:
                    progress_callback(task.task_id, 100, "歸檔完成")
                
                task.logger.log_completion(
                    True, 
                    f"成功處理 {task.processed_count} 個檔案，錯誤 {len(task.errors)} 個"
                )
            
        except Exception as e:
            task.status = ArchiveStatus.FAILED
            error_msg = f"歸檔任務失敗: {str(e)}"
            task.errors.append(error_msg)
            
            if progress_callback:
                progress_callback(task.task_id, -1, error_msg)
            
            task.logger.log_error(error_msg, e)
        
        finally:
            task.end_time = time.time()
    
    def _initialize_file_id(self, task: ArchiveTask) -> None:
        """初始化檔案 ID 計數器"""
        csv_path = Path(task.options.processed_folder) / "媒體入庫資訊.csv"
        
        if csv_path.exists():
            try:
                if HAS_PANDAS:
                    # 使用 pandas 讀取
                    df = pd.read_csv(csv_path, dtype={"檔案ID": str})
                    if not df.empty and "檔案ID" in df.columns:
                        # 提取數字 ID
                        numeric_ids = pd.to_numeric(
                            df["檔案ID"].str.extract(r"(\d+)")[0], 
                            errors="coerce"
                        ).dropna()
                        
                        if not numeric_ids.empty:
                            self.current_id = int(numeric_ids.max()) + 1
                else:
                    # 使用 csv 模組讀取
                    import csv
                    import re
                    max_id = 0
                    
                    with open(csv_path, 'r', encoding='utf-8-sig') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            file_id = row.get('檔案ID', '')
                            match = re.search(r'(\d+)', file_id)
                            if match:
                                current_id = int(match.group(1))
                                max_id = max(max_id, current_id)
                    
                    if max_id > 0:
                        self.current_id = max_id + 1
                
                task.logger.log_step("ID 初始化", f"檔案 ID 從 {self.current_id} 開始")
                
            except Exception as e:
                task.logger.log_error(f"讀取現有 ID 失敗: {str(e)}")
                self.current_id = 1
        else:
            self.current_id = 1
    
    def _scan_files(self, task: ArchiveTask) -> List[Path]:
        """掃描需要處理的檔案"""
        source_path = Path(task.options.source_folder)
        files_to_process = []
        
        if task.options.include_subdirectories:
            pattern = "**/*.*"
        else:
            pattern = "*.*"
        
        for file_path in source_path.glob(pattern):
            if (file_path.is_file() and 
                self.is_supported_format(str(file_path)) and
                not file_path.name.startswith("._")):  # 跳過 macOS 隱藏檔
                
                files_to_process.append(file_path)
        
        return files_to_process
    
    def _process_single_file(self, task: ArchiveTask, file_path: Path) -> Optional[MediaMetadata]:
        """處理單個檔案"""
        task.logger.log_step("檔案處理", f"分析 {file_path.name}")
        
        file_type = self.get_file_type(str(file_path))
        if not file_type:
            return None
        
        # AI 分析
        analysis_result = self._analyze_media_file(task, file_path, file_type)
        if not analysis_result:
            return None
        
        # 生成元數據
        metadata = self._generate_metadata(task, file_path, file_type, analysis_result)
        
        return metadata
    
    def _analyze_media_file(self, task: ArchiveTask, file_path: Path, 
                          file_type: str) -> Optional[Dict]:
        """使用 AI 分析媒體檔案"""
        try:
            model = self.genai.GenerativeModel(task.options.ai_model)
            
            # 準備媒體檔案
            if file_type == "圖片":
                from PIL import Image
                media_file = Image.open(file_path)
            else:
                # 上傳檔案到 Google AI
                task.logger.log_step("檔案上傳", f"上傳 {file_type} 檔案")
                media_file = self.genai.upload_file(path=str(file_path))
                
                # 等待處理完成
                while media_file.state.name == "PROCESSING":
                    time.sleep(2)
                    media_file = self.genai.get_file(media_file.name)
                
                if media_file.state.name == "FAILED":
                    raise ArchiveError(f"Google AI 處理 {file_type} 失敗")
            
            # 生成分析提示
            prompt = self._get_analysis_prompt(file_type)
            
            # 執行分析
            response = model.generate_content([prompt, media_file])
            
            # 解析結果
            result_text = response.text.strip()
            
            # 清理 JSON 格式
            import re
            result_text = re.sub(r'^```json\s*|```\s*$', '', result_text, flags=re.MULTILINE)
            
            return json.loads(result_text)
            
        except Exception as e:
            task.logger.log_error(f"AI 分析失敗: {str(e)}")
            return None
    
    def _get_analysis_prompt(self, file_type: str) -> str:
        """取得 AI 分析提示"""
        base_prompt = f"""
        你是一位精通 IPTC 元數據標準與創意分析的資深數位資產管理專家。
        請分析這個{file_type}並生成精確、豐富的元數據。
        
        請完成以下任務並嚴格依照 JSON 格式回傳：
        1. suggested_title: 一個簡潔、引人注目的繁體中文標題
        2. labels: 最多 15 個具體的繁體中文標籤 (由廣至細)
        3. description: 一段約 40-60 字的繁體中文描述
        4. keywords: 3-5 個最核心的繁體中文關鍵字
        5. mood: 從 [快樂, 溫馨, 悲傷, 寧靜, 懷舊, 緊張, 史詩感, 神秘, 浪漫, 其他] 中選擇一個
        """
        
        if file_type in ["圖片", "影片"]:
            technical_prompt = """
        6. technical_analysis:
            * shot_type: 從 [特寫, 中景, 全景, 遠景, 鳥瞰, 低角度, 其他] 中選擇
            * composition_style: 從 [三分法, 引導線, 對稱, 框架構圖, 其他] 中選擇
            * lighting_style: 從 [自然光, 攝影棚光, 輪廓光, 柔光, 硬光, 其他] 中選擇
            """
        elif file_type == "音訊":
            technical_prompt = """
        6. technical_analysis:
            * music_genre: 從 [古典, 爵士, 搖滾, 流行, 電子, 其他] 中選擇
            * instrumentation: 列出 1-3 種最主要的樂器
            * vocal_style: 從 [男聲, 女聲, 童聲, 合唱, 旁白, 無人聲, 其他] 中選擇
            """
        else:
            technical_prompt = ""
        
        category_prompt = """
        7. category: 選擇最適合的主分類和子分類
            * main_category: 從 [人物, 自然, 動物, 地點, 物件, 事件, 藝術與記錄, 其他] 中選擇
            * sub_category: 根據主分類提供具體的子分類
        """
        
        return base_prompt + technical_prompt + category_prompt
    
    def _generate_metadata(self, task: ArchiveTask, file_path: Path, 
                         file_type: str, analysis_result: Dict) -> MediaMetadata:
        """生成媒體元數據"""
        # 生成檔案 ID
        formatted_id = f"{self.current_id:06d}"
        
        # 生成新檔案名稱
        category_data = analysis_result.get('category', {})
        main_category = category_data.get('main_category', '其他')
        sub_category = category_data.get('sub_category', '未分類')
        keywords = analysis_result.get('keywords', [])
        
        # 清理關鍵字用於檔案名稱
        sanitized_keywords = []
        for keyword in keywords[:2]:  # 只取前兩個關鍵字
            sanitized = keyword.replace('/', '_').replace('\\', '_')
            sanitized = ''.join(c for c in sanitized if c.isalnum() or c in ['_', '-'])
            if sanitized:
                sanitized_keywords.append(sanitized)
        
        time_stamp = datetime.now().strftime('%H%M%S')
        
        if file_type == "音訊":
            # 音訊檔案保留原始檔名
            original_stem = file_path.stem
            new_filename = f"{original_stem}_{formatted_id}-{main_category}_{sub_category}_{'_'.join(sanitized_keywords)}_{time_stamp}{file_path.suffix}"
        else:
            new_filename = f"{formatted_id}-{main_category}_{sub_category}_{'_'.join(sanitized_keywords)}_{time_stamp}{file_path.suffix}"
        
        # 建立目標路徑
        target_dir = Path(task.options.processed_folder) / file_type / main_category / sub_category
        target_path = target_dir / new_filename
        
        # 建立元數據
        metadata = MediaMetadata(
            file_id=formatted_id,
            suggested_title=analysis_result.get('suggested_title', ''),
            labels=analysis_result.get('labels', []),
            description=analysis_result.get('description', ''),
            keywords=keywords,
            mood=analysis_result.get('mood', '無'),
            category=category_data,
            technical_analysis=analysis_result.get('technical_analysis', {}),
            processing_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            original_path=str(file_path.absolute()),
            new_path=str(target_path.absolute())
        )
        
        self.current_id += 1
        return metadata
    
    def _organize_files(self, task: ArchiveTask) -> None:
        """組織檔案到目標位置"""
        task.logger.log_step("檔案組織", f"移動 {len(task.results)} 個檔案")
        
        for metadata in task.results:
            try:
                source_path = Path(metadata.original_path)
                target_path = Path(metadata.new_path)
                
                # 建立目標目錄
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 移動檔案
                if task.options.create_backup:
                    # 複製而非移動
                    shutil.copy2(source_path, target_path)
                else:
                    shutil.move(str(source_path), str(target_path))
                
                task.logger.log_step("檔案移動", f"{source_path.name} -> {target_path.name}")
                
            except Exception as e:
                error_msg = f"移動檔案失敗 {metadata.original_path}: {str(e)}"
                task.errors.append(error_msg)
                task.logger.log_error(error_msg)
    
    def _generate_report(self, task: ArchiveTask) -> None:
        """生成歸檔報告"""
        csv_path = Path(task.options.processed_folder) / "媒體入庫資訊.csv"
        
        # 準備資料
        report_data = []
        for metadata in task.results:
            tech_analysis_str = json.dumps(metadata.technical_analysis, ensure_ascii=False)
            
            row_data = {
                '檔案ID': metadata.file_id,
                '檔案名稱': Path(metadata.new_path).name,
                '檔案類型': self.get_file_type(metadata.original_path),
                '建議標題': metadata.suggested_title,
                '主分類': metadata.category.get('main_category', ''),
                '子分類': metadata.category.get('sub_category', ''),
                '情緒氛圍': metadata.mood,
                '存放路徑': str(Path(metadata.new_path).relative_to(task.options.processed_folder)),
                'AI生成標籤': ', '.join(metadata.labels),
                'AI生成描述': metadata.description,
                'AI生成關鍵字': ', '.join(metadata.keywords),
                'AI技術分析': tech_analysis_str,
                '處理日期': metadata.processing_date,
                '本地完整路徑': metadata.new_path
            }
            report_data.append(row_data)
        
        # 寫入 CSV
        if HAS_PANDAS:
            # 使用 pandas 寫入
            df = pd.DataFrame(report_data)
            
            if csv_path.exists():
                # 追加到現有檔案
                df.to_csv(csv_path, mode='a', header=False, index=False, encoding='utf-8-sig')
            else:
                # 建立新檔案
                df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        else:
            # 使用 csv 模組寫入
            import csv
            
            # 定義欄位順序
            fieldnames = [
                '檔案ID', '檔案名稱', '檔案類型', '建議標題', '主分類', '子分類',
                '情緒氛圍', '存放路徑', 'AI生成標籤', 'AI生成描述', 'AI生成關鍵字',
                'AI技術分析', '處理日期', '本地完整路徑'
            ]
            
            file_exists = csv_path.exists()
            
            with open(csv_path, 'a' if file_exists else 'w', 
                     newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                # 如果是新檔案，寫入標題行
                if not file_exists:
                    writer.writeheader()
                
                # 寫入資料
                writer.writerows(report_data)
        
        task.logger.log_step("報告生成", f"已更新 {csv_path}")
    
    def get_task_status(self, task_id: str) -> Optional[ArchiveTask]:
        """取得任務狀態"""
        return self.active_tasks.get(task_id)
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任務"""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task.is_cancelled = True
            return True
        return False
    
    def cleanup_completed_tasks(self) -> None:
        """清理已完成的任務"""
        completed_tasks = [
            task_id for task_id, task in self.active_tasks.items()
            if task.status in [ArchiveStatus.COMPLETED, 
                             ArchiveStatus.FAILED,
                             ArchiveStatus.CANCELLED]
        ]
        
        for task_id in completed_tasks:
            del self.active_tasks[task_id]
        
        self.logger.info(f"清理了 {len(completed_tasks)} 個已完成的任務")
    
    def analyze_single_file(self, file_path: str, api_key: str) -> Optional[Dict]:
        """分析單個檔案（不移動檔案）"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return None
            
            file_type = self.get_file_type(str(file_path))
            if not file_type:
                return None
            
            # 臨時設定API金鑰
            if self.genai and api_key:
                self.genai.configure(api_key=api_key)
            
            # 執行AI分析
            analysis_result = self._analyze_media_file_direct(file_path, file_type)
            
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"分析檔案失敗 {file_path}: {str(e)}")
            return None
    
    def _analyze_media_file_direct(self, file_path: Path, file_type: str) -> Optional[Dict]:
        """直接分析媒體檔案（不依賴任務）"""
        try:
            model = self.genai.GenerativeModel("gemini-1.5-pro-latest")
            
            # 準備媒體檔案
            if file_type == "圖片":
                from PIL import Image
                media_file = Image.open(file_path)
            else:
                # 上傳檔案到 Google AI
                media_file = self.genai.upload_file(path=str(file_path))
                
                # 等待處理完成
                while media_file.state.name == "PROCESSING":
                    time.sleep(2)
                    media_file = self.genai.get_file(media_file.name)
                
                if media_file.state.name == "FAILED":
                    raise ArchiveError(f"Google AI 處理 {file_type} 失敗")
            
            # 生成分析提示
            prompt = self._get_enhanced_analysis_prompt(file_type)
            
            # 執行分析
            response = model.generate_content([prompt, media_file])
            
            # 解析結果
            result_text = response.text.strip()
            
            # 清理 JSON 格式
            import re
            result_text = re.sub(r'^```json\s*|```\s*$', '', result_text, flags=re.MULTILINE)
            
            return json.loads(result_text)
            
        except Exception as e:
            self.logger.error(f"AI 分析失敗: {str(e)}")
            return None
    
    def _get_enhanced_analysis_prompt(self, file_type: str) -> str:
        """取得增強的AI分析提示"""
        base_prompt = f"""
        你是一位精通 IPTC 元數據標準與創意分析的資深數位資產管理專家。
        請分析這個{file_type}並生成精確、豐富的元數據。
        
        請完成以下任務並嚴格依照 JSON 格式回傳：
        1. suggested_title: 一個簡潔、引人注目的繁體中文標題（10-20字）
        2. labels: 最多 15 個具體的繁體中文標籤，從廣泛到具體排序
        3. description: 一段約 40-80 字的繁體中文描述，要生動且具體
        4. keywords: 3-8 個最核心的繁體中文關鍵字
        5. mood: 從 [快樂, 溫馨, 悲傷, 寧靜, 懷舊, 緊張, 史詩感, 神秘, 浪漫, 活潑, 莊嚴, 其他] 中選擇一個
        6. color_palette: 主要顏色調（如：暖色調、冷色調、單色、彩色等）
        7. quality_score: 1-10分的品質評分
        8. content_tags: 內容相關標籤（人物、物件、場景等）
        """
        
        if file_type in ["圖片", "影片"]:
            technical_prompt = """
        9. technical_analysis:
            * shot_type: 從 [特寫, 中景, 全景, 遠景, 鳥瞰, 低角度, 平視, 仰視, 其他] 中選擇
            * composition_style: 從 [三分法, 引導線, 對稱, 框架構圖, 黃金比例, 中心構圖, 其他] 中選擇
            * lighting_style: 從 [自然光, 攝影棚光, 輪廓光, 柔光, 硬光, 逆光, 側光, 其他] 中選擇
            * visual_style: 從 [寫實, 抽象, 復古, 現代, 極簡, 華麗, 其他] 中選擇
            * estimated_resolution: 預估解析度等級 (低, 中, 高, 超高)
            """
        elif file_type == "音訊":
            technical_prompt = """
        9. technical_analysis:
            * music_genre: 從 [古典, 爵士, 搖滾, 流行, 電子, 民謠, 藍調, 嘻哈, 其他] 中選擇
            * instrumentation: 列出 1-5 種最主要的樂器或聲音
            * vocal_style: 從 [男聲, 女聲, 童聲, 合唱, 旁白, 無人聲, 混合, 其他] 中選擇
            * tempo: 從 [很慢, 慢, 中等, 快, 很快] 中選擇
            * audio_quality: 從 [低, 中, 高, 專業] 中選擇音質等級
            """
        else:
            technical_prompt = ""
        
        category_prompt = """
        10. category: 選擇最適合的主分類和子分類
            * main_category: 從 [人物, 自然, 動物, 地點, 物件, 事件, 藝術, 記錄, 教育, 娛樂, 其他] 中選擇
            * sub_category: 根據主分類提供具體的子分類（例如：人物->肖像、自然->風景等）
        
        11. usage_suggestions: 建議的使用場景（例如：社交媒體、印刷品、網站背景等）
        
        12. similar_content_tags: 可能相關的搜尋標籤，幫助使用者找到類似內容
        
        請確保回傳的是有效的JSON格式，所有字串都用雙引號包圍。
        """
        
        return base_prompt + technical_prompt + category_prompt
    
    def suggest_folder_structure(self, analysis_results: List[Dict]) -> Dict[str, List[str]]:
        """根據分析結果建議資料夾結構"""
        if not analysis_results:
            return {}
        
        structure_suggestions = {}
        
        # 按主分類分組
        category_groups = {}
        for result in analysis_results:
            category = result.get('category', {})
            main_cat = category.get('main_category', '其他')
            sub_cat = category.get('sub_category', '未分類')
            
            if main_cat not in category_groups:
                category_groups[main_cat] = {}
            
            if sub_cat not in category_groups[main_cat]:
                category_groups[main_cat][sub_cat] = []
            
            category_groups[main_cat][sub_cat].append(result.get('suggested_title', '未命名'))
        
        # 生成建議結構
        for main_cat, sub_cats in category_groups.items():
            structure_suggestions[main_cat] = []
            
            for sub_cat, titles in sub_cats.items():
                if len(titles) > 3:  # 如果該子分類有超過3個檔案，建議建立子資料夾
                    structure_suggestions[main_cat].append(f"{sub_cat} ({len(titles)}個檔案)")
                else:
                    structure_suggestions[main_cat].extend([f"{sub_cat}/{title}" for title in titles])
        
        return structure_suggestions
    
    def get_smart_tags_suggestions(self, existing_tags: List[str], 
                                 analysis_result: Dict) -> List[str]:
        """基於現有標籤和分析結果提供智能標籤建議"""
        suggestions = []
        
        # 從分析結果中提取標籤
        result_tags = analysis_result.get('labels', [])
        result_keywords = analysis_result.get('keywords', [])
        content_tags = analysis_result.get('content_tags', [])
        
        all_new_tags = result_tags + result_keywords + content_tags
        
        # 與現有標籤比較，找出相似但不完全相同的標籤
        for new_tag in all_new_tags:
            if new_tag not in existing_tags:
                # 檢查是否有相似的現有標籤
                similar_found = False
                for existing_tag in existing_tags:
                    if self._calculate_tag_similarity(new_tag, existing_tag) > 0.7:
                        suggestions.append(f"建議使用 '{existing_tag}' 而非 '{new_tag}'")
                        similar_found = True
                        break
                
                if not similar_found:
                    suggestions.append(new_tag)
        
        # 基於情緒和風格建議相關標籤
        mood = analysis_result.get('mood', '')
        if mood and mood != '其他':
            mood_related_tags = self._get_mood_related_tags(mood)
            for tag in mood_related_tags:
                if tag not in existing_tags and tag not in suggestions:
                    suggestions.append(tag)
        
        return suggestions[:10]  # 限制建議數量
    
    def _calculate_tag_similarity(self, tag1: str, tag2: str) -> float:
        """計算標籤相似度"""
        # 簡單的字串相似度計算
        if tag1 == tag2:
            return 1.0
        
        # 檢查包含關係
        if tag1 in tag2 or tag2 in tag1:
            return 0.8
        
        # 檢查共同字元
        common_chars = set(tag1) & set(tag2)
        total_chars = set(tag1) | set(tag2)
        
        if total_chars:
            return len(common_chars) / len(total_chars)
        
        return 0.0
    
    def _get_mood_related_tags(self, mood: str) -> List[str]:
        """取得情緒相關的標籤"""
        mood_tags = {
            '快樂': ['歡樂', '愉快', '開心', '正面', '活力'],
            '溫馨': ['溫暖', '舒適', '家庭', '親情', '和諧'],
            '悲傷': ['憂鬱', '沉重', '感傷', '思念', '離別'],
            '寧靜': ['平靜', '安詳', '冥想', '放鬆', '禪意'],
            '懷舊': ['復古', '回憶', '經典', '歲月', '時光'],
            '緊張': ['刺激', '懸疑', '急迫', '壓力', '動感'],
            '史詩感': ['壯闊', '宏偉', '英雄', '史詩', '磅礴'],
            '神秘': ['神祕', '未知', '探索', '奇幻', '超自然'],
            '浪漫': ['愛情', '甜蜜', '溫柔', '浪漫', '情侶'],
            '活潑': ['生動', '有趣', '青春', '活力', '動態'],
            '莊嚴': ['正式', '神聖', '威嚴', '典雅', '肅穆']
        }
        
        return mood_tags.get(mood, [])


# 自定義例外類別
class ArchiveError(CrossPlatformError):
    """歸檔相關錯誤"""
    pass


# 全域歸檔管理器實例
archive_manager = ArchiveManager()


if __name__ == "__main__":
    # 測試程式
    print("=== 歸檔管理器測試 ===")
    
    print(f"AI 服務可用: {archive_manager.is_ai_available()}")
    print(f"支援格式: {len(archive_manager.get_supported_formats())} 種")
    
    # 測試檔案格式檢查
    test_files = ["test.jpg", "test.mp4", "test.mp3", "test.txt"]
    for file in test_files:
        file_type = archive_manager.get_file_type(file)
        print(f"{file}: {file_type if file_type else '不支援'}")