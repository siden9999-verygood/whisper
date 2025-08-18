#!/usr/bin/env python3
"""
跨平台打包腳本
支援 Windows、macOS 和 Linux 的自動化打包
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import json
import zipfile
import tarfile
import time

# 添加專案根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from platform_adapter import platform_adapter


class BuildManager:
    """打包管理器"""
    
    def __init__(self):
        self.project_root = project_root
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist"
        self.current_platform = platform_adapter.get_platform()
        
        # 應用程式資訊
        self.app_info = {
            "name": "AI智慧工作站",
            "version": "4.0.0",
            "description": "跨平台媒體處理工作站",
            "author": "Kiro AI Assistant",
            "main_script": "gui_main.py"
        }
        
        # 必要檔案和目錄
        self.required_files = [
            "gui_main.py",
            "platform_adapter.py",
            "config_service.py",
            "logging_service.py",
            "enhanced_search_manager.py",
            "transcription_manager.py",
            "archive_manager.py",
            "monitoring_manager.py",
            "diagnostics_manager.py",
            "error_handler.py",
            "natural_language_search.py",
            "performance_monitor.py",
            "query_parser.py",
            "download_manager.py",
            "install.py",
            "requirements.txt",
            "README.md"
        ]
        
        self.required_dirs = [
            "whisper_resources"
        ]
    
    def print_header(self, title):
        """列印標題"""
        print("\n" + "=" * 70)
        print(f" {title}")
        print("=" * 70)
    
    def print_section(self, title):
        """列印章節標題"""
        print(f"\n{'-' * 50}")
        print(f" {title}")
        print(f"{'-' * 50}")
    
    def run_command(self, command, cwd=None):
        """執行命令"""
        try:
            print(f"執行命令: {' '.join(command)}")
            result = subprocess.run(
                command,
                cwd=cwd or self.project_root,
                check=True,
                capture_output=True,
                text=True
            )
            if result.stdout:
                print(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            print(f"命令執行失敗: {e}")
            if e.stdout:
                print(f"標準輸出: {e.stdout}")
            if e.stderr:
                print(f"錯誤輸出: {e.stderr}")
            return False
        except Exception as e:
            print(f"執行命令時發生錯誤: {e}")
            return False
    
    def check_dependencies(self):
        """檢查打包依賴"""
        self.print_section("檢查打包依賴")
        
        # 檢查 Python 版本
        python_version = sys.version_info
        print(f"Python 版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        if python_version < (3, 8):
            print("❌ Python 版本過低，需要 3.8 或更高版本")
            return False
        
        # 檢查必要的打包工具
        required_tools = ['pip']
        optional_tools = ['pyinstaller', 'cx_Freeze', 'auto-py-to-exe']
        
        for tool in required_tools:
            if not self.check_tool_available(tool):
                print(f"❌ 缺少必要工具: {tool}")
                return False
        
        # 檢查可選工具
        available_packagers = []
        for tool in optional_tools:
            if self.check_tool_available(tool):
                available_packagers.append(tool)
        
        if not available_packagers:
            print("❌ 沒有可用的打包工具")
            print("請安裝以下工具之一:")
            print("  pip install pyinstaller")
            print("  pip install cx_Freeze")
            print("  pip install auto-py-to-exe")
            return False
        
        print(f"✅ 可用的打包工具: {', '.join(available_packagers)}")
        return True
    
    def check_tool_available(self, tool):
        """檢查工具是否可用"""
        try:
            subprocess.run([tool, '--version'], 
                         capture_output=True, 
                         check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def prepare_build_environment(self):
        """準備打包環境"""
        self.print_section("準備打包環境")
        
        # 清理舊的打包目錄
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
            print(f"清理舊的打包目錄: {self.build_dir}")
        
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
            print(f"清理舊的發布目錄: {self.dist_dir}")
        
        # 建立打包目錄
        self.build_dir.mkdir(exist_ok=True)
        self.dist_dir.mkdir(exist_ok=True)
        
        print("✅ 打包環境準備完成")
        return True
    
    def install_dependencies(self):
        """安裝依賴套件"""
        self.print_section("安裝依賴套件")
        
        requirements_file = self.project_root / "requirements.txt"
        if not requirements_file.exists():
            print("⚠️  requirements.txt 不存在，跳過依賴安裝")
            return True
        
        # 安裝依賴
        command = [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)]
        success = self.run_command(command)
        
        if success:
            print("✅ 依賴套件安裝完成")
        else:
            print("❌ 依賴套件安裝失敗")
        
        return success
    
    def run_tests(self):
        """執行測試"""
        self.print_section("執行測試")
        
        test_script = self.project_root / "run_all_tests.py"
        if not test_script.exists():
            print("⚠️  測試腳本不存在，跳過測試")
            return True
        
        # 執行測試
        command = [sys.executable, str(test_script)]
        success = self.run_command(command)
        
        if success:
            print("✅ 測試通過")
        else:
            print("❌ 測試失敗")
            response = input("測試失敗，是否繼續打包？ (y/N): ")
            if response.lower() != 'y':
                return False
        
        return True
    
    def build_with_pyinstaller(self):
        """使用 PyInstaller 打包"""
        self.print_section("使用 PyInstaller 打包")
        
        if not self.check_tool_available('pyinstaller'):
            print("PyInstaller 不可用")
            return False
        
        # PyInstaller 命令參數
        command = [
            "pyinstaller",
            "--onedir",  # 打包成目錄
            "--windowed",  # Windows 下隱藏控制台
            "--name", self.app_info["name"],
            "--distpath", str(self.dist_dir),
            "--workpath", str(self.build_dir),
            "--specpath", str(self.build_dir),
        ]
        
        # 添加資源檔案
        for required_dir in self.required_dirs:
            dir_path = self.project_root / required_dir
            if dir_path.exists():
                command.extend(["--add-data", f"{dir_path}{os.pathsep}{required_dir}"])
        
        # 添加隱藏導入
        hidden_imports = [
            "tkinter",
            "PIL",
            "pandas",
            "google.generativeai",
            "opencc",
            "psutil",
            "watchdog"
        ]
        
        for module in hidden_imports:
            command.extend(["--hidden-import", module])
        
        # 主腳本
        command.append(str(self.project_root / self.app_info["main_script"]))
        
        # 執行打包
        success = self.run_command(command)
        
        if success:
            print("✅ PyInstaller 打包完成")
            return True
        else:
            print("❌ PyInstaller 打包失敗")
            return False
    
    def build_with_cx_freeze(self):
        """使用 cx_Freeze 打包"""
        self.print_section("使用 cx_Freeze 打包")
        
        if not self.check_tool_available('cxfreeze'):
            print("cx_Freeze 不可用")
            return False
        
        # 建立 setup.py 檔案
        setup_content = f'''
import sys
from cx_Freeze import setup, Executable

# 依賴套件
packages = ["tkinter", "PIL", "pandas", "google.generativeai", "opencc", "psutil", "watchdog"]

# 包含檔案
include_files = []

# 建立執行檔
executables = [
    Executable(
        "{self.app_info["main_script"]}",
        base="Win32GUI" if sys.platform == "win32" else None,
        target_name="{self.app_info["name"]}"
    )
]

setup(
    name="{self.app_info["name"]}",
    version="{self.app_info["version"]}",
    description="{self.app_info["description"]}",
    options={{
        "build_exe": {{
            "packages": packages,
            "include_files": include_files,
            "build_exe": "{self.dist_dir / self.app_info["name"]}"
        }}
    }},
    executables=executables
)
'''
        
        setup_file = self.build_dir / "setup.py"
        setup_file.write_text(setup_content, encoding='utf-8')
        
        # 執行打包
        command = [sys.executable, str(setup_file), "build"]
        success = self.run_command(command)
        
        if success:
            print("✅ cx_Freeze 打包完成")
            return True
        else:
            print("❌ cx_Freeze 打包失敗")
            return False
    
    def create_portable_package(self):
        """建立可攜式套件"""
        self.print_section("建立可攜式套件")
        
        # 建立可攜式目錄
        portable_dir = self.dist_dir / f"{self.app_info['name']}_Portable"
        portable_dir.mkdir(exist_ok=True)
        
        # 複製必要檔案
        for file_name in self.required_files:
            src_file = self.project_root / file_name
            if src_file.exists():
                dst_file = portable_dir / file_name
                if src_file.is_file():
                    shutil.copy2(src_file, dst_file)
                else:
                    shutil.copytree(src_file, dst_file, dirs_exist_ok=True)
                print(f"複製: {file_name}")
        
        # 複製必要目錄
        for dir_name in self.required_dirs:
            src_dir = self.project_root / dir_name
            if src_dir.exists():
                dst_dir = portable_dir / dir_name
                shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
                print(f"複製目錄: {dir_name}")
        
        # 建立啟動腳本
        self.create_launch_scripts(portable_dir)
        
        # 建立安裝腳本
        install_script = portable_dir / "install_dependencies.py"
        install_script.write_text(
            (self.project_root / "install.py").read_text(encoding='utf-8'),
            encoding='utf-8'
        )
        
        print("✅ 可攜式套件建立完成")
        return True
    
    def create_launch_scripts(self, target_dir):
        """建立啟動腳本"""
        # Windows 啟動腳本
        if self.current_platform == "windows":
            bat_content = f'''@echo off
cd /d "%~dp0"
python {self.app_info["main_script"]}
if errorlevel 1 (
    echo.
    echo 程式執行失敗，請檢查 Python 環境和依賴套件
    echo 可以執行 install_dependencies.py 來安裝依賴
    pause
)
'''
            bat_file = target_dir / "start.bat"
            bat_file.write_text(bat_content, encoding='utf-8')
        
        # Unix 啟動腳本
        sh_content = f'''#!/bin/bash
cd "$(dirname "$0")"
python3 {self.app_info["main_script"]}
if [ $? -ne 0 ]; then
    echo
    echo "程式執行失敗，請檢查 Python 環境和依賴套件"
    echo "可以執行 python3 install_dependencies.py 來安裝依賴"
    read -p "按 Enter 鍵繼續..."
fi
'''
        sh_file = target_dir / "start.sh"
        sh_file.write_text(sh_content, encoding='utf-8')
        
        # 設定執行權限
        if self.current_platform in ["macos", "linux"]:
            os.chmod(sh_file, 0o755)
    
    def create_installer(self):
        """建立安裝程式"""
        self.print_section("建立安裝程式")
        
        if self.current_platform == "windows":
            return self.create_windows_installer()
        elif self.current_platform == "macos":
            return self.create_macos_installer()
        else:
            return self.create_linux_installer()
    
    def create_windows_installer(self):
        """建立 Windows 安裝程式"""
        try:
            # 檢查是否有 NSIS 或 Inno Setup
            if self.check_tool_available('makensis'):
                return self.create_nsis_installer()
            else:
                print("⚠️  NSIS 不可用，跳過 Windows 安裝程式建立")
                return True
        except Exception as e:
            print(f"建立 Windows 安裝程式時發生錯誤: {e}")
            return False
    
    def create_nsis_installer(self):
        """建立 NSIS 安裝程式"""
        nsis_script = f'''
!define APPNAME "{self.app_info["name"]}"
!define VERSION "{self.app_info["version"]}"
!define DESCRIPTION "{self.app_info["description"]}"

Name "${{APPNAME}}"
OutFile "{self.dist_dir}\\${{APPNAME}}_Setup.exe"
InstallDir "$PROGRAMFILES\\${{APPNAME}}"

Page directory
Page instfiles

Section "MainSection" SEC01
    SetOutPath "$INSTDIR"
    File /r "{self.dist_dir}\\{self.app_info["name"]}_Portable\\*"
    
    CreateDirectory "$SMPROGRAMS\\${{APPNAME}}"
    CreateShortCut "$SMPROGRAMS\\${{APPNAME}}\\${{APPNAME}}.lnk" "$INSTDIR\\start.bat"
    CreateShortCut "$DESKTOP\\${{APPNAME}}.lnk" "$INSTDIR\\start.bat"
    
    WriteUninstaller "$INSTDIR\\Uninstall.exe"
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\\Uninstall.exe"
    RMDir /r "$INSTDIR"
    Delete "$SMPROGRAMS\\${{APPNAME}}\\${{APPNAME}}.lnk"
    RMDir "$SMPROGRAMS\\${{APPNAME}}"
    Delete "$DESKTOP\\${{APPNAME}}.lnk"
SectionEnd
'''
        
        nsis_file = self.build_dir / "installer.nsi"
        nsis_file.write_text(nsis_script, encoding='utf-8')
        
        # 編譯安裝程式
        command = ["makensis", str(nsis_file)]
        return self.run_command(command)
    
    def create_macos_installer(self):
        """建立 macOS 安裝程式"""
        print("⚠️  macOS 安裝程式建立功能尚未實現")
        return True
    
    def create_linux_installer(self):
        """建立 Linux 安裝程式"""
        print("⚠️  Linux 安裝程式建立功能尚未實現")
        return True
    
    def create_distribution_packages(self):
        """建立發布套件"""
        self.print_section("建立發布套件")
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        # 建立 ZIP 套件
        zip_name = f"{self.app_info['name']}_v{self.app_info['version']}_{self.current_platform}_{timestamp}.zip"
        zip_path = self.dist_dir / zip_name
        
        portable_dir = self.dist_dir / f"{self.app_info['name']}_Portable"
        if portable_dir.exists():
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in portable_dir.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(portable_dir)
                        zipf.write(file_path, arcname)
            
            print(f"✅ ZIP 套件已建立: {zip_name}")
        
        # 建立 TAR.GZ 套件（Unix 系統）
        if self.current_platform in ["macos", "linux"]:
            tar_name = f"{self.app_info['name']}_v{self.app_info['version']}_{self.current_platform}_{timestamp}.tar.gz"
            tar_path = self.dist_dir / tar_name
            
            with tarfile.open(tar_path, 'w:gz') as tarf:
                for file_path in portable_dir.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(portable_dir)
                        tarf.add(file_path, arcname)
            
            print(f"✅ TAR.GZ 套件已建立: {tar_name}")
        
        return True
    
    def generate_build_info(self):
        """生成打包資訊"""
        self.print_section("生成打包資訊")
        
        build_info = {
            "app_info": self.app_info,
            "build_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "platform": self.current_platform,
            "system_info": platform_adapter.get_system_info(),
            "python_version": sys.version,
            "build_files": []
        }
        
        # 記錄打包檔案
        for item in self.dist_dir.iterdir():
            if item.is_file():
                build_info["build_files"].append({
                    "name": item.name,
                    "size": item.stat().st_size,
                    "type": "file"
                })
            elif item.is_dir():
                build_info["build_files"].append({
                    "name": item.name,
                    "type": "directory"
                })
        
        # 儲存打包資訊
        info_file = self.dist_dir / "build_info.json"
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(build_info, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 打包資訊已儲存: {info_file}")
        return True
    
    def build(self, build_type="portable"):
        """執行打包"""
        self.print_header(f"AI 智慧工作站 - 跨平台打包 ({self.current_platform})")
        
        print(f"打包類型: {build_type}")
        print(f"目標平台: {self.current_platform}")
        print(f"專案路徑: {self.project_root}")
        
        # 打包步驟
        build_steps = [
            ("檢查打包依賴", self.check_dependencies),
            ("準備打包環境", self.prepare_build_environment),
            ("安裝依賴套件", self.install_dependencies),
            ("執行測試", self.run_tests),
        ]
        
        # 根據打包類型添加步驟
        if build_type == "portable":
            build_steps.append(("建立可攜式套件", self.create_portable_package))
        elif build_type == "pyinstaller":
            build_steps.append(("PyInstaller 打包", self.build_with_pyinstaller))
        elif build_type == "cx_freeze":
            build_steps.append(("cx_Freeze 打包", self.build_with_cx_freeze))
        
        build_steps.extend([
            ("建立發布套件", self.create_distribution_packages),
            ("生成打包資訊", self.generate_build_info),
        ])
        
        # 執行打包步驟
        start_time = time.time()
        
        for step_name, step_func in build_steps:
            print(f"\n🔄 {step_name}...")
            try:
                success = step_func()
                if success:
                    print(f"✅ {step_name} 完成")
                else:
                    print(f"❌ {step_name} 失敗")
                    return False
            except Exception as e:
                print(f"❌ {step_name} 發生錯誤: {e}")
                return False
        
        # 打包完成
        end_time = time.time()
        build_time = end_time - start_time
        
        self.print_header("打包完成")
        print(f"打包時間: {build_time:.2f} 秒")
        print(f"輸出目錄: {self.dist_dir}")
        
        # 列出打包結果
        print("\n打包結果:")
        for item in self.dist_dir.iterdir():
            if item.is_file():
                size_mb = item.stat().st_size / (1024 * 1024)
                print(f"  📄 {item.name} ({size_mb:.1f} MB)")
            elif item.is_dir():
                print(f"  📁 {item.name}/")
        
        print("\n🎉 打包成功完成！")
        return True


def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI 智慧工作站跨平台打包工具")
    parser.add_argument(
        "--type", 
        choices=["portable", "pyinstaller", "cx_freeze"],
        default="portable",
        help="打包類型 (預設: portable)"
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="跳過測試"
    )
    
    args = parser.parse_args()
    
    # 建立打包管理器
    builder = BuildManager()
    
    # 如果指定跳過測試，修改測試步驟
    if args.skip_tests:
        builder.run_tests = lambda: True
    
    try:
        # 執行打包
        success = builder.build(build_type=args.type)
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\n⚠️  打包被使用者中斷")
        return 1
    except Exception as e:
        print(f"\n❌ 打包過程中發生未預期的錯誤: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())