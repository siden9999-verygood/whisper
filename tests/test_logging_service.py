"""
日誌服務測試
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import logging
from datetime import datetime, timedelta

from logging_service import LoggingService, TaskLogger


class TestLoggingService(unittest.TestCase):
    """測試 LoggingService 類別"""
    
    def setUp(self):
        """測試前設定"""
        # 建立臨時日誌目錄
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # 建立測試用的日誌服務
        self.logging_service = LoggingService()
        
        # 暫時替換日誌目錄
        self.original_log_dir = self.logging_service.log_dir
        self.logging_service.log_dir = self.temp_dir
        
        # 重新設定主要日誌記錄器
        self.logging_service._setup_main_logger()
    
    def tearDown(self):
        """測試後清理"""
        # 恢復原始日誌目錄
        self.logging_service.log_dir = self.original_log_dir
        
        # 清理臨時目錄
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_logger_creation(self):
        """測試日誌記錄器建立"""
        logger = self.logging_service.get_logger("test_logger")
        
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, "test_logger")
        self.assertIn("test_logger", self.logging_service.loggers)
    
    def test_log_levels(self):
        """測試不同日誌等級"""
        test_logger = "test_levels"
        
        # 測試各種日誌等級
        self.logging_service.debug("Debug message", test_logger)
        self.logging_service.info("Info message", test_logger)
        self.logging_service.warning("Warning message", test_logger)
        self.logging_service.error("Error message", test_logger)
        self.logging_service.critical("Critical message", test_logger)
        
        # 檢查日誌檔案是否建立
        log_file = self.temp_dir / "app.log"
        self.assertTrue(log_file.exists())
        
        # 檢查日誌內容
        log_content = log_file.read_text(encoding='utf-8')
        self.assertIn("Info message", log_content)
        self.assertIn("Warning message", log_content)
        self.assertIn("Error message", log_content)
        self.assertIn("Critical message", log_content)
    
    def test_exception_logging(self):
        """測試例外記錄"""
        try:
            raise ValueError("Test exception")
        except ValueError as e:
            self.logging_service.log_exception(e, "test_exception")
        
        # 檢查錯誤日誌檔案
        error_log_file = self.temp_dir / "error.log"
        self.assertTrue(error_log_file.exists())
        
        error_content = error_log_file.read_text(encoding='utf-8')
        self.assertIn("Test exception", error_content)
        self.assertIn("ValueError", error_content)
    
    def test_session_logger(self):
        """測試會話日誌記錄器"""
        session_id = "test_session_123"
        session_logger = self.logging_service.create_session_log(session_id)
        
        self.assertIsInstance(session_logger, logging.Logger)
        self.assertEqual(session_logger.name, f"Session_{session_id}")
        
        # 記錄一些訊息
        session_logger.info("Session test message")
        
        # 檢查會話日誌檔案
        session_log_file = self.temp_dir / f"session_{session_id}.log"
        self.assertTrue(session_log_file.exists())
        
        session_content = session_log_file.read_text(encoding='utf-8')
        self.assertIn("Session test message", session_content)
    
    def test_get_log_files(self):
        """測試取得日誌檔案清單"""
        # 記錄一些訊息以建立日誌檔案
        self.logging_service.info("Test message")
        self.logging_service.error("Test error")
        
        log_files = self.logging_service.get_log_files()
        
        self.assertIsInstance(log_files, list)
        self.assertGreater(len(log_files), 0)
        
        # 檢查是否包含預期的日誌檔案
        file_names = [f.name for f in log_files]
        self.assertIn("app.log", file_names)
        self.assertIn("error.log", file_names)
    
    def test_get_recent_logs(self):
        """測試取得最近的日誌記錄"""
        # 記錄一些測試訊息
        test_messages = ["Message 1", "Message 2", "Message 3"]
        for msg in test_messages:
            self.logging_service.info(msg)
        
        # 取得最近的日誌
        recent_logs = self.logging_service.get_recent_logs(lines=5)
        
        self.assertIsInstance(recent_logs, list)
        self.assertGreater(len(recent_logs), 0)
        
        # 檢查是否包含測試訊息
        log_content = ''.join(recent_logs)
        for msg in test_messages:
            self.assertIn(msg, log_content)
    
    def test_search_logs(self):
        """測試日誌搜尋"""
        # 記錄一些測試訊息
        self.logging_service.info("Search test message 1")
        self.logging_service.info("Another message")
        self.logging_service.info("Search test message 2")
        
        # 搜尋包含 "Search test" 的日誌
        results = self.logging_service.search_logs("Search test")
        
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 2)
        
        # 檢查搜尋結果
        for result in results:
            self.assertIn("Search test", result['content'])
            self.assertIn('line_number', result)
    
    def test_filter_logs_by_level(self):
        """測試依等級過濾日誌"""
        # 記錄不同等級的訊息
        self.logging_service.info("Info message")
        self.logging_service.warning("Warning message")
        self.logging_service.error("Error message")
        
        # 過濾錯誤等級的日誌
        error_logs = self.logging_service.filter_logs_by_level("ERROR")
        
        self.assertIsInstance(error_logs, list)
        self.assertGreater(len(error_logs), 0)
        
        # 檢查過濾結果
        for log in error_logs:
            self.assertIn("ERROR", log['content'])
    
    def test_filter_logs_by_date(self):
        """測試依日期過濾日誌"""
        # 記錄一些訊息
        self.logging_service.info("Date filter test")
        
        # 設定日期範圍（今天）
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        
        # 過濾今天的日誌
        today_logs = self.logging_service.filter_logs_by_date(start_date, end_date)
        
        self.assertIsInstance(today_logs, list)
        # 應該至少有一筆今天的日誌
        self.assertGreater(len(today_logs), 0)
    
    def test_cleanup_old_logs(self):
        """測試清理舊日誌"""
        # 建立一個舊的日誌檔案
        old_log_file = self.temp_dir / "old.log"
        old_log_file.write_text("Old log content")
        
        # 修改檔案時間為31天前
        import os
        old_time = datetime.now().timestamp() - (31 * 24 * 3600)
        os.utime(old_log_file, (old_time, old_time))
        
        # 執行清理
        self.logging_service.cleanup_old_logs(days_to_keep=30)
        
        # 檢查舊檔案是否被刪除
        self.assertFalse(old_log_file.exists())
    
    def test_log_statistics(self):
        """測試日誌統計"""
        # 記錄不同等級的訊息
        self.logging_service.info("Info message 1")
        self.logging_service.info("Info message 2")
        self.logging_service.warning("Warning message")
        self.logging_service.error("Error message")
        
        # 取得統計資訊
        stats = self.logging_service.get_log_statistics()
        
        self.assertIsInstance(stats, dict)
        self.assertIn('total_lines', stats)
        self.assertIn('levels', stats)
        self.assertIn('file_size', stats)
        
        # 檢查等級統計
        levels = stats['levels']
        self.assertGreater(levels['INFO'], 0)
        self.assertGreater(levels['WARNING'], 0)
        self.assertGreater(levels['ERROR'], 0)


class TestTaskLogger(unittest.TestCase):
    """測試 TaskLogger 類別"""
    
    def setUp(self):
        """測試前設定"""
        # 建立臨時日誌目錄
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # 建立測試用的日誌服務
        self.logging_service = LoggingService()
        self.logging_service.log_dir = self.temp_dir
        self.logging_service._setup_main_logger()
    
    def tearDown(self):
        """測試後清理"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_task_logger_creation(self):
        """測試任務日誌記錄器建立"""
        task_name = "test_task"
        task_logger = TaskLogger(task_name, self.logging_service)
        
        self.assertEqual(task_logger.task_name, task_name)
        self.assertIsInstance(task_logger.start_time, datetime)
        self.assertIsInstance(task_logger.logger, logging.Logger)
    
    def test_task_progress_logging(self):
        """測試任務進度記錄"""
        task_logger = TaskLogger("progress_test", self.logging_service)
        
        # 記錄進度
        task_logger.log_progress("Processing files", 25.5)
        task_logger.log_progress("Almost done", 90.0)
        task_logger.log_progress("Finished")
        
        # 檢查日誌內容
        log_file = self.temp_dir / "app.log"
        log_content = log_file.read_text(encoding='utf-8')
        
        self.assertIn("[25.5%] Processing files", log_content)
        self.assertIn("[90.0%] Almost done", log_content)
        self.assertIn("Finished", log_content)
    
    def test_task_step_logging(self):
        """測試任務步驟記錄"""
        task_logger = TaskLogger("step_test", self.logging_service)
        
        # 記錄步驟
        task_logger.log_step("Initialize", "Setting up environment")
        task_logger.log_step("Process", "Processing data")
        task_logger.log_step("Cleanup")
        
        # 檢查日誌內容
        log_file = self.temp_dir / "app.log"
        log_content = log_file.read_text(encoding='utf-8')
        
        self.assertIn("步驟: Initialize - Setting up environment", log_content)
        self.assertIn("步驟: Process - Processing data", log_content)
        self.assertIn("步驟: Cleanup", log_content)
    
    def test_task_error_logging(self):
        """測試任務錯誤記錄"""
        task_logger = TaskLogger("error_test", self.logging_service)
        
        # 記錄錯誤
        try:
            raise ValueError("Test task error")
        except ValueError as e:
            task_logger.log_error("Task failed", e)
        
        # 檢查錯誤日誌
        error_log_file = self.temp_dir / "error.log"
        error_content = error_log_file.read_text(encoding='utf-8')
        
        self.assertIn("任務錯誤: Task failed", error_content)
        self.assertIn("Test task error", error_content)
    
    def test_task_completion_logging(self):
        """測試任務完成記錄"""
        task_logger = TaskLogger("completion_test", self.logging_service)
        
        # 模擬一些處理時間
        import time
        time.sleep(0.1)
        
        # 記錄成功完成
        task_logger.log_completion(True, "Task completed successfully")
        
        # 檢查日誌內容
        log_file = self.temp_dir / "app.log"
        log_content = log_file.read_text(encoding='utf-8')
        
        self.assertIn("任務成功: completion_test", log_content)
        self.assertIn("Task completed successfully", log_content)
        self.assertIn("耗時:", log_content)
        
        # 測試失敗完成
        task_logger2 = TaskLogger("failure_test", self.logging_service)
        task_logger2.log_completion(False, "Task failed")
        
        log_content = log_file.read_text(encoding='utf-8')
        self.assertIn("任務失敗: failure_test", log_content)


if __name__ == '__main__':
    unittest.main()
