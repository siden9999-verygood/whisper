#!/usr/bin/env python3
"""
版本控制和發布腳本
管理版本號、建立發布標籤、生成更新日誌
"""

import os
import sys
import subprocess
import json
import re
from pathlib import Path
from datetime import datetime
import argparse

# 添加專案根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from platform_adapter import platform_adapter


class ReleaseManager:
    """發布管理器"""
    
    def __init__(self):
        self.project_root = project_root
        self.version_file = self.project_root / "version.json"
        self.changelog_file = self.project_root / "CHANGELOG.md"
        
        # 載入當前版本資訊
        self.version_info = self._load_version_info()
    
    def _load_version_info(self) -> dict:
        """載入版本資訊"""
        if self.version_file.exists():
            try:
                with open(self.version_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"載入版本資訊失敗: {e}")
        
        # 預設版本資訊
        return {
            "version": "4.0.0",
            "build_number": 1,
            "release_date": "",
            "release_notes": [],
            "pre_release": False
        }
    
    def _save_version_info(self):
        """儲存版本資訊"""
        try:
            with open(self.version_file, 'w', encoding='utf-8') as f:
                json.dump(self.version_info, f, indent=2, ensure_ascii=False)
            print(f"版本資訊已儲存: {self.version_file}")
        except Exception as e:
            print(f"儲存版本資訊失敗: {e}")
    
    def get_current_version(self) -> str:
        """取得當前版本"""
        return self.version_info["version"]
    
    def increment_version(self, part: str = "patch") -> str:
        """遞增版本號"""
        current = self.version_info["version"]
        parts = current.split('.')
        
        if len(parts) != 3:
            raise ValueError(f"無效的版本格式: {current}")
        
        major, minor, patch = map(int, parts)
        
        if part == "major":
            major += 1
            minor = 0
            patch = 0
        elif part == "minor":
            minor += 1
            patch = 0
        elif part == "patch":
            patch += 1
        else:
            raise ValueError(f"無效的版本部分: {part}")
        
        new_version = f"{major}.{minor}.{patch}"
        self.version_info["version"] = new_version
        self.version_info["build_number"] += 1
        
        print(f"版本已更新: {current} -> {new_version}")
        return new_version
    
    def set_version(self, version: str):
        """設定版本號"""
        # 驗證版本格式
        if not re.match(r'^\d+\.\d+\.\d+$', version):
            raise ValueError(f"無效的版本格式: {version}")
        
        old_version = self.version_info["version"]
        self.version_info["version"] = version
        self.version_info["build_number"] += 1
        
        print(f"版本已設定: {old_version} -> {version}")
    
    def add_release_note(self, note: str, category: str = "feature"):
        """添加發布說明"""
        if "release_notes" not in self.version_info:
            self.version_info["release_notes"] = []
        
        self.version_info["release_notes"].append({
            "category": category,
            "description": note,
            "timestamp": datetime.now().isoformat()
        })
        
        print(f"已添加發布說明 ({category}): {note}")
    
    def generate_changelog(self) -> str:
        """生成更新日誌"""
        changelog_content = f"# 更新日誌\n\n"
        
        # 當前版本
        version = self.version_info["version"]
        release_date = self.version_info.get("release_date", datetime.now().strftime("%Y-%m-%d"))
        
        changelog_content += f"## [{version}] - {release_date}\n\n"
        
        # 分類發布說明
        categories = {
            "feature": "### 新功能",
            "improvement": "### 改進",
            "bugfix": "### 錯誤修復",
            "security": "### 安全性",
            "breaking": "### 重大變更"
        }
        
        release_notes = self.version_info.get("release_notes", [])
        
        for category, title in categories.items():
            notes = [note for note in release_notes if note.get("category") == category]
            if notes:
                changelog_content += f"{title}\n\n"
                for note in notes:
                    changelog_content += f"- {note['description']}\n"
                changelog_content += "\n"
        
        # 如果沒有發布說明，添加預設內容
        if not release_notes:
            changelog_content += "### 改進\n\n- 一般性改進和錯誤修復\n\n"
        
        return changelog_content
    
    def update_changelog_file(self):
        """更新更新日誌檔案"""
        new_changelog = self.generate_changelog()
        
        # 如果檔案存在，讀取現有內容
        existing_content = ""
        if self.changelog_file.exists():
            try:
                with open(self.changelog_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 尋找第二個版本標題的位置
                    lines = content.split('\n')
                    version_count = 0
                    for i, line in enumerate(lines):
                        if line.startswith('## ['):
                            version_count += 1
                            if version_count == 2:
                                existing_content = '\n'.join(lines[i:])
                                break
                    else:
                        # 如果沒有找到第二個版本，保留所有內容
                        if version_count == 1:
                            existing_content = '\n'.join(lines[4:])  # 跳過標題和第一個版本標題
            except Exception as e:
                print(f"讀取現有更新日誌失敗: {e}")
        
        # 合併新舊內容
        full_changelog = new_changelog
        if existing_content.strip():
            full_changelog += existing_content
        
        # 寫入檔案
        try:
            with open(self.changelog_file, 'w', encoding='utf-8') as f:
                f.write(full_changelog)
            print(f"更新日誌已更新: {self.changelog_file}")
        except Exception as e:
            print(f"更新更新日誌失敗: {e}")
    
    def update_source_files(self):
        """更新原始碼中的版本號"""
        version = self.version_info["version"]
        
        # 更新 gui_main.py 中的版本號
        gui_main_file = self.project_root / "gui_main.py"
        if gui_main_file.exists():
            try:
                content = gui_main_file.read_text(encoding='utf-8')
                
                # 更新 APP_VERSION
                content = re.sub(
                    r'APP_VERSION = "[^"]*"',
                    f'APP_VERSION = "v{version}"',
                    content
                )
                
                # 更新 APP_TITLE
                content = re.sub(
                    r'APP_TITLE = f"[^"]*"',
                    f'APP_TITLE = f"{{APP_NAME}} {{APP_VERSION}} (增強版)"',
                    content
                )
                
                gui_main_file.write_text(content, encoding='utf-8')
                print(f"已更新 gui_main.py 中的版本號: {version}")
                
            except Exception as e:
                print(f"更新 gui_main.py 失敗: {e}")
        
        # 更新 update_manager.py 中的版本號
        update_manager_file = self.project_root / "update_manager.py"
        if update_manager_file.exists():
            try:
                content = update_manager_file.read_text(encoding='utf-8')
                
                # 更新 current_version
                content = re.sub(
                    r'self\.current_version = Version\("[^"]*"\)',
                    f'self.current_version = Version("{version}")',
                    content
                )
                
                update_manager_file.write_text(content, encoding='utf-8')
                print(f"已更新 update_manager.py 中的版本號: {version}")
                
            except Exception as e:
                print(f"更新 update_manager.py 失敗: {e}")
    
    def create_git_tag(self) -> bool:
        """建立 Git 標籤"""
        try:
            version = self.version_info["version"]
            tag_name = f"v{version}"
            
            # 檢查是否已存在該標籤
            result = subprocess.run(
                ["git", "tag", "-l", tag_name],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.stdout.strip():
                print(f"標籤 {tag_name} 已存在")
                return False
            
            # 建立標籤
            tag_message = f"Release {version}"
            if self.version_info.get("release_notes"):
                tag_message += f"\n\n發布說明:\n"
                for note in self.version_info["release_notes"]:
                    tag_message += f"- {note['description']}\n"
            
            result = subprocess.run(
                ["git", "tag", "-a", tag_name, "-m", tag_message],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                print(f"Git 標籤已建立: {tag_name}")
                return True
            else:
                print(f"建立 Git 標籤失敗: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"建立 Git 標籤時發生錯誤: {e}")
            return False
    
    def commit_version_changes(self) -> bool:
        """提交版本變更"""
        try:
            version = self.version_info["version"]
            
            # 添加變更的檔案
            files_to_add = [
                str(self.version_file),
                str(self.changelog_file),
                "gui_main.py",
                "update_manager.py"
            ]
            
            for file_path in files_to_add:
                if Path(self.project_root / file_path).exists():
                    subprocess.run(
                        ["git", "add", file_path],
                        cwd=self.project_root,
                        check=True
                    )
            
            # 提交變更
            commit_message = f"Release v{version}"
            result = subprocess.run(
                ["git", "commit", "-m", commit_message],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                print(f"版本變更已提交: {commit_message}")
                return True
            else:
                print(f"提交版本變更失敗: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"提交版本變更時發生錯誤: {e}")
            return False
    
    def build_release(self, build_type: str = "portable") -> bool:
        """建立發布版本"""
        try:
            print(f"開始建立發布版本 ({build_type})...")
            
            # 執行打包腳本
            build_script = self.project_root / "build_scripts" / "build.py"
            if not build_script.exists():
                print("打包腳本不存在")
                return False
            
            result = subprocess.run(
                [sys.executable, str(build_script), "--type", build_type],
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                print("發布版本建立完成")
                return True
            else:
                print("建立發布版本失敗")
                return False
                
        except Exception as e:
            print(f"建立發布版本時發生錯誤: {e}")
            return False
    
    def create_release(self, version_part: str = "patch", 
                      build_type: str = "portable",
                      skip_tests: bool = False,
                      skip_git: bool = False) -> bool:
        """建立完整發布"""
        try:
            print("=" * 60)
            print("AI 智慧工作站 - 發布管理")
            print("=" * 60)
            
            # 1. 遞增版本號
            if version_part:
                self.increment_version(version_part)
            
            # 2. 設定發布日期
            self.version_info["release_date"] = datetime.now().strftime("%Y-%m-%d")
            
            # 3. 儲存版本資訊
            self._save_version_info()
            
            # 4. 更新原始碼中的版本號
            self.update_source_files()
            
            # 5. 更新更新日誌
            self.update_changelog_file()
            
            # 6. 執行測試（如果不跳過）
            if not skip_tests:
                print("\n執行測試...")
                test_script = self.project_root / "run_all_tests.py"
                if test_script.exists():
                    result = subprocess.run([sys.executable, str(test_script)])
                    if result.returncode != 0:
                        print("測試失敗，是否繼續發布？")
                        response = input("繼續 (y/N): ")
                        if response.lower() != 'y':
                            return False
            
            # 7. Git 操作（如果不跳過）
            if not skip_git:
                print("\n執行 Git 操作...")
                if not self.commit_version_changes():
                    print("提交變更失敗")
                    return False
                
                if not self.create_git_tag():
                    print("建立標籤失敗")
                    return False
            
            # 8. 建立發布版本
            print(f"\n建立發布版本 ({build_type})...")
            if not self.build_release(build_type):
                print("建立發布版本失敗")
                return False
            
            # 9. 完成
            version = self.version_info["version"]
            print("\n" + "=" * 60)
            print(f"🎉 發布完成！版本: v{version}")
            print("=" * 60)
            
            print(f"\n發布資訊:")
            print(f"  版本: {version}")
            print(f"  建置編號: {self.version_info['build_number']}")
            print(f"  發布日期: {self.version_info['release_date']}")
            print(f"  平台: {platform_adapter.get_platform()}")
            
            if self.version_info.get("release_notes"):
                print(f"\n發布說明:")
                for note in self.version_info["release_notes"]:
                    print(f"  - {note['description']}")
            
            return True
            
        except Exception as e:
            print(f"建立發布時發生錯誤: {e}")
            return False


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="AI 智慧工作站發布管理工具")
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 版本命令
    version_parser = subparsers.add_parser('version', help='版本管理')
    version_parser.add_argument('--show', action='store_true', help='顯示當前版本')
    version_parser.add_argument('--set', help='設定版本號')
    version_parser.add_argument('--increment', choices=['major', 'minor', 'patch'], 
                               help='遞增版本號')
    
    # 發布說明命令
    notes_parser = subparsers.add_parser('notes', help='發布說明管理')
    notes_parser.add_argument('--add', help='添加發布說明')
    notes_parser.add_argument('--category', choices=['feature', 'improvement', 'bugfix', 'security', 'breaking'],
                             default='feature', help='發布說明類別')
    
    # 更新日誌命令
    changelog_parser = subparsers.add_parser('changelog', help='更新日誌管理')
    changelog_parser.add_argument('--generate', action='store_true', help='生成更新日誌')
    changelog_parser.add_argument('--update', action='store_true', help='更新更新日誌檔案')
    
    # 發布命令
    release_parser = subparsers.add_parser('release', help='建立發布')
    release_parser.add_argument('--increment', choices=['major', 'minor', 'patch'],
                               default='patch', help='版本遞增類型')
    release_parser.add_argument('--build-type', choices=['portable', 'pyinstaller', 'cx_freeze'],
                               default='portable', help='建置類型')
    release_parser.add_argument('--skip-tests', action='store_true', help='跳過測試')
    release_parser.add_argument('--skip-git', action='store_true', help='跳過 Git 操作')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # 建立發布管理器
    release_manager = ReleaseManager()
    
    try:
        if args.command == 'version':
            if args.show:
                print(f"當前版本: {release_manager.get_current_version()}")
                print(f"建置編號: {release_manager.version_info['build_number']}")
            elif args.set:
                release_manager.set_version(args.set)
                release_manager._save_version_info()
            elif args.increment:
                release_manager.increment_version(args.increment)
                release_manager._save_version_info()
        
        elif args.command == 'notes':
            if args.add:
                release_manager.add_release_note(args.add, args.category)
                release_manager._save_version_info()
        
        elif args.command == 'changelog':
            if args.generate:
                changelog = release_manager.generate_changelog()
                print(changelog)
            elif args.update:
                release_manager.update_changelog_file()
        
        elif args.command == 'release':
            success = release_manager.create_release(
                version_part=args.increment,
                build_type=args.build_type,
                skip_tests=args.skip_tests,
                skip_git=args.skip_git
            )
            return 0 if success else 1
        
        return 0
        
    except Exception as e:
        print(f"執行命令時發生錯誤: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())