"""
診斷管理器模組
提供系統診斷、問題報告和效能分析功能
"""

import os
import sys
import json
import zipfile
import platform
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import traceback

from platform_adapter import platform_adapter, CrossPlatformError
from config_service import config_service
from logging_service import logging_service


@dataclass
class DiagnosticInfo:
    """診斷資訊"""
    timestamp: str
    system_info: Dict[str, Any]
    config_info: Dict[str, Any]
    performance_info: Dict[str, Any]
    error_logs: List[str]
    recent_activities: List[str]
    dependency_status: Dict[str, bool]
    file_system_info: Dict[str, Any]


@dataclass
class PerformanceMetrics:
    """效能指標"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    process_count: int
    startup_time: Optional[float] = None
    last_operation_time: Optional[float] = None


class DiagnosticsManager:
    """診斷管理器"""
    
    def __init__(self):
        self.config = config_service.get_config()
        self.logger = logging_service.get_logger("DiagnosticsManager")
        self.startup_time = datetime.now()
        
        # 診斷資料儲存路徑
        self.diagnostics_dir = platform_adapter.get_config_dir() / "diagnostics"
        self.diagnostics_dir.mkdir(exist_ok=True)
        
        # 效能歷史記錄
        self.performance_history: List[PerformanceMetrics] = []
        self.max_history_size = 1000
    
    def run_full_diagnostics(self) -> DiagnosticInfo:
        """執行完整系統診斷"""
        self.logger.info("開始執行完整系統診斷")
        
        try:
            diagnostic_info = DiagnosticInfo(
                timestamp=datetime.now().isoformat(),
                system_info=self._collect_system_info(),
                config_info=self._collect_config_info(),
                performance_info=self._collect_performance_info(),
                error_logs=self._collect_error_logs(),
                recent_activities=self._collect_recent_activities(),
                dependency_status=self._check_dependencies(),
                file_system_info=self._collect_file_system_info()
            )
            
            self.logger.info("系統診斷完成")
            return diagnostic_info
            
        except Exception as e:
            self.logger.error(f"執行系統診斷時發生錯誤: {str(e)}")
            raise DiagnosticsError(f"診斷失敗: {str(e)}") from e
    
    def _collect_system_info(self) -> Dict[str, Any]:
        """收集系統資訊"""
        try:
            import psutil
            
            system_info = platform_adapter.get_system_info()
            
            # 添加更詳細的系統資訊
            system_info.update({
                "python_executable": sys.executable,
                "python_path": sys.path,
                "environment_variables": dict(os.environ),
                "current_working_directory": os.getcwd(),
                "total_memory": psutil.virtual_memory().total,
                "available_memory": psutil.virtual_memory().available,
                "cpu_count": psutil.cpu_count(),
                "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
                "uptime_seconds": (datetime.now() - datetime.fromtimestamp(psutil.boot_time())).total_seconds()
            })
            
            return system_info
            
        except Exception as e:
            self.logger.error(f"收集系統資訊時發生錯誤: {str(e)}")
            return {"error": str(e)}
    
    def _collect_config_info(self) -> Dict[str, Any]:
        """收集配置資訊"""
        try:
            config = self.config
            
            # 隱藏敏感資訊
            config_info = {
                "ai_model": config.ai_model,
                "default_language": config.default_language,
                "default_threads": config.default_threads,
                "window_size": f"{config.window_width}x{config.window_height}",
                "theme": config.theme,
                "search_history_limit": config.search_history_limit,
                "results_per_page": config.results_per_page,
                "max_concurrent_downloads": config.max_concurrent_downloads,
                "api_key_configured": bool(config.api_key and config.api_key != ""),
                "source_folder_configured": bool(config.source_folder),
                "processed_folder_configured": bool(config.processed_folder),
                "output_formats": {
                    "srt": config.output_srt,
                    "txt": config.output_txt,
                    "vtt": config.output_vtt,
                    "lrc": config.output_lrc,
                    "csv": config.output_csv
                },
                "post_processing": {
                    "segmentation": config.enable_segmentation,
                    "remove_punctuation": config.remove_punctuation,
                    "traditional_chinese": config.convert_to_traditional_chinese,
                    "translate_english": config.translate_to_english
                }
            }
            
            # 路徑驗證結果
            config_info["path_validation"] = config_service.validate_paths()
            
            return config_info
            
        except Exception as e:
            self.logger.error(f"收集配置資訊時發生錯誤: {str(e)}")
            return {"error": str(e)}
    
    def _collect_performance_info(self) -> Dict[str, Any]:
        """收集效能資訊"""
        try:
            import psutil
            
            # 當前效能指標
            current_metrics = PerformanceMetrics(
                cpu_usage=psutil.cpu_percent(interval=1),
                memory_usage=psutil.virtual_memory().percent,
                disk_usage=psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent,
                process_count=len(psutil.pids()),
                startup_time=(datetime.now() - self.startup_time).total_seconds()
            )
            
            # 添加到歷史記錄
            self.performance_history.append(current_metrics)
            if len(self.performance_history) > self.max_history_size:
                self.performance_history = self.performance_history[-self.max_history_size:]
            
            # 計算統計資料
            if len(self.performance_history) > 1:
                recent_metrics = self.performance_history[-60:]  # 最近60個記錄
                avg_cpu = sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics)
                avg_memory = sum(m.memory_usage for m in recent_metrics) / len(recent_metrics)
                max_cpu = max(m.cpu_usage for m in recent_metrics)
                max_memory = max(m.memory_usage for m in recent_metrics)
            else:
                avg_cpu = avg_memory = max_cpu = max_memory = current_metrics.cpu_usage
            
            performance_info = {
                "current": asdict(current_metrics),
                "averages": {
                    "cpu_usage": avg_cpu,
                    "memory_usage": avg_memory
                },
                "peaks": {
                    "max_cpu_usage": max_cpu,
                    "max_memory_usage": max_memory
                },
                "history_size": len(self.performance_history),
                "recommendations": self._generate_performance_recommendations(current_metrics)
            }
            
            return performance_info
            
        except Exception as e:
            self.logger.error(f"收集效能資訊時發生錯誤: {str(e)}")
            return {"error": str(e)}
    
    def _collect_error_logs(self) -> List[str]:
        """收集錯誤日誌"""
        try:
            error_logs = []
            
            # 讀取錯誤日誌檔案
            error_log_path = logging_service.log_dir / "error.log"
            if error_log_path.exists():
                with open(error_log_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # 取得最近100行錯誤日誌
                    error_logs = lines[-100:] if len(lines) > 100 else lines
            
            return [line.strip() for line in error_logs if line.strip()]
            
        except Exception as e:
            self.logger.error(f"收集錯誤日誌時發生錯誤: {str(e)}")
            return [f"收集錯誤日誌失敗: {str(e)}"]
    
    def _collect_recent_activities(self) -> List[str]:
        """收集最近活動記錄"""
        try:
            activities = []
            
            # 讀取主要日誌檔案
            main_log_path = logging_service.log_dir / "app.log"
            if main_log_path.exists():
                with open(main_log_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # 取得最近50行活動記錄
                    activities = lines[-50:] if len(lines) > 50 else lines
            
            return [line.strip() for line in activities if line.strip()]
            
        except Exception as e:
            self.logger.error(f"收集活動記錄時發生錯誤: {str(e)}")
            return [f"收集活動記錄失敗: {str(e)}"]
    
    def _check_dependencies(self) -> Dict[str, bool]:
        """檢查依賴項狀態"""
        dependencies = {}
        
        # Python 套件檢查
        required_packages = [
            'google.generativeai',
            'pandas',
            'PIL',
            'srt',
            'opencc',
            'psutil',
            'watchdog'
        ]
        
        for package in required_packages:
            try:
                __import__(package)
                dependencies[package] = True
            except ImportError:
                dependencies[package] = False
        
        # 系統檔案檢查
        path_validation = config_service.validate_paths()
        dependencies.update(path_validation)
        
        return dependencies
    
    def _collect_file_system_info(self) -> Dict[str, Any]:
        """收集檔案系統資訊"""
        try:
            import psutil
            
            file_system_info = {}
            
            # 磁碟使用情況
            disk_usage = {}
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_usage[partition.device] = {
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free,
                        "percent": (usage.used / usage.total) * 100,
                        "filesystem": partition.fstype
                    }
                except PermissionError:
                    continue
            
            file_system_info["disk_usage"] = disk_usage
            
            # 重要目錄資訊
            important_dirs = {
                "config_dir": platform_adapter.get_config_dir(),
                "temp_dir": platform_adapter.get_temp_dir(),
                "whisper_resources": config_service.get_whisper_resources_path(),
                "log_dir": logging_service.log_dir
            }
            
            dir_info = {}
            for name, path in important_dirs.items():
                try:
                    if path.exists():
                        # 計算目錄大小
                        total_size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
                        file_count = len([f for f in path.rglob('*') if f.is_file()])
                        
                        dir_info[name] = {
                            "path": str(path),
                            "exists": True,
                            "size_bytes": total_size,
                            "file_count": file_count,
                            "readable": os.access(path, os.R_OK),
                            "writable": os.access(path, os.W_OK)
                        }
                    else:
                        dir_info[name] = {
                            "path": str(path),
                            "exists": False
                        }
                except Exception as e:
                    dir_info[name] = {
                        "path": str(path),
                        "error": str(e)
                    }
            
            file_system_info["directories"] = dir_info
            
            return file_system_info
            
        except Exception as e:
            self.logger.error(f"收集檔案系統資訊時發生錯誤: {str(e)}")
            return {"error": str(e)}
    
    def _generate_performance_recommendations(self, metrics: PerformanceMetrics) -> List[str]:
        """生成效能建議"""
        recommendations = []
        
        if metrics.cpu_usage > 80:
            recommendations.append("CPU 使用率過高，建議關閉其他不必要的程式")
        
        if metrics.memory_usage > 85:
            recommendations.append("記憶體使用率過高，建議重啟程式或增加系統記憶體")
        
        if metrics.disk_usage > 90:
            recommendations.append("磁碟空間不足，建議清理不需要的檔案")
        
        if metrics.process_count > 200:
            recommendations.append("系統程序數量過多，可能影響效能")
        
        if metrics.startup_time and metrics.startup_time > 30:
            recommendations.append("程式啟動時間過長，建議檢查系統效能")
        
        if not recommendations:
            recommendations.append("系統效能良好，無需特別調整")
        
        return recommendations
    
    def generate_diagnostic_report(self, diagnostic_info: DiagnosticInfo) -> str:
        """生成診斷報告"""
        report_lines = []
        
        # 報告標題
        report_lines.append("=" * 60)
        report_lines.append("AI 智慧工作站 - 系統診斷報告")
        report_lines.append("=" * 60)
        report_lines.append(f"生成時間: {diagnostic_info.timestamp}")
        report_lines.append("")
        
        # 系統資訊
        report_lines.append("【系統資訊】")
        system_info = diagnostic_info.system_info
        if "error" not in system_info:
            report_lines.append(f"作業系統: {system_info.get('system', 'Unknown')} {system_info.get('release', '')}")
            report_lines.append(f"處理器: {system_info.get('processor', 'Unknown')}")
            report_lines.append(f"Python 版本: {system_info.get('python_version', 'Unknown')}")
            report_lines.append(f"總記憶體: {system_info.get('total_memory', 0) // (1024**3)} GB")
            report_lines.append(f"CPU 核心數: {system_info.get('cpu_count', 'Unknown')}")
        else:
            report_lines.append(f"系統資訊收集失敗: {system_info['error']}")
        report_lines.append("")
        
        # 效能資訊
        report_lines.append("【效能狀態】")
        perf_info = diagnostic_info.performance_info
        if "error" not in perf_info:
            current = perf_info.get("current", {})
            report_lines.append(f"CPU 使用率: {current.get('cpu_usage', 0):.1f}%")
            report_lines.append(f"記憶體使用率: {current.get('memory_usage', 0):.1f}%")
            report_lines.append(f"磁碟使用率: {current.get('disk_usage', 0):.1f}%")
            report_lines.append(f"程序數量: {current.get('process_count', 0)}")
            
            # 效能建議
            recommendations = perf_info.get("recommendations", [])
            if recommendations:
                report_lines.append("效能建議:")
                for rec in recommendations:
                    report_lines.append(f"  - {rec}")
        else:
            report_lines.append(f"效能資訊收集失敗: {perf_info['error']}")
        report_lines.append("")
        
        # 依賴項狀態
        report_lines.append("【依賴項檢查】")
        deps = diagnostic_info.dependency_status
        for dep_name, status in deps.items():
            status_text = "✓ 正常" if status else "✗ 缺失"
            report_lines.append(f"{dep_name}: {status_text}")
        report_lines.append("")
        
        # 配置狀態
        report_lines.append("【配置狀態】")
        config_info = diagnostic_info.config_info
        if "error" not in config_info:
            report_lines.append(f"AI 模型: {config_info.get('ai_model', 'Unknown')}")
            report_lines.append(f"預設語言: {config_info.get('default_language', 'Unknown')}")
            report_lines.append(f"API 金鑰: {'已配置' if config_info.get('api_key_configured') else '未配置'}")
            
            path_validation = config_info.get('path_validation', {})
            report_lines.append("重要路徑檢查:")
            for path_name, exists in path_validation.items():
                status_text = "✓ 存在" if exists else "✗ 不存在"
                report_lines.append(f"  {path_name}: {status_text}")
        else:
            report_lines.append(f"配置資訊收集失敗: {config_info['error']}")
        report_lines.append("")
        
        # 最近錯誤
        if diagnostic_info.error_logs:
            report_lines.append("【最近錯誤】")
            recent_errors = diagnostic_info.error_logs[-10:]  # 最近10個錯誤
            for error in recent_errors:
                report_lines.append(f"  {error}")
            report_lines.append("")
        
        # 檔案系統狀態
        report_lines.append("【檔案系統狀態】")
        fs_info = diagnostic_info.file_system_info
        if "error" not in fs_info:
            directories = fs_info.get("directories", {})
            for dir_name, dir_info in directories.items():
                if "error" in dir_info:
                    report_lines.append(f"{dir_name}: 錯誤 - {dir_info['error']}")
                elif dir_info.get("exists"):
                    size_mb = dir_info.get("size_bytes", 0) / (1024 * 1024)
                    report_lines.append(f"{dir_name}: {size_mb:.1f} MB, {dir_info.get('file_count', 0)} 個檔案")
                else:
                    report_lines.append(f"{dir_name}: 不存在")
        else:
            report_lines.append(f"檔案系統資訊收集失敗: {fs_info['error']}")
        
        report_lines.append("")
        report_lines.append("=" * 60)
        report_lines.append("報告結束")
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)
    
    def export_diagnostic_package(self, diagnostic_info: DiagnosticInfo) -> str:
        """匯出診斷套件"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            package_name = f"diagnostic_package_{timestamp}.zip"
            package_path = self.diagnostics_dir / package_name
            
            with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 添加診斷報告
                report_content = self.generate_diagnostic_report(diagnostic_info)
                zipf.writestr("diagnostic_report.txt", report_content)
                
                # 添加原始診斷資料
                diagnostic_json = json.dumps(asdict(diagnostic_info), indent=2, ensure_ascii=False)
                zipf.writestr("diagnostic_data.json", diagnostic_json)
                
                # 添加日誌檔案
                log_files = logging_service.get_log_files()
                for log_file in log_files:
                    if log_file.exists() and log_file.stat().st_size < 10 * 1024 * 1024:  # 小於10MB
                        zipf.write(log_file, f"logs/{log_file.name}")
                
                # 添加配置檔案
                config_file = config_service.config_file
                if config_file.exists():
                    zipf.write(config_file, "config.json")
            
            self.logger.info(f"診斷套件已匯出: {package_path}")
            return str(package_path)
            
        except Exception as e:
            self.logger.error(f"匯出診斷套件時發生錯誤: {str(e)}")
            raise DiagnosticsError(f"匯出診斷套件失敗: {str(e)}") from e
    
    def quick_health_check(self) -> Dict[str, Any]:
        """快速健康檢查"""
        try:
            health_status = {
                "overall_status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "checks": {}
            }
            
            issues = []
            
            # 檢查依賴項
            deps = self._check_dependencies()
            missing_deps = [name for name, status in deps.items() if not status]
            if missing_deps:
                issues.append(f"缺少依賴項: {', '.join(missing_deps)}")
                health_status["checks"]["dependencies"] = "warning"
            else:
                health_status["checks"]["dependencies"] = "ok"
            
            # 檢查效能
            import psutil
            cpu_usage = psutil.cpu_percent(interval=1)
            memory_usage = psutil.virtual_memory().percent
            
            if cpu_usage > 90:
                issues.append(f"CPU 使用率過高: {cpu_usage:.1f}%")
                health_status["checks"]["performance"] = "critical"
            elif cpu_usage > 70:
                health_status["checks"]["performance"] = "warning"
            else:
                health_status["checks"]["performance"] = "ok"
            
            if memory_usage > 90:
                issues.append(f"記憶體使用率過高: {memory_usage:.1f}%")
                health_status["checks"]["memory"] = "critical"
            elif memory_usage > 80:
                health_status["checks"]["memory"] = "warning"
            else:
                health_status["checks"]["memory"] = "ok"
            
            # 檢查磁碟空間
            disk_usage = psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent
            if disk_usage > 95:
                issues.append(f"磁碟空間不足: {disk_usage:.1f}%")
                health_status["checks"]["disk"] = "critical"
            elif disk_usage > 85:
                health_status["checks"]["disk"] = "warning"
            else:
                health_status["checks"]["disk"] = "ok"
            
            # 檢查日誌錯誤
            error_logs = self._collect_error_logs()
            recent_errors = [log for log in error_logs if "ERROR" in log or "CRITICAL" in log]
            if len(recent_errors) > 10:
                issues.append(f"最近錯誤過多: {len(recent_errors)} 個")
                health_status["checks"]["errors"] = "warning"
            else:
                health_status["checks"]["errors"] = "ok"
            
            # 設定整體狀態
            if any(status == "critical" for status in health_status["checks"].values()):
                health_status["overall_status"] = "critical"
            elif any(status == "warning" for status in health_status["checks"].values()):
                health_status["overall_status"] = "warning"
            
            health_status["issues"] = issues
            health_status["metrics"] = {
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "disk_usage": disk_usage,
                "error_count": len(recent_errors)
            }
            
            return health_status
            
        except Exception as e:
            self.logger.error(f"快速健康檢查時發生錯誤: {str(e)}")
            return {
                "overall_status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }


# 自定義例外類別
class DiagnosticsError(CrossPlatformError):
    """診斷相關錯誤"""
    pass


# 全域診斷管理器實例
diagnostics_manager = DiagnosticsManager()


if __name__ == "__main__":
    # 測試程式
    print("=== 診斷管理器測試 ===")
    
    # 快速健康檢查
    health = diagnostics_manager.quick_health_check()
    print(f"整體狀態: {health['overall_status']}")
    print(f"檢查結果: {health['checks']}")
    
    if health.get('issues'):
        print("發現問題:")
        for issue in health['issues']:
            print(f"  - {issue}")
    
    # 完整診斷（可選）
    try:
        print("\n執行完整診斷...")
        diagnostic_info = diagnostics_manager.run_full_diagnostics()
        report = diagnostics_manager.generate_diagnostic_report(diagnostic_info)
        print("診斷報告已生成")
        print(f"報告長度: {len(report)} 字元")
    except Exception as e:
        print(f"完整診斷失敗: {e}")