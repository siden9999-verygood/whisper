#!/usr/bin/env python3
"""
自動化測試腳本
執行完整的測試套件並生成詳細報告
"""

import sys
import os
import subprocess
from pathlib import Path
import time
import json

# 添加專案根目錄到路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from platform_adapter import platform_adapter


def print_header(title):
    """列印標題"""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def print_section(title):
    """列印章節標題"""
    print(f"\n{'-' * 50}")
    print(f" {title}")
    print(f"{'-' * 50}")


def run_command(command, cwd=None):
    """執行命令並返回結果"""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            shell=False
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def check_dependencies():
    """檢查測試依賴"""
    print_section("檢查測試依賴")
    
    required_modules = [
        'unittest',
        'pathlib',
        'tempfile',
        'shutil',
        'json',
        'threading',
        'concurrent.futures'
    ]
    
    optional_modules = [
        'psutil',
        'pytest',
        'coverage'
    ]
    
    missing_required = []
    missing_optional = []
    
    # 檢查必要模組
    for module in required_modules:
        try:
            __import__(module)
            print(f"✓ {module}")
        except ImportError:
            missing_required.append(module)
            print(f"✗ {module} (必要)")
    
    # 檢查可選模組
    for module in optional_modules:
        try:
            __import__(module)
            print(f"✓ {module} (可選)")
        except ImportError:
            missing_optional.append(module)
            print(f"- {module} (可選，未安裝)")
    
    if missing_required:
        print(f"\n❌ 缺少必要模組: {', '.join(missing_required)}")
        return False
    
    if missing_optional:
        print(f"\n⚠️  缺少可選模組: {', '.join(missing_optional)}")
        print("   某些進階測試功能可能不可用")
    
    print("\n✅ 依賴檢查完成")
    return True


def run_unit_tests():
    """執行單元測試"""
    print_section("執行單元測試")
    
    test_command = [sys.executable, "tests/run_tests.py", "--verbose", "--save-report"]
    success, stdout, stderr = run_command(test_command, cwd=project_root)
    
    print(stdout)
    if stderr:
        print("錯誤輸出:")
        print(stderr)
    
    return success


def run_coverage_analysis():
    """執行覆蓋率分析"""
    print_section("執行覆蓋率分析")
    
    try:
        import coverage
        
        # 建立覆蓋率物件
        cov = coverage.Coverage()
        cov.start()
        
        # 執行測試
        test_command = [sys.executable, "tests/run_tests.py", "--quiet"]
        success, stdout, stderr = run_command(test_command, cwd=project_root)
        
        cov.stop()
        cov.save()
        
        # 生成報告
        print("覆蓋率報告:")
        cov.report()
        
        # 生成 HTML 報告
        html_dir = project_root / "htmlcov"
        cov.html_report(directory=str(html_dir))
        print(f"\nHTML 覆蓋率報告已生成: {html_dir}/index.html")
        
        return success
        
    except ImportError:
        print("coverage 模組未安裝，跳過覆蓋率分析")
        print("安裝方法: pip install coverage")
        return True


def run_performance_tests():
    """執行效能測試"""
    print_section("執行效能測試")
    
    test_command = [sys.executable, "-m", "unittest", "tests.test_performance", "-v"]
    success, stdout, stderr = run_command(test_command, cwd=project_root)
    
    print(stdout)
    if stderr:
        print("錯誤輸出:")
        print(stderr)
    
    return success


def run_cross_platform_tests():
    """執行跨平台測試"""
    print_section("執行跨平台測試")
    
    current_platform = platform_adapter.get_platform()
    print(f"當前平台: {current_platform}")
    
    test_command = [sys.executable, "-m", "unittest", "tests.test_cross_platform", "-v"]
    success, stdout, stderr = run_command(test_command, cwd=project_root)
    
    print(stdout)
    if stderr:
        print("錯誤輸出:")
        print(stderr)
    
    return success


def run_integration_tests():
    """執行整合測試"""
    print_section("執行整合測試")
    
    test_command = [sys.executable, "-m", "unittest", "tests.test_integration", "-v"]
    success, stdout, stderr = run_command(test_command, cwd=project_root)
    
    print(stdout)
    if stderr:
        print("錯誤輸出:")
        print(stderr)
    
    return success


def generate_test_report():
    """生成測試報告"""
    print_section("生成測試報告")
    
    report_data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "platform": platform_adapter.get_platform(),
        "system_info": platform_adapter.get_system_info(),
        "python_version": sys.version,
        "test_results": {}
    }
    
    # 讀取測試報告檔案
    test_report_file = project_root / "tests" / "test_report.txt"
    if test_report_file.exists():
        report_data["detailed_report"] = test_report_file.read_text(encoding='utf-8')
    
    # 儲存 JSON 報告
    json_report_file = project_root / "test_report.json"
    with open(json_report_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    print(f"詳細測試報告已儲存: {json_report_file}")
    
    return True


def cleanup_test_files():
    """清理測試檔案"""
    print_section("清理測試檔案")
    
    cleanup_patterns = [
        "test_output",
        "__pycache__",
        "*.pyc",
        ".coverage",
        "htmlcov"
    ]
    
    import glob
    import shutil
    
    for pattern in cleanup_patterns:
        matches = glob.glob(str(project_root / "**" / pattern), recursive=True)
        for match in matches:
            try:
                path = Path(match)
                if path.is_file():
                    path.unlink()
                    print(f"刪除檔案: {path}")
                elif path.is_dir():
                    shutil.rmtree(path)
                    print(f"刪除目錄: {path}")
            except Exception as e:
                print(f"清理 {match} 時發生錯誤: {e}")
    
    print("清理完成")
    return True


def main():
    """主函數"""
    print_header("AI 智慧工作站 - 自動化測試套件")
    
    start_time = time.time()
    
    # 測試步驟
    test_steps = [
        ("檢查測試依賴", check_dependencies),
        ("執行單元測試", run_unit_tests),
        ("執行跨平台測試", run_cross_platform_tests),
        ("執行效能測試", run_performance_tests),
        ("執行整合測試", run_integration_tests),
        ("執行覆蓋率分析", run_coverage_analysis),
        ("生成測試報告", generate_test_report),
    ]
    
    results = {}
    
    # 執行測試步驟
    for step_name, step_func in test_steps:
        print(f"\n🔄 {step_name}...")
        try:
            success = step_func()
            results[step_name] = success
            
            if success:
                print(f"✅ {step_name} 完成")
            else:
                print(f"❌ {step_name} 失敗")
                
        except Exception as e:
            print(f"❌ {step_name} 發生錯誤: {e}")
            results[step_name] = False
    
    # 總結
    end_time = time.time()
    total_time = end_time - start_time
    
    print_header("測試總結")
    
    passed_steps = sum(1 for success in results.values() if success)
    total_steps = len(results)
    
    print(f"執行時間: {total_time:.2f} 秒")
    print(f"測試步驟: {passed_steps}/{total_steps} 通過")
    
    print("\n詳細結果:")
    for step_name, success in results.items():
        status = "✅ 通過" if success else "❌ 失敗"
        print(f"  {step_name}: {status}")
    
    # 清理選項
    if "--cleanup" in sys.argv:
        cleanup_test_files()
    
    # 返回適當的退出碼
    if all(results.values()):
        print("\n🎉 所有測試步驟都成功完成！")
        return 0
    else:
        print(f"\n⚠️  有 {total_steps - passed_steps} 個測試步驟失敗")
        return 1


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  測試被使用者中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 執行測試時發生未預期的錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)