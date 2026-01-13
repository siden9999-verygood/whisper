"""
模型下載器
從 Hugging Face 下載 Whisper ggml-large-v2.bin 模型
"""

import os
import sys
import urllib.request
from pathlib import Path
from typing import Optional, Callable


class ModelDownloader:
    """Whisper 模型下載器"""
    
    # Hugging Face 模型 URL
    MODEL_URL = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v2.bin"
    MODEL_NAME = "ggml-large-v2.bin"
    MODEL_SIZE = 3_094_623_691  # 約 3GB
    
    def __init__(self):
        """初始化下載器"""
        # 確定資源目錄
        if getattr(sys, 'frozen', False):
            self.base_path = Path(sys.executable).parent
        else:
            self.base_path = Path(__file__).parent
        
        self.resources_dir = self.base_path / "whisper_resources"
        self.model_path = self.resources_dir / self.MODEL_NAME
        
        # 確保資源目錄存在
        self.resources_dir.mkdir(parents=True, exist_ok=True)
    
    def is_model_available(self) -> bool:
        """檢查模型是否已下載"""
        if not self.model_path.exists():
            return False
        
        # 檢查檔案大小是否正確（至少 2.8GB）
        file_size = self.model_path.stat().st_size
        return file_size > 2_800_000_000
    
    def get_model_path(self) -> Path:
        """取得模型路徑"""
        return self.model_path
    
    def download_model(self, progress_callback: Optional[Callable[[float], None]] = None) -> bool:
        """
        下載模型
        
        Args:
            progress_callback: 進度回調函數，接收 0.0-1.0 的進度值
            
        Returns:
            是否下載成功
        """
        if self.is_model_available():
            print(f"模型已存在：{self.model_path}")
            return True
        
        print(f"開始下載模型：{self.MODEL_URL}")
        print(f"目標位置：{self.model_path}")
        print(f"檔案大小：約 {self.MODEL_SIZE / 1024 / 1024 / 1024:.1f} GB")
        
        temp_path = self.model_path.with_suffix('.tmp')
        
        try:
            # 建立下載請求
            request = urllib.request.Request(
                self.MODEL_URL,
                headers={'User-Agent': 'Mozilla/5.0 (Whisper Transcriber)'}
            )
            
            with urllib.request.urlopen(request, timeout=30) as response:
                total_size = int(response.headers.get('Content-Length', self.MODEL_SIZE))
                downloaded = 0
                chunk_size = 1024 * 1024  # 1MB chunks
                
                with open(temp_path, 'wb') as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback:
                            progress = downloaded / total_size
                            progress_callback(min(progress, 1.0))
                        
                        # 顯示進度
                        progress_pct = (downloaded / total_size) * 100
                        downloaded_mb = downloaded / 1024 / 1024
                        total_mb = total_size / 1024 / 1024
                        print(f"\r下載進度：{progress_pct:.1f}% ({downloaded_mb:.0f}/{total_mb:.0f} MB)", end="")
            
            print()  # 換行
            
            # 重命名臨時檔案
            temp_path.rename(self.model_path)
            print(f"模型下載完成：{self.model_path}")
            return True
            
        except Exception as e:
            print(f"\n下載失敗：{e}")
            # 清理臨時檔案
            if temp_path.exists():
                temp_path.unlink()
            raise RuntimeError(f"模型下載失敗：{e}")
    
    def get_download_size_str(self) -> str:
        """取得下載大小的字串表示"""
        return f"{self.MODEL_SIZE / 1024 / 1024 / 1024:.1f} GB"


# 測試
if __name__ == "__main__":
    downloader = ModelDownloader()
    
    print(f"模型路徑：{downloader.model_path}")
    print(f"模型是否可用：{downloader.is_model_available()}")
    
    if not downloader.is_model_available():
        response = input("是否要下載模型？(y/n): ")
        if response.lower() == 'y':
            downloader.download_model()
