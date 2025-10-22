#!/usr/bin/env python3
"""
安裝程式建立腳本
支援 Windows、macOS 和 Linux 的安裝程式建立
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import json
import tempfile

# 添加專案根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from platform_adapter import platform_adapter


class InstallerCreator:
    """安裝程式建立器"""
    
    def __init__(self):
        self.project_root = project_root
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist"
        self.current_platform = platform_adapter.get_platform()
        
        # 載入版本資訊
        self.version_info = self._load_version_info()
        
        # 應用程式資訊
        self.app_info = {
            "name": "AI智慧工作站",
            "version": self.version_info.get("version", "4.0.0"),
            "description": "跨平台媒體處理工作站",
            "author": "Kiro AI Assistant",
            "publisher": "Kiro AI Assistant",
            "website": "https://github.com/kiro-ai/workstation",
            "support_url": "https://github.com/kiro-ai/workstation/issues",
            "license": "MIT License"
        }
    
    def _load_version_info(self) -> dict:
        """載入版本資訊"""
        version_file = self.project_root / "version.json"
        if version_file.exists():
            try:
                with open(version_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"載入版本資訊失敗: {e}")
        
        return {"version": "4.0.0"}
    
    def create_windows_installer(self) -> bool:
        """建立 Windows 安裝程式"""
        if self.current_platform != "windows":
            print("只能在 Windows 平台建立 Windows 安裝程式")
            return False
        
        print("建立 Windows 安裝程式...")
        
        # 優先使用 PyInstaller 的 onedir 輸出目錄
        pyinstaller_dir = self.dist_dir / self.app_info['name']
        if not pyinstaller_dir.exists():
            print(f"找不到 PyInstaller 輸出: {pyinstaller_dir}")
            print("請先執行: python build_scripts/build.py --type pyinstaller --skip-tests")
            return False

        # 檢查是否有可用的安裝程式建立工具
        if self._check_nsis():
            return self._create_nsis_installer(pyinstaller_dir)
        elif self._check_inno_setup():
            return self._create_inno_setup_installer(pyinstaller_dir)
        else:
            print("沒有找到可用的安裝程式建立工具")
            print("請安裝 NSIS 或 Inno Setup")
            return False
    
    def _check_nsis(self) -> bool:
        """檢查 NSIS 是否可用"""
        try:
            subprocess.run(['makensis', '/VERSION'], 
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _check_inno_setup(self) -> bool:
        """檢查 Inno Setup 是否可用"""
        try:
            # 常見的 Inno Setup 安裝路徑
            inno_paths = [
                r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
                r"C:\Program Files\Inno Setup 6\ISCC.exe",
                r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
                r"C:\Program Files\Inno Setup 5\ISCC.exe"
            ]
            
            for path in inno_paths:
                if Path(path).exists():
                    self.inno_setup_path = path
                    return True
            
            return False
        except Exception:
            return False
    
    def _create_nsis_installer(self, source_dir: Path) -> bool:
        """使用 NSIS 建立安裝程式"""
        try:
            print("使用 NSIS 建立安裝程式...")
            # 建立 NSIS 腳本
            nsis_script = self._generate_nsis_script(source_dir)
            nsis_file = self.build_dir / "installer.nsi"
            
            with open(nsis_file, 'w', encoding='utf-8') as f:
                f.write(nsis_script)
            
            # 編譯安裝程式
            installer_name = f"{self.app_info['name']}_v{self.app_info['version']}_Setup.exe"
            
            result = subprocess.run([
                'makensis',
                f'/DOUTFILE={self.dist_dir / installer_name}',
                str(nsis_file)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Windows 安裝程式建立完成: {installer_name}")
                return True
            else:
                print(f"❌ NSIS 編譯失敗: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"建立 NSIS 安裝程式時發生錯誤: {e}")
            return False
    
    def _generate_nsis_script(self, source_dir: Path) -> str:
        """生成 NSIS 安裝腳本"""
        return f'''
; AI 智慧工作站安裝程式
; 使用 NSIS 建立

!define APPNAME "{self.app_info['name']}"
!define VERSION "{self.app_info['version']}"
!define DESCRIPTION "{self.app_info['description']}"
!define PUBLISHER "{self.app_info['publisher']}"
!define WEBSITE "{self.app_info['website']}"
!define SUPPORT_URL "{self.app_info['support_url']}"

; 安裝程式設定
Name "${{APPNAME}}"
OutFile "${{OUTFILE}}"
InstallDir "$PROGRAMFILES\\${{APPNAME}}"
InstallDirRegKey HKLM "Software\\${{APPNAME}}" "InstallDir"
RequestExecutionLevel admin

; 版本資訊
VIProductVersion "{self.app_info['version']}.0"
VIAddVersionKey "ProductName" "${{APPNAME}}"
VIAddVersionKey "ProductVersion" "${{VERSION}}"
VIAddVersionKey "CompanyName" "${{PUBLISHER}}"
VIAddVersionKey "FileDescription" "${{DESCRIPTION}}"
VIAddVersionKey "LegalCopyright" "© 2024 ${{PUBLISHER}}"

; 現代化介面
!include "MUI2.nsh"

; 介面設定
!define MUI_ABORTWARNING
!define MUI_ICON "${{NSISDIR}}\\Contrib\\Graphics\\Icons\\modern-install.ico"
!define MUI_UNICON "${{NSISDIR}}\\Contrib\\Graphics\\Icons\\modern-uninstall.ico"

; 安裝頁面
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "{self.project_root / 'LICENSE'}"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; 解除安裝頁面
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; 語言
!insertmacro MUI_LANGUAGE "TradChinese"

; 安裝區段
Section "MainSection" SEC01
    SetOutPath "$INSTDIR"
    
    ; 複製所有檔案
    File /r "{source_dir}\\*"
    
    ; 建立開始選單項目
    CreateDirectory "$SMPROGRAMS\\${{APPNAME}}"
    CreateShortCut "$SMPROGRAMS\\${{APPNAME}}\\${{APPNAME}}.lnk" "$INSTDIR\\{self.app_info['name']}.exe" "" "$INSTDIR\\icon.ico"
    CreateShortCut "$SMPROGRAMS\\${{APPNAME}}\\解除安裝.lnk" "$INSTDIR\\Uninstall.exe"
    
    ; 建立桌面捷徑
    CreateShortCut "$DESKTOP\\${{APPNAME}}.lnk" "$INSTDIR\\{self.app_info['name']}.exe" "" "$INSTDIR\\icon.ico"
    
    ; 寫入登錄檔
    WriteRegStr HKLM "Software\\${{APPNAME}}" "InstallDir" "$INSTDIR"
    WriteRegStr HKLM "Software\\${{APPNAME}}" "Version" "${{VERSION}}"
    
    ; 寫入解除安裝資訊
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "DisplayName" "${{APPNAME}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "DisplayVersion" "${{VERSION}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "Publisher" "${{PUBLISHER}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "URLInfoAbout" "${{WEBSITE}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "HelpLink" "${{SUPPORT_URL}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "UninstallString" "$INSTDIR\\Uninstall.exe"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "QuietUninstallString" "$INSTDIR\\Uninstall.exe /S"
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "NoModify" 1
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "NoRepair" 1
    
    ; 建立解除安裝程式
    WriteUninstaller "$INSTDIR\\Uninstall.exe"
SectionEnd

; 解除安裝區段
Section "Uninstall"
    ; 刪除檔案
    RMDir /r "$INSTDIR"
    
    ; 刪除開始選單項目
    RMDir /r "$SMPROGRAMS\\${{APPNAME}}"
    
    ; 刪除桌面捷徑
    Delete "$DESKTOP\\${{APPNAME}}.lnk"
    
    ; 刪除登錄檔項目
    DeleteRegKey HKLM "Software\\${{APPNAME}}"
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}"
SectionEnd
'''
    
    def _create_inno_setup_installer(self, source_dir: Path) -> bool:
        """使用 Inno Setup 建立安裝程式"""
        try:
            print("使用 Inno Setup 建立安裝程式...")
            # 建立 Inno Setup 腳本
            iss_script = self._generate_inno_setup_script(source_dir)
            iss_file = self.build_dir / "installer.iss"
            
            with open(iss_file, 'w', encoding='utf-8') as f:
                f.write(iss_script)
            
            # 編譯安裝程式
            result = subprocess.run([
                self.inno_setup_path,
                str(iss_file)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                installer_name = f"{self.app_info['name']}_v{self.app_info['version']}_Setup.exe"
                print(f"✅ Windows 安裝程式建立完成: {installer_name}")
                return True
            else:
                print(f"❌ Inno Setup 編譯失敗: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"建立 Inno Setup 安裝程式時發生錯誤: {e}")
            return False
    
    def _generate_inno_setup_script(self, source_dir: Path) -> str:
        """生成 Inno Setup 安裝腳本"""
        return f'''
; AI 智慧工作站安裝程式
; 使用 Inno Setup 建立

[Setup]
AppId={{{{12345678-1234-1234-1234-123456789012}}}}
AppName={self.app_info['name']}
AppVersion={self.app_info['version']}
AppPublisher={self.app_info['publisher']}
AppPublisherURL={self.app_info['website']}
AppSupportURL={self.app_info['support_url']}
AppUpdatesURL={self.app_info['website']}
DefaultDirName={{autopf}}\\{self.app_info['name']}
DefaultGroupName={self.app_info['name']}
AllowNoIcons=yes
LicenseFile={self.project_root / 'LICENSE'}
OutputDir={self.dist_dir}
OutputBaseFilename={self.app_info['name']}_v{self.app_info['version']}_Setup
; 如需自訂圖示，將 icon.ico 放入 PyInstaller 輸出資料夾
; SetupIconFile={source_dir / 'icon.ico'}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

[Languages]
Name: "chinesetrad"; MessagesFile: "compiler:Languages\\ChineseTraditional.isl"

[Tasks]
Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"; Flags: unchecked

[Files]
Source: "{source_dir}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{{group}}\\{self.app_info['name']}"; Filename: "{{app}}\\{self.app_info['name']}.exe"; IconFilename: "{{app}}\\icon.ico"
Name: "{{group}}\\{{cm:UninstallProgram,{self.app_info['name']}}}"; Filename: "{{uninstallexe}}"
Name: "{{autodesktop}}\\{self.app_info['name']}"; Filename: "{{app}}\\{self.app_info['name']}.exe"; IconFilename: "{{app}}\\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{{app}}\\{self.app_info['name']}.exe"; Description: "{{cm:LaunchProgram,{self.app_info['name']}}}"; Flags: nowait postinstall skipifsilent
'''
    
    def create_macos_installer(self) -> bool:
        """建立 macOS 安裝程式"""
        if self.current_platform != "macos":
            print("只能在 macOS 平台建立 macOS 安裝程式")
            return False
        
        print("建立 macOS 安裝程式...")
        
        try:
            # 準備應用程式包
            app_name = f"{self.app_info['name']}.app"
            app_dir = self.dist_dir / app_name
            
            if app_dir.exists():
                shutil.rmtree(app_dir)
            
            # 建立應用程式包結構
            contents_dir = app_dir / "Contents"
            macos_dir = contents_dir / "MacOS"
            resources_dir = contents_dir / "Resources"
            
            contents_dir.mkdir(parents=True)
            macos_dir.mkdir()
            resources_dir.mkdir()
            
            # 複製應用程式檔案
            portable_dir = self.dist_dir / f"{self.app_info['name']}_Portable"
            if portable_dir.exists():
                for item in portable_dir.iterdir():
                    if item.is_file():
                        shutil.copy2(item, macos_dir)
                    else:
                        shutil.copytree(item, macos_dir / item.name, dirs_exist_ok=True)
            
            # 建立 Info.plist
            info_plist = self._generate_info_plist()
            with open(contents_dir / "Info.plist", 'w', encoding='utf-8') as f:
                f.write(info_plist)
            
            # 建立啟動腳本
            launcher_script = f'''#!/bin/bash
cd "$(dirname "$0")"
python3 gui_main.py
'''
            launcher_path = macos_dir / self.app_info['name']
            with open(launcher_path, 'w', encoding='utf-8') as f:
                f.write(launcher_script)
            
            # 設定執行權限
            os.chmod(launcher_path, 0o755)
            
            # 建立 DMG 檔案
            dmg_name = f"{self.app_info['name']}_v{self.app_info['version']}.dmg"
            dmg_path = self.dist_dir / dmg_name
            
            if dmg_path.exists():
                dmg_path.unlink()
            
            # 使用 hdiutil 建立 DMG
            result = subprocess.run([
                'hdiutil', 'create',
                '-volname', self.app_info['name'],
                '-srcfolder', str(app_dir),
                '-ov',
                '-format', 'UDZO',
                str(dmg_path)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ macOS 安裝程式建立完成: {dmg_name}")
                return True
            else:
                print(f"❌ DMG 建立失敗: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"建立 macOS 安裝程式時發生錯誤: {e}")
            return False
    
    def _generate_info_plist(self) -> str:
        """生成 macOS Info.plist"""
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>zh_TW</string>
    <key>CFBundleDisplayName</key>
    <string>{self.app_info['name']}</string>
    <key>CFBundleExecutable</key>
    <string>{self.app_info['name']}</string>
    <key>CFBundleIdentifier</key>
    <string>com.kiro.ai-workstation</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>{self.app_info['name']}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>{self.app_info['version']}</string>
    <key>CFBundleVersion</key>
    <string>{self.app_info['version']}</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.14</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSHumanReadableCopyright</key>
    <string>© 2024 {self.app_info['publisher']}</string>
</dict>
</plist>
'''
    
    def create_linux_installer(self) -> bool:
        """建立 Linux 安裝程式"""
        if self.current_platform != "linux":
            print("只能在 Linux 平台建立 Linux 安裝程式")
            return False
        
        print("建立 Linux 安裝程式...")
        
        try:
            # 建立 DEB 套件
            if self._create_deb_package():
                print("✅ DEB 套件建立完成")
            
            # 建立 RPM 套件
            if self._create_rpm_package():
                print("✅ RPM 套件建立完成")
            
            # 建立 AppImage
            if self._create_appimage():
                print("✅ AppImage 建立完成")
            
            return True
            
        except Exception as e:
            print(f"建立 Linux 安裝程式時發生錯誤: {e}")
            return False
    
    def _create_deb_package(self) -> bool:
        """建立 DEB 套件"""
        try:
            # 建立 DEB 套件結構
            deb_dir = self.build_dir / "deb"
            if deb_dir.exists():
                shutil.rmtree(deb_dir)
            
            debian_dir = deb_dir / "DEBIAN"
            usr_dir = deb_dir / "usr"
            bin_dir = usr_dir / "bin"
            share_dir = usr_dir / "share"
            app_dir = share_dir / "ai-workstation"
            desktop_dir = share_dir / "applications"
            
            for dir_path in [debian_dir, bin_dir, app_dir, desktop_dir]:
                dir_path.mkdir(parents=True)
            
            # 複製應用程式檔案
            portable_dir = self.dist_dir / f"{self.app_info['name']}_Portable"
            if portable_dir.exists():
                for item in portable_dir.iterdir():
                    if item.is_file():
                        shutil.copy2(item, app_dir)
                    else:
                        shutil.copytree(item, app_dir / item.name, dirs_exist_ok=True)
            
            # 建立啟動腳本
            launcher_script = f'''#!/bin/bash
cd /usr/share/ai-workstation
python3 gui_main.py "$@"
'''
            launcher_path = bin_dir / "ai-workstation"
            with open(launcher_path, 'w', encoding='utf-8') as f:
                f.write(launcher_script)
            os.chmod(launcher_path, 0o755)
            
            # 建立 control 檔案
            control_content = f'''Package: ai-workstation
Version: {self.app_info['version']}
Section: utils
Priority: optional
Architecture: all
Depends: python3, python3-pip, python3-tk
Maintainer: {self.app_info['publisher']} <support@example.com>
Description: {self.app_info['description']}
 跨平台媒體處理工作站，支援語音轉錄、AI 分析、媒體搜尋等功能。
'''
            with open(debian_dir / "control", 'w', encoding='utf-8') as f:
                f.write(control_content)
            
            # 建立 .desktop 檔案
            desktop_content = f'''[Desktop Entry]
Name={self.app_info['name']}
Comment={self.app_info['description']}
Exec=ai-workstation
Icon=ai-workstation
Terminal=false
Type=Application
Categories=AudioVideo;Audio;Video;
'''
            with open(desktop_dir / "ai-workstation.desktop", 'w', encoding='utf-8') as f:
                f.write(desktop_content)
            
            # 建立 DEB 套件
            deb_name = f"ai-workstation_{self.app_info['version']}_all.deb"
            deb_path = self.dist_dir / deb_name
            
            result = subprocess.run([
                'dpkg-deb', '--build', str(deb_dir), str(deb_path)
            ], capture_output=True, text=True)
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"建立 DEB 套件時發生錯誤: {e}")
            return False
    
    def _create_rpm_package(self) -> bool:
        """建立 RPM 套件"""
        # RPM 套件建立較複雜，這裡提供基本框架
        print("RPM 套件建立功能尚未完全實現")
        return True
    
    def _create_appimage(self) -> bool:
        """建立 AppImage"""
        # AppImage 建立較複雜，這裡提供基本框架
        print("AppImage 建立功能尚未完全實現")
        return True
    
    def create_uninstaller(self) -> bool:
        """建立解除安裝程式"""
        try:
            print("建立解除安裝程式...")
            
            if self.current_platform == "windows":
                return self._create_windows_uninstaller()
            elif self.current_platform == "macos":
                return self._create_macos_uninstaller()
            else:
                return self._create_linux_uninstaller()
                
        except Exception as e:
            print(f"建立解除安裝程式時發生錯誤: {e}")
            return False
    
    def _create_windows_uninstaller(self) -> bool:
        """建立 Windows 解除安裝程式"""
        uninstaller_script = f'''@echo off
echo 正在解除安裝 {self.app_info['name']}...

REM 停止應用程式
taskkill /f /im "python.exe" 2>nul
taskkill /f /im "pythonw.exe" 2>nul

REM 刪除開始選單項目
rmdir /s /q "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\{self.app_info['name']}" 2>nul

REM 刪除桌面捷徑
del "%USERPROFILE%\\Desktop\\{self.app_info['name']}.lnk" 2>nul

REM 刪除登錄檔項目
reg delete "HKLM\\Software\\{self.app_info['name']}" /f 2>nul
reg delete "HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{self.app_info['name']}" /f 2>nul

REM 刪除應用程式檔案
cd /d "%~dp0"
cd ..
rmdir /s /q "%CD%" 2>nul

echo 解除安裝完成
pause
'''
        
        uninstaller_path = self.dist_dir / f"{self.app_info['name']}_Portable" / "uninstall.bat"
        with open(uninstaller_path, 'w', encoding='utf-8') as f:
            f.write(uninstaller_script)
        
        print("✅ Windows 解除安裝程式建立完成")
        return True
    
    def _create_macos_uninstaller(self) -> bool:
        """建立 macOS 解除安裝程式"""
        uninstaller_script = f'''#!/bin/bash
echo "正在解除安裝 {self.app_info['name']}..."

# 停止應用程式
pkill -f "gui_main.py"

# 刪除應用程式包
rm -rf "/Applications/{self.app_info['name']}.app"

# 刪除使用者資料
rm -rf "$HOME/Library/Application Support/AIWorkstation"
rm -rf "$HOME/Library/Logs/AIWorkstation"

echo "解除安裝完成"
'''
        
        uninstaller_path = self.dist_dir / f"{self.app_info['name']}_Portable" / "uninstall.sh"
        with open(uninstaller_path, 'w', encoding='utf-8') as f:
            f.write(uninstaller_script)
        
        os.chmod(uninstaller_path, 0o755)
        
        print("✅ macOS 解除安裝程式建立完成")
        return True
    
    def _create_linux_uninstaller(self) -> bool:
        """建立 Linux 解除安裝程式"""
        uninstaller_script = f'''#!/bin/bash
echo "正在解除安裝 {self.app_info['name']}..."

# 停止應用程式
pkill -f "gui_main.py"

# 刪除應用程式檔案
sudo rm -rf /usr/share/ai-workstation
sudo rm -f /usr/bin/ai-workstation
sudo rm -f /usr/share/applications/ai-workstation.desktop

# 刪除使用者資料
rm -rf "$HOME/.config/aiworkstation"
rm -rf "$HOME/.local/share/aiworkstation"

echo "解除安裝完成"
'''
        
        uninstaller_path = self.dist_dir / f"{self.app_info['name']}_Portable" / "uninstall.sh"
        with open(uninstaller_path, 'w', encoding='utf-8') as f:
            f.write(uninstaller_script)
        
        os.chmod(uninstaller_path, 0o755)
        
        print("✅ Linux 解除安裝程式建立完成")
        return True
    
    def create_installer(self) -> bool:
        """建立安裝程式"""
        print(f"為 {self.current_platform} 平台建立安裝程式...")
        
        success = False
        
        if self.current_platform == "windows":
            success = self.create_windows_installer()
        elif self.current_platform == "macos":
            success = self.create_macos_installer()
        elif self.current_platform == "linux":
            success = self.create_linux_installer()
        else:
            print(f"不支援的平台: {self.current_platform}")
            return False
        
        if success:
            # 建立解除安裝程式
            self.create_uninstaller()
        
        return success


def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI 智慧工作站安裝程式建立工具")
    parser.add_argument(
        "--platform",
        choices=["windows", "macos", "linux", "all"],
        default="current",
        help="目標平台 (預設: current)"
    )
    
    args = parser.parse_args()
    
    creator = InstallerCreator()
    
    try:
        if args.platform == "all":
            # 為所有平台建立安裝程式（需要在對應平台上執行）
            print("注意: 每個平台的安裝程式需要在對應平台上建立")
            success = creator.create_installer()
        elif args.platform == "current":
            success = creator.create_installer()
        else:
            # 指定平台
            if args.platform != creator.current_platform:
                print(f"警告: 當前平台是 {creator.current_platform}，但指定建立 {args.platform} 安裝程式")
            success = creator.create_installer()
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"建立安裝程式時發生錯誤: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
