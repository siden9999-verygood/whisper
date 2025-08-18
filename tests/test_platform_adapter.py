"""
跨平台適配器測試
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import os

from platform_adapter import platform_adapter, file_manager, path_manager
from platform_adapter import PlatformAdapter, FileManager, PathManager


class TestPlatformAdapter(unittest.TestCase):
    """測試 PlatformAdapter 類別"""
    
    def setUp(self):
        """測試前設定"""
        self.adapter = PlatformAdapter()
    
    def test_platform_detection(self):
        """測試平台偵測"""
        platform = self.adapter.get_platform()
        self.assertIn(platform, ['windows', 'macos', 'linux'])
    
    def test_platform_checks(self):
        """測試平台檢查方法"""
        # 確保只有一個平台為 True
        platforms = [
            self.adapter.is_windows(),
            self.adapter.is_macos(),
            self.adapter.is_linux()
        ]
        self.assertEqual(sum(platforms), 1)
    
    def test_base_path(self):
        """測試基礎路徑取得"""
        base_path = self.adapter.base_path
        self.assertIsInstance(base_path, Path)
        self.assertTrue(base_path.exists())
    
    def test_config_dir(self):
        """測試配置目錄取得"""
        config_dir = self.adapter.get_config_dir()
        self.assertIsInstance(config_dir, Path)
        self.assertTrue(config_dir.exists())
    
    def test_temp_dir(self):
        """測試臨時目錄取得"""
        temp_dir = self.adapter.get_temp_dir()
        self.assertIsInstance(temp_dir, Path)
        self.assertTrue(temp_dir.exists())
    
    def test_executable_path(self):
        """測試執行檔路徑取得"""
        exe_path = self.adapter.get_executable_path("test")
        self.assertIsInstance(exe_path, Path)
        
        # 檢查副檔名
        if self.adapter.is_windows():
            self.assertTrue(str(exe_path).endswith('.exe'))
        else:
            self.assertFalse(str(exe_path).endswith('.exe'))
    
    def test_normalize_path(self):
        """測試路徑標準化"""
        test_path = "test/path/file.txt"
        normalized = self.adapter.normalize_path(test_path)
        self.assertIsInstance(normalized, str)
        self.assertTrue(os.path.isabs(normalized))
    
    def test_system_info(self):
        """測試系統資訊取得"""
        info = self.adapter.get_system_info()
        self.assertIsInstance(info, dict)
        
        required_keys = ['platform', 'system', 'python_version', 'base_path']
        for key in required_keys:
            self.assertIn(key, info)
            self.assertIsNotNone(info[key])


class TestFileManager(unittest.TestCase):
    """測試 FileManager 類別"""
    
    def setUp(self):
        """測試前設定"""
        self.adapter = PlatformAdapter()
        self.file_manager = FileManager(self.adapter)
        self.test_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """測試後清理"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_create_directory(self):
        """測試目錄建立"""
        test_dir = self.test_dir / "new_directory"
        result = self.file_manager.create_directory(str(test_dir))
        
        self.assertTrue(result)
        self.assertTrue(test_dir.exists())
        self.assertTrue(test_dir.is_dir())
    
    def test_copy_file(self):
        """測試檔案複製"""
        # 建立測試檔案
        source_file = self.test_dir / "source.txt"
        dest_file = self.test_dir / "dest.txt"
        
        source_file.write_text("測試內容", encoding='utf-8')
        
        # 複製檔案
        result = self.file_manager.copy_file(str(source_file), str(dest_file))
        
        self.assertTrue(result)
        self.assertTrue(dest_file.exists())
        self.assertEqual(source_file.read_text(encoding='utf-8'), 
                        dest_file.read_text(encoding='utf-8'))
    
    def test_move_file(self):
        """測試檔案移動"""
        # 建立測試檔案
        source_file = self.test_dir / "source.txt"
        dest_file = self.test_dir / "dest.txt"
        
        test_content = "測試內容"
        source_file.write_text(test_content, encoding='utf-8')
        
        # 移動檔案
        result = self.file_manager.move_file(str(source_file), str(dest_file))
        
        self.assertTrue(result)
        self.assertFalse(source_file.exists())
        self.assertTrue(dest_file.exists())
        self.assertEqual(dest_file.read_text(encoding='utf-8'), test_content)
    
    def test_delete_file(self):
        """測試檔案刪除"""
        # 建立測試檔案
        test_file = self.test_dir / "test.txt"
        test_file.write_text("測試內容", encoding='utf-8')
        
        # 刪除檔案
        result = self.file_manager.delete_file(str(test_file))
        
        self.assertTrue(result)
        self.assertFalse(test_file.exists())
    
    def test_get_file_info(self):
        """測試檔案資訊取得"""
        # 建立測試檔案
        test_file = self.test_dir / "test.txt"
        test_content = "測試內容"
        test_file.write_text(test_content, encoding='utf-8')
        
        # 取得檔案資訊
        info = self.file_manager.get_file_info(str(test_file))
        
        self.assertIsInstance(info, dict)
        self.assertEqual(info['name'], 'test.txt')
        self.assertEqual(info['size'], len(test_content.encode('utf-8')))
        self.assertTrue(info['is_file'])
        self.assertFalse(info['is_directory'])
        self.assertEqual(info['extension'], '.txt')


class TestPathManager(unittest.TestCase):
    """測試 PathManager 類別"""
    
    def setUp(self):
        """測試前設定"""
        self.adapter = PlatformAdapter()
        self.path_manager = PathManager(self.adapter)
    
    def test_join_paths(self):
        """測試路徑連接"""
        result = self.path_manager.join_paths("folder", "subfolder", "file.txt")
        expected = str(Path("folder") / "subfolder" / "file.txt")
        self.assertEqual(result, expected)
    
    def test_sanitize_filename(self):
        """測試檔案名稱清理"""
        if self.adapter.is_windows():
            # Windows 不允許的字元
            dirty_name = "test<>file?.txt"
            clean_name = self.path_manager.sanitize_filename(dirty_name)
            self.assertNotIn('<', clean_name)
            self.assertNotIn('>', clean_name)
            self.assertNotIn('?', clean_name)
        else:
            # Unix 系統不允許的字元
            dirty_name = "test/file.txt"
            clean_name = self.path_manager.sanitize_filename(dirty_name)
            self.assertNotIn('/', clean_name)
    
    def test_is_valid_path(self):
        """測試路徑有效性檢查"""
        valid_path = "/valid/path"
        self.assertTrue(self.path_manager.is_valid_path(valid_path))
        
        # 測試空路徑
        self.assertFalse(self.path_manager.is_valid_path(""))
    
    def test_get_home_directory(self):
        """測試取得使用者主目錄"""
        home_dir = self.path_manager.get_home_directory()
        self.assertIsInstance(home_dir, str)
        self.assertTrue(Path(home_dir).exists())
    
    def test_get_desktop_directory(self):
        """測試取得桌面目錄"""
        desktop_dir = self.path_manager.get_desktop_directory()
        self.assertIsInstance(desktop_dir, str)
        # 桌面目錄可能不存在，所以不檢查存在性
    
    def test_get_documents_directory(self):
        """測試取得文件目錄"""
        docs_dir = self.path_manager.get_documents_directory()
        self.assertIsInstance(docs_dir, str)
    
    def test_get_downloads_directory(self):
        """測試取得下載目錄"""
        downloads_dir = self.path_manager.get_downloads_directory()
        self.assertIsInstance(downloads_dir, str)


if __name__ == '__main__':
    unittest.main()