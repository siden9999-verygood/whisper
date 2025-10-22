"""
日誌服務模組
提供統一的日誌記錄和管理功能
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from logging.handlers import RotatingFileHandler
from platform_adapter import platform_adapter
from config_service import config_service


class LoggingService:
    """日誌服務類別"""
    
    # 日誌等級
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL
    
    def __init__(self):
        self.log_dir = platform_adapter.get_config_dir() / "logs"
        self.log_dir.mkdir(exist_ok=True)
        
        self.loggers: Dict[str, logging.Logger] = {}
        self._setup_main_logger()
    
    def _setup_main_logger(self) -> None:
        """設定主要日誌記錄器"""
        logger_name = "AIWorkstation"
        
        # 建立主要日誌記錄器
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        
        # 清除現有的處理器（確保先關閉避免資源洩漏）
        for h in list(logger.handlers):
            try:
                h.close()
            except Exception:
                pass
            logger.removeHandler(h)
        
        # 建立格式器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 檔案處理器 (輪轉日誌)
        log_file = self.log_dir / "app.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # 控制台處理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 錯誤檔案處理器
        error_file = self.log_dir / "error.log"
        error_handler = RotatingFileHandler(
            error_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)
        
        self.loggers[logger_name] = logger
        self.main_logger = logger
    
    def get_logger(self, name: str) -> logging.Logger:
        """取得指定名稱的日誌記錄器"""
        if name not in self.loggers:
            logger = logging.getLogger(name)
            logger.setLevel(logging.DEBUG)
            
            # 使用主要日誌記錄器的處理器
            for handler in self.main_logger.handlers:
                logger.addHandler(handler)
            
            self.loggers[name] = logger
        
        return self.loggers[name]
    
    def debug(self, message: str, logger_name: str = "AIWorkstation") -> None:
        """記錄除錯訊息"""
        self.get_logger(logger_name).debug(message)
    
    def info(self, message: str, logger_name: str = "AIWorkstation") -> None:
        """記錄資訊訊息"""
        self.get_logger(logger_name).info(message)
    
    def warning(self, message: str, logger_name: str = "AIWorkstation") -> None:
        """記錄警告訊息"""
        self.get_logger(logger_name).warning(message)
    
    def error(self, message: str, logger_name: str = "AIWorkstation", 
              exc_info: bool = False) -> None:
        """記錄錯誤訊息"""
        self.get_logger(logger_name).error(message, exc_info=exc_info)
    
    def critical(self, message: str, logger_name: str = "AIWorkstation", 
                exc_info: bool = False) -> None:
        """記錄嚴重錯誤訊息"""
        self.get_logger(logger_name).critical(message, exc_info=exc_info)
    
    def log_exception(self, exception: Exception, 
                     logger_name: str = "AIWorkstation") -> None:
        """記錄例外資訊"""
        self.get_logger(logger_name).exception(f"發生例外: {str(exception)}")
    
    def log_system_info(self) -> None:
        """記錄系統資訊"""
        system_info = platform_adapter.get_system_info()
        self.info("=== 系統資訊 ===")
        for key, value in system_info.items():
            self.info(f"{key}: {value}")
    
    def log_config_info(self) -> None:
        """記錄配置資訊"""
        config = config_service.get_config()
        self.info("=== 配置資訊 ===")
        self.info(f"AI 模型: {config.ai_model}")
        self.info(f"預設語言: {config.default_language}")
        self.info(f"視窗大小: {config.window_width}x{config.window_height}")
        
        # 驗證路徑
        validation_results = config_service.validate_paths()
        self.info("=== 路徑驗證 ===")
        for path_name, exists in validation_results.items():
            status = "存在" if exists else "不存在"
            self.info(f"{path_name}: {status}")
    
    def create_session_log(self, session_id: str) -> logging.Logger:
        """建立會話專用的日誌記錄器"""
        logger_name = f"Session_{session_id}"
        
        if logger_name not in self.loggers:
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.DEBUG)
            
            # 建立會話專用的檔案處理器
            session_log_file = self.log_dir / f"session_{session_id}.log"
            session_handler = logging.FileHandler(
                session_log_file,
                encoding='utf-8'
            )
            session_handler.setLevel(logging.DEBUG)
            
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            session_handler.setFormatter(formatter)
            logger.addHandler(session_handler)
            
            self.loggers[logger_name] = logger
        
        return self.loggers[logger_name]
    
    def cleanup_old_logs(self, days_to_keep: int = 30) -> None:
        """清理舊的日誌檔案"""
        try:
            cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 3600)
            
            for log_file in self.log_dir.glob("*.log*"):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    self.info(f"已刪除舊日誌檔案: {log_file.name}")
        
        except Exception as e:
            self.error(f"清理舊日誌檔案時發生錯誤: {e}")
    
    def get_log_files(self) -> list:
        """取得所有日誌檔案清單"""
        return list(self.log_dir.glob("*.log*"))
    
    def get_recent_logs(self, lines: int = 100, 
                       log_file: str = "app.log") -> list:
        """取得最近的日誌記錄"""
        try:
            log_path = self.log_dir / log_file
            if not log_path.exists():
                return []
            
            with open(log_path, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                return all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        except Exception as e:
            self.error(f"讀取日誌檔案時發生錯誤: {e}")
            return []
    
    def search_logs(self, query: str, log_file: str = "app.log", 
                   max_results: int = 100, case_sensitive: bool = False) -> list:
        """搜尋日誌記錄"""
        try:
            log_path = self.log_dir / log_file
            if not log_path.exists():
                return []
            
            results = []
            search_query = query if case_sensitive else query.lower()
            
            with open(log_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    search_line = line if case_sensitive else line.lower()
                    if search_query in search_line:
                        results.append({
                            'line_number': line_num,
                            'content': line.strip(),
                            'timestamp': self._extract_timestamp(line)
                        })
                        
                        if len(results) >= max_results:
                            break
            
            return results
        
        except Exception as e:
            self.error(f"搜尋日誌時發生錯誤: {e}")
            return []
    
    def filter_logs_by_level(self, level: str, log_file: str = "app.log", 
                           max_results: int = 100) -> list:
        """依日誌等級過濾日誌"""
        try:
            log_path = self.log_dir / log_file
            if not log_path.exists():
                return []
            
            results = []
            level_upper = level.upper()
            
            with open(log_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    if f" - {level_upper} - " in line:
                        results.append({
                            'line_number': line_num,
                            'content': line.strip(),
                            'timestamp': self._extract_timestamp(line),
                            'level': level_upper
                        })
                        
                        if len(results) >= max_results:
                            break
            
            return results
        
        except Exception as e:
            self.error(f"過濾日誌時發生錯誤: {e}")
            return []
    
    def filter_logs_by_date(self, start_date: datetime, end_date: datetime = None,
                           log_file: str = "app.log", max_results: int = 100) -> list:
        """依日期範圍過濾日誌"""
        try:
            log_path = self.log_dir / log_file
            if not log_path.exists():
                return []
            
            if end_date is None:
                end_date = datetime.now()
            
            results = []
            
            with open(log_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    timestamp = self._extract_timestamp(line)
                    if timestamp and start_date <= timestamp <= end_date:
                        results.append({
                            'line_number': line_num,
                            'content': line.strip(),
                            'timestamp': timestamp
                        })
                        
                        if len(results) >= max_results:
                            break
            
            return results
        
        except Exception as e:
            self.error(f"依日期過濾日誌時發生錯誤: {e}")
            return []
    
    def _extract_timestamp(self, log_line: str) -> Optional[datetime]:
        """從日誌行中提取時間戳"""
        try:
            # 假設日誌格式為: 2024-01-01 12:00:00 - LoggerName - LEVEL - Message
            if ' - ' in log_line:
                timestamp_str = log_line.split(' - ')[0]
                return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        except:
            pass
        return None
    
    def get_log_statistics(self, log_file: str = "app.log") -> dict:
        """取得日誌統計資訊"""
        try:
            log_path = self.log_dir / log_file
            if not log_path.exists():
                return {}
            
            stats = {
                'total_lines': 0,
                'levels': {'DEBUG': 0, 'INFO': 0, 'WARNING': 0, 'ERROR': 0, 'CRITICAL': 0},
                'file_size': log_path.stat().st_size,
                'last_modified': datetime.fromtimestamp(log_path.stat().st_mtime),
                'date_range': {'start': None, 'end': None}
            }
            
            with open(log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    stats['total_lines'] += 1
                    
                    # 統計日誌等級
                    for level in stats['levels']:
                        if f" - {level} - " in line:
                            stats['levels'][level] += 1
                            break
                    
                    # 記錄日期範圍
                    timestamp = self._extract_timestamp(line)
                    if timestamp:
                        if stats['date_range']['start'] is None or timestamp < stats['date_range']['start']:
                            stats['date_range']['start'] = timestamp
                        if stats['date_range']['end'] is None or timestamp > stats['date_range']['end']:
                            stats['date_range']['end'] = timestamp
            
            return stats
        
        except Exception as e:
            self.error(f"取得日誌統計時發生錯誤: {e}")
            return {}


class TaskLogger:
    """任務專用日誌記錄器"""
    
    def __init__(self, task_name: str, logging_service: LoggingService):
        self.task_name = task_name
        self.logging_service = logging_service
        self.logger = logging_service.get_logger(f"Task_{task_name}")
        self.start_time = datetime.now()
        
        self.logger.info(f"=== 任務開始: {task_name} ===")
    
    def log_progress(self, message: str, progress: Optional[float] = None) -> None:
        """記錄任務進度"""
        if progress is not None:
            message = f"[{progress:.1f}%] {message}"
        self.logger.info(message)
    
    def log_step(self, step_name: str, details: str = "") -> None:
        """記錄任務步驟"""
        message = f"步驟: {step_name}"
        if details:
            message += f" - {details}"
        self.logger.info(message)
    
    def log_error(self, error_message: str, exception: Optional[Exception] = None) -> None:
        """記錄任務錯誤"""
        self.logger.error(f"任務錯誤: {error_message}")
        if exception:
            self.logger.exception(f"例外詳情: {str(exception)}")
    
    def log_completion(self, success: bool = True, summary: str = "") -> None:
        """記錄任務完成"""
        duration = datetime.now() - self.start_time
        status = "成功" if success else "失敗"
        
        message = f"=== 任務{status}: {self.task_name} (耗時: {duration}) ==="
        if summary:
            message += f"\n摘要: {summary}"
        
        if success:
            self.logger.info(message)
        else:
            self.logger.error(message)


# 全域日誌服務實例
logging_service = LoggingService()


# 便利函數
def get_logger(name: str = "AIWorkstation") -> logging.Logger:
    """取得日誌記錄器的便利函數"""
    return logging_service.get_logger(name)


def log_info(message: str, logger_name: str = "AIWorkstation") -> None:
    """記錄資訊的便利函數"""
    logging_service.info(message, logger_name)


def log_error(message: str, logger_name: str = "AIWorkstation", 
              exc_info: bool = False) -> None:
    """記錄錯誤的便利函數"""
    logging_service.error(message, logger_name, exc_info)


def log_exception(exception: Exception, 
                 logger_name: str = "AIWorkstation") -> None:
    """記錄例外的便利函數"""
    logging_service.log_exception(exception, logger_name)


if __name__ == "__main__":
    # 測試程式
    print("=== 日誌服務測試 ===")
    
    # 記錄系統和配置資訊
    logging_service.log_system_info()
    logging_service.log_config_info()
    
    # 測試不同等級的日誌
    logging_service.debug("這是除錯訊息")
    logging_service.info("這是資訊訊息")
    logging_service.warning("這是警告訊息")
    logging_service.error("這是錯誤訊息")
    
    # 測試任務日誌
    task_logger = TaskLogger("測試任務", logging_service)
    task_logger.log_step("初始化", "準備測試資料")
    task_logger.log_progress("處理中", 50.0)
    task_logger.log_completion(True, "測試完成")
    
    # 顯示日誌檔案
    log_files = logging_service.get_log_files()
    print(f"\n日誌檔案: {[f.name for f in log_files]}")
    
    # 顯示最近的日誌
    recent_logs = logging_service.get_recent_logs(5)
    print(f"\n最近 5 行日誌:")
    for line in recent_logs:
        print(line.strip())
