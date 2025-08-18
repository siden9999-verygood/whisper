"""
下載管理器模組
提供檔案下載、進度追蹤和佇列管理功能
"""

import os
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib
import requests
from urllib.parse import urlparse, unquote

from platform_adapter import platform_adapter, file_manager
from config_service import config_service
from logging_service import logging_service


class DownloadStatus(Enum):
    """下載狀態枚舉"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DownloadItem:
    """下載項目資料類別"""
    id: str
    url: str
    filename: str
    destination: str
    status: DownloadStatus = DownloadStatus.PENDING
    progress: float = 0.0
    downloaded_bytes: int = 0
    total_bytes: int = 0
    speed: float = 0.0  # bytes per second
    eta: Optional[int] = None  # estimated time remaining in seconds
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    chunk_size: int = 8192
    headers: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class DownloadManager:
    """下載管理器"""
    
    def __init__(self):
        self.config = config_service.get_config()
        self.logger = logging_service.get_logger("DownloadManager")
        
        # 下載項目管理
        self.downloads: Dict[str, DownloadItem] = {}
        self.download_queue: List[str] = []
        self.active_downloads: Dict[str, threading.Thread] = {}
        
        # 配置
        self.max_concurrent_downloads = 3
        self.default_timeout = 30
        self.default_chunk_size = 8192
        self.resume_support = True
        
        # 統計資訊
        self.total_downloaded = 0
        self.total_failed = 0
        self.session_start_time = datetime.now()
        
        # 事件回調
        self.progress_callbacks: List[Callable] = []
        self.status_callbacks: List[Callable] = []
        
        # 下載目錄
        self.download_dir = self._get_download_directory()
        
        # 啟動管理執行緒
        self.manager_thread = threading.Thread(target=self._download_manager_loop, daemon=True)
        self.manager_running = True
        self.manager_thread.start()
    
    def _get_download_directory(self) -> Path:
        """取得下載目錄"""
        # 優先使用配置中的下載目錄
        if hasattr(self.config, 'download_folder') and self.config.download_folder:
            download_dir = Path(self.config.download_folder)
        else:
            # 使用系統預設下載目錄
            download_dir = Path(platform_adapter.path_manager.get_downloads_directory())
        
        # 確保目錄存在
        download_dir.mkdir(parents=True, exist_ok=True)
        return download_dir
    
    def add_download(self, url: str, filename: Optional[str] = None, 
                    destination: Optional[str] = None, 
                    headers: Optional[Dict[str, str]] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> str:
        """添加下載任務"""
        try:
            # 生成唯一ID
            download_id = self._generate_download_id(url)
            
            # 解析檔案名
            if not filename:
                filename = self._extract_filename_from_url(url)
            
            # 設定目標路徑
            if not destination:
                destination = str(self.download_dir)
            
            # 確保目標目錄存在
            dest_path = Path(destination)
            dest_path.mkdir(parents=True, exist_ok=True)
            
            # 建立下載項目
            download_item = DownloadItem(
                id=download_id,
                url=url,
                filename=filename,
                destination=str(dest_path / filename),
                headers=headers or {},
                metadata=metadata or {}
            )
            
            # 檢查檔案是否已存在
            if Path(download_item.destination).exists():
                if self._should_overwrite_existing_file(download_item):
                    self.logger.info(f"將覆蓋現有檔案: {download_item.destination}")
                else:
                    download_item.filename = self._get_unique_filename(download_item.destination)
                    download_item.destination = str(dest_path / download_item.filename)
            
            # 添加到管理器
            self.downloads[download_id] = download_item
            self.download_queue.append(download_id)
            
            self.logger.info(f"已添加下載任務: {filename} ({url})")
            self._notify_status_change(download_item)
            
            return download_id
            
        except Exception as e:
            self.logger.error(f"添加下載任務失敗: {str(e)}")
            raise
    
    def add_batch_downloads(self, urls: List[str], destination: Optional[str] = None) -> List[str]:
        """批次添加下載任務"""
        download_ids = []
        
        for url in urls:
            try:
                download_id = self.add_download(url, destination=destination)
                download_ids.append(download_id)
            except Exception as e:
                self.logger.error(f"批次添加下載失敗 ({url}): {str(e)}")
        
        self.logger.info(f"批次添加了 {len(download_ids)} 個下載任務")
        return download_ids
    
    def start_download(self, download_id: str) -> bool:
        """開始指定的下載"""
        if download_id not in self.downloads:
            self.logger.error(f"下載任務不存在: {download_id}")
            return False
        
        download_item = self.downloads[download_id]
        
        if download_item.status == DownloadStatus.DOWNLOADING:
            self.logger.warning(f"下載已在進行中: {download_id}")
            return True
        
        if download_item.status == DownloadStatus.COMPLETED:
            self.logger.warning(f"下載已完成: {download_id}")
            return True
        
        # 檢查並發下載限制
        if len(self.active_downloads) >= self.max_concurrent_downloads:
            self.logger.info(f"達到並發下載限制，將下載加入佇列: {download_id}")
            if download_id not in self.download_queue:
                self.download_queue.append(download_id)
            return True
        
        # 開始下載
        return self._start_download_thread(download_id)
    
    def pause_download(self, download_id: str) -> bool:
        """暫停下載"""
        if download_id not in self.downloads:
            return False
        
        download_item = self.downloads[download_id]
        
        if download_item.status == DownloadStatus.DOWNLOADING:
            download_item.status = DownloadStatus.PAUSED
            self._notify_status_change(download_item)
            self.logger.info(f"已暫停下載: {download_id}")
            return True
        
        return False
    
    def resume_download(self, download_id: str) -> bool:
        """恢復下載"""
        if download_id not in self.downloads:
            return False
        
        download_item = self.downloads[download_id]
        
        if download_item.status == DownloadStatus.PAUSED:
            download_item.status = DownloadStatus.PENDING
            return self.start_download(download_id)
        
        return False
    
    def cancel_download(self, download_id: str) -> bool:
        """取消下載"""
        if download_id not in self.downloads:
            return False
        
        download_item = self.downloads[download_id]
        download_item.status = DownloadStatus.CANCELLED
        
        # 從佇列中移除
        if download_id in self.download_queue:
            self.download_queue.remove(download_id)
        
        # 停止活動的下載執行緒
        if download_id in self.active_downloads:
            # 執行緒會在下次檢查狀態時自動停止
            pass
        
        self._notify_status_change(download_item)
        self.logger.info(f"已取消下載: {download_id}")
        return True
    
    def remove_download(self, download_id: str, delete_file: bool = False) -> bool:
        """移除下載任務"""
        if download_id not in self.downloads:
            return False
        
        download_item = self.downloads[download_id]
        
        # 先取消下載
        self.cancel_download(download_id)
        
        # 刪除檔案（如果需要）
        if delete_file and Path(download_item.destination).exists():
            try:
                Path(download_item.destination).unlink()
                self.logger.info(f"已刪除下載檔案: {download_item.destination}")
            except Exception as e:
                self.logger.error(f"刪除下載檔案失敗: {str(e)}")
        
        # 從管理器中移除
        del self.downloads[download_id]
        
        self.logger.info(f"已移除下載任務: {download_id}")
        return True
    
    def get_download_info(self, download_id: str) -> Optional[DownloadItem]:
        """取得下載資訊"""
        return self.downloads.get(download_id)
    
    def get_all_downloads(self) -> List[DownloadItem]:
        """取得所有下載任務"""
        return list(self.downloads.values())
    
    def get_downloads_by_status(self, status: DownloadStatus) -> List[DownloadItem]:
        """根據狀態取得下載任務"""
        return [item for item in self.downloads.values() if item.status == status]
    
    def clear_completed_downloads(self) -> int:
        """清除已完成的下載任務"""
        completed_ids = [
            item.id for item in self.downloads.values() 
            if item.status == DownloadStatus.COMPLETED
        ]
        
        for download_id in completed_ids:
            del self.downloads[download_id]
        
        self.logger.info(f"已清除 {len(completed_ids)} 個已完成的下載任務")
        return len(completed_ids)
    
    def get_download_statistics(self) -> Dict[str, Any]:
        """取得下載統計資訊"""
        stats = {
            "total_downloads": len(self.downloads),
            "pending": len(self.get_downloads_by_status(DownloadStatus.PENDING)),
            "downloading": len(self.get_downloads_by_status(DownloadStatus.DOWNLOADING)),
            "paused": len(self.get_downloads_by_status(DownloadStatus.PAUSED)),
            "completed": len(self.get_downloads_by_status(DownloadStatus.COMPLETED)),
            "failed": len(self.get_downloads_by_status(DownloadStatus.FAILED)),
            "cancelled": len(self.get_downloads_by_status(DownloadStatus.CANCELLED)),
            "total_downloaded_bytes": sum(item.downloaded_bytes for item in self.downloads.values()),
            "session_duration": (datetime.now() - self.session_start_time).total_seconds(),
            "active_downloads": len(self.active_downloads),
            "queue_length": len(self.download_queue)
        }
        
        # 計算平均下載速度
        downloading_items = self.get_downloads_by_status(DownloadStatus.DOWNLOADING)
        if downloading_items:
            stats["average_speed"] = sum(item.speed for item in downloading_items) / len(downloading_items)
        else:
            stats["average_speed"] = 0.0
        
        return stats
    
    def add_progress_callback(self, callback: Callable[[DownloadItem], None]) -> None:
        """添加進度回調函數"""
        self.progress_callbacks.append(callback)
    
    def add_status_callback(self, callback: Callable[[DownloadItem], None]) -> None:
        """添加狀態變更回調函數"""
        self.status_callbacks.append(callback)
    
    def _generate_download_id(self, url: str) -> str:
        """生成下載ID"""
        timestamp = str(int(time.time() * 1000))
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        return f"dl_{timestamp}_{url_hash}"
    
    def _extract_filename_from_url(self, url: str) -> str:
        """從URL提取檔案名"""
        try:
            parsed_url = urlparse(url)
            filename = unquote(os.path.basename(parsed_url.path))
            
            if not filename or '.' not in filename:
                # 如果無法從URL提取檔案名，使用預設名稱
                filename = f"download_{int(time.time())}"
            
            return filename
            
        except Exception as e:
            self.logger.error(f"提取檔案名失敗: {str(e)}")
            return f"download_{int(time.time())}"
    
    def _should_overwrite_existing_file(self, download_item: DownloadItem) -> bool:
        """檢查是否應該覆蓋現有檔案"""
        # 這裡可以實現更複雜的邏輯，比如檢查檔案大小、修改時間等
        return False
    
    def _get_unique_filename(self, filepath: str) -> str:
        """取得唯一的檔案名"""
        path = Path(filepath)
        base_name = path.stem
        extension = path.suffix
        counter = 1
        
        while True:
            new_name = f"{base_name}_{counter}{extension}"
            new_path = path.parent / new_name
            
            if not new_path.exists():
                return new_name
            
            counter += 1
    
    def _start_download_thread(self, download_id: str) -> bool:
        """啟動下載執行緒"""
        try:
            download_item = self.downloads[download_id]
            download_item.status = DownloadStatus.DOWNLOADING
            download_item.started_at = datetime.now()
            
            # 建立並啟動下載執行緒
            thread = threading.Thread(
                target=self._download_worker,
                args=(download_id,),
                daemon=True
            )
            
            self.active_downloads[download_id] = thread
            thread.start()
            
            self._notify_status_change(download_item)
            self.logger.info(f"已開始下載: {download_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"啟動下載執行緒失敗: {str(e)}")
            return False
    
    def _download_worker(self, download_id: str) -> None:
        """下載工作執行緒"""
        download_item = self.downloads[download_id]
        
        try:
            self._perform_download(download_item)
            
        except Exception as e:
            self.logger.error(f"下載失敗 ({download_id}): {str(e)}")
            download_item.status = DownloadStatus.FAILED
            download_item.error_message = str(e)
            
        finally:
            # 清理
            if download_id in self.active_downloads:
                del self.active_downloads[download_id]
            
            self._notify_status_change(download_item)
    
    def _perform_download(self, download_item: DownloadItem) -> None:
        """執行實際下載"""
        # 檢查是否支援斷點續傳
        resume_pos = 0
        if self.resume_support and Path(download_item.destination).exists():
            resume_pos = Path(download_item.destination).stat().st_size
            download_item.downloaded_bytes = resume_pos
        
        # 準備請求標頭
        headers = download_item.headers.copy()
        if resume_pos > 0:
            headers['Range'] = f'bytes={resume_pos}-'
        
        # 發送請求
        response = requests.get(
            download_item.url,
            headers=headers,
            stream=True,
            timeout=self.default_timeout
        )
        
        response.raise_for_status()
        
        # 取得檔案總大小
        if 'content-length' in response.headers:
            content_length = int(response.headers['content-length'])
            if resume_pos > 0:
                download_item.total_bytes = resume_pos + content_length
            else:
                download_item.total_bytes = content_length
        
        # 開始下載
        mode = 'ab' if resume_pos > 0 else 'wb'
        start_time = time.time()
        last_update_time = start_time
        
        with open(download_item.destination, mode) as f:
            for chunk in response.iter_content(chunk_size=download_item.chunk_size):
                # 檢查是否被取消或暫停
                if download_item.status in [DownloadStatus.CANCELLED, DownloadStatus.PAUSED]:
                    break
                
                if chunk:
                    f.write(chunk)
                    download_item.downloaded_bytes += len(chunk)
                    
                    # 更新進度和速度
                    current_time = time.time()
                    if current_time - last_update_time >= 1.0:  # 每秒更新一次
                        elapsed_time = current_time - start_time
                        if elapsed_time > 0:
                            download_item.speed = download_item.downloaded_bytes / elapsed_time
                        
                        # 計算進度
                        if download_item.total_bytes > 0:
                            download_item.progress = (download_item.downloaded_bytes / download_item.total_bytes) * 100
                            
                            # 計算預估剩餘時間
                            if download_item.speed > 0:
                                remaining_bytes = download_item.total_bytes - download_item.downloaded_bytes
                                download_item.eta = int(remaining_bytes / download_item.speed)
                        
                        self._notify_progress_change(download_item)
                        last_update_time = current_time
        
        # 檢查下載是否完成
        if download_item.status == DownloadStatus.DOWNLOADING:
            download_item.status = DownloadStatus.COMPLETED
            download_item.completed_at = datetime.now()
            download_item.progress = 100.0
            self.total_downloaded += 1
            
            self.logger.info(f"下載完成: {download_item.filename}")
        elif download_item.status == DownloadStatus.CANCELLED:
            # 如果被取消，刪除部分下載的檔案
            try:
                if Path(download_item.destination).exists():
                    Path(download_item.destination).unlink()
            except Exception as e:
                self.logger.error(f"刪除取消的下載檔案失敗: {str(e)}")
    
    def _download_manager_loop(self) -> None:
        """下載管理器主循環"""
        while self.manager_running:
            try:
                # 處理佇列中的下載
                while (len(self.active_downloads) < self.max_concurrent_downloads and 
                       self.download_queue):
                    
                    download_id = self.download_queue.pop(0)
                    
                    if download_id in self.downloads:
                        download_item = self.downloads[download_id]
                        
                        if download_item.status == DownloadStatus.PENDING:
                            self._start_download_thread(download_id)
                
                # 清理已完成的執行緒
                completed_threads = []
                for download_id, thread in self.active_downloads.items():
                    if not thread.is_alive():
                        completed_threads.append(download_id)
                
                for download_id in completed_threads:
                    del self.active_downloads[download_id]
                
                # 重試失敗的下載
                self._retry_failed_downloads()
                
                time.sleep(1)  # 每秒檢查一次
                
            except Exception as e:
                self.logger.error(f"下載管理器循環錯誤: {str(e)}")
                time.sleep(5)
    
    def _retry_failed_downloads(self) -> None:
        """重試失敗的下載"""
        for download_item in self.downloads.values():
            if (download_item.status == DownloadStatus.FAILED and 
                download_item.retry_count < download_item.max_retries):
                
                download_item.retry_count += 1
                download_item.status = DownloadStatus.PENDING
                download_item.error_message = None
                
                if download_item.id not in self.download_queue:
                    self.download_queue.append(download_item.id)
                
                self.logger.info(f"重試下載 ({download_item.retry_count}/{download_item.max_retries}): {download_item.id}")
    
    def _notify_progress_change(self, download_item: DownloadItem) -> None:
        """通知進度變更"""
        for callback in self.progress_callbacks:
            try:
                callback(download_item)
            except Exception as e:
                self.logger.error(f"進度回調錯誤: {str(e)}")
    
    def _notify_status_change(self, download_item: DownloadItem) -> None:
        """通知狀態變更"""
        for callback in self.status_callbacks:
            try:
                callback(download_item)
            except Exception as e:
                self.logger.error(f"狀態回調錯誤: {str(e)}")
    
    def shutdown(self) -> None:
        """關閉下載管理器"""
        self.logger.info("正在關閉下載管理器...")
        
        # 停止管理器循環
        self.manager_running = False
        
        # 暫停所有活動的下載
        for download_id in list(self.active_downloads.keys()):
            self.pause_download(download_id)
        
        # 等待所有執行緒完成
        for thread in self.active_downloads.values():
            thread.join(timeout=5)
        
        self.logger.info("下載管理器已關閉")


# 全域下載管理器實例
download_manager = DownloadManager()


if __name__ == "__main__":
    # 測試程式
    print("=== 下載管理器測試 ===")
    
    # 測試添加下載
    test_url = "https://httpbin.org/bytes/1024"  # 測試用URL
    download_id = download_manager.add_download(test_url, "test_file.bin")
    print(f"已添加下載: {download_id}")
    
    # 開始下載
    download_manager.start_download(download_id)
    
    # 等待一段時間
    time.sleep(2)
    
    # 檢查狀態
    download_info = download_manager.get_download_info(download_id)
    if download_info:
        print(f"下載狀態: {download_info.status}")
        print(f"下載進度: {download_info.progress:.1f}%")
    
    # 取得統計資訊
    stats = download_manager.get_download_statistics()
    print(f"統計資訊: {stats}")
    
    print("測試完成")