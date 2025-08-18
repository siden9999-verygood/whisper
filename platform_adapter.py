"""
跨平台適配器模組
處理 Windows 和 macOS 之間的差異，提供統一的介面
"""

import os
import sys
import platform
from pathlib import Path
from typing import Optional, Dict, List
import subprocess


class PlatformAdapter:
    """處理跨平台相容性的核心類別"""
    
    # 支援的平台
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"
    
    # 執行檔副檔名映射
    EXECUTABLE_EXTENSIONS = {
        WINDOWS: ".exe",
        MACOS: "",
        LINUX: ""
    }
    
    def __init__(self):
        self.current_platform = self._detect_platform()
        self.base_path = self._get_base_path()
        
    @staticmethod
    def _detect_platform() -> str:
        """偵測當前作業系統平台"""
        system = platform.system().lower()
        if system == "windows":
            return PlatformAdapter.WINDOWS
        elif system == "darwin":
            return PlatformAdapter.MACOS
        elif system == "linux":
            return PlatformAdapter.LINUX
        else:
            raise PlatformNotSupportedError(f"不支援的作業系統: {system}")
    
    @staticmethod
    def _get_base_path() -> Path:
        """取得應用程式基礎路徑"""
        if getattr(sys, 'frozen', False):
            # 打包後的執行檔
            return Path(sys.executable).parent
        else:
            # 開發環境
            try:
                return Path(__file__).parent.absolute()
            except NameError:
                return Path.cwd()
    
    def get_platform(self) -> str:
        """取得當前平台類型"""
        return self.current_platform
    
    def is_windows(self) -> bool:
        """檢查是否為 Windows 平台"""
        return self.current_platform == self.WINDOWS
    
    def is_macos(self) -> bool:
        """檢查是否為 macOS 平台"""
        return self.current_platform == self.MACOS
    
    def is_linux(self) -> bool:
        """檢查是否為 Linux 平台"""
        return self.current_platform == self.LINUX
    
    def get_executable_path(self, base_name: str, resource_folder: str = None) -> Path:
        """根據平台取得正確的執行檔路徑"""
        extension = self.EXECUTABLE_EXTENSIONS.get(self.current_platform, "")
        executable_name = f"{base_name}{extension}"
        
        if resource_folder:
            resource_path = self.get_resource_path(resource_folder)
            return resource_path / executable_name
        else:
            return self.base_path / executable_name
    
    def get_resource_path(self, resource_name: str) -> Path:
        """取得資源檔案的正確路徑"""
        resource_path = self.base_path / resource_name
        
        # 檢查資源是否存在
        if not resource_path.exists():
            # 嘗試在上層目錄尋找
            parent_resource = self.base_path.parent / resource_name
            if parent_resource.exists():
                return parent_resource
        
        return resource_path
    
    def normalize_path(self, path: str) -> str:
        """標準化檔案路徑格式"""
        return str(Path(path).resolve())
    
    def get_path_separator(self) -> str:
        """取得路徑分隔符"""
        return os.sep
    
    def get_config_dir(self) -> Path:
        """取得設定檔目錄"""
        if self.is_windows():
            config_dir = Path(os.environ.get('APPDATA', '')) / 'AIWorkstation'
        elif self.is_macos():
            config_dir = Path.home() / 'Library' / 'Application Support' / 'AIWorkstation'
        else:  # Linux
            config_dir = Path.home() / '.config' / 'aiworkstation'
        
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir
    
    def get_temp_dir(self) -> Path:
        """取得臨時檔案目錄"""
        import tempfile
        temp_dir = Path(tempfile.gettempdir()) / 'AIWorkstation'
        temp_dir.mkdir(parents=True, exist_ok=True)
        return temp_dir
    
    def run_command(self, command: List[str], cwd: Optional[str] = None, 
                   capture_output: bool = True, timeout: Optional[int] = None) -> subprocess.CompletedProcess:
        """執行系統命令"""
        try:
            # 設定預設超時時間（30分鐘）
            if timeout is None:
                timeout = 1800
            
            if self.is_windows():
                # Windows 需要特殊處理
                result = subprocess.run(
                    command,
                    cwd=cwd,
                    capture_output=capture_output,
                    text=True,
                    shell=False,
                    timeout=timeout,
                    creationflags=subprocess.CREATE_NO_WINDOW if capture_output else 0
                )
            else:
                # macOS 和 Linux
                result = subprocess.run(
                    command,
                    cwd=cwd,
                    capture_output=capture_output,
                    text=True,
                    shell=False,
                    timeout=timeout
                )
            return result
        except FileNotFoundError as e:
            raise ExecutableNotFoundError(f"找不到執行檔: {command[0]}") from e
        except Exception as e:
            raise CommandExecutionError(f"命令執行失敗: {' '.join(command)}") from e
    
    def get_system_info(self) -> Dict[str, str]:
        """取得系統資訊"""
        return {
            "platform": self.current_platform,
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "base_path": str(self.base_path)
        }


class FileManager:
    """跨平台檔案管理器"""
    
    def __init__(self, platform_adapter: PlatformAdapter):
        self.platform_adapter = platform_adapter
    
    def copy_file(self, source: str, destination: str, 
                 progress_callback: Optional[callable] = None) -> bool:
        """複製檔案，支援進度回調"""
        import shutil
        
        try:
            source_path = Path(source)
            dest_path = Path(destination)
            
            # 確保目標目錄存在
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            if progress_callback:
                # 帶進度的複製
                self._copy_with_progress(source_path, dest_path, progress_callback)
            else:
                # 簡單複製
                shutil.copy2(source_path, dest_path)
            
            return True
        except Exception as e:
            raise FileCopyError(f"檔案複製失敗: {source} -> {destination}") from e
    
    def _copy_with_progress(self, source: Path, destination: Path, 
                           progress_callback: callable):
        """帶進度的檔案複製"""
        file_size = source.stat().st_size
        copied_size = 0
        
        with open(source, 'rb') as src, open(destination, 'wb') as dst:
            while True:
                chunk = src.read(64 * 1024)  # 64KB chunks
                if not chunk:
                    break
                dst.write(chunk)
                copied_size += len(chunk)
                
                if progress_callback:
                    progress = (copied_size / file_size) * 100
                    progress_callback(progress, copied_size, file_size)
    
    def move_file(self, source: str, destination: str) -> bool:
        """移動檔案"""
        import shutil
        
        try:
            source_path = Path(source)
            dest_path = Path(destination)
            
            # 確保目標目錄存在
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(source_path), str(dest_path))
            return True
        except Exception as e:
            raise FileMoveError(f"檔案移動失敗: {source} -> {destination}") from e
    
    def delete_file(self, file_path: str) -> bool:
        """刪除檔案"""
        try:
            Path(file_path).unlink()
            return True
        except Exception as e:
            raise FileDeleteError(f"檔案刪除失敗: {file_path}") from e
    
    def create_directory(self, dir_path: str) -> bool:
        """建立目錄"""
        try:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            raise DirectoryCreateError(f"目錄建立失敗: {dir_path}") from e
    
    def get_file_info(self, file_path: str) -> Dict:
        """取得檔案資訊"""
        try:
            path = Path(file_path)
            stat = path.stat()
            
            return {
                "name": path.name,
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "created": stat.st_ctime,
                "is_file": path.is_file(),
                "is_directory": path.is_dir(),
                "extension": path.suffix.lower(),
                "absolute_path": str(path.absolute())
            }
        except Exception as e:
            raise FileInfoError(f"無法取得檔案資訊: {file_path}") from e


class PathManager:
    """路徑管理器"""
    
    def __init__(self, platform_adapter: PlatformAdapter):
        self.platform_adapter = platform_adapter
    
    def join_paths(self, *paths) -> str:
        """安全地連接路徑"""
        return str(Path(*paths))
    
    def get_relative_path(self, path: str, base_path: str) -> str:
        """取得相對路徑"""
        try:
            return str(Path(path).relative_to(Path(base_path)))
        except ValueError:
            # 如果無法建立相對路徑，返回絕對路徑
            return str(Path(path).absolute())
    
    def ensure_path_exists(self, path: str) -> bool:
        """確保路徑存在"""
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception:
            return False
    
    def is_valid_path(self, path: str) -> bool:
        """檢查路徑是否有效"""
        try:
            Path(path)
            return True
        except (ValueError, OSError):
            return False
    
    def sanitize_filename(self, filename: str) -> str:
        """清理檔案名稱，移除不合法字元"""
        if self.platform_adapter.is_windows():
            # Windows 不允許的字元
            invalid_chars = '<>:"/\\|?*'
            # Windows 保留名稱
            reserved_names = {
                'CON', 'PRN', 'AUX', 'NUL',
                'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
                'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
            }
        else:
            # macOS 和 Linux 不允許的字元
            invalid_chars = '/'
            reserved_names = set()
        
        # 移除不合法字元
        sanitized = ''.join(c for c in filename if c not in invalid_chars)
        
        # 移除前後空白和點
        sanitized = sanitized.strip('. ')
        
        # 檢查保留名稱
        name_without_ext = sanitized.split('.')[0].upper()
        if name_without_ext in reserved_names:
            sanitized = f"_{sanitized}"
        
        # 限制檔案名長度
        max_length = 200 if self.platform_adapter.is_windows() else 255
        if len(sanitized) > max_length:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:max_length-len(ext)] + ext
        
        # 確保不是空字串
        if not sanitized:
            sanitized = "untitled"
        
        return sanitized
    
    def get_available_drives(self) -> List[str]:
        """取得可用的磁碟機（僅Windows）"""
        if not self.platform_adapter.is_windows():
            return ['/']
        
        import string
        drives = []
        for letter in string.ascii_uppercase:
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                drives.append(drive)
        return drives
    
    def get_home_directory(self) -> str:
        """取得使用者主目錄"""
        return str(Path.home())
    
    def get_desktop_directory(self) -> str:
        """取得桌面目錄"""
        if self.platform_adapter.is_windows():
            import winreg
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                  r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders") as key:
                    desktop_path = winreg.QueryValueEx(key, "Desktop")[0]
                    return desktop_path
            except:
                pass
        
        # 預設路徑
        return str(Path.home() / "Desktop")
    
    def get_documents_directory(self) -> str:
        """取得文件目錄"""
        if self.platform_adapter.is_windows():
            import winreg
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                  r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders") as key:
                    docs_path = winreg.QueryValueEx(key, "Personal")[0]
                    return docs_path
            except:
                pass
        
        # 預設路徑
        return str(Path.home() / "Documents")
    
    def get_downloads_directory(self) -> str:
        """取得下載目錄"""
        downloads_path = Path.home() / "Downloads"
        if downloads_path.exists():
            return str(downloads_path)
        
        # 備用路徑
        return self.get_documents_directory()
    
    def open_file_explorer(self, path: str) -> bool:
        """開啟檔案總管/Finder"""
        try:
            path = Path(path)
            if not path.exists():
                return False
            
            if self.platform_adapter.is_windows():
                os.startfile(str(path))
            elif self.platform_adapter.is_macos():
                subprocess.run(['open', str(path)])
            else:  # Linux
                subprocess.run(['xdg-open', str(path)])
            
            return True
        except Exception:
            return False
    
    def get_file_associations(self, extension: str) -> List[str]:
        """取得檔案關聯程式"""
        associations = []
        
        if self.platform_adapter.is_windows():
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, extension) as key:
                    file_type = winreg.QueryValue(key, "")
                    if file_type:
                        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, 
                                          f"{file_type}\\shell\\open\\command") as cmd_key:
                            command = winreg.QueryValue(cmd_key, "")
                            associations.append(command)
            except:
                pass
        elif self.platform_adapter.is_macos():
            try:
                result = subprocess.run(['mdls', '-name', 'kMDItemContentTypeTree', 
                                       f'dummy{extension}'], 
                                      capture_output=True, text=True)
                # 簡化處理，實際需要更複雜的邏輯
                if result.returncode == 0:
                    associations.append("系統預設")
            except:
                pass
        
        return associations


# 自定義例外類別
class CrossPlatformError(Exception):
    """跨平台相關錯誤的基礎類別"""
    pass


class PlatformNotSupportedError(CrossPlatformError):
    """不支援的平台錯誤"""
    pass


class ExecutableNotFoundError(CrossPlatformError):
    """找不到執行檔錯誤"""
    pass


class CommandExecutionError(CrossPlatformError):
    """命令執行錯誤"""
    pass


class FileCopyError(CrossPlatformError):
    """檔案複製錯誤"""
    pass


class FileMoveError(CrossPlatformError):
    """檔案移動錯誤"""
    pass


class FileDeleteError(CrossPlatformError):
    """檔案刪除錯誤"""
    pass


class DirectoryCreateError(CrossPlatformError):
    """目錄建立錯誤"""
    pass


class FileInfoError(CrossPlatformError):
    """檔案資訊錯誤"""
    pass


# 全域實例
platform_adapter = PlatformAdapter()
file_manager = FileManager(platform_adapter)
path_manager = PathManager(platform_adapter)


if __name__ == "__main__":
    # 測試程式
    print("=== 跨平台適配器測試 ===")
    print(f"當前平台: {platform_adapter.get_platform()}")
    print(f"基礎路徑: {platform_adapter.base_path}")
    print(f"設定目錄: {platform_adapter.get_config_dir()}")
    print(f"臨時目錄: {platform_adapter.get_temp_dir()}")
    
    print("\n=== 系統資訊 ===")
    for key, value in platform_adapter.get_system_info().items():
        print(f"{key}: {value}")
    
    print("\n=== 路徑測試 ===")
    test_path = path_manager.join_paths("test", "folder", "file.txt")
    print(f"連接路徑: {test_path}")
    print(f"清理檔案名: {path_manager.sanitize_filename('test<>file?.txt')}")