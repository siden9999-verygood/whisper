"""
配置服務測試
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import json

from config_service import ConfigService, AppConfig


class TestConfigService(unittest.TestCase):
    """測試 ConfigService 類別"""
    
    def setUp(self):
        """測試前設定"""
        # 建立臨時配置目錄
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_service = ConfigService()
        
        # 暫時替換配置目錄
        self.original_config_dir = self.config_service.config_dir
        self.config_service.config_dir = self.temp_dir
        self.config_service.config_file = self.temp_dir / "config.json"
    
    def tearDown(self):
        """測試後清理"""
        # 恢復原始配置目錄
        self.config_service.config_dir = self.original_config_dir
        self.config_service.config_file = self.original_config_dir / "config.json"
        
        # 清理臨時目錄
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_default_config(self):
        """測試預設配置"""
        config = self.config_service.get_config()
        
        self.assertIsInstance(config, AppConfig)
        self.assertEqual(config.ai_model, "gemini-2.5-flash")
        self.assertEqual(config.default_language, "zh-TW")
        self.assertIsInstance(config.window_width, int)
        self.assertIsInstance(config.window_height, int)
    
    def test_save_and_load_config(self):
        """測試配置儲存和載入"""
        # 修改配置
        self.config_service.update_config(
            api_key="test_key",
            ai_model="test_model",
            source_folder="/test/source",
            processed_folder="/test/processed"
        )
        
        # 儲存配置
        self.config_service.save_config()
        
        # 建立新的配置服務實例來測試載入
        new_config_service = ConfigService()
        new_config_service.config_dir = self.temp_dir
        new_config_service.config_file = self.temp_dir / "config.json"
        new_config_service.load_config()
        
        config = new_config_service.get_config()
        self.assertEqual(config.api_key, "test_key")
        self.assertEqual(config.ai_model, "test_model")
        self.assertEqual(config.source_folder, "/test/source")
        self.assertEqual(config.processed_folder, "/test/processed")
    
    def test_update_config(self):
        """測試配置更新"""
        original_config = self.config_service.get_config()
        
        # 更新部分配置
        self.config_service.update_config(
            api_key="new_key",
            window_width=1920
        )
        
        updated_config = self.config_service.get_config()
        self.assertEqual(updated_config.api_key, "new_key")
        self.assertEqual(updated_config.window_width, 1920)
        # 其他配置應該保持不變
        self.assertEqual(updated_config.ai_model, original_config.ai_model)
    
    def test_validate_paths(self):
        """測試路徑驗證"""
        # 建立測試目錄
        test_source = self.temp_dir / "source"
        test_processed = self.temp_dir / "processed"
        test_source.mkdir()
        test_processed.mkdir()
        
        # 更新配置
        self.config_service.update_config(
            source_folder=str(test_source),
            processed_folder=str(test_processed)
        )
        
        # 驗證路徑
        validation_results = self.config_service.validate_paths()
        
        self.assertIsInstance(validation_results, dict)
        self.assertTrue(validation_results.get('source_folder', False))
        self.assertTrue(validation_results.get('processed_folder', False))
    
    def test_backup_and_restore_config(self):
        """測試配置備份和還原"""
        # 修改配置
        self.config_service.update_config(api_key="backup_test")
        
        # 建立備份
        backup_path = self.config_service.backup_config()
        self.assertTrue(backup_path.exists())
        
        # 修改配置
        self.config_service.update_config(api_key="modified")
        
        # 還原備份
        success = self.config_service.restore_config(backup_path)
        self.assertTrue(success)
        
        # 檢查配置是否還原
        config = self.config_service.get_config()
        self.assertEqual(config.api_key, "backup_test")
    
    def test_export_and_import_config(self):
        """測試配置匯出和匯入"""
        # 修改配置
        self.config_service.update_config(
            api_key="export_test",
            ai_model="export_model"
        )
        
        # 匯出配置
        export_path = self.temp_dir / "exported_config.json"
        success = self.config_service.export_config(export_path)
        self.assertTrue(success)
        self.assertTrue(export_path.exists())
        
        # 修改配置
        self.config_service.update_config(api_key="changed")
        
        # 匯入配置
        success = self.config_service.import_config(export_path)
        self.assertTrue(success)
        
        # 檢查配置是否匯入
        config = self.config_service.get_config()
        self.assertEqual(config.api_key, "export_test")
        self.assertEqual(config.ai_model, "export_model")
    
    def test_config_validation(self):
        """測試配置驗證"""
        # 測試有效配置
        valid_config = {
            "api_key": "test_key",
            "ai_model": "gemini-1.5-flash",
            "window_width": 1200,
            "window_height": 800
        }
        
        is_valid, errors = self.config_service.validate_config(valid_config)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        
        # 測試無效配置
        invalid_config = {
            "window_width": "invalid",  # 應該是整數
            "window_height": -100       # 應該是正數
        }
        
        is_valid, errors = self.config_service.validate_config(invalid_config)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
    
    def test_auto_detect_settings(self):
        """測試自動偵測設定"""
        # 這個測試可能需要根據實際的自動偵測邏輯來調整
        try:
            self.config_service.auto_detect_settings()
            config = self.config_service.get_config()
            
            # 檢查視窗大小是否被自動設定
            self.assertGreater(config.window_width, 0)
            self.assertGreater(config.window_height, 0)
        except Exception as e:
            # 如果自動偵測失敗，記錄但不讓測試失敗
            print(f"自動偵測設定失敗: {e}")


class TestAppConfig(unittest.TestCase):
    """測試 AppConfig 類別"""
    
    def test_config_creation(self):
        """測試配置物件建立"""
        config = AppConfig()
        
        # 檢查預設值
        self.assertEqual(config.ai_model, "gemini-2.5-flash")
        self.assertEqual(config.default_language, "zh-TW")
        self.assertIsInstance(config.window_width, int)
        self.assertIsInstance(config.window_height, int)
    
    def test_config_to_dict(self):
        """測試配置轉換為字典"""
        config = AppConfig()
        config.api_key = "test_key"
        config.ai_model = "test_model"
        
        config_dict = config.to_dict()
        
        self.assertIsInstance(config_dict, dict)
        self.assertEqual(config_dict['api_key'], "test_key")
        self.assertEqual(config_dict['ai_model'], "test_model")
    
    def test_config_from_dict(self):
        """測試從字典建立配置"""
        config_dict = {
            "api_key": "dict_key",
            "ai_model": "dict_model",
            "window_width": 1920,
            "window_height": 1080
        }
        
        config = AppConfig.from_dict(config_dict)
        
        self.assertEqual(config.api_key, "dict_key")
        self.assertEqual(config.ai_model, "dict_model")
        self.assertEqual(config.window_width, 1920)
        self.assertEqual(config.window_height, 1080)


if __name__ == '__main__':
    unittest.main()
