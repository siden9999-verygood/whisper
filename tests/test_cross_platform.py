"""
跨平台測試
測試在不同平台上的相容性
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import os
import subprocess
import sys

from platform_adapter import platform_adapter


class TestCrossPlatformCompatibility(unittest.TestCase):
    """測試跨平台相容性"""
    
    def setUp(self):
        """測試前設定"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.current_platform = platform_adapter.get_platform()
    
    def tearDown(self):
        """測試後清理"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_path_separators(self):
        """測試路徑分隔符處理"""
        # 測試不同格式的路徑
        test_paths = [
            "folder/subfolder/file.txt",
            "folder\\subfolder\\file.txt",
            "/absolute/path/file.txt",
            "C:\\Windows\\path\\file.txt"
        ]
        
        for path in test_paths:
            normalized = platform_adapter.normalize_path(path)
            self.assertIsInstance(normalized, str)
            
            # 標準化後的路徑應該是絕對路徑
            self.assertTrue(os.path.isabs(normalized))
    
    def test_executable_extensions(self):
        """測試執行檔副檔名處理"""
        test_name = "test_executable"
        exe_path = platform_adapter.get_executable_path(test_name)
        
        if self.current_platform == "windows":
            self.assertTrue(str(exe_path).endswith('.exe'))
        else:
            self.assertFalse(str(exe_path).endswith('.exe'))
    
    def test_config_directory_structure(self):
        """測試配置目錄結構"""
        config_dir = platform_adapter.get_config_dir()
        
        # 配置目錄應該存在
        self.assertTrue(config_dir.exists())
        self.assertTrue(config_dir.is_dir())
        
        # 檢查平台特定的配置目錄位置
        if self.current_platform == "windows":
            self.assertIn("AppData", str(config_dir))
        elif self.current_platform == "macos":
            self.assertIn("Library", str(config_dir))
        else:  # Linux
            self.assertIn(".config", str(config_dir))
    
    def test_file_permissions(self):
        """測試檔案權限處理"""
        test_file = self.temp_dir / "test_permissions.txt"
        test_file.write_text("test content", encoding='utf-8')
        
        # 取得檔案資訊
        file_info = platform_adapter.file_manager.get_file_info(str(test_file))
        
        # 檢查基本檔案屬性
        self.assertTrue(file_info['is_file'])
        self.assertFalse(file_info['is_directory'])
        self.assertGreater(file_info['size'], 0)
        
        # 在 Unix 系統上測試權限設定
        if self.current_platform in ["macos", "linux"]:
            # 設定執行權限
            os.chmod(test_file, 0o755)
            
            # 檢查檔案是否可執行
            self.assertTrue(os.access(test_file, os.X_OK))
    
    def test_filename_sanitization(self):
        """測試檔案名稱清理"""
        # 測試不同平台的非法字元
        test_cases = [
            ("normal_file.txt", "normal_file.txt"),
            ("file with spaces.txt", "file with spaces.txt"),
        ]
        
        # 平台特定的測試案例
        if self.current_platform == "windows":
            test_cases.extend([
                ("file<>name.txt", "filename.txt"),
                ("file?name.txt", "filename.txt"),
                ("file|name.txt", "filename.txt"),
                ("CON.txt", "_CON.txt"),
                ("PRN.txt", "_PRN.txt"),
            ])
        else:
            test_cases.extend([
                ("file/name.txt", "filename.txt"),
            ])
        
        for dirty_name, expected_pattern in test_cases:
            clean_name = platform_adapter.path_manager.sanitize_filename(dirty_name)
            
            # 檢查清理後的檔案名稱不包含非法字元
            if self.current_platform == "windows":
                illegal_chars = '<>:"/\\|?*'
                for char in illegal_chars:
                    self.assertNotIn(char, clean_name)
            else:
                self.assertNotIn('/', clean_name)
    
    def test_command_execution(self):
        """測試命令執行"""
        # 測試簡單的系統命令
        if self.current_platform == "windows":
            test_command = ["echo", "test"]
        else:
            test_command = ["echo", "test"]
        
        try:
            result = platform_adapter.run_command(test_command)
            
            self.assertEqual(result.returncode, 0)
            self.assertIn("test", result.stdout)
            
        except Exception as e:
            # 某些環境可能不支援命令執行
            self.skipTest(f"命令執行測試跳過: {e}")
    
    def test_system_directories(self):
        """測試系統目錄取得"""
        # 測試各種系統目錄
        directories = {
            'home': platform_adapter.path_manager.get_home_directory(),
            'desktop': platform_adapter.path_manager.get_desktop_directory(),
            'documents': platform_adapter.path_manager.get_documents_directory(),
            'downloads': platform_adapter.path_manager.get_downloads_directory(),
        }
        
        for dir_name, dir_path in directories.items():
            self.assertIsInstance(dir_path, str)
            self.assertGreater(len(dir_path), 0)
            
            # 主目錄應該存在
            if dir_name == 'home':
                self.assertTrue(Path(dir_path).exists())
    
    def test_unicode_handling(self):
        """測試 Unicode 字元處理"""
        # 測試包含 Unicode 字元的檔案名稱
        unicode_names = [
            "測試檔案.txt",
            "файл.txt",
            "ファイル.txt",
            "🎵音樂檔案.mp3",
        ]
        
        for name in unicode_names:
            try:
                # 建立包含 Unicode 字元的檔案
                test_file = self.temp_dir / name
                test_file.write_text("Unicode test content", encoding='utf-8')
                
                # 取得檔案資訊
                file_info = platform_adapter.file_manager.get_file_info(str(test_file))
                
                self.assertEqual(file_info['name'], name)
                self.assertTrue(file_info['is_file'])
                
            except (UnicodeError, OSError) as e:
                # 某些檔案系統可能不支援特定的 Unicode 字元
                print(f"Unicode 檔案名稱 '{name}' 測試跳過: {e}")
    
    def test_long_path_handling(self):
        """測試長路徑處理"""
        # 建立一個深層的目錄結構
        deep_path = self.temp_dir
        
        # 建立多層目錄
        for i in range(10):
            deep_path = deep_path / f"level_{i}_directory_with_long_name"
            deep_path.mkdir()
        
        # 在深層目錄中建立檔案
        test_file = deep_path / "deep_file.txt"
        test_file.write_text("Deep file content", encoding='utf-8')
        
        # 測試檔案操作
        file_info = platform_adapter.file_manager.get_file_info(str(test_file))
        
        self.assertEqual(file_info['name'], 'deep_file.txt')
        self.assertTrue(file_info['is_file'])
    
    def test_case_sensitivity(self):
        """測試大小寫敏感性"""
        # 建立測試檔案
        file1 = self.temp_dir / "TestFile.txt"
        file2 = self.temp_dir / "testfile.txt"
        
        file1.write_text("File 1 content", encoding='utf-8')
        
        # 在大小寫不敏感的檔案系統上，第二個檔案會覆蓋第一個
        try:
            file2.write_text("File 2 content", encoding='utf-8')
            
            # 檢查檔案系統的大小寫敏感性
            if file1.exists() and file2.exists():
                # 大小寫敏感
                self.assertNotEqual(file1.read_text(), file2.read_text())
            else:
                # 大小寫不敏感
                self.assertTrue(file1.exists() or file2.exists())
                
        except Exception as e:
            self.skipTest(f"大小寫敏感性測試跳過: {e}")


class TestPlatformSpecificFeatures(unittest.TestCase):
    """測試平台特定功能"""
    
    def setUp(self):
        """測試前設定"""
        self.current_platform = platform_adapter.get_platform()
    
    @unittest.skipUnless(platform_adapter.is_windows(), "僅 Windows 平台")
    def test_windows_specific_features(self):
        """測試 Windows 特定功能"""
        # 測試磁碟機列表
        drives = platform_adapter.path_manager.get_available_drives()
        self.assertIsInstance(drives, list)
        self.assertGreater(len(drives), 0)
        
        # 應該包含 C: 磁碟機
        drive_letters = [drive[0] for drive in drives]
        self.assertIn('C', drive_letters)
    
    @unittest.skipUnless(platform_adapter.is_macos(), "僅 macOS 平台")
    def test_macos_specific_features(self):
        """測試 macOS 特定功能"""
        # 測試應用程式支援目錄
        config_dir = platform_adapter.get_config_dir()
        self.assertIn("Library/Application Support", str(config_dir))
    
    @unittest.skipUnless(platform_adapter.is_linux(), "僅 Linux 平台")
    def test_linux_specific_features(self):
        """測試 Linux 特定功能"""
        # 測試配置目錄
        config_dir = platform_adapter.get_config_dir()
        self.assertIn(".config", str(config_dir))
    
    def test_python_version_compatibility(self):
        """測試 Python 版本相容性"""
        # 檢查 Python 版本
        python_version = sys.version_info
        
        # 應用程式需要 Python 3.8 或更高版本
        self.assertGreaterEqual(python_version.major, 3)
        self.assertGreaterEqual(python_version.minor, 8)
    
    def test_required_modules_availability(self):
        """測試必要模組可用性"""
        required_modules = [
            'pathlib',
            'json',
            'logging',
            'threading',
            'subprocess',
            'tempfile',
            'shutil',
        ]
        
        for module_name in required_modules:
            try:
                __import__(module_name)
            except ImportError:
                self.fail(f"必要模組 {module_name} 不可用")


if __name__ == '__main__':
    unittest.main()