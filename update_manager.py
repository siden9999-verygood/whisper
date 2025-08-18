"""
自動更新管理器
處理應用程式的版本檢查和自動更新功能
"""

import os
import sys
import json
import requests
import hashlib
import zipfile
import shutil
from pathlib import Path
from typing import Dict, Optional, Tuple
import threading
import time
from datetime import datetime, timedelta

from platform_adapter import platform_adapter
from config_service import config_service
from logging_service import logging_service


class Version:
    """版本類別"""
    
    def __init__(self, version_string: str):
        self.version_string = version_string
        self.parts = self._parse_version(version_string)
    
    def _parse_version(self, version_string: str) -> Tuple[int, int, int]:
        """解析版本字串"""
        try:
            # 移除 'v' 前綴（如果有）
            if version_string.startswith('v'):
                version_string = version_string[1:]
            
            # 分割版本號
            parts = version_string.split('.')
            major = int(parts[0]) if len(parts) > 0 else 0
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0
            
            return (major, minor, patch)
        except (ValueError, IndexError):
            return (0, 0, 0)
    
    def __str__(self):
        return self.version_string
    
    def __eq__(self, other):
        return self.parts == other.parts
    
    def __lt__(self, other):
        return self.parts < other.parts
    
    def __le__(self, other):
        return self.parts <= other.parts
    
    def __gt__(self, other):
        return self.parts > other.parts
    
    def __ge__(self, other):
        return self.parts >= other.parts


class UpdateInfo:
    """更新資訊類別"""
    
    def __init__(self, data: Dict):
        self.version = Version(data.get('version', '0.0.0'))
        self.release_date = data.get('release_date', '')
        self.download_url = data.get('download_url', '')
        self.file_size = data.get('file_size', 0)
        self.checksum = data.get('checksum', '')
        self.release_notes = data.get('release_notes', '')
        self.is_critical = data.get('is_critical', False)
        self.min_version = Version(data.get('min_version', '0.0.0'))
        self.platform_specific = data.get('platform_specific', {})
    
    def get_platform_info(self, platform: str) -> Dict:
        """取得平台特定資訊"""
        return self.platform_specific.get(platform, {})


class UpdateManager:
    """更新管理器"""
    
    def __init__(self):
        self.current_version = Version("4.0.0")  # 當前版本
        self.update_server_url = "https://api.example.com/updates"  # 更新伺服器 URL
        self.check_interval = 24 * 3600  # 檢查間隔（秒）
        self.last_check_time = None
        self.update_available = False
        self.latest_update_info = None
        
        # 更新相關路徑
        self.app_dir = platform_adapter.base_path
        self.temp_dir = platform_adapter.get_temp_dir() / "updates"
        self.backup_dir = platform_adapter.get_config_dir() / "backups"
        
        # 確保目錄存在
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 載入上次檢查時間
        self._load_update_cache()
    
    def _load_update_cache(self):
        """載入更新快取"""
        try:
            cache_file = platform_adapter.get_config_dir() / "update_cache.json"
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    self.last_check_time = cache_data.get('last_check_time')
                    if cache_data.get('update_info'):
                        self.latest_update_info = UpdateInfo(cache_data['update_info'])
                        self.update_available = True
        except Exception as e:
            logging_service.warning(f"載入更新快取失敗: {e}")
    
    def _save_update_cache(self):
        """儲存更新快取"""
        try:
            cache_file = platform_adapter.get_config_dir() / "update_cache.json"
            cache_data = {
                'last_check_time': self.last_check_time,
                'update_info': None
            }
            
            if self.latest_update_info:
                cache_data['update_info'] = {
                    'version': str(self.latest_update_info.version),
                    'release_date': self.latest_update_info.release_date,
                    'download_url': self.latest_update_info.download_url,
                    'file_size': self.latest_update_info.file_size,
                    'checksum': self.latest_update_info.checksum,
                    'release_notes': self.latest_update_info.release_notes,
                    'is_critical': self.latest_update_info.is_critical,
                    'min_version': str(self.latest_update_info.min_version),
                    'platform_specific': self.latest_update_info.platform_specific
                }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logging_service.warning(f"儲存更新快取失敗: {e}")
    
    def should_check_for_updates(self) -> bool:
        """檢查是否應該檢查更新"""
        if not self.last_check_time:
            return True
        
        try:
            last_check = datetime.fromisoformat(self.last_check_time)
            now = datetime.now()
            return (now - last_check).total_seconds() > self.check_interval
        except:
            return True
    
    def check_for_updates(self, force: bool = False) -> Optional[UpdateInfo]:
        """檢查更新"""
        if not force and not self.should_check_for_updates():
            logging_service.debug("跳過更新檢查（未到檢查時間）")
            return self.latest_update_info if self.update_available else None
        
        try:
            logging_service.info("檢查應用程式更新...")
            
            # 準備請求參數
            params = {
                'current_version': str(self.current_version),
                'platform': platform_adapter.get_platform(),
                'system_info': platform_adapter.get_system_info()
            }
            
            # 發送請求到更新伺服器
            response = requests.get(
                self.update_server_url,
                params=params,
                timeout=30,
                headers={'User-Agent': 'AI-Workstation-UpdateChecker/4.0'}
            )
            
            if response.status_code == 200:
                update_data = response.json()
                
                if update_data.get('has_update', False):
                    self.latest_update_info = UpdateInfo(update_data['update_info'])
                    self.update_available = True
                    
                    logging_service.info(f"發現新版本: {self.latest_update_info.version}")
                    
                    # 檢查是否為重要更新
                    if self.latest_update_info.is_critical:
                        logging_service.warning("這是一個重要更新，建議立即安裝")
                    
                else:
                    self.update_available = False
                    self.latest_update_info = None
                    logging_service.info("目前已是最新版本")
                
                # 更新檢查時間
                self.last_check_time = datetime.now().isoformat()
                self._save_update_cache()
                
                return self.latest_update_info
            
            elif response.status_code == 204:
                # 沒有更新
                self.update_available = False
                self.latest_update_info = None
                self.last_check_time = datetime.now().isoformat()
                self._save_update_cache()
                logging_service.info("目前已是最新版本")
                return None
            
            else:
                logging_service.warning(f"檢查更新失敗，伺服器回應: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            logging_service.warning(f"檢查更新時網路錯誤: {e}")
            return None
        except Exception as e:
            logging_service.error(f"檢查更新時發生錯誤: {e}")
            return None
    
    def download_update(self, update_info: UpdateInfo, 
                       progress_callback: Optional[callable] = None) -> Optional[Path]:
        """下載更新檔案"""
        try:
            logging_service.info(f"開始下載更新: {update_info.version}")
            
            # 取得平台特定的下載 URL
            platform_info = update_info.get_platform_info(platform_adapter.get_platform())
            download_url = platform_info.get('download_url', update_info.download_url)
            
            if not download_url:
                logging_service.error("沒有可用的下載連結")
                return None
            
            # 準備下載檔案路徑
            filename = f"update_{update_info.version}_{platform_adapter.get_platform()}.zip"
            download_path = self.temp_dir / filename
            
            # 如果檔案已存在且校驗和正確，直接返回
            if download_path.exists() and self._verify_checksum(download_path, update_info.checksum):
                logging_service.info("更新檔案已存在且校驗和正確")
                return download_path
            
            # 下載檔案
            response = requests.get(download_url, stream=True, timeout=60)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # 回調進度
                        if progress_callback and total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            progress_callback(progress, downloaded_size, total_size)
            
            # 驗證校驗和
            if update_info.checksum and not self._verify_checksum(download_path, update_info.checksum):
                logging_service.error("更新檔案校驗和不正確")
                download_path.unlink()
                return None
            
            logging_service.info(f"更新檔案下載完成: {download_path}")
            return download_path
            
        except Exception as e:
            logging_service.error(f"下載更新失敗: {e}")
            return None
    
    def _verify_checksum(self, file_path: Path, expected_checksum: str) -> bool:
        """驗證檔案校驗和"""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            
            actual_checksum = sha256_hash.hexdigest()
            return actual_checksum.lower() == expected_checksum.lower()
            
        except Exception as e:
            logging_service.error(f"驗證校驗和時發生錯誤: {e}")
            return False
    
    def create_backup(self) -> bool:
        """建立當前版本的備份"""
        try:
            logging_service.info("建立應用程式備份...")
            
            # 備份檔案名稱
            backup_name = f"backup_{self.current_version}_{int(time.time())}"
            backup_path = self.backup_dir / backup_name
            
            # 建立備份目錄
            backup_path.mkdir(exist_ok=True)
            
            # 複製重要檔案
            important_files = [
                "gui_main.py",
                "platform_adapter.py",
                "config_service.py",
                "logging_service.py",
                "requirements.txt"
            ]
            
            for file_name in important_files:
                src_file = self.app_dir / file_name
                if src_file.exists():
                    dst_file = backup_path / file_name
                    if src_file.is_file():
                        shutil.copy2(src_file, dst_file)
                    else:
                        shutil.copytree(src_file, dst_file, dirs_exist_ok=True)
            
            # 記錄備份資訊
            backup_info = {
                'version': str(self.current_version),
                'backup_time': datetime.now().isoformat(),
                'platform': platform_adapter.get_platform(),
                'files': important_files
            }
            
            info_file = backup_path / "backup_info.json"
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, indent=2, ensure_ascii=False)
            
            logging_service.info(f"備份建立完成: {backup_path}")
            return True
            
        except Exception as e:
            logging_service.error(f"建立備份失敗: {e}")
            return False
    
    def install_update(self, update_file: Path, 
                      progress_callback: Optional[callable] = None) -> bool:
        """安裝更新"""
        try:
            logging_service.info("開始安裝更新...")
            
            # 建立備份
            if not self.create_backup():
                logging_service.error("建立備份失敗，取消更新")
                return False
            
            # 解壓更新檔案
            temp_extract_dir = self.temp_dir / "extract"
            if temp_extract_dir.exists():
                shutil.rmtree(temp_extract_dir)
            temp_extract_dir.mkdir()
            
            with zipfile.ZipFile(update_file, 'r') as zip_ref:
                zip_ref.extractall(temp_extract_dir)
            
            # 尋找更新檔案
            update_files = list(temp_extract_dir.rglob('*'))
            total_files = len([f for f in update_files if f.is_file()])
            processed_files = 0
            
            # 複製更新檔案
            for item in update_files:
                if item.is_file():
                    # 計算相對路徑
                    rel_path = item.relative_to(temp_extract_dir)
                    target_path = self.app_dir / rel_path
                    
                    # 確保目標目錄存在
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 複製檔案
                    shutil.copy2(item, target_path)
                    processed_files += 1
                    
                    # 回調進度
                    if progress_callback:
                        progress = (processed_files / total_files) * 100
                        progress_callback(progress, processed_files, total_files)
            
            # 清理臨時檔案
            shutil.rmtree(temp_extract_dir)
            update_file.unlink()
            
            # 更新版本資訊
            self.current_version = self.latest_update_info.version
            self.update_available = False
            self.latest_update_info = None
            
            logging_service.info(f"更新安裝完成，新版本: {self.current_version}")
            return True
            
        except Exception as e:
            logging_service.error(f"安裝更新失敗: {e}")
            return False
    
    def rollback_update(self, backup_name: str) -> bool:
        """回滾更新"""
        try:
            logging_service.info(f"開始回滾更新: {backup_name}")
            
            backup_path = self.backup_dir / backup_name
            if not backup_path.exists():
                logging_service.error(f"備份不存在: {backup_path}")
                return False
            
            # 讀取備份資訊
            info_file = backup_path / "backup_info.json"
            if info_file.exists():
                with open(info_file, 'r', encoding='utf-8') as f:
                    backup_info = json.load(f)
                    backup_files = backup_info.get('files', [])
            else:
                # 如果沒有備份資訊，掃描所有檔案
                backup_files = [f.name for f in backup_path.iterdir() if f.is_file()]
            
            # 還原檔案
            for file_name in backup_files:
                src_file = backup_path / file_name
                dst_file = self.app_dir / file_name
                
                if src_file.exists():
                    if src_file.is_file():
                        shutil.copy2(src_file, dst_file)
                    else:
                        if dst_file.exists():
                            shutil.rmtree(dst_file)
                        shutil.copytree(src_file, dst_file)
            
            logging_service.info("更新回滾完成")
            return True
            
        except Exception as e:
            logging_service.error(f"回滾更新失敗: {e}")
            return False
    
    def get_available_backups(self) -> list:
        """取得可用的備份清單"""
        backups = []
        
        try:
            for backup_dir in self.backup_dir.iterdir():
                if backup_dir.is_dir():
                    info_file = backup_dir / "backup_info.json"
                    if info_file.exists():
                        with open(info_file, 'r', encoding='utf-8') as f:
                            backup_info = json.load(f)
                            backups.append({
                                'name': backup_dir.name,
                                'version': backup_info.get('version', 'Unknown'),
                                'backup_time': backup_info.get('backup_time', ''),
                                'platform': backup_info.get('platform', ''),
                                'path': str(backup_dir)
                            })
                    else:
                        # 沒有資訊檔案的備份
                        backups.append({
                            'name': backup_dir.name,
                            'version': 'Unknown',
                            'backup_time': '',
                            'platform': '',
                            'path': str(backup_dir)
                        })
        
        except Exception as e:
            logging_service.error(f"取得備份清單失敗: {e}")
        
        return sorted(backups, key=lambda x: x['backup_time'], reverse=True)
    
    def cleanup_old_backups(self, keep_count: int = 5):
        """清理舊備份"""
        try:
            backups = self.get_available_backups()
            
            if len(backups) > keep_count:
                old_backups = backups[keep_count:]
                
                for backup in old_backups:
                    backup_path = Path(backup['path'])
                    if backup_path.exists():
                        shutil.rmtree(backup_path)
                        logging_service.info(f"已刪除舊備份: {backup['name']}")
                
                logging_service.info(f"清理完成，保留 {keep_count} 個最新備份")
        
        except Exception as e:
            logging_service.error(f"清理舊備份失敗: {e}")
    
    def start_background_check(self):
        """啟動背景更新檢查"""
        def background_check():
            while True:
                try:
                    if self.should_check_for_updates():
                        self.check_for_updates()
                    
                    # 等待一小時後再次檢查
                    time.sleep(3600)
                    
                except Exception as e:
                    logging_service.error(f"背景更新檢查錯誤: {e}")
                    time.sleep(3600)  # 錯誤後等待一小時
        
        # 啟動背景線程
        thread = threading.Thread(target=background_check, daemon=True)
        thread.start()
        logging_service.info("背景更新檢查已啟動")


# 全域更新管理器實例
update_manager = UpdateManager()


if __name__ == "__main__":
    # 測試更新管理器
    print("=== 更新管理器測試 ===")
    
    # 檢查更新
    update_info = update_manager.check_for_updates(force=True)
    
    if update_info:
        print(f"發現新版本: {update_info.version}")
        print(f"發布日期: {update_info.release_date}")
        print(f"檔案大小: {update_info.file_size} bytes")
        print(f"是否重要更新: {update_info.is_critical}")
        print(f"更新說明: {update_info.release_notes}")
    else:
        print("目前已是最新版本")
    
    # 顯示可用備份
    backups = update_manager.get_available_backups()
    print(f"\n可用備份: {len(backups)} 個")
    for backup in backups:
        print(f"  {backup['name']} - 版本: {backup['version']}")