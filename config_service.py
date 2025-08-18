"""
配置服務模組
處理應用程式設定的載入、儲存和管理
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from platform_adapter import platform_adapter, CrossPlatformError


@dataclass
class AppConfig:
    """應用程式配置資料類別"""
    # API 設定
    api_key: str = ""
    ai_model: str = "gemini-1.5-pro-latest"
    
    # 資料夾設定
    source_folder: str = ""
    processed_folder: str = ""
    
    # 轉錄設定
    default_model: str = "Medium (中等)"
    default_language: str = "zh"
    default_threads: int = 4
    default_temperature: float = 0.0
    
    # 輸出格式設定
    output_srt: bool = True
    output_txt: bool = False
    output_vtt: bool = False
    output_lrc: bool = False
    output_csv: bool = False
    
    # 後處理設定
    enable_segmentation: bool = False
    remove_punctuation: bool = False
    convert_to_traditional_chinese: bool = False
    translate_to_english: bool = False
    
    # UI 設定
    window_width: int = 1200
    window_height: int = 900
    theme: str = "default"
    
    # 搜尋設定
    search_history_limit: int = 50
    results_per_page: int = 20
    enable_auto_suggestions: bool = True
    
    # 下載設定
    default_download_folder: str = ""
    max_concurrent_downloads: int = 3
    chunk_size: int = 64 * 1024  # 64KB
    
    # 雲端同步設定
    cloud_sync_enabled: bool = False
    cloud_provider: str = ""  # "google_drive", "dropbox", "onedrive"
    sync_interval: int = 300  # 5 minutes
    
    # 自動化設定
    auto_process_enabled: bool = False
    watch_folders: list = None
    schedule_enabled: bool = False
    
    def __post_init__(self):
        if self.watch_folders is None:
            self.watch_folders = []


class ConfigService:
    """配置服務類別"""
    
    CONFIG_FILENAME = "config.json"
    BACKUP_FILENAME = "config.backup.json"
    
    def __init__(self):
        self.config_dir = platform_adapter.get_config_dir()
        self.config_file = self.config_dir / self.CONFIG_FILENAME
        self.backup_file = self.config_dir / self.BACKUP_FILENAME
        self._config = AppConfig()
        self._load_config()
    
    def _load_config(self) -> None:
        """載入配置檔案"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 更新配置物件
                for key, value in config_data.items():
                    if hasattr(self._config, key):
                        setattr(self._config, key, value)
                
                print(f"配置已從 {self.config_file} 載入")
            else:
                print("配置檔案不存在，使用預設配置")
                self._save_config()  # 建立預設配置檔案
                
        except Exception as e:
            print(f"載入配置失敗: {e}")
            self._try_restore_backup()
    
    def _try_restore_backup(self) -> None:
        """嘗試從備份恢復配置"""
        try:
            if self.backup_file.exists():
                with open(self.backup_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                for key, value in config_data.items():
                    if hasattr(self._config, key):
                        setattr(self._config, key, value)
                
                print("已從備份檔案恢復配置")
                self._save_config()  # 重新建立主配置檔案
            else:
                print("備份檔案也不存在，使用預設配置")
                
        except Exception as e:
            print(f"從備份恢復配置失敗: {e}")
            print("使用預設配置")
    
    def _save_config(self) -> None:
        """儲存配置檔案"""
        try:
            # 建立備份
            if self.config_file.exists():
                import shutil
                shutil.copy2(self.config_file, self.backup_file)
            
            # 儲存配置
            config_dict = asdict(self._config)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=4, ensure_ascii=False)
            
            print(f"配置已儲存至 {self.config_file}")
            
        except Exception as e:
            raise ConfigSaveError(f"儲存配置失敗: {e}") from e
    
    def get_config(self) -> AppConfig:
        """取得配置物件"""
        return self._config
    
    def update_config(self, **kwargs) -> None:
        """更新配置"""
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
            else:
                print(f"警告: 未知的配置項目 '{key}'")
        
        self._save_config()
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """取得單一配置值"""
        return getattr(self._config, key, default)
    
    def set_value(self, key: str, value: Any) -> None:
        """設定單一配置值"""
        if hasattr(self._config, key):
            setattr(self._config, key, value)
            self._save_config()
        else:
            raise ConfigKeyError(f"未知的配置項目: {key}")
    
    def reset_to_defaults(self) -> None:
        """重設為預設配置"""
        self._config = AppConfig()
        self._save_config()
        print("配置已重設為預設值")
    
    def export_config(self, export_path: str) -> None:
        """匯出配置到指定路徑"""
        try:
            config_dict = asdict(self._config)
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=4, ensure_ascii=False)
            print(f"配置已匯出至 {export_path}")
        except Exception as e:
            raise ConfigExportError(f"匯出配置失敗: {e}") from e
    
    def import_config(self, import_path: str) -> None:
        """從指定路徑匯入配置"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 驗證並更新配置
            for key, value in config_data.items():
                if hasattr(self._config, key):
                    setattr(self._config, key, value)
            
            self._save_config()
            print(f"配置已從 {import_path} 匯入")
            
        except Exception as e:
            raise ConfigImportError(f"匯入配置失敗: {e}") from e
    
    def get_whisper_resources_path(self) -> Path:
        """取得 Whisper 資源路徑"""
        # 統一使用 whisper_resources 資料夾名稱
        resource_name = "whisper_resources"
        
        return platform_adapter.get_resource_path(resource_name)
    
    def get_ffmpeg_path(self) -> Path:
        """取得 FFmpeg 執行檔路徑"""
        whisper_path = self.get_whisper_resources_path()
        # FFmpeg 檔案直接在 whisper_resources 資料夾中
        ffmpeg_file = whisper_path / "ffmpeg"
        if ffmpeg_file.exists():
            return ffmpeg_file
        # 如果不存在，嘗試系統安裝的 FFmpeg
        return platform_adapter.get_executable_path("ffmpeg", "/opt/homebrew/bin")
    
    def get_whisper_main_path(self) -> Path:
        """取得 Whisper main 執行檔路徑"""
        whisper_path = self.get_whisper_resources_path()
        return platform_adapter.get_executable_path("main", str(whisper_path))
    
    def validate_paths(self) -> Dict[str, bool]:
        """驗證重要路徑是否存在"""
        validation_results = {}
        
        # 檢查 Whisper 資源
        whisper_path = self.get_whisper_resources_path()
        validation_results["whisper_resources"] = whisper_path.exists()
        
        # 檢查 FFmpeg
        ffmpeg_path = self.get_ffmpeg_path()
        validation_results["ffmpeg"] = ffmpeg_path.exists()
        
        # 檢查 Whisper main
        main_path = self.get_whisper_main_path()
        validation_results["whisper_main"] = main_path.exists()
        
        # 檢查使用者設定的資料夾
        if self._config.source_folder:
            validation_results["source_folder"] = Path(self._config.source_folder).exists()
        
        if self._config.processed_folder:
            validation_results["processed_folder"] = Path(self._config.processed_folder).exists()
        
        if self._config.default_download_folder:
            validation_results["download_folder"] = Path(self._config.default_download_folder).exists()
        
        return validation_results
    
    def get_missing_dependencies(self) -> List[str]:
        """取得缺少的相依性清單"""
        missing = []
        validation_results = self.validate_paths()
        
        if not validation_results.get("whisper_resources", False):
            missing.append("Whisper 資源檔案")
        
        if not validation_results.get("ffmpeg", False):
            missing.append("FFmpeg 執行檔")
        
        if not validation_results.get("whisper_main", False):
            missing.append("Whisper 主程式")
        
        return missing
    
    def _get_screen_resolution(self) -> tuple:
        """跨平台取得螢幕解析度"""
        try:
            # 首先嘗試使用 tkinter
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()  # 隱藏視窗
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            root.destroy()
            return screen_width, screen_height
        except (ImportError, Exception):
            pass
        
        try:
            # 在 Windows 上嘗試使用 win32api
            if platform_adapter.is_windows():
                import win32api
                screen_width = win32api.GetSystemMetrics(0)
                screen_height = win32api.GetSystemMetrics(1)
                return screen_width, screen_height
        except (ImportError, Exception):
            pass
        
        try:
            # 在 macOS 上嘗試使用 AppKit
            if platform_adapter.is_macos():
                from AppKit import NSScreen
                screen = NSScreen.mainScreen()
                screen_rect = screen.frame()
                return int(screen_rect.size.width), int(screen_rect.size.height)
        except (ImportError, Exception):
            pass
        
        try:
            # 嘗試使用 subprocess 調用系統命令
            if platform_adapter.is_macos():
                result = platform_adapter.run_command(['system_profiler', 'SPDisplaysDataType'])
                # 簡化處理，實際需要解析輸出
                return 1920, 1080  # 預設值
            elif platform_adapter.is_linux():
                result = platform_adapter.run_command(['xrandr'])
                # 簡化處理，實際需要解析輸出
                return 1920, 1080  # 預設值
        except Exception:
            pass
        
        # 如果所有方法都失敗，返回預設值
        return 1200, 800
    
    def auto_detect_settings(self) -> Dict[str, Any]:
        """自動檢測系統設定"""
        detected_settings = {}
        
        try:
            # 自動檢測下載資料夾
            if not self._config.default_download_folder:
                if platform_adapter.is_windows():
                    downloads = Path.home() / "Downloads"
                elif platform_adapter.is_macos():
                    downloads = Path.home() / "Downloads"
                else:
                    downloads = Path.home() / "Downloads"
                
                if downloads.exists():
                    detected_settings["default_download_folder"] = str(downloads)
            
            # 自動檢測最佳執行緒數
            import psutil
            cpu_count = psutil.cpu_count()
            if cpu_count:
                # 使用 CPU 核心數的 75%，但至少1個，最多8個
                optimal_threads = max(1, min(8, int(cpu_count * 0.75)))
                detected_settings["default_threads"] = optimal_threads
            
            # 自動檢測記憶體相關設定
            memory = psutil.virtual_memory()
            if memory.total > 8 * 1024**3:  # 8GB以上
                detected_settings["chunk_size"] = 128 * 1024  # 128KB
                detected_settings["max_concurrent_downloads"] = 5
            elif memory.total > 4 * 1024**3:  # 4GB以上
                detected_settings["chunk_size"] = 64 * 1024   # 64KB
                detected_settings["max_concurrent_downloads"] = 3
            else:  # 4GB以下
                detected_settings["chunk_size"] = 32 * 1024   # 32KB
                detected_settings["max_concurrent_downloads"] = 2
            
            # 自動檢測螢幕解析度並設定視窗大小
            screen_width, screen_height = self._get_screen_resolution()
            if screen_width and screen_height:
                # 設定視窗為螢幕的80%，但不超過1600x1200
                window_width = min(1600, int(screen_width * 0.8))
                window_height = min(1200, int(screen_height * 0.8))
                
                detected_settings["window_width"] = window_width
                detected_settings["window_height"] = window_height
            else:
                pass
            
        except Exception as e:
            print(f"自動檢測設定時發生錯誤: {e}")
        
        return detected_settings
    
    def apply_auto_detected_settings(self) -> None:
        """應用自動檢測的設定"""
        detected = self.auto_detect_settings()
        
        for key, value in detected.items():
            if hasattr(self._config, key):
                current_value = getattr(self._config, key)
                # 只在當前值為預設值時才更新
                if self._is_default_value(key, current_value):
                    setattr(self._config, key, value)
                    print(f"自動設定 {key}: {value}")
        
        if detected:
            self._save_config()
    
    def _is_default_value(self, key: str, value: Any) -> bool:
        """檢查是否為預設值"""
        default_config = AppConfig()
        default_value = getattr(default_config, key, None)
        return value == default_value
    
    def create_backup(self) -> str:
        """建立配置備份"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"config_backup_{timestamp}.json"
            backup_path = self.config_dir / backup_name
            
            if self.config_file.exists():
                import shutil
                shutil.copy2(self.config_file, backup_path)
                print(f"配置備份已建立: {backup_path}")
                return str(backup_path)
            else:
                print("配置檔案不存在，無法建立備份")
                return ""
                
        except Exception as e:
            raise ConfigSaveError(f"建立配置備份失敗: {e}") from e
    
    def restore_from_backup(self, backup_path: str) -> bool:
        """從備份恢復配置"""
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                print(f"備份檔案不存在: {backup_path}")
                return False
            
            # 建立當前配置的備份
            if self.config_file.exists():
                self.create_backup()
            
            # 恢復備份
            import shutil
            shutil.copy2(backup_file, self.config_file)
            
            # 重新載入配置
            self._load_config()
            
            print(f"配置已從備份恢復: {backup_path}")
            return True
            
        except Exception as e:
            print(f"從備份恢復配置失敗: {e}")
            return False
    
    def get_backup_list(self) -> List[Dict[str, Any]]:
        """取得備份清單"""
        backups = []
        
        try:
            for backup_file in self.config_dir.glob("config_backup_*.json"):
                stat = backup_file.stat()
                backups.append({
                    "path": str(backup_file),
                    "name": backup_file.name,
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_ctime),
                    "modified": datetime.fromtimestamp(stat.st_mtime)
                })
            
            # 按修改時間排序（最新的在前）
            backups.sort(key=lambda x: x["modified"], reverse=True)
            
        except Exception as e:
            print(f"取得備份清單失敗: {e}")
        
        return backups
    
    def cleanup_old_backups(self, keep_count: int = 10) -> None:
        """清理舊的備份檔案"""
        try:
            backups = self.get_backup_list()
            
            if len(backups) > keep_count:
                old_backups = backups[keep_count:]
                
                for backup in old_backups:
                    backup_path = Path(backup["path"])
                    backup_path.unlink()
                    print(f"已刪除舊備份: {backup['name']}")
                
                print(f"清理了 {len(old_backups)} 個舊備份檔案")
            
        except Exception as e:
            print(f"清理舊備份失敗: {e}")
    
    def validate_config(self) -> Dict[str, List[str]]:
        """驗證配置有效性"""
        issues = {
            "errors": [],
            "warnings": [],
            "suggestions": []
        }
        
        config = self._config
        
        # 檢查 API 金鑰
        if not config.api_key or config.api_key == "":
            issues["errors"].append("未設定 Google AI API 金鑰")
        elif len(config.api_key) < 20:
            issues["warnings"].append("API 金鑰長度可能不正確")
        
        # 檢查資料夾路徑
        if config.source_folder and not Path(config.source_folder).exists():
            issues["errors"].append(f"來源資料夾不存在: {config.source_folder}")
        
        if config.processed_folder and not Path(config.processed_folder).exists():
            issues["warnings"].append(f"處理資料夾不存在: {config.processed_folder}")
        
        if config.default_download_folder and not Path(config.default_download_folder).exists():
            issues["warnings"].append(f"下載資料夾不存在: {config.default_download_folder}")
        
        # 檢查數值範圍
        if config.default_threads < 1 or config.default_threads > 16:
            issues["warnings"].append(f"執行緒數設定異常: {config.default_threads}")
        
        if config.default_temperature < 0 or config.default_temperature > 1:
            issues["warnings"].append(f"溫度參數設定異常: {config.default_temperature}")
        
        if config.window_width < 800 or config.window_height < 600:
            issues["suggestions"].append("視窗大小可能過小，建議至少 800x600")
        
        # 檢查效能設定
        if config.max_concurrent_downloads > 10:
            issues["warnings"].append("並發下載數過高，可能影響系統效能")
        
        if config.chunk_size > 1024 * 1024:  # 1MB
            issues["suggestions"].append("區塊大小過大，可能影響記憶體使用")
        
        return issues


# 自定義例外類別
class ConfigError(CrossPlatformError):
    """配置相關錯誤的基礎類別"""
    pass


class ConfigSaveError(ConfigError):
    """配置儲存錯誤"""
    pass


class ConfigKeyError(ConfigError):
    """配置鍵值錯誤"""
    pass


class ConfigExportError(ConfigError):
    """配置匯出錯誤"""
    pass


class ConfigImportError(ConfigError):
    """配置匯入錯誤"""
    pass


# 全域配置服務實例
config_service = ConfigService()


if __name__ == "__main__":
    # 測試程式
    print("=== 配置服務測試 ===")
    
    config = config_service.get_config()
    print(f"API 金鑰: {config.api_key[:10]}..." if config.api_key else "API 金鑰: 未設定")
    print(f"AI 模型: {config.ai_model}")
    print(f"預設語言: {config.default_language}")
    print(f"視窗大小: {config.window_width}x{config.window_height}")
    
    print("\n=== 路徑驗證 ===")
    validation_results = config_service.validate_paths()
    for path_name, exists in validation_results.items():
        status = "✓" if exists else "✗"
        print(f"{status} {path_name}")
    
    missing_deps = config_service.get_missing_dependencies()
    if missing_deps:
        print(f"\n缺少的相依性: {', '.join(missing_deps)}")
    else:
        print("\n所有相依性都已滿足")