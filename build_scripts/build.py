#!/usr/bin/env python3
"""
跨平台打包腳本
將語音轉錄工具打包為可執行檔
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import platform


class AppBuilder:
    """應用程式打包器"""
    
    APP_NAME = "語音轉錄工具"
    APP_NAME_EN = "VoiceTranscriber"
    VERSION = "1.0.0"
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist"
        self.resources_dir = self.project_root / "whisper_resources"
        
        # 主程式檔案
        self.main_script = self.project_root / "app_main.py"
        
        # 需要包含的模組
        self.modules = [
            "app_main.py",
            "model_downloader.py",
            "transcription_core.py",
        ]
        
        # 需要包含的資源（不含模型）
        self.resources = [
            "whisper_resources/main",      # macOS
            "whisper_resources/main.exe",  # Windows
            "whisper_resources/ffmpeg",    # macOS
            "whisper_resources/ffmpeg.exe", # Windows
        ]
    
    def print_header(self, text):
        print(f"\n{'='*60}")
        print(f"  {text}")
        print(f"{'='*60}\n")
    
    def check_pyinstaller(self):
        """檢查 PyInstaller 是否安裝"""
        try:
            import PyInstaller
            print(f"✅ PyInstaller 版本：{PyInstaller.__version__}")
            return True
        except ImportError:
            print("❌ PyInstaller 未安裝")
            print("正在安裝 PyInstaller...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            return True
    
    def clean_build(self):
        """清理舊的建置檔案"""
        print("清理舊的建置檔案...")
        
        for dir_path in [self.build_dir, self.dist_dir]:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"  已刪除：{dir_path}")
        
        # 清理 .spec 檔案
        for spec_file in self.project_root.glob("*.spec"):
            spec_file.unlink()
            print(f"  已刪除：{spec_file}")
    
    def build_windows(self):
        """建置 Windows 版本"""
        self.print_header("建置 Windows 版本")
        
        if platform.system() != "Windows":
            print("⚠️ 警告：非 Windows 系統，跳過 Windows 建置")
            print("  請在 Windows 系統上執行此腳本以建置 Windows 版本")
            return False
        
        return self._run_pyinstaller("windows")
    
    def build_macos(self):
        """建置 macOS 版本"""
        self.print_header("建置 macOS 版本")
        
        if platform.system() != "Darwin":
            print("⚠️ 警告：非 macOS 系統，跳過 macOS 建置")
            print("  請在 macOS 系統上執行此腳本以建置 macOS 版本")
            return False
        
        return self._run_pyinstaller("macos")
    
    def _run_pyinstaller(self, target_platform):
        """執行 PyInstaller"""
        # 確定資源檔案
        datas = []
        
        # 添加 whisper 執行檔和 ffmpeg
        if target_platform == "windows":
            resource_files = ["main.exe", "ffmpeg.exe"]
        else:
            resource_files = ["main", "ffmpeg"]
        
        for res_file in resource_files:
            res_path = self.resources_dir / res_file
            if res_path.exists():
                datas.append(f"--add-data={res_path}{os.pathsep}whisper_resources")
                print(f"  包含資源：{res_file}")
        
        # Frameworks 目錄（macOS）
        frameworks_dir = self.resources_dir / "Frameworks"
        if frameworks_dir.exists() and target_platform == "macos":
            datas.append(f"--add-data={frameworks_dir}{os.pathsep}whisper_resources/Frameworks")
        
        # 建構 PyInstaller 命令
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--name", self.APP_NAME_EN,
            "--onedir",
            "--clean",
            "--noconfirm",
        ]
        
        # 平台特定選項
        if target_platform == "macos":
            cmd.extend([
                "--windowed",
                "--osx-bundle-identifier", "com.siden9999.voicetranscriber",
            ])
        elif target_platform == "windows":
            cmd.extend([
                "--windowed",
                "--console",  # 暫時保留控制台以便調試
            ])
        
        # 添加資源
        cmd.extend(datas)
        
        # 隱藏導入
        cmd.extend([
            "--hidden-import=customtkinter",
            "--hidden-import=srt",
            "--hidden-import=opencc",
        ])
        
        # 排除不需要的模組
        cmd.extend([
            "--exclude-module=matplotlib",
            "--exclude-module=scipy",
            "--exclude-module=pandas",
            "--exclude-module=numpy",
            "--exclude-module=PIL",
            "--exclude-module=cv2",
        ])
        
        # 主程式
        cmd.append(str(self.main_script))
        
        print(f"執行命令：{' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, cwd=self.project_root, check=True)
            print(f"✅ {target_platform} 版本建置成功！")
            print(f"  輸出目錄：{self.dist_dir / self.APP_NAME_EN}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 建置失敗：{e}")
            return False
    
    def create_dmg(self):
        """建立 macOS DMG 安裝包"""
        if platform.system() != "Darwin":
            print("⚠️ 只能在 macOS 上建立 DMG")
            return False
        
        self.print_header("建立 DMG 安裝包")
        
        app_path = self.dist_dir / f"{self.APP_NAME_EN}.app"
        dmg_path = self.dist_dir / f"{self.APP_NAME_EN}-{self.VERSION}.dmg"
        
        if not app_path.exists():
            print(f"❌ 找不到 .app：{app_path}")
            return False
        
        # 使用 hdiutil 建立 DMG
        cmd = [
            "hdiutil", "create",
            "-volname", self.APP_NAME,
            "-srcfolder", str(app_path),
            "-ov",
            "-format", "UDZO",
            str(dmg_path)
        ]
        
        try:
            subprocess.run(cmd, check=True)
            print(f"✅ DMG 建立成功：{dmg_path}")
            print(f"  檔案大小：{dmg_path.stat().st_size / 1024 / 1024:.1f} MB")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ DMG 建立失敗：{e}")
            return False
    
    def build(self):
        """執行完整建置"""
        self.print_header(f"開始建置 {self.APP_NAME} v{self.VERSION}")
        
        # 檢查 PyInstaller
        if not self.check_pyinstaller():
            return False
        
        # 清理
        self.clean_build()
        
        # 根據平台建置
        current_platform = platform.system()
        
        if current_platform == "Darwin":
            success = self.build_macos()
            if success:
                self.create_dmg()
        elif current_platform == "Windows":
            success = self.build_windows()
        else:
            print(f"⚠️ 不支援的平台：{current_platform}")
            success = False
        
        if success:
            self.print_header("建置完成！")
            print(f"輸出目錄：{self.dist_dir}")
            print("\n注意事項：")
            print("1. 首次執行時會自動從 Hugging Face 下載 Whisper 模型（約 3GB）")
            print("2. macOS 版本首次執行可能需要右鍵選擇「打開」")
            print("3. Windows 版本可能需要確認安全警告")
        
        return success


def main():
    builder = AppBuilder()
    success = builder.build()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
