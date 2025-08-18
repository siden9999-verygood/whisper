"""
監控管理器模組
處理資料夾監控、效能監控和系統診斷功能
"""

import os
import time
import threading
import psutil
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
from queue import Queue

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False
    Observer = None
    FileSystemEventHandler = object  # 提供一個基本的類別作為替代

from platform_adapter import platform_adapter, CrossPlatformError
from config_service import config_service
from logging_service import logging_service, TaskLogger


class MonitoringStatus(Enum):
    """監控狀態枚舉"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


@dataclass
class FolderMonitorConfig:
    """資料夾監控配置"""
    folder_path: str
    auto_transcribe: bool = True
    auto_archive: bool = True
    file_patterns: List[str] = None
    recursive: bool = True
    
    def __post_init__(self):
        if self.file_patterns is None:
            self.file_patterns = ["*.mp3", "*.wav", "*.mp4", "*.mov", "*.jpg", "*.png"]


@dataclass
class ProcessingRule:
    """處理規則"""
    file_type: str  # audio, video, image
    action: str     # transcribe, archive, both
    priority: int = 1
    enabled: bool = True


@dataclass
class SystemMetrics:
    """系統指標"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    network_io: Dict[str, int]
    process_count: int
    temperature: Optional[float] = None


@dataclass
class ProcessingStats:
    """處理統計"""
    total_files: int = 0
    processed_files: int = 0
    failed_files: int = 0
    processing_time: float = 0.0
    last_processed: Optional[datetime] = None


@dataclass
class ProcessingHistory:
    """處理歷史記錄"""
    file_path: str
    file_type: str
    action: str
    status: str  # success, failed, skipped
    start_time: datetime
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    file_size: int = 0


@dataclass
class NotificationConfig:
    """通知配置"""
    enabled: bool = True
    show_success: bool = False
    show_errors: bool = True
    show_warnings: bool = True
    max_notifications: int = 100


class FileEventHandler(FileSystemEventHandler):
    """檔案事件處理器"""
    
    def __init__(self, monitoring_manager):
        super().__init__()
        self.monitoring_manager = monitoring_manager
        self.logger = logging_service.get_logger("FileEventHandler")
    
    def on_created(self, event):
        """檔案建立事件"""
        if not event.is_directory and self.monitoring_manager:
            self.monitoring_manager._handle_new_file(event.src_path)
    
    def on_moved(self, event):
        """檔案移動事件"""
        if not event.is_directory and self.monitoring_manager:
            self.monitoring_manager._handle_new_file(event.dest_path)


class MonitoringManager:
    """監控管理器"""
    
    def __init__(self):
        self.config = config_service.get_config()
        self.logger = logging_service.get_logger("MonitoringManager")
        
        # 監控狀態
        self.status = MonitoringStatus.STOPPED
        self.folder_monitors: Dict[str, Observer] = {}
        self.processing_queue = Queue()
        self.processing_thread = None
        self.metrics_thread = None
        
        # 配置
        self.monitor_configs: Dict[str, FolderMonitorConfig] = {}
        self.processing_rules: List[ProcessingRule] = []
        self.stats = ProcessingStats()
        
        # 處理歷史和通知
        self.processing_history: List[ProcessingHistory] = []
        self.max_history_size = 1000
        self.notification_config = NotificationConfig()
        self.notifications: List[Dict[str, Any]] = []
        
        # 系統監控
        self.system_metrics: List[SystemMetrics] = []
        self.metrics_interval = 5.0  # 5秒收集一次指標
        self.max_metrics_history = 1440  # 保留12小時的資料 (5秒 * 1440 = 2小時)
        
        # 初始化預設處理規則
        self._initialize_default_rules()
        
        # 檢查依賴
        if not HAS_WATCHDOG:
            self.logger.warning("watchdog 套件未安裝，資料夾監控功能將不可用")
    
    def _initialize_default_rules(self):
        """初始化預設處理規則"""
        self.processing_rules = [
            ProcessingRule("audio", "transcribe", priority=1),
            ProcessingRule("video", "transcribe", priority=2),
            ProcessingRule("image", "archive", priority=3),
        ]
    
    def add_processing_rule(self, rule: ProcessingRule) -> bool:
        """添加處理規則"""
        try:
            # 檢查是否已存在相同的規則
            for existing_rule in self.processing_rules:
                if (existing_rule.file_type == rule.file_type and 
                    existing_rule.action == rule.action):
                    self.logger.warning(f"處理規則已存在: {rule.file_type} -> {rule.action}")
                    return False
            
            self.processing_rules.append(rule)
            self.processing_rules.sort(key=lambda x: x.priority)
            
            self.logger.info(f"添加處理規則: {rule.file_type} -> {rule.action}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加處理規則失敗: {str(e)}")
            return False
    
    def remove_processing_rule(self, file_type: str, action: str) -> bool:
        """移除處理規則"""
        try:
            for i, rule in enumerate(self.processing_rules):
                if rule.file_type == file_type and rule.action == action:
                    del self.processing_rules[i]
                    self.logger.info(f"移除處理規則: {file_type} -> {action}")
                    return True
            
            self.logger.warning(f"找不到處理規則: {file_type} -> {action}")
            return False
            
        except Exception as e:
            self.logger.error(f"移除處理規則失敗: {str(e)}")
            return False
    
    def update_processing_rule(self, file_type: str, action: str, **kwargs) -> bool:
        """更新處理規則"""
        try:
            for rule in self.processing_rules:
                if rule.file_type == file_type and rule.action == action:
                    for key, value in kwargs.items():
                        if hasattr(rule, key):
                            setattr(rule, key, value)
                    
                    self.logger.info(f"更新處理規則: {file_type} -> {action}")
                    return True
            
            self.logger.warning(f"找不到處理規則: {file_type} -> {action}")
            return False
            
        except Exception as e:
            self.logger.error(f"更新處理規則失敗: {str(e)}")
            return False
    
    def add_folder_monitor(self, folder_path: str, config: FolderMonitorConfig = None) -> bool:
        """添加資料夾監控"""
        if not HAS_WATCHDOG:
            self.logger.error("無法添加資料夾監控：watchdog 套件未安裝")
            return False
        
        folder_path = str(Path(folder_path).resolve())
        
        if not Path(folder_path).exists():
            self.logger.error(f"資料夾不存在: {folder_path}")
            return False
        
        if folder_path in self.folder_monitors:
            self.logger.warning(f"資料夾已在監控中: {folder_path}")
            return True
        
        try:
            # 建立監控配置
            if config is None:
                config = FolderMonitorConfig(folder_path)
            
            self.monitor_configs[folder_path] = config
            
            # 建立觀察者
            observer = Observer()
            event_handler = FileEventHandler(self)
            observer.schedule(event_handler, folder_path, recursive=config.recursive)
            
            # 啟動監控
            observer.start()
            self.folder_monitors[folder_path] = observer
            
            self.logger.info(f"開始監控資料夾: {folder_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加資料夾監控失敗: {str(e)}")
            return False
    
    def remove_folder_monitor(self, folder_path: str) -> bool:
        """移除資料夾監控"""
        folder_path = str(Path(folder_path).resolve())
        
        if folder_path not in self.folder_monitors:
            self.logger.warning(f"資料夾未在監控中: {folder_path}")
            return False
        
        try:
            observer = self.folder_monitors[folder_path]
            observer.stop()
            observer.join()
            
            del self.folder_monitors[folder_path]
            del self.monitor_configs[folder_path]
            
            self.logger.info(f"停止監控資料夾: {folder_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"移除資料夾監控失敗: {str(e)}")
            return False
    
    def start_monitoring(self) -> bool:
        """開始監控服務"""
        if self.status == MonitoringStatus.RUNNING:
            self.logger.warning("監控服務已在運行中")
            return True
        
        try:
            self.status = MonitoringStatus.STARTING
            
            # 啟動處理執行緒
            self.processing_thread = threading.Thread(
                target=self._processing_worker,
                daemon=True
            )
            self.processing_thread.start()
            
            # 啟動系統指標收集執行緒
            self.metrics_thread = threading.Thread(
                target=self._metrics_collector,
                daemon=True
            )
            self.metrics_thread.start()
            
            self.status = MonitoringStatus.RUNNING
            self.logger.info("監控服務已啟動")
            return True
            
        except Exception as e:
            self.status = MonitoringStatus.ERROR
            self.logger.error(f"啟動監控服務失敗: {str(e)}")
            return False
    
    def stop_monitoring(self) -> bool:
        """停止監控服務"""
        if self.status == MonitoringStatus.STOPPED:
            return True
        
        try:
            self.status = MonitoringStatus.STOPPED
            
            # 停止所有資料夾監控
            for folder_path in list(self.folder_monitors.keys()):
                self.remove_folder_monitor(folder_path)
            
            self.logger.info("監控服務已停止")
            return True
            
        except Exception as e:
            self.logger.error(f"停止監控服務失敗: {str(e)}")
            return False
    
    def _handle_new_file(self, file_path: str):
        """處理新檔案"""
        file_path = Path(file_path)
        
        # 檢查檔案是否符合處理條件
        if not self._should_process_file(file_path):
            return
        
        # 等待檔案寫入完成
        if not self._wait_for_file_ready(file_path):
            self.logger.warning(f"檔案未準備就緒，跳過處理: {file_path}")
            return
        
        # 加入處理佇列
        self.processing_queue.put(str(file_path))
        self.stats.total_files += 1
        
        self.logger.info(f"檢測到新檔案: {file_path.name}")
    
    def _should_process_file(self, file_path: Path) -> bool:
        """檢查檔案是否應該處理"""
        # 檢查檔案副檔名
        suffix = file_path.suffix.lower()
        
        # 音頻檔案
        audio_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac'}
        # 影片檔案
        video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv'}
        # 圖片檔案
        image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif'}
        
        if suffix not in (audio_extensions | video_extensions | image_extensions):
            return False
        
        # 檢查檔案大小（跳過太小的檔案）
        try:
            if file_path.stat().st_size < 1024:  # 小於1KB
                return False
        except OSError:
            return False
        
        # 檢查是否為臨時檔案
        if file_path.name.startswith('.') or file_path.name.startswith('~'):
            return False
        
        return True
    
    def _wait_for_file_ready(self, file_path: Path, timeout: int = 30) -> bool:
        """等待檔案寫入完成"""
        start_time = time.time()
        last_size = 0
        
        while time.time() - start_time < timeout:
            try:
                current_size = file_path.stat().st_size
                if current_size == last_size and current_size > 0:
                    # 檔案大小穩定，等待額外1秒確保寫入完成
                    time.sleep(1)
                    return True
                last_size = current_size
                time.sleep(0.5)
            except OSError:
                time.sleep(0.5)
                continue
        
        return False
    
    def _processing_worker(self):
        """處理工作執行緒"""
        while self.status == MonitoringStatus.RUNNING:
            try:
                # 從佇列取得檔案
                if self.processing_queue.empty():
                    time.sleep(1)
                    continue
                
                file_path = self.processing_queue.get(timeout=1)
                self._process_file(file_path)
                
            except Exception as e:
                self.logger.error(f"處理檔案時發生錯誤: {str(e)}")
                time.sleep(1)
    
    def _process_file(self, file_path: str):
        """處理單個檔案"""
        start_time = datetime.now()
        file_path = Path(file_path)
        
        # 建立處理歷史記錄
        history_record = ProcessingHistory(
            file_path=str(file_path),
            file_type="",
            action="",
            status="processing",
            start_time=start_time,
            file_size=0
        )
        
        try:
            # 取得檔案大小
            history_record.file_size = file_path.stat().st_size
            
            # 判斷檔案類型
            file_type = self._get_file_type(file_path)
            if not file_type:
                history_record.status = "skipped"
                history_record.error_message = "不支援的檔案類型"
                history_record.end_time = datetime.now()
                self._add_history_record(history_record)
                return
            
            history_record.file_type = file_type
            
            # 根據處理規則決定動作
            actions = self._get_processing_actions(file_type)
            if not actions:
                history_record.status = "skipped"
                history_record.error_message = "沒有匹配的處理規則"
                history_record.end_time = datetime.now()
                self._add_history_record(history_record)
                return
            
            # 處理每個動作
            overall_success = True
            for action in actions:
                action_history = ProcessingHistory(
                    file_path=str(file_path),
                    file_type=file_type,
                    action=action,
                    status="processing",
                    start_time=datetime.now(),
                    file_size=history_record.file_size
                )
                
                try:
                    if action == "transcribe":
                        success = self._transcribe_file(file_path)
                    elif action == "archive":
                        success = self._archive_file(file_path)
                    else:
                        success = False
                    
                    action_history.end_time = datetime.now()
                    action_history.status = "success" if success else "failed"
                    
                    if not success:
                        overall_success = False
                        action_history.error_message = f"{action} 處理失敗"
                    
                    self._add_history_record(action_history)
                    
                except Exception as e:
                    overall_success = False
                    action_history.end_time = datetime.now()
                    action_history.status = "failed"
                    action_history.error_message = str(e)
                    self._add_history_record(action_history)
            
            # 更新統計
            if overall_success:
                self.stats.processed_files += 1
                self.stats.last_processed = datetime.now()
                self._send_notification("success", f"成功處理檔案: {file_path.name}")
            else:
                self.stats.failed_files += 1
                self._send_notification("error", f"處理檔案失敗: {file_path.name}")
            
            processing_time = (datetime.now() - start_time).total_seconds()
            self.stats.processing_time += processing_time
            
            self.logger.info(f"檔案處理完成: {file_path.name} (耗時: {processing_time:.2f}s)")
            
        except Exception as e:
            self.stats.failed_files += 1
            history_record.status = "failed"
            history_record.error_message = str(e)
            history_record.end_time = datetime.now()
            self._add_history_record(history_record)
            
            self._send_notification("error", f"處理檔案時發生錯誤: {file_path.name} - {str(e)}")
            self.logger.error(f"處理檔案失敗 {file_path}: {str(e)}")
    
    def _add_history_record(self, record: ProcessingHistory):
        """添加處理歷史記錄"""
        self.processing_history.append(record)
        
        # 限制歷史記錄數量
        if len(self.processing_history) > self.max_history_size:
            self.processing_history = self.processing_history[-self.max_history_size:]
    
    def _send_notification(self, level: str, message: str):
        """發送通知"""
        if not self.notification_config.enabled:
            return
        
        # 檢查通知級別設定
        if level == "success" and not self.notification_config.show_success:
            return
        if level == "error" and not self.notification_config.show_errors:
            return
        if level == "warning" and not self.notification_config.show_warnings:
            return
        
        notification = {
            "timestamp": datetime.now(),
            "level": level,
            "message": message
        }
        
        self.notifications.append(notification)
        
        # 限制通知數量
        if len(self.notifications) > self.notification_config.max_notifications:
            self.notifications = self.notifications[-self.notification_config.max_notifications:]
        
        # 記錄到日誌
        if level == "error":
            self.logger.error(f"通知: {message}")
        elif level == "warning":
            self.logger.warning(f"通知: {message}")
        else:
            self.logger.info(f"通知: {message}")
    
    def _get_file_type(self, file_path: Path) -> Optional[str]:
        """取得檔案類型"""
        suffix = file_path.suffix.lower()
        
        audio_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac'}
        video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv'}
        image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif'}
        
        if suffix in audio_extensions:
            return "audio"
        elif suffix in video_extensions:
            return "video"
        elif suffix in image_extensions:
            return "image"
        
        return None
    
    def _get_processing_actions(self, file_type: str) -> List[str]:
        """取得處理動作"""
        actions = []
        
        for rule in self.processing_rules:
            if rule.file_type == file_type and rule.enabled:
                if rule.action == "both":
                    actions.extend(["transcribe", "archive"])
                else:
                    actions.append(rule.action)
        
        return list(set(actions))  # 去重
    
    def _transcribe_file(self, file_path: Path) -> bool:
        """轉錄檔案"""
        try:
            # 導入轉錄管理器
            from transcription_manager import transcription_manager, TranscriptionOptions
            
            # 檢查檔案格式是否支援
            if not transcription_manager.is_supported_format(str(file_path)):
                self.logger.warning(f"不支援的檔案格式: {file_path.name}")
                return False
            
            # 建立轉錄選項
            options = TranscriptionOptions(
                model="ggml-medium.bin",
                language="zh",
                output_srt=True,
                output_txt=True
            )
            
            # 建立轉錄任務
            task_id = transcription_manager.create_transcription_task(
                input_file=str(file_path),
                output_dir=str(file_path.parent),
                options=options
            )
            
            # 開始轉錄
            transcription_manager.start_transcription(task_id)
            
            # 等待任務完成
            max_wait_time = 300  # 5分鐘超時
            wait_time = 0
            while wait_time < max_wait_time:
                task = transcription_manager.get_task_status(task_id)
                if task is None:
                    break
                
                if task.status.value in ["completed", "failed", "cancelled"]:
                    break
                
                time.sleep(2)
                wait_time += 2
            
            # 檢查結果
            task = transcription_manager.get_task_status(task_id)
            if task and task.status.value == "completed":
                self.logger.info(f"轉錄完成: {file_path.name}")
                return True
            else:
                error_msg = task.error_message if task else "任務超時"
                self.logger.error(f"轉錄失敗: {file_path.name} - {error_msg}")
                return False
                
        except Exception as e:
            self.logger.error(f"轉錄檔案失敗: {str(e)}")
            return False
    
    def _archive_file(self, file_path: Path) -> bool:
        """歸檔檔案"""
        try:
            # 導入歸檔管理器
            from archive_manager import archive_manager, ArchiveOptions
            
            # 檢查檔案格式是否支援
            if not archive_manager.is_supported_format(str(file_path)):
                self.logger.warning(f"不支援的檔案格式: {file_path.name}")
                return False
            
            # 建立歸檔選項
            options = ArchiveOptions(
                source_folder=str(file_path.parent),
                destination_folder=str(file_path.parent / "archived"),
                use_ai_analysis=True,
                create_folder_structure=True,
                move_files=True,
                generate_report=False
            )
            
            # 建立歸檔任務
            task_id = archive_manager.create_archive_task(options)
            
            # 開始歸檔
            archive_manager.start_archive_task(task_id)
            
            # 等待任務完成
            max_wait_time = 180  # 3分鐘超時
            wait_time = 0
            while wait_time < max_wait_time:
                task = archive_manager.get_task_status(task_id)
                if task is None:
                    break
                
                if task.status.value in ["completed", "failed", "cancelled"]:
                    break
                
                time.sleep(2)
                wait_time += 2
            
            # 檢查結果
            task = archive_manager.get_task_status(task_id)
            if task and task.status.value == "completed":
                self.logger.info(f"歸檔完成: {file_path.name}")
                return True
            else:
                error_msg = task.error_message if task else "任務超時"
                self.logger.error(f"歸檔失敗: {file_path.name} - {error_msg}")
                return False
                
        except Exception as e:
            self.logger.error(f"歸檔檔案失敗: {str(e)}")
            return False
    
    def _metrics_collector(self):
        """系統指標收集器"""
        while self.status == MonitoringStatus.RUNNING:
            try:
                metrics = self._collect_system_metrics()
                self.system_metrics.append(metrics)
                
                # 限制歷史資料數量
                if len(self.system_metrics) > self.max_metrics_history:
                    self.system_metrics = self.system_metrics[-self.max_metrics_history:]
                
                time.sleep(self.metrics_interval)
                
            except Exception as e:
                self.logger.error(f"收集系統指標時發生錯誤: {str(e)}")
                time.sleep(self.metrics_interval)
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """收集系統指標"""
        try:
            # CPU 使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 記憶體使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # 磁碟使用率
            disk = psutil.disk_usage('/')
            disk_usage_percent = (disk.used / disk.total) * 100
            
            # 網路 I/O
            network_io = psutil.net_io_counters()._asdict()
            
            # 程序數量
            process_count = len(psutil.pids())
            
            # 溫度（如果可用）
            temperature = None
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    # 取得第一個溫度感測器的值
                    for name, entries in temps.items():
                        if entries:
                            temperature = entries[0].current
                            break
            except:
                pass
            
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_usage_percent=disk_usage_percent,
                network_io=network_io,
                process_count=process_count,
                temperature=temperature
            )
            
        except Exception as e:
            self.logger.error(f"收集系統指標失敗: {str(e)}")
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_usage_percent=0.0,
                network_io={},
                process_count=0
            )
    
    def get_system_status(self) -> Dict[str, Any]:
        """取得系統狀態"""
        if not self.system_metrics:
            return {}
        
        latest_metrics = self.system_metrics[-1]
        
        # 計算平均值（最近10分鐘）
        recent_metrics = [
            m for m in self.system_metrics 
            if (datetime.now() - m.timestamp).total_seconds() <= 600
        ]
        
        if recent_metrics:
            avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
            avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
        else:
            avg_cpu = latest_metrics.cpu_percent
            avg_memory = latest_metrics.memory_percent
        
        return {
            "monitoring_status": self.status.value,
            "monitored_folders": len(self.folder_monitors),
            "processing_queue_size": self.processing_queue.qsize(),
            "current_cpu": latest_metrics.cpu_percent,
            "current_memory": latest_metrics.memory_percent,
            "current_disk": latest_metrics.disk_usage_percent,
            "average_cpu_10min": avg_cpu,
            "average_memory_10min": avg_memory,
            "process_count": latest_metrics.process_count,
            "temperature": latest_metrics.temperature,
            "stats": {
                "total_files": self.stats.total_files,
                "processed_files": self.stats.processed_files,
                "failed_files": self.stats.failed_files,
                "success_rate": (self.stats.processed_files / max(self.stats.total_files, 1)) * 100,
                "average_processing_time": self.stats.processing_time / max(self.stats.processed_files, 1),
                "last_processed": self.stats.last_processed.isoformat() if self.stats.last_processed else None
            }
        }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """取得效能報告"""
        if not self.system_metrics:
            return {"error": "沒有可用的系統指標資料"}
        
        # 分析最近1小時的資料
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_metrics = [
            m for m in self.system_metrics 
            if m.timestamp >= one_hour_ago
        ]
        
        if not recent_metrics:
            return {"error": "沒有最近的系統指標資料"}
        
        # 計算統計資料
        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_percent for m in recent_metrics]
        
        report = {
            "report_period": "最近1小時",
            "data_points": len(recent_metrics),
            "cpu_stats": {
                "average": sum(cpu_values) / len(cpu_values),
                "max": max(cpu_values),
                "min": min(cpu_values),
                "current": cpu_values[-1]
            },
            "memory_stats": {
                "average": sum(memory_values) / len(memory_values),
                "max": max(memory_values),
                "min": min(memory_values),
                "current": memory_values[-1]
            },
            "disk_usage": recent_metrics[-1].disk_usage_percent,
            "recommendations": []
        }
        
        # 生成建議
        if report["cpu_stats"]["average"] > 80:
            report["recommendations"].append("CPU 使用率過高，建議減少並發處理數量")
        
        if report["memory_stats"]["average"] > 85:
            report["recommendations"].append("記憶體使用率過高，建議清理快取或重啟程式")
        
        if report["disk_usage"] > 90:
            report["recommendations"].append("磁碟空間不足，建議清理舊檔案")
        
        if self.stats.failed_files > 0:
            failure_rate = (self.stats.failed_files / self.stats.total_files) * 100
            if failure_rate > 10:
                report["recommendations"].append(f"檔案處理失敗率過高 ({failure_rate:.1f}%)，請檢查日誌")
        
        return report
    
    def get_monitored_folders(self) -> List[Dict[str, Any]]:
        """取得監控資料夾清單"""
        folders = []
        for folder_path, config in self.monitor_configs.items():
            folders.append({
                "path": folder_path,
                "auto_transcribe": config.auto_transcribe,
                "auto_archive": config.auto_archive,
                "recursive": config.recursive,
                "file_patterns": config.file_patterns,
                "status": "running" if folder_path in self.folder_monitors else "stopped"
            })
        return folders
    
    def get_processing_rules(self) -> List[Dict[str, Any]]:
        """取得處理規則清單"""
        rules = []
        for rule in self.processing_rules:
            rules.append({
                "file_type": rule.file_type,
                "action": rule.action,
                "priority": rule.priority,
                "enabled": rule.enabled
            })
        return rules
    
    def get_processing_history(self, limit: int = 100, file_type: str = None, 
                             status: str = None) -> List[Dict[str, Any]]:
        """取得處理歷史記錄"""
        history = self.processing_history.copy()
        
        # 過濾條件
        if file_type:
            history = [h for h in history if h.file_type == file_type]
        
        if status:
            history = [h for h in history if h.status == status]
        
        # 按時間排序（最新的在前）
        history.sort(key=lambda x: x.start_time, reverse=True)
        
        # 限制數量
        history = history[:limit]
        
        # 轉換為字典格式
        result = []
        for record in history:
            result.append({
                "file_path": record.file_path,
                "file_name": Path(record.file_path).name,
                "file_type": record.file_type,
                "action": record.action,
                "status": record.status,
                "start_time": record.start_time.isoformat(),
                "end_time": record.end_time.isoformat() if record.end_time else None,
                "duration": (record.end_time - record.start_time).total_seconds() if record.end_time else None,
                "error_message": record.error_message,
                "file_size": record.file_size
            })
        
        return result
    
    def get_notifications(self, limit: int = 50, level: str = None) -> List[Dict[str, Any]]:
        """取得通知清單"""
        notifications = self.notifications.copy()
        
        # 過濾級別
        if level:
            notifications = [n for n in notifications if n["level"] == level]
        
        # 按時間排序（最新的在前）
        notifications.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # 限制數量
        notifications = notifications[:limit]
        
        # 轉換時間格式
        for notification in notifications:
            notification["timestamp"] = notification["timestamp"].isoformat()
        
        return notifications
    
    def clear_notifications(self) -> bool:
        """清除所有通知"""
        try:
            self.notifications.clear()
            self.logger.info("已清除所有通知")
            return True
        except Exception as e:
            self.logger.error(f"清除通知失敗: {str(e)}")
            return False
    
    def clear_processing_history(self) -> bool:
        """清除處理歷史記錄"""
        try:
            self.processing_history.clear()
            self.logger.info("已清除處理歷史記錄")
            return True
        except Exception as e:
            self.logger.error(f"清除處理歷史記錄失敗: {str(e)}")
            return False
    
    def update_notification_config(self, **kwargs) -> bool:
        """更新通知配置"""
        try:
            for key, value in kwargs.items():
                if hasattr(self.notification_config, key):
                    setattr(self.notification_config, key, value)
            
            self.logger.info("通知配置已更新")
            return True
        except Exception as e:
            self.logger.error(f"更新通知配置失敗: {str(e)}")
            return False
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """取得詳細的處理統計資料"""
        # 基本統計
        stats = {
            "total_files": self.stats.total_files,
            "processed_files": self.stats.processed_files,
            "failed_files": self.stats.failed_files,
            "success_rate": (self.stats.processed_files / max(self.stats.total_files, 1)) * 100,
            "average_processing_time": self.stats.processing_time / max(self.stats.processed_files, 1),
            "last_processed": self.stats.last_processed.isoformat() if self.stats.last_processed else None
        }
        
        # 按檔案類型統計
        file_type_stats = {}
        for record in self.processing_history:
            if record.file_type not in file_type_stats:
                file_type_stats[record.file_type] = {
                    "total": 0,
                    "success": 0,
                    "failed": 0,
                    "total_size": 0
                }
            
            file_type_stats[record.file_type]["total"] += 1
            file_type_stats[record.file_type]["total_size"] += record.file_size
            
            if record.status == "success":
                file_type_stats[record.file_type]["success"] += 1
            elif record.status == "failed":
                file_type_stats[record.file_type]["failed"] += 1
        
        # 計算成功率
        for file_type, data in file_type_stats.items():
            if data["total"] > 0:
                data["success_rate"] = (data["success"] / data["total"]) * 100
            else:
                data["success_rate"] = 0
        
        stats["by_file_type"] = file_type_stats
        
        # 按動作統計
        action_stats = {}
        for record in self.processing_history:
            if record.action not in action_stats:
                action_stats[record.action] = {
                    "total": 0,
                    "success": 0,
                    "failed": 0
                }
            
            action_stats[record.action]["total"] += 1
            
            if record.status == "success":
                action_stats[record.action]["success"] += 1
            elif record.status == "failed":
                action_stats[record.action]["failed"] += 1
        
        # 計算成功率
        for action, data in action_stats.items():
            if data["total"] > 0:
                data["success_rate"] = (data["success"] / data["total"]) * 100
            else:
                data["success_rate"] = 0
        
        stats["by_action"] = action_stats
        
        # 最近24小時統計
        twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
        recent_records = [
            r for r in self.processing_history 
            if r.start_time >= twenty_four_hours_ago
        ]
        
        stats["last_24_hours"] = {
            "total": len(recent_records),
            "success": len([r for r in recent_records if r.status == "success"]),
            "failed": len([r for r in recent_records if r.status == "failed"]),
            "total_size": sum(r.file_size for r in recent_records)
        }
        
        return stats
    
    def pause_monitoring(self) -> bool:
        """暫停監控"""
        if self.status != MonitoringStatus.RUNNING:
            return False
        
        try:
            self.status = MonitoringStatus.PAUSED
            self.logger.info("監控已暫停")
            self._send_notification("warning", "監控系統已暫停")
            return True
        except Exception as e:
            self.logger.error(f"暫停監控失敗: {str(e)}")
            return False
    
    def resume_monitoring(self) -> bool:
        """恢復監控"""
        if self.status != MonitoringStatus.PAUSED:
            return False
        
        try:
            self.status = MonitoringStatus.RUNNING
            self.logger.info("監控已恢復")
            self._send_notification("info", "監控系統已恢復")
            return True
        except Exception as e:
            self.logger.error(f"恢復監控失敗: {str(e)}")
            return False


# 自定義例外類別
class MonitoringError(CrossPlatformError):
    """監控相關錯誤"""
    pass


# 全域監控管理器實例
monitoring_manager = None

def get_monitoring_manager():
    """取得監控管理器實例"""
    global monitoring_manager
    if monitoring_manager is None:
        monitoring_manager = MonitoringManager()
    return monitoring_manager


if __name__ == "__main__":
    # 測試程式
    print("=== 監控管理器測試 ===")
    
    # 測試系統指標收集
    metrics = monitoring_manager._collect_system_metrics()
    print(f"CPU: {metrics.cpu_percent}%")
    print(f"記憶體: {metrics.memory_percent}%")
    print(f"磁碟: {metrics.disk_usage_percent}%")
    print(f"程序數: {metrics.process_count}")
    
    if HAS_WATCHDOG:
        print("watchdog 可用，可以使用資料夾監控功能")
    else:
        print("watchdog 不可用，請安裝: pip install watchdog")