"""
測試運行器
執行所有測試並生成報告
"""

import unittest
import sys
import os
from pathlib import Path
import time
from io import StringIO

# 添加專案根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestResult:
    """測試結果類別"""
    
    def __init__(self):
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.error_tests = 0
        self.skipped_tests = 0
        self.start_time = None
        self.end_time = None
        self.failures = []
        self.errors = []
        self.skipped = []
    
    def add_result(self, result):
        """添加測試結果"""
        self.total_tests += result.testsRun
        self.failed_tests += len(result.failures)
        self.error_tests += len(result.errors)
        self.skipped_tests += len(result.skipped) if hasattr(result, 'skipped') else 0
        self.passed_tests = self.total_tests - self.failed_tests - self.error_tests - self.skipped_tests
        
        self.failures.extend(result.failures)
        self.errors.extend(result.errors)
        if hasattr(result, 'skipped'):
            self.skipped.extend(result.skipped)
    
    def get_duration(self):
        """取得測試執行時間"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0
    
    def get_success_rate(self):
        """取得成功率"""
        if self.total_tests == 0:
            return 0
        return (self.passed_tests / self.total_tests) * 100


class TestRunner:
    """測試運行器"""
    
    def __init__(self):
        self.test_modules = [
            'test_platform_adapter',
            'test_config_service',
            'test_logging_service',
            'test_cross_platform',
            'test_performance',
            'test_integration'
        ]
        self.result = TestResult()
    
    def discover_tests(self):
        """發現測試"""
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        for module_name in self.test_modules:
            try:
                module = __import__(module_name)
                module_suite = loader.loadTestsFromModule(module)
                suite.addTest(module_suite)
                print(f"✓ 載入測試模組: {module_name}")
            except ImportError as e:
                print(f"✗ 無法載入測試模組 {module_name}: {e}")
            except Exception as e:
                print(f"✗ 載入測試模組 {module_name} 時發生錯誤: {e}")
        
        return suite
    
    def run_tests(self, verbosity=2):
        """執行測試"""
        print("=" * 70)
        print("AI 智慧工作站 - 測試套件")
        print("=" * 70)
        
        # 發現測試
        suite = self.discover_tests()
        
        if suite.countTestCases() == 0:
            print("沒有找到任何測試")
            return self.result
        
        print(f"找到 {suite.countTestCases()} 個測試")
        print("-" * 70)
        
        # 執行測試
        self.result.start_time = time.time()
        
        # 建立測試運行器
        stream = StringIO()
        runner = unittest.TextTestRunner(
            stream=stream,
            verbosity=verbosity,
            buffer=True
        )
        
        # 執行每個測試模組
        for module_name in self.test_modules:
            print(f"\n執行 {module_name} 測試...")
            
            try:
                module = __import__(module_name)
                loader = unittest.TestLoader()
                module_suite = loader.loadTestsFromModule(module)
                
                if module_suite.countTestCases() > 0:
                    module_result = runner.run(module_suite)
                    self.result.add_result(module_result)
                    
                    # 顯示模組測試結果
                    passed = module_result.testsRun - len(module_result.failures) - len(module_result.errors)
                    print(f"  測試: {module_result.testsRun}, 通過: {passed}, 失敗: {len(module_result.failures)}, 錯誤: {len(module_result.errors)}")
                else:
                    print(f"  沒有找到測試")
                    
            except Exception as e:
                print(f"  執行測試時發生錯誤: {e}")
        
        self.result.end_time = time.time()
        
        return self.result
    
    def generate_report(self):
        """生成測試報告"""
        print("\n" + "=" * 70)
        print("測試報告")
        print("=" * 70)
        
        # 基本統計
        print(f"總測試數量: {self.result.total_tests}")
        print(f"通過: {self.result.passed_tests}")
        print(f"失敗: {self.result.failed_tests}")
        print(f"錯誤: {self.result.error_tests}")
        print(f"跳過: {self.result.skipped_tests}")
        print(f"成功率: {self.result.get_success_rate():.1f}%")
        print(f"執行時間: {self.result.get_duration():.2f} 秒")
        
        # 失敗詳情
        if self.result.failures:
            print(f"\n失敗詳情 ({len(self.result.failures)} 個):")
            print("-" * 50)
            for i, (test, traceback) in enumerate(self.result.failures, 1):
                print(f"{i}. {test}")
                print(f"   {traceback.strip()}")
                print()
        
        # 錯誤詳情
        if self.result.errors:
            print(f"\n錯誤詳情 ({len(self.result.errors)} 個):")
            print("-" * 50)
            for i, (test, traceback) in enumerate(self.result.errors, 1):
                print(f"{i}. {test}")
                print(f"   {traceback.strip()}")
                print()
        
        # 跳過詳情
        if self.result.skipped:
            print(f"\n跳過詳情 ({len(self.result.skipped)} 個):")
            print("-" * 50)
            for i, (test, reason) in enumerate(self.result.skipped, 1):
                print(f"{i}. {test}")
                print(f"   原因: {reason}")
                print()
        
        # 總結
        print("=" * 70)
        if self.result.failed_tests == 0 and self.result.error_tests == 0:
            print("🎉 所有測試通過！")
        else:
            print(f"⚠️  有 {self.result.failed_tests + self.result.error_tests} 個測試未通過")
        
        return self.result.failed_tests == 0 and self.result.error_tests == 0
    
    def save_report(self, filename="test_report.txt"):
        """儲存測試報告到檔案"""
        try:
            report_path = Path(__file__).parent / filename
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("AI 智慧工作站 - 測試報告\n")
                f.write("=" * 50 + "\n")
                f.write(f"生成時間: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                f.write("測試統計:\n")
                f.write(f"  總測試數量: {self.result.total_tests}\n")
                f.write(f"  通過: {self.result.passed_tests}\n")
                f.write(f"  失敗: {self.result.failed_tests}\n")
                f.write(f"  錯誤: {self.result.error_tests}\n")
                f.write(f"  跳過: {self.result.skipped_tests}\n")
                f.write(f"  成功率: {self.result.get_success_rate():.1f}%\n")
                f.write(f"  執行時間: {self.result.get_duration():.2f} 秒\n\n")
                
                if self.result.failures:
                    f.write("失敗詳情:\n")
                    for i, (test, traceback) in enumerate(self.result.failures, 1):
                        f.write(f"{i}. {test}\n")
                        f.write(f"   {traceback.strip()}\n\n")
                
                if self.result.errors:
                    f.write("錯誤詳情:\n")
                    for i, (test, traceback) in enumerate(self.result.errors, 1):
                        f.write(f"{i}. {test}\n")
                        f.write(f"   {traceback.strip()}\n\n")
            
            print(f"\n測試報告已儲存到: {report_path}")
            
        except Exception as e:
            print(f"儲存測試報告失敗: {e}")


def main():
    """主函數"""
    # 檢查命令列參數
    verbosity = 2
    save_report = False
    
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg == '--quiet' or arg == '-q':
                verbosity = 1
            elif arg == '--verbose' or arg == '-v':
                verbosity = 2
            elif arg == '--save-report' or arg == '-s':
                save_report = True
            elif arg == '--help' or arg == '-h':
                print("使用方法: python run_tests.py [選項]")
                print("選項:")
                print("  -q, --quiet      安靜模式")
                print("  -v, --verbose    詳細模式")
                print("  -s, --save-report 儲存測試報告")
                print("  -h, --help       顯示幫助")
                return 0
    
    # 建立測試運行器
    runner = TestRunner()
    
    try:
        # 執行測試
        result = runner.run_tests(verbosity=verbosity)
        
        # 生成報告
        success = runner.generate_report()
        
        # 儲存報告（如果需要）
        if save_report:
            runner.save_report()
        
        # 返回適當的退出碼
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n測試被使用者中斷")
        return 1
    except Exception as e:
        print(f"執行測試時發生未預期的錯誤: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())