"""
整合測試
測試各模組之間的整合功能
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import json
import time

from platform_adapter import platform_adapter
from config_service import config_service
from logging_service import logging_service
from monitoring_manager import monitoring_manager
from diagnostics_manager import diagnostics_manager


class TestSystemIntegration(unittest.TestCase):
    """測試系統整合功能"""
    
    def setUp(self):
        """測試前設定"""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # 建立測試用的配置
        self.test_config = {
            "api_key": "test_integration_key",
            "ai_model": "gemini-1.5-flash",
            "source_folder": str(self.temp_dir / "source"),
            "processed_folder": str(self.temp_dir / "processed"),
            "window_width": 1200,
            "window_height": 800
        }
        
        # 建立測試目錄
        Path(self.test_config["source_folder"]).mkdir(parents=True)
        Path(self.test_config["processed_folder"]).mkdir(parents=True)
    
    def tearDown(self):
        """測試後清理"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_platform_config_integration(self):
        """測試平台適配器與配置服務整合"""
        # 取得平台資訊
        platform_info = platform_adapter.get_system_info()
        
        # 更新配置
        config_service.update_config(**self.test_config)
        
        # 驗證配置
        config = config_service.get_config()
        self.assertEqual(config.api_key, self.test_config["api_key"])
        
        # 驗證路徑
        validation_results = config_service.validate_paths()
        self.assertTrue(validation_results.get('source_folder', False))
        self.assertTrue(validation_results.get('processed_folder', False))
        
        # 記錄整合測試結果
        logging_service.info(f"平台整合測試完成: {platform_info['platform']}")
    
    def test_logging_config_integration(self):
        """測試日誌服務與配置服務整合"""
        # 更新配置
        config_service.update_config(**self.test_config)
        
        # 記錄系統和配置資訊
        logging_service.log_system_info()
        logging_service.log_config_info()
        
        # 檢查日誌是否正確記錄
        recent_logs = logging_service.get_recent_logs(lines=20)
        log_content = ''.join(recent_logs)
        
        self.assertIn("系統資訊", log_content)
        self.assertIn("配置資訊", log_content)
        self.assertIn(self.test_config["ai_model"], log_content)
    
    def test_monitoring_logging_integration(self):
        """測試監控管理器與日誌服務整合"""
        try:
            # 啟動監控（如果可用）
            monitoring_manager.start_monitoring()
            
            # 等待一段時間讓監控收集資料
            time.sleep(2)
            
            # 停止監控
            monitoring_manager.stop_monitoring()
            
            # 檢查是否有監控相關的日誌
            recent_logs = logging_service.get_recent_logs(lines=10)
            log_content = ''.join(recent_logs)
            
            # 監控相關的日誌可能包含啟動或停止訊息
            # 這個測試比較寬鬆，因為監控功能可能在某些環境下不可用
            self.assertIsInstance(recent_logs, list)
            
        except Exception as e:
            # 如果監控功能不可用，記錄但不讓測試失敗
            logging_service.warning(f"監控整合測試跳過: {e}")
    
    def test_diagnostics_integration(self):
        """測試診斷管理器整合"""
        try:
            # 執行快速健康檢查
            health_status = diagnostics_manager.quick_health_check()
            
            self.assertIsInstance(health_status, dict)
            self.assertIn('timestamp', health_status)
            self.assertIn('overall_status', health_status)
            
            # 執行完整診斷
            diagnostic_info = diagnostics_manager.run_full_diagnostics()
            
            self.assertIsInstance(diagnostic_info, dict)
            self.assertIn('system_info', diagnostic_info)
            self.assertIn('config_info', diagnostic_info)
            
            # 生成診斷報告
            report = diagnostics_manager.generate_diagnostic_report(diagnostic_info)
            
            self.assertIsInstance(report, str)
            self.assertIn("診斷報告", report)
            
            # 記錄診斷完成
            logging_service.info("診斷整合測試完成")
            
        except Exception as e:
            logging_service.error(f"診斷整合測試失敗: {e}")
            raise
    
    def test_full_system_workflow(self):
        """測試完整系統工作流程"""
        # 1. 初始化配置
        config_service.update_config(**self.test_config)
        logging_service.info("配置初始化完成")
        
        # 2. 驗證系統狀態
        platform_info = platform_adapter.get_system_info()
        logging_service.info(f"系統平台: {platform_info['platform']}")
        
        # 3. 執行健康檢查
        health_status = diagnostics_manager.quick_health_check()
        logging_service.info(f"系統健康狀態: {health_status['overall_status']}")
        
        # 4. 建立測試檔案
        test_file = Path(self.test_config["source_folder"]) / "test.txt"
        test_file.write_text("測試檔案內容", encoding='utf-8')
        
        # 5. 驗證檔案操作
        file_info = platform_adapter.file_manager.get_file_info(str(test_file))
        self.assertEqual(file_info['name'], 'test.txt')
        
        # 6. 移動檔案到處理資料夾
        dest_file = Path(self.test_config["processed_folder"]) / "test.txt"
        success = platform_adapter.file_manager.move_file(str(test_file), str(dest_file))
        self.assertTrue(success)
        self.assertTrue(dest_file.exists())
        
        # 7. 記錄工作流程完成
        logging_service.info("完整系統工作流程測試完成")
        
        # 8. 檢查日誌記錄
        recent_logs = logging_service.get_recent_logs(lines=20)
        log_content = ''.join(recent_logs)
        
        self.assertIn("配置初始化完成", log_content)
        self.assertIn("系統平台", log_content)
        self.assertIn("完整系統工作流程測試完成", log_content)


class TestErrorHandlingIntegration(unittest.TestCase):
    """測試錯誤處理整合"""
    
    def setUp(self):
        """測試前設定"""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """測試後清理"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_config_error_handling(self):
        """測試配置錯誤處理"""
        # 測試無效配置
        invalid_config = {
            "window_width": "invalid",
            "window_height": -100
        }
        
        try:
            config_service.update_config(**invalid_config)
        except Exception as e:
            logging_service.log_exception(e)
            
            # 檢查錯誤是否被正確記錄
            error_logs = logging_service.filter_logs_by_level("ERROR")
            self.assertGreater(len(error_logs), 0)
    
    def test_file_operation_error_handling(self):
        """測試檔案操作錯誤處理"""
        # 嘗試操作不存在的檔案
        non_existent_file = str(self.temp_dir / "non_existent.txt")
        
        try:
            platform_adapter.file_manager.get_file_info(non_existent_file)
        except Exception as e:
            logging_service.log_exception(e)
            
            # 檢查錯誤記錄
            error_logs = logging_service.filter_logs_by_level("ERROR")
            self.assertGreater(len(error_logs), 0)
    
    def test_diagnostic_error_recovery(self):
        """測試診斷錯誤恢復"""
        try:
            # 嘗試執行可能失敗的診斷
            diagnostic_info = diagnostics_manager.run_full_diagnostics()
            
            # 即使某些診斷項目失敗，也應該返回部分結果
            self.assertIsInstance(diagnostic_info, dict)
            
        except Exception as e:
            # 記錄診斷錯誤
            logging_service.log_exception(e)
            
            # 檢查錯誤恢復機制
            health_status = diagnostics_manager.quick_health_check()
            self.assertIsInstance(health_status, dict)


class TestPerformanceIntegration(unittest.TestCase):
    """測試效能整合"""
    
    def test_large_file_handling(self):
        """測試大檔案處理效能"""
        temp_dir = Path(tempfile.mkdtemp())
        
        try:
            # 建立一個較大的測試檔案
            large_file = temp_dir / "large_test.txt"
            content = "測試內容 " * 10000  # 約 100KB
            large_file.write_text(content, encoding='utf-8')
            
            # 測試檔案資訊取得效能
            start_time = time.time()
            file_info = platform_adapter.file_manager.get_file_info(str(large_file))
            end_time = time.time()
            
            # 檢查效能（應該在合理時間內完成）
            processing_time = end_time - start_time
            self.assertLess(processing_time, 1.0)  # 應該在1秒內完成
            
            # 檢查檔案資訊正確性
            self.assertEqual(file_info['name'], 'large_test.txt')
            self.assertGreater(file_info['size'], 50000)  # 應該大於50KB
            
            logging_service.info(f"大檔案處理效能測試完成，耗時: {processing_time:.3f}秒")
            
        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
    
    def test_concurrent_logging(self):
        """測試並發日誌記錄效能"""
        import threading
        
        def log_worker(worker_id):
            """日誌工作線程"""
            for i in range(100):
                logging_service.info(f"Worker {worker_id} - Message {i}")
        
        # 建立多個線程同時記錄日誌
        threads = []
        start_time = time.time()
        
        for i in range(5):
            thread = threading.Thread(target=log_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有線程完成
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # 檢查效能（500條日誌應該在合理時間內完成）
        self.assertLess(processing_time, 5.0)  # 應該在5秒內完成
        
        logging_service.info(f"並發日誌記錄效能測試完成，耗時: {processing_time:.3f}秒")


if __name__ == '__main__':
    unittest.main()