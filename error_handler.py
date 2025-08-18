"""
統一錯誤處理模組
提供應用程式級別的錯誤處理和異常管理
"""

import sys
import traceback
import logging
from typing import Optional, Callable, Any
from pathlib import Path
from datetime import datetime

from logging_service import logging_service


class ErrorSeverity:
    """錯誤嚴重程度"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ApplicationError(Exception):
    """應用程式基礎錯誤類別"""
    
    def __init__(self, message: str, severity: str = ErrorSeverity.ERROR, 
                 context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.severity = severity
        self.context = context or {}
        self.timestamp = datetime.now()


class ConfigurationError(ApplicationError):
    """配置相關錯誤"""
    pass


class DependencyError(ApplicationError):
    """依賴項錯誤"""
    pass


class ProcessingError(ApplicationError):
    """處理過程錯誤"""
    pass


class FileSystemError(ApplicationError):
    """檔案系統錯誤"""
    pass


class NetworkError(ApplicationError):
    """網路相關錯誤"""
    pass


class ErrorHandler:
    """統一錯誤處理器"""
    
    def __init__(self):
        self.logger = logging_service.get_logger("ErrorHandler")
        self.error_callbacks: Dict[str, Callable] = {}
        self.error_count = 0
        self.last_errors = []
        self.max_error_history = 100
    
    def register_callback(self, error_type: str, callback: Callable):
        """註冊錯誤回調函數"""
        self.error_callbacks[error_type] = callback
    
    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """處理未捕獲的異常"""
        if issubclass(exc_type, KeyboardInterrupt):
            # 允許 Ctrl+C 正常退出
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        error_msg = f"未處理的異常: {exc_type.__name__}: {exc_value}"
        tb_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        
        self.logger.critical(f"{error_msg}\n{tb_str}")
        
        # 記錄錯誤
        self._record_error(error_msg, ErrorSeverity.CRITICAL, {
            "exception_type": exc_type.__name__,
            "traceback": tb_str
        })
        
        # 顯示用戶友好的錯誤訊息
        self._show_error_message(
            "程式錯誤",
            f"程式遇到未預期的錯誤:\n{exc_type.__name__}: {exc_value}\n\n"
            f"請檢查日誌檔案或聯繫技術支援。"
        )
    
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """處理應用程式錯誤"""
        if isinstance(error, ApplicationError):
            severity = error.severity
            message = error.message
            error_context = {**error.context, **(context or {})}
        else:
            severity = ErrorSeverity.ERROR
            message = str(error)
            error_context = context or {}
        
        # 記錄錯誤
        self._record_error(message, severity, error_context)
        
        # 根據錯誤類型執行回調
        error_type = type(error).__name__
        if error_type in self.error_callbacks:
            try:
                self.error_callbacks[error_type](error, error_context)
            except Exception as callback_error:
                self.logger.error(f"錯誤回調執行失敗: {callback_error}")
        
        # 根據嚴重程度決定處理方式
        if severity == ErrorSeverity.CRITICAL:
            self._handle_critical_error(error, error_context)
        elif severity == ErrorSeverity.ERROR:
            self._handle_error(error, error_context)
        elif severity == ErrorSeverity.WARNING:
            self._handle_warning(error, error_context)
    
    def _record_error(self, message: str, severity: str, context: Dict[str, Any]):
        """記錄錯誤到歷史"""
        self.error_count += 1
        
        error_record = {
            "id": self.error_count,
            "timestamp": datetime.now(),
            "message": message,
            "severity": severity,
            "context": context
        }
        
        self.last_errors.append(error_record)
        
        # 限制錯誤歷史數量
        if len(self.last_errors) > self.max_error_history:
            self.last_errors = self.last_errors[-self.max_error_history:]
        
        # 記錄到日誌
        log_method = getattr(self.logger, severity.lower(), self.logger.error)
        log_method(f"{message} | Context: {context}")
    
    def _handle_critical_error(self, error: Exception, context: Dict[str, Any]):
        """處理嚴重錯誤"""
        self._show_error_message(
            "嚴重錯誤",
            f"程式遇到嚴重錯誤，可能需要重新啟動:\n{error}\n\n"
            f"錯誤已記錄到日誌檔案。"
        )
    
    def _handle_error(self, error: Exception, context: Dict[str, Any]):
        """處理一般錯誤"""
        self._show_error_message("錯誤", f"操作失敗:\n{error}")
    
    def _handle_warning(self, error: Exception, context: Dict[str, Any]):
        """處理警告"""
        self._show_warning_message("警告", str(error))
    
    def _show_error_message(self, title: str, message: str):
        """跨平台顯示錯誤訊息"""
        try:
            # 嘗試使用 tkinter 顯示 GUI 訊息框
            import tkinter.messagebox as messagebox
            messagebox.showerror(title, message)
        except (ImportError, Exception):
            # 如果 GUI 不可用，則輸出到控制台
            print(f"{title}: {message}")
    
    def _show_warning_message(self, title: str, message: str):
        """跨平台顯示警告訊息"""
        try:
            # 嘗試使用 tkinter 顯示 GUI 訊息框
            import tkinter.messagebox as messagebox
            messagebox.showwarning(title, message)
        except (ImportError, Exception):
            # 如果 GUI 不可用，則輸出到控制台
            print(f"{title}: {message}")
    
    def get_error_summary(self) -> Dict[str, Any]:
        """取得錯誤摘要"""
        severity_counts = {}
        for error in self.last_errors:
            severity = error["severity"]
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            "total_errors": self.error_count,
            "recent_errors": len(self.last_errors),
            "severity_breakdown": severity_counts,
            "last_error": self.last_errors[-1] if self.last_errors else None
        }
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """取得最近的錯誤"""
        return self.last_errors[-limit:] if self.last_errors else []
    
    def clear_error_history(self):
        """清除錯誤歷史"""
        self.last_errors.clear()
        self.logger.info("錯誤歷史已清除")


# 全域錯誤處理器實例
error_handler = ErrorHandler()

# 設定全域異常處理
sys.excepthook = error_handler.handle_exception


def handle_error(error: Exception, context: Optional[Dict[str, Any]] = None):
    """便捷的錯誤處理函數"""
    error_handler.handle_error(error, context)


def safe_execute(func: Callable, *args, **kwargs) -> Any:
    """安全執行函數，自動處理異常"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        handle_error(e, {"function": func.__name__, "args": args, "kwargs": kwargs})
        return None


if __name__ == "__main__":
    # 測試錯誤處理
    print("=== 錯誤處理模組測試 ===")
    
    # 測試不同類型的錯誤
    try:
        raise ConfigurationError("測試配置錯誤", ErrorSeverity.WARNING)
    except Exception as e:
        handle_error(e)
    
    try:
        raise ProcessingError("測試處理錯誤", ErrorSeverity.ERROR)
    except Exception as e:
        handle_error(e)
    
    # 顯示錯誤摘要
    summary = error_handler.get_error_summary()
    print(f"錯誤摘要: {summary}")