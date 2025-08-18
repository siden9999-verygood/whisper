#!/usr/bin/env python3
"""
AI 智慧工作站 - 跨平台安裝腳本
支援 Windows、macOS 和 Linux
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
import json


class InstallationManager:
    """安裝管理器"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.python_version = sys.version_info
        self.base_path = Path(__file__).parent
        
        # 最低系統需求
        self.min_python_version = (3, 8)
        self.required_packages = [
            'google-generativeai>=0.3.0',
            'pandas>=1.5.0',
            'Pillow>=9.0.0',
            'srt>=3.5.0',
            'opencc-python-reimplemented>=1.1.0',
            'psutil>=5.9.0',
            'watchdog>=2.1.0',
            'requests>=2.25.0'
        ]
        
        # 可選套件
        self.optional_packages = [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0'
        ]
    
    def print_header(self):
        """顯示安裝標題"""
        print("=" * 60)
        print("AI 智慧工作站 v3.0 - 跨平台安裝程式")
        print("=" * 60)
        print(f"作業系統: {platform.system()} {platform.release()}")
        print(f"Python 版本: {sys.version}")
        print(f"安裝路徑: {self.base_path}")
        print()
    
    def check_system_requirements(self) -> bool:
        """檢查系統需求"""
        print("🔍 檢查系統需求...")
        
        # 檢查 Python 版本
        if self.python_version < self.min_python_version:
            print(f"❌ Python 版本過低: {self.python_version}")
            print(f"   需要 Python {self.min_python_version[0]}.{self.min_python_version[1]} 或更高版本")
            return False
        
        print(f"✅ Python 版本: {self.python_version[0]}.{self.python_version[1]}.{self.python_version[2]}")
        
        # 檢查 pip
        try:
            subprocess.run([sys.executable, '-m', 'pip', '--version'], 
                         check=True, capture_output=True)
            print("✅ pip 可用")
        except subprocess.CalledProcessError:
            print("❌ pip 不可用")
            return False
        
        # 檢查磁碟空間
        try:
            import shutil
            free_space = shutil.disk_usage(self.base_path).free
            required_space = 500 * 1024 * 1024  # 500MB
            
            if free_space < required_space:
                print(f"❌ 磁碟空間不足: {free_space // (1024*1024)} MB 可用")
                print(f"   需要至少 {required_space // (1024*1024)} MB")
                return False
            
            print(f"✅ 磁碟空間: {free_space // (1024*1024)} MB 可用")
        except Exception as e:
            print(f"⚠️  無法檢查磁碟空間: {e}")
        
        return True
    
    def install_packages(self) -> bool:
        """安裝 Python 套件"""
        print("📦 安裝 Python 套件...")
        
        # 升級 pip
        try:
            print("  升級 pip...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'], 
                         check=True, capture_output=True)
            print("  ✅ pip 已升級")
        except subprocess.CalledProcessError as e:
            print(f"  ⚠️  pip 升級失敗: {e}")
        
        # 安裝必要套件
        failed_packages = []
        
        for package in self.required_packages:
            try:
                print(f"  安裝 {package}...")
                subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                             check=True, capture_output=True)
                print(f"  ✅ {package}")
            except subprocess.CalledProcessError as e:
                print(f"  ❌ {package} 安裝失敗")
                failed_packages.append(package)
        
        # 安裝可選套件
        print("  安裝可選套件...")
        for package in self.optional_packages:
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                             check=True, capture_output=True)
                print(f"  ✅ {package} (可選)")
            except subprocess.CalledProcessError:
                print(f"  ⚠️  {package} 安裝失敗 (可選)")
        
        if failed_packages:
            print(f"❌ 以下套件安裝失敗: {', '.join(failed_packages)}")
            return False
        
        print("✅ 所有必要套件安裝完成")
        return True
    
    def verify_installation(self) -> bool:
        """驗證安裝"""
        print("🔍 驗證安裝...")
        
        # 測試導入核心模組
        test_imports = [
            ('google.generativeai', 'Google Generative AI'),
            ('pandas', 'Pandas'),
            ('PIL', 'Pillow'),
            ('srt', 'SRT'),
            ('opencc', 'OpenCC'),
            ('psutil', 'psutil'),
            ('watchdog', 'Watchdog')
        ]
        
        failed_imports = []
        
        for module_name, display_name in test_imports:
            try:
                __import__(module_name)
                print(f"  ✅ {display_name}")
            except ImportError:
                print(f"  ❌ {display_name}")
                failed_imports.append(display_name)
        
        # 測試自定義模組
        custom_modules = [
            'platform_adapter',
            'config_service',
            'logging_service',
            'monitoring_manager',
            'diagnostics_manager'
        ]
        
        for module_name in custom_modules:
            try:
                module_path = self.base_path / f"{module_name}.py"
                if module_path.exists():
                    print(f"  ✅ {module_name}.py")
                else:
                    print(f"  ❌ {module_name}.py 不存在")
                    failed_imports.append(module_name)
            except Exception as e:
                print(f"  ❌ {module_name}: {e}")
                failed_imports.append(module_name)
        
        if failed_imports:
            print(f"❌ 以下模組驗證失敗: {', '.join(failed_imports)}")
            return False
        
        print("✅ 所有模組驗證通過")
        return True
    
    def setup_directories(self) -> bool:
        """設定目錄結構"""
        print("📁 設定目錄結構...")
        
        try:
            # 建立配置目錄
            if self.system == 'windows':
                config_dir = Path(os.environ.get('APPDATA', '')) / 'AIWorkstation'
            elif self.system == 'darwin':
                config_dir = Path.home() / 'Library' / 'Application Support' / 'AIWorkstation'
            else:  # Linux
                config_dir = Path.home() / '.config' / 'aiworkstation'
            
            config_dir.mkdir(parents=True, exist_ok=True)
            print(f"  ✅ 配置目錄: {config_dir}")
            
            # 建立日誌目錄
            log_dir = config_dir / 'logs'
            log_dir.mkdir(exist_ok=True)
            print(f"  ✅ 日誌目錄: {log_dir}")
            
            # 建立診斷目錄
            diag_dir = config_dir / 'diagnostics'
            diag_dir.mkdir(exist_ok=True)
            print(f"  ✅ 診斷目錄: {diag_dir}")
            
            return True
            
        except Exception as e:
            print(f"❌ 目錄設定失敗: {e}")
            return False
    
    def create_shortcuts(self) -> bool:
        """建立快捷方式"""
        print("🔗 建立快捷方式...")
        
        try:
            # 建立啟動腳本
            if self.system == 'windows':
                script_content = f'''@echo off
cd /d "{self.base_path}"
python gui_main.py
pause
'''
                script_path = self.base_path / 'start.bat'
                with open(script_path, 'w', encoding='utf-8') as f:
                    f.write(script_content)
                print(f"  ✅ Windows 啟動腳本: {script_path}")
                
            else:  # macOS/Linux
                script_content = f'''#!/bin/bash
cd "{self.base_path}"
python3 gui_main.py
'''
                script_path = self.base_path / 'start.sh'
                with open(script_path, 'w', encoding='utf-8') as f:
                    f.write(script_content)
                
                # 設定執行權限
                os.chmod(script_path, 0o755)
                print(f"  ✅ Unix 啟動腳本: {script_path}")
            
            return True
            
        except Exception as e:
            print(f"❌ 快捷方式建立失敗: {e}")
            return False
    
    def run_tests(self) -> bool:
        """執行測試"""
        print("🧪 執行基本測試...")
        
        try:
            # 測試配置服務
            test_script = '''
import sys
sys.path.insert(0, ".")
from config_service import config_service
from logging_service import logging_service
from diagnostics_manager import diagnostics_manager

# 測試配置服務
config = config_service.get_config()
print(f"配置載入成功: {config.ai_model}")

# 測試日誌服務
logger = logging_service.get_logger("InstallTest")
logger.info("安裝測試日誌")

# 測試診斷服務
health = diagnostics_manager.quick_health_check()
print(f"系統健康檢查: {health['overall_status']}")

print("所有測試通過")
'''
            
            result = subprocess.run([sys.executable, '-c', test_script], 
                                  cwd=self.base_path, 
                                  capture_output=True, 
                                  text=True)
            
            if result.returncode == 0:
                print("  ✅ 基本功能測試通過")
                return True
            else:
                print(f"  ❌ 測試失敗: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ 測試執行失敗: {e}")
            return False
    
    def print_completion_message(self):
        """顯示完成訊息"""
        print()
        print("=" * 60)
        print("🎉 安裝完成！")
        print("=" * 60)
        print()
        print("啟動方式:")
        
        if self.system == 'windows':
            print("  方式1: 雙擊 start.bat")
            print("  方式2: python gui_main.py")
        else:
            print("  方式1: ./start.sh")
            print("  方式2: python3 gui_main.py")
        
        print()
        print("功能說明:")
        print("  🎤 語音轉錄 - 使用 Whisper.cpp 進行語音轉文字")
        print("  🤖 AI 分析 - 使用 Google Gemini 進行智能分析")
        print("  🗂️  媒體歸檔 - 自動分類和組織媒體檔案")
        print("  🔍 智能搜尋 - 自然語言搜尋媒體內容")
        print("  📊 效能監控 - 系統資源監控和最佳化")
        print()
        print("如需幫助，請查看 README.md 或執行診斷功能")
        print()
    
    def install(self) -> bool:
        """執行完整安裝"""
        self.print_header()
        
        steps = [
            ("檢查系統需求", self.check_system_requirements),
            ("安裝 Python 套件", self.install_packages),
            ("設定目錄結構", self.setup_directories),
            ("驗證安裝", self.verify_installation),
            ("建立快捷方式", self.create_shortcuts),
            ("執行基本測試", self.run_tests)
        ]
        
        for step_name, step_func in steps:
            print(f"\n📋 {step_name}...")
            if not step_func():
                print(f"\n❌ 安裝失敗於步驟: {step_name}")
                return False
        
        self.print_completion_message()
        return True


def main():
    """主函數"""
    installer = InstallationManager()
    
    try:
        success = installer.install()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  安裝被使用者中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 安裝過程中發生未預期的錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()