"""
效能測試
測試系統在各種負載下的效能表現
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import time
import threading
import concurrent.futures
import gc
import sys

from platform_adapter import platform_adapter
from config_service import config_service
from logging_service import logging_service


class TestPerformance(unittest.TestCase):
    """效能測試基礎類別"""
    
    def setUp(self):
        """測試前設定"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.performance_threshold = {
            'file_operation': 1.0,  # 檔案操作應在1秒內完成
            'config_operation': 0.1,  # 配置操作應在0.1秒內完成
            'logging_operation': 0.01,  # 日誌操作應在0.01秒內完成
        }
    
    def tearDown(self):
        """測試後清理"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def measure_time(self, func, *args, **kwargs):
        """測量函數執行時間"""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return result, end_time - start_time
    
    def assert_performance(self, execution_time, threshold, operation_name):
        """斷言效能符合要求"""
        self.assertLess(
            execution_time, 
            threshold,
            f"{operation_name} 執行時間 {execution_time:.3f}s 超過閾值 {threshold}s"
        )


class TestFileOperationPerformance(TestPerformance):
    """檔案操作效能測試"""
    
    def test_single_file_operations(self):
        """測試單一檔案操作效能"""
        # 建立測試檔案
        test_file = self.temp_dir / "performance_test.txt"
        test_content = "Performance test content " * 1000  # 約 25KB
        
        # 測試檔案寫入效能
        _, write_time = self.measure_time(
            test_file.write_text, 
            test_content, 
            encoding='utf-8'
        )
        self.assert_performance(write_time, self.performance_threshold['file_operation'], "檔案寫入")
        
        # 測試檔案讀取效能
        _, read_time = self.measure_time(
            test_file.read_text, 
            encoding='utf-8'
        )
        self.assert_performance(read_time, self.performance_threshold['file_operation'], "檔案讀取")
        
        # 測試檔案資訊取得效能
        _, info_time = self.measure_time(
            platform_adapter.file_manager.get_file_info,
            str(test_file)
        )
        self.assert_performance(info_time, self.performance_threshold['file_operation'], "檔案資訊取得")
    
    def test_multiple_file_operations(self):
        """測試多檔案操作效能"""
        file_count = 100
        files = []
        
        # 建立多個測試檔案
        start_time = time.time()
        for i in range(file_count):
            test_file = self.temp_dir / f"test_file_{i}.txt"
            test_file.write_text(f"Content for file {i}", encoding='utf-8')
            files.append(test_file)
        creation_time = time.time() - start_time
        
        # 檔案建立應該在合理時間內完成
        self.assertLess(creation_time, 5.0, f"建立 {file_count} 個檔案耗時過長: {creation_time:.3f}s")
        
        # 測試批次檔案資訊取得
        start_time = time.time()
        for file_path in files:
            platform_adapter.file_manager.get_file_info(str(file_path))
        batch_info_time = time.time() - start_time
        
        self.assertLess(batch_info_time, 2.0, f"批次取得檔案資訊耗時過長: {batch_info_time:.3f}s")
        
        # 測試批次檔案刪除
        start_time = time.time()
        for file_path in files:
            platform_adapter.file_manager.delete_file(str(file_path))
        deletion_time = time.time() - start_time
        
        self.assertLess(deletion_time, 2.0, f"批次刪除檔案耗時過長: {deletion_time:.3f}s")
    
    def test_large_file_operations(self):
        """測試大檔案操作效能"""
        # 建立一個較大的測試檔案 (約 1MB)
        large_content = "Large file content " * 50000
        large_file = self.temp_dir / "large_test.txt"
        
        # 測試大檔案寫入
        _, write_time = self.measure_time(
            large_file.write_text,
            large_content,
            encoding='utf-8'
        )
        self.assertLess(write_time, 5.0, f"大檔案寫入耗時過長: {write_time:.3f}s")
        
        # 測試大檔案讀取
        _, read_time = self.measure_time(
            large_file.read_text,
            encoding='utf-8'
        )
        self.assertLess(read_time, 5.0, f"大檔案讀取耗時過長: {read_time:.3f}s")
        
        # 測試大檔案複製
        dest_file = self.temp_dir / "large_copy.txt"
        _, copy_time = self.measure_time(
            platform_adapter.file_manager.copy_file,
            str(large_file),
            str(dest_file)
        )
        self.assertLess(copy_time, 5.0, f"大檔案複製耗時過長: {copy_time:.3f}s")


class TestConfigurationPerformance(TestPerformance):
    """配置操作效能測試"""
    
    def test_config_load_save_performance(self):
        """測試配置載入和儲存效能"""
        # 測試配置載入
        _, load_time = self.measure_time(config_service.load_config)
        self.assert_performance(load_time, self.performance_threshold['config_operation'], "配置載入")
        
        # 測試配置儲存
        _, save_time = self.measure_time(config_service.save_config)
        self.assert_performance(save_time, self.performance_threshold['config_operation'], "配置儲存")
    
    def test_config_update_performance(self):
        """測試配置更新效能"""
        test_updates = {
            'api_key': 'performance_test_key',
            'ai_model': 'performance_test_model',
            'window_width': 1920,
            'window_height': 1080
        }
        
        # 測試配置更新
        _, update_time = self.measure_time(
            config_service.update_config,
            **test_updates
        )
        self.assert_performance(update_time, self.performance_threshold['config_operation'], "配置更新")
    
    def test_config_validation_performance(self):
        """測試配置驗證效能"""
        test_config = {
            'api_key': 'test_key',
            'ai_model': 'gemini-1.5-flash',
            'window_width': 1200,
            'window_height': 800,
            'source_folder': str(self.temp_dir / 'source'),
            'processed_folder': str(self.temp_dir / 'processed')
        }
        
        # 測試配置驗證
        _, validation_time = self.measure_time(
            config_service.validate_config,
            test_config
        )
        self.assert_performance(validation_time, self.performance_threshold['config_operation'], "配置驗證")


class TestLoggingPerformance(TestPerformance):
    """日誌效能測試"""
    
    def test_single_log_performance(self):
        """測試單一日誌記錄效能"""
        test_message = "Performance test log message"
        
        # 測試不同等級的日誌記錄效能
        log_methods = [
            ('debug', logging_service.debug),
            ('info', logging_service.info),
            ('warning', logging_service.warning),
            ('error', logging_service.error),
        ]
        
        for level_name, log_method in log_methods:
            _, log_time = self.measure_time(log_method, test_message)
            self.assert_performance(
                log_time, 
                self.performance_threshold['logging_operation'], 
                f"{level_name} 日誌記錄"
            )
    
    def test_batch_logging_performance(self):
        """測試批次日誌記錄效能"""
        message_count = 1000
        
        # 測試批次日誌記錄
        start_time = time.time()
        for i in range(message_count):
            logging_service.info(f"Batch log message {i}")
        batch_time = time.time() - start_time
        
        # 批次日誌記錄應該在合理時間內完成
        self.assertLess(batch_time, 5.0, f"批次記錄 {message_count} 條日誌耗時過長: {batch_time:.3f}s")
        
        # 平均每條日誌的記錄時間
        avg_time = batch_time / message_count
        self.assertLess(avg_time, 0.01, f"平均日誌記錄時間過長: {avg_time:.6f}s")
    
    def test_concurrent_logging_performance(self):
        """測試並發日誌記錄效能"""
        thread_count = 10
        messages_per_thread = 100
        
        def log_worker(worker_id):
            """日誌工作線程"""
            for i in range(messages_per_thread):
                logging_service.info(f"Worker {worker_id} - Message {i}")
        
        # 測試並發日誌記錄
        start_time = time.time()
        
        threads = []
        for i in range(thread_count):
            thread = threading.Thread(target=log_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        concurrent_time = time.time() - start_time
        total_messages = thread_count * messages_per_thread
        
        # 並發日誌記錄應該在合理時間內完成
        self.assertLess(concurrent_time, 10.0, f"並發記錄 {total_messages} 條日誌耗時過長: {concurrent_time:.3f}s")
    
    def test_log_search_performance(self):
        """測試日誌搜尋效能"""
        # 先記錄一些測試日誌
        for i in range(500):
            logging_service.info(f"Search test message {i}")
            if i % 10 == 0:
                logging_service.info(f"Special search target {i}")
        
        # 測試日誌搜尋效能
        _, search_time = self.measure_time(
            logging_service.search_logs,
            "Special search target"
        )
        
        self.assertLess(search_time, 2.0, f"日誌搜尋耗時過長: {search_time:.3f}s")


class TestMemoryPerformance(TestPerformance):
    """記憶體效能測試"""
    
    def test_memory_usage(self):
        """測試記憶體使用情況"""
        try:
            import psutil
            process = psutil.Process()
            
            # 記錄初始記憶體使用量
            initial_memory = process.memory_info().rss
            
            # 執行一些操作
            self._perform_memory_intensive_operations()
            
            # 強制垃圾回收
            gc.collect()
            
            # 記錄操作後的記憶體使用量
            final_memory = process.memory_info().rss
            
            # 記憶體增長應該在合理範圍內
            memory_growth = final_memory - initial_memory
            memory_growth_mb = memory_growth / (1024 * 1024)
            
            self.assertLess(memory_growth_mb, 100, f"記憶體增長過多: {memory_growth_mb:.1f}MB")
            
        except ImportError:
            self.skipTest("psutil 不可用，跳過記憶體測試")
    
    def _perform_memory_intensive_operations(self):
        """執行記憶體密集操作"""
        # 建立和刪除大量檔案
        files = []
        for i in range(100):
            test_file = self.temp_dir / f"memory_test_{i}.txt"
            test_file.write_text(f"Memory test content {i}" * 100, encoding='utf-8')
            files.append(test_file)
        
        # 讀取所有檔案
        for file_path in files:
            content = file_path.read_text(encoding='utf-8')
        
        # 刪除所有檔案
        for file_path in files:
            file_path.unlink()
        
        # 記錄大量日誌
        for i in range(200):
            logging_service.info(f"Memory test log {i}")
        
        # 執行配置操作
        for i in range(50):
            config_service.update_config(api_key=f"memory_test_key_{i}")


class TestStressTest(TestPerformance):
    """壓力測試"""
    
    def test_high_load_file_operations(self):
        """測試高負載檔案操作"""
        file_count = 500
        
        # 使用線程池進行並發檔案操作
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # 提交檔案建立任務
            futures = []
            start_time = time.time()
            
            for i in range(file_count):
                future = executor.submit(self._create_test_file, i)
                futures.append(future)
            
            # 等待所有任務完成
            concurrent.futures.wait(futures)
            
            creation_time = time.time() - start_time
            
            # 高負載檔案操作應該在合理時間內完成
            self.assertLess(creation_time, 30.0, f"高負載檔案建立耗時過長: {creation_time:.3f}s")
    
    def _create_test_file(self, file_id):
        """建立測試檔案"""
        test_file = self.temp_dir / f"stress_test_{file_id}.txt"
        content = f"Stress test file {file_id} content " * 100
        test_file.write_text(content, encoding='utf-8')
        
        # 取得檔案資訊
        platform_adapter.file_manager.get_file_info(str(test_file))
        
        return test_file
    
    def test_sustained_logging(self):
        """測試持續日誌記錄"""
        duration = 10  # 持續10秒
        start_time = time.time()
        message_count = 0
        
        # 持續記錄日誌
        while time.time() - start_time < duration:
            logging_service.info(f"Sustained logging test message {message_count}")
            message_count += 1
            time.sleep(0.01)  # 稍微延遲以避免過度負載
        
        actual_duration = time.time() - start_time
        
        # 檢查日誌記錄效率
        messages_per_second = message_count / actual_duration
        self.assertGreater(messages_per_second, 50, f"日誌記錄效率過低: {messages_per_second:.1f} msg/s")


if __name__ == '__main__':
    # 設定測試超時
    unittest.main(verbosity=2)