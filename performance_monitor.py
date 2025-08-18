"""
效能監控系統模組
提供系統資源監控、效能最佳化建議和自動調整功能
"""

import time
import threading
import psutil
import gc
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque
import json

from platform_adapter import platform_adapter
from config_service import config_service
from logging_service import logging_service, TaskLogger


class PerformanceLevel(Enum):
    """效能等級"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


class ResourceType(Enum):
    """資源類型"""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    PROCESS = "process"


@dataclass
class PerformanceMetric:
    """效能指標"""
    timestamp: datetime
    resource_type: ResourceType
    value: float
    unit: str
    threshold_warning: float = 80.0
    threshold_critical: float = 95.0
    
    @property
    def level(self) -> PerformanceLevel:
        """取得效能等級"""
        if self.value >= self.threshold_critical:
            return PerformanceLevel.CRITICAL
        elif self.value >= self.threshold_warning:
            return PerformanceLevel.POOR
        elif self.value >= 60:
            return PerformanceLevel.FAIR
        elif self.value >= 30:
            return PerformanceLevel.GOOD
        else:
            return PerformanceLevel.EXCELLENT


@dataclass
class PerformanceAlert:
    """效能警告"""
    timestamp: datetime
    resource_type: ResourceType
    level: PerformanceLevel
    message: str
    value: float
    threshold: float
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class OptimizationSuggestion:
    """最佳化建議"""
    category: str
    priority: int  # 1-5, 1 是最高優先級
    title: str
    description: str
    action: str
    estimated_impact: str
    auto_applicable: bool = False
    applied: bool = False
    applied_at: Optional[datetime] = None


@dataclass
class PerformanceReport:
    """效能報告"""
    report_id: str
    start_time: datetime
    end_time: datetime
    overall_score: float
    metrics_summary: Dict[ResourceType, Dict[str, float]]
    alerts: List[PerformanceAlert]
    suggestions: List[OptimizationSuggestion]
    trends: Dict[str, Any]


class PerformanceMonitor:
    """效能監控器"""
    
    def __init__(self):
        self.config = config_service.get_config()
        self.logger = logging_service.get_logger("PerformanceMonitor")
        
        # 監控狀態
        self.is_monitoring = False
        self.monitoring_thread = None
        self.collection_interval = 5.0  # 5秒收集一次
        
        # 資料儲存
        self.metrics_history: Dict[ResourceType, deque] = {
            ResourceType.CPU: deque(maxlen=1440),      # 2小時資料
            ResourceType.MEMORY: deque(maxlen=1440),
            ResourceType.DISK: deque(maxlen=1440),
            ResourceType.NETWORK: deque(maxlen=1440),
            ResourceType.PROCESS: deque(maxlen=1440)
        }
        
        self.alerts: List[PerformanceAlert] = []
        self.suggestions: List[OptimizationSuggestion] = []
        self.reports: List[PerformanceReport] = []
        
        # 閾值設定
        self.thresholds = {
            ResourceType.CPU: {'warning': 80.0, 'critical': 95.0},
            ResourceType.MEMORY: {'warning': 85.0, 'critical': 95.0},
            ResourceType.DISK: {'warning': 90.0, 'critical': 98.0},
            ResourceType.NETWORK: {'warning': 80.0, 'critical': 95.0},
            ResourceType.PROCESS: {'warning': 100, 'critical': 200}
        }
        
        # 自動優化設定
        self.auto_optimization_enabled = True
        self.optimization_callbacks: Dict[str, Callable] = {}
        
        # 基準效能資料
        self.baseline_metrics: Dict[ResourceType, float] = {}
        self._establish_baseline()
    
    def start_monitoring(self) -> bool:
        """開始效能監控"""
        if self.is_monitoring:
            self.logger.warning("效能監控已在運行中")
            return True
        
        try:
            self.is_monitoring = True
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True
            )
            self.monitoring_thread.start()
            
            self.logger.info("效能監控已啟動")
            return True
            
        except Exception as e:
            self.is_monitoring = False
            self.logger.error(f"啟動效能監控失敗: {str(e)}")
            return False
    
    def stop_monitoring(self) -> bool:
        """停止效能監控"""
        if not self.is_monitoring:
            return True
        
        try:
            self.is_monitoring = False
            if self.monitoring_thread:
                self.monitoring_thread.join(timeout=5)
            
            self.logger.info("效能監控已停止")
            return True
            
        except Exception as e:
            self.logger.error(f"停止效能監控失敗: {str(e)}")
            return False
    
    def _monitoring_loop(self):
        """監控循環"""
        while self.is_monitoring:
            try:
                # 收集效能指標
                metrics = self._collect_metrics()
                
                # 儲存指標
                for metric in metrics:
                    self.metrics_history[metric.resource_type].append(metric)
                
                # 檢查警告
                self._check_alerts(metrics)
                
                # 生成最佳化建議
                self._generate_suggestions(metrics)
                
                # 自動優化
                if self.auto_optimization_enabled:
                    self._apply_auto_optimizations()
                
                time.sleep(self.collection_interval)
                
            except Exception as e:
                self.logger.error(f"效能監控循環錯誤: {str(e)}")
                time.sleep(self.collection_interval)
    
    def _collect_metrics(self) -> List[PerformanceMetric]:
        """收集效能指標"""
        metrics = []
        timestamp = datetime.now()
        
        try:
            # CPU 使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics.append(PerformanceMetric(
                timestamp=timestamp,
                resource_type=ResourceType.CPU,
                value=cpu_percent,
                unit="%",
                threshold_warning=self.thresholds[ResourceType.CPU]['warning'],
                threshold_critical=self.thresholds[ResourceType.CPU]['critical']
            ))
            
            # 記憶體使用率
            memory = psutil.virtual_memory()
            metrics.append(PerformanceMetric(
                timestamp=timestamp,
                resource_type=ResourceType.MEMORY,
                value=memory.percent,
                unit="%",
                threshold_warning=self.thresholds[ResourceType.MEMORY]['warning'],
                threshold_critical=self.thresholds[ResourceType.MEMORY]['critical']
            ))
            
            # 磁碟使用率
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            metrics.append(PerformanceMetric(
                timestamp=timestamp,
                resource_type=ResourceType.DISK,
                value=disk_percent,
                unit="%",
                threshold_warning=self.thresholds[ResourceType.DISK]['warning'],
                threshold_critical=self.thresholds[ResourceType.DISK]['critical']
            ))
            
            # 網路 I/O（簡化為總位元組數變化率）
            try:
                net_io = psutil.net_io_counters()
                if hasattr(self, '_last_net_io'):
                    bytes_sent_rate = (net_io.bytes_sent - self._last_net_io.bytes_sent) / self.collection_interval
                    bytes_recv_rate = (net_io.bytes_recv - self._last_net_io.bytes_recv) / self.collection_interval
                    total_rate = (bytes_sent_rate + bytes_recv_rate) / (1024 * 1024)  # MB/s
                    
                    metrics.append(PerformanceMetric(
                        timestamp=timestamp,
                        resource_type=ResourceType.NETWORK,
                        value=total_rate,
                        unit="MB/s",
                        threshold_warning=50.0,  # 50 MB/s
                        threshold_critical=100.0  # 100 MB/s
                    ))
                
                self._last_net_io = net_io
            except:
                pass
            
            # 程序數量
            process_count = len(psutil.pids())
            metrics.append(PerformanceMetric(
                timestamp=timestamp,
                resource_type=ResourceType.PROCESS,
                value=process_count,
                unit="count",
                threshold_warning=self.thresholds[ResourceType.PROCESS]['warning'],
                threshold_critical=self.thresholds[ResourceType.PROCESS]['critical']
            ))
            
        except Exception as e:
            self.logger.error(f"收集效能指標失敗: {str(e)}")
        
        return metrics
    
    def _check_alerts(self, metrics: List[PerformanceMetric]):
        """檢查效能警告"""
        for metric in metrics:
            # 檢查是否需要發出警告
            if metric.level in [PerformanceLevel.POOR, PerformanceLevel.CRITICAL]:
                # 檢查是否已有相同的未解決警告
                existing_alert = None
                for alert in self.alerts:
                    if (alert.resource_type == metric.resource_type and 
                        not alert.resolved and
                        alert.level == metric.level):
                        existing_alert = alert
                        break
                
                if not existing_alert:
                    # 創建新警告
                    alert = PerformanceAlert(
                        timestamp=metric.timestamp,
                        resource_type=metric.resource_type,
                        level=metric.level,
                        message=self._generate_alert_message(metric),
                        value=metric.value,
                        threshold=metric.threshold_warning if metric.level == PerformanceLevel.POOR else metric.threshold_critical
                    )
                    self.alerts.append(alert)
                    self.logger.warning(f"效能警告: {alert.message}")
            
            # 檢查是否可以解決現有警告
            elif metric.level in [PerformanceLevel.EXCELLENT, PerformanceLevel.GOOD, PerformanceLevel.FAIR]:
                for alert in self.alerts:
                    if (alert.resource_type == metric.resource_type and 
                        not alert.resolved):
                        alert.resolved = True
                        alert.resolved_at = metric.timestamp
                        self.logger.info(f"效能警告已解決: {alert.message}")
    
    def _generate_alert_message(self, metric: PerformanceMetric) -> str:
        """生成警告訊息"""
        resource_names = {
            ResourceType.CPU: "CPU",
            ResourceType.MEMORY: "記憶體",
            ResourceType.DISK: "磁碟",
            ResourceType.NETWORK: "網路",
            ResourceType.PROCESS: "程序"
        }
        
        resource_name = resource_names.get(metric.resource_type, str(metric.resource_type))
        
        if metric.level == PerformanceLevel.CRITICAL:
            return f"{resource_name}使用率嚴重過高: {metric.value:.1f}{metric.unit}"
        else:
            return f"{resource_name}使用率過高: {metric.value:.1f}{metric.unit}"
    
    def _generate_suggestions(self, metrics: List[PerformanceMetric]):
        """生成最佳化建議"""
        for metric in metrics:
            if metric.level in [PerformanceLevel.POOR, PerformanceLevel.CRITICAL]:
                suggestions = self._get_optimization_suggestions(metric)
                
                for suggestion in suggestions:
                    # 檢查是否已有相同建議
                    existing = any(
                        s.title == suggestion.title and not s.applied 
                        for s in self.suggestions
                    )
                    
                    if not existing:
                        self.suggestions.append(suggestion)
    
    def _get_optimization_suggestions(self, metric: PerformanceMetric) -> List[OptimizationSuggestion]:
        """取得特定資源的最佳化建議"""
        suggestions = []
        
        if metric.resource_type == ResourceType.CPU:
            if metric.value > 90:
                suggestions.append(OptimizationSuggestion(
                    category="CPU",
                    priority=1,
                    title="降低並發處理數量",
                    description="CPU使用率過高，建議減少同時處理的任務數量",
                    action="reduce_concurrent_tasks",
                    estimated_impact="可降低CPU使用率20-30%",
                    auto_applicable=True
                ))
            
            if metric.value > 80:
                suggestions.append(OptimizationSuggestion(
                    category="CPU",
                    priority=2,
                    title="啟用低優先級處理",
                    description="將非關鍵任務設為低優先級",
                    action="enable_low_priority_processing",
                    estimated_impact="可降低CPU使用率10-15%",
                    auto_applicable=True
                ))
        
        elif metric.resource_type == ResourceType.MEMORY:
            if metric.value > 90:
                suggestions.append(OptimizationSuggestion(
                    category="記憶體",
                    priority=1,
                    title="執行垃圾回收",
                    description="記憶體使用率過高，建議執行垃圾回收",
                    action="force_garbage_collection",
                    estimated_impact="可釋放5-15%記憶體",
                    auto_applicable=True
                ))
            
            if metric.value > 85:
                suggestions.append(OptimizationSuggestion(
                    category="記憶體",
                    priority=2,
                    title="清理快取",
                    description="清理搜尋快取和臨時資料",
                    action="clear_caches",
                    estimated_impact="可釋放10-20%記憶體",
                    auto_applicable=True
                ))
        
        elif metric.resource_type == ResourceType.DISK:
            if metric.value > 95:
                suggestions.append(OptimizationSuggestion(
                    category="磁碟",
                    priority=1,
                    title="清理臨時檔案",
                    description="磁碟空間不足，建議清理臨時檔案",
                    action="cleanup_temp_files",
                    estimated_impact="可釋放100MB-1GB空間",
                    auto_applicable=True
                ))
            
            if metric.value > 90:
                suggestions.append(OptimizationSuggestion(
                    category="磁碟",
                    priority=2,
                    title="清理舊日誌",
                    description="清理超過30天的日誌檔案",
                    action="cleanup_old_logs",
                    estimated_impact="可釋放50-500MB空間",
                    auto_applicable=True
                ))
        
        return suggestions
    
    def _apply_auto_optimizations(self):
        """應用自動最佳化"""
        for suggestion in self.suggestions:
            if (suggestion.auto_applicable and 
                not suggestion.applied and 
                suggestion.priority <= 2):  # 只自動應用高優先級建議
                
                try:
                    if self._execute_optimization(suggestion):
                        suggestion.applied = True
                        suggestion.applied_at = datetime.now()
                        self.logger.info(f"已自動應用最佳化: {suggestion.title}")
                except Exception as e:
                    self.logger.error(f"自動最佳化失敗 {suggestion.title}: {str(e)}")
    
    def _execute_optimization(self, suggestion: OptimizationSuggestion) -> bool:
        """執行最佳化動作"""
        action = suggestion.action
        
        try:
            if action == "force_garbage_collection":
                gc.collect()
                return True
            
            elif action == "clear_caches":
                # 清理搜尋快取
                if hasattr(self, '_search_manager'):
                    self._search_manager.clear_cache()
                return True
            
            elif action == "cleanup_temp_files":
                temp_dir = platform_adapter.get_temp_dir()
                self._cleanup_directory(temp_dir, days_old=1)
                return True
            
            elif action == "cleanup_old_logs":
                from logging_service import logging_service
                logging_service.cleanup_old_logs(days_to_keep=30)
                return True
            
            elif action == "reduce_concurrent_tasks":
                # 這需要與任務管理器整合
                callback = self.optimization_callbacks.get(action)
                if callback:
                    return callback()
                return False
            
            elif action == "enable_low_priority_processing":
                # 這需要與任務管理器整合
                callback = self.optimization_callbacks.get(action)
                if callback:
                    return callback()
                return False
            
            else:
                self.logger.warning(f"未知的最佳化動作: {action}")
                return False
                
        except Exception as e:
            self.logger.error(f"執行最佳化動作失敗 {action}: {str(e)}")
            return False
    
    def _cleanup_directory(self, directory: Path, days_old: int = 7):
        """清理目錄中的舊檔案"""
        if not directory.exists():
            return
        
        cutoff_time = datetime.now() - timedelta(days=days_old)
        
        for file_path in directory.rglob('*'):
            if file_path.is_file():
                try:
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_time:
                        file_path.unlink()
                except Exception as e:
                    self.logger.warning(f"清理檔案失敗 {file_path}: {str(e)}")
    
    def _establish_baseline(self):
        """建立基準效能資料"""
        try:
            # 收集基準資料
            baseline_metrics = self._collect_metrics()
            
            for metric in baseline_metrics:
                self.baseline_metrics[metric.resource_type] = metric.value
            
            self.logger.info("已建立效能基準資料")
            
        except Exception as e:
            self.logger.error(f"建立效能基準失敗: {str(e)}")
    
    def register_optimization_callback(self, action: str, callback: Callable) -> None:
        """註冊最佳化回調函數"""
        self.optimization_callbacks[action] = callback
        self.logger.info(f"已註冊最佳化回調: {action}")
    
    def get_current_status(self) -> Dict[str, Any]:
        """取得當前效能狀態"""
        if not self.is_monitoring:
            return {"status": "not_monitoring"}
        
        current_metrics = {}
        overall_score = 100.0
        
        for resource_type, metrics_queue in self.metrics_history.items():
            if metrics_queue:
                latest_metric = metrics_queue[-1]
                current_metrics[resource_type.value] = {
                    "value": latest_metric.value,
                    "unit": latest_metric.unit,
                    "level": latest_metric.level.value,
                    "timestamp": latest_metric.timestamp.isoformat()
                }
                
                # 計算整體分數（簡化算法）
                if latest_metric.level == PerformanceLevel.CRITICAL:
                    overall_score -= 30
                elif latest_metric.level == PerformanceLevel.POOR:
                    overall_score -= 20
                elif latest_metric.level == PerformanceLevel.FAIR:
                    overall_score -= 10
        
        overall_score = max(0, overall_score)
        
        # 統計警告
        active_alerts = [a for a in self.alerts if not a.resolved]
        resolved_alerts = [a for a in self.alerts if a.resolved]
        
        # 統計建議
        pending_suggestions = [s for s in self.suggestions if not s.applied]
        applied_suggestions = [s for s in self.suggestions if s.applied]
        
        return {
            "status": "monitoring",
            "overall_score": overall_score,
            "current_metrics": current_metrics,
            "alerts": {
                "active": len(active_alerts),
                "resolved": len(resolved_alerts),
                "total": len(self.alerts)
            },
            "suggestions": {
                "pending": len(pending_suggestions),
                "applied": len(applied_suggestions),
                "total": len(self.suggestions)
            },
            "monitoring_duration": self._get_monitoring_duration(),
            "auto_optimization": self.auto_optimization_enabled
        }
    
    def _get_monitoring_duration(self) -> str:
        """取得監控持續時間"""
        if not self.metrics_history[ResourceType.CPU]:
            return "0s"
        
        first_metric = None
        for metrics_queue in self.metrics_history.values():
            if metrics_queue:
                if first_metric is None or metrics_queue[0].timestamp < first_metric:
                    first_metric = metrics_queue[0].timestamp
        
        if first_metric:
            duration = datetime.now() - first_metric
            return str(duration).split('.')[0]  # 移除微秒
        
        return "0s"
    
    def generate_performance_report(self, hours: int = 24) -> PerformanceReport:
        """生成效能報告"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # 收集指定時間範圍內的資料
        metrics_summary = {}
        trends = {}
        
        for resource_type, metrics_queue in self.metrics_history.items():
            relevant_metrics = [
                m for m in metrics_queue 
                if start_time <= m.timestamp <= end_time
            ]
            
            if relevant_metrics:
                values = [m.value for m in relevant_metrics]
                metrics_summary[resource_type] = {
                    "average": sum(values) / len(values),
                    "max": max(values),
                    "min": min(values),
                    "current": values[-1],
                    "samples": len(values)
                }
                
                # 簡單趨勢分析
                if len(values) >= 2:
                    recent_avg = sum(values[-10:]) / min(10, len(values))
                    earlier_avg = sum(values[:10]) / min(10, len(values))
                    trend = "increasing" if recent_avg > earlier_avg else "decreasing"
                    trends[resource_type.value] = trend
        
        # 計算整體分數
        overall_score = 100.0
        for resource_type, summary in metrics_summary.items():
            avg_value = summary["average"]
            thresholds = self.thresholds.get(resource_type, {})
            
            if avg_value >= thresholds.get('critical', 95):
                overall_score -= 25
            elif avg_value >= thresholds.get('warning', 80):
                overall_score -= 15
            elif avg_value >= 60:
                overall_score -= 5
        
        overall_score = max(0, overall_score)
        
        # 過濾相關警告和建議
        relevant_alerts = [
            a for a in self.alerts 
            if start_time <= a.timestamp <= end_time
        ]
        
        relevant_suggestions = [
            s for s in self.suggestions 
            if not s.applied_at or start_time <= s.applied_at <= end_time
        ]
        
        report = PerformanceReport(
            report_id=f"perf_report_{int(end_time.timestamp())}",
            start_time=start_time,
            end_time=end_time,
            overall_score=overall_score,
            metrics_summary=metrics_summary,
            alerts=relevant_alerts,
            suggestions=relevant_suggestions,
            trends=trends
        )
        
        self.reports.append(report)
        
        # 限制報告數量
        if len(self.reports) > 50:
            self.reports = self.reports[-50:]
        
        return report
    
    def get_optimization_recommendations(self) -> List[OptimizationSuggestion]:
        """取得最佳化建議"""
        # 按優先級排序
        pending_suggestions = [s for s in self.suggestions if not s.applied]
        return sorted(pending_suggestions, key=lambda x: x.priority)
    
    def apply_suggestion(self, suggestion_title: str) -> bool:
        """手動應用建議"""
        for suggestion in self.suggestions:
            if suggestion.title == suggestion_title and not suggestion.applied:
                try:
                    if self._execute_optimization(suggestion):
                        suggestion.applied = True
                        suggestion.applied_at = datetime.now()
                        self.logger.info(f"已手動應用最佳化: {suggestion.title}")
                        return True
                except Exception as e:
                    self.logger.error(f"手動最佳化失敗 {suggestion.title}: {str(e)}")
                    return False
        
        return False
    
    def set_auto_optimization(self, enabled: bool) -> None:
        """設定自動最佳化"""
        self.auto_optimization_enabled = enabled
        self.logger.info(f"自動最佳化已{'啟用' if enabled else '停用'}")
    
    def clear_alerts(self) -> None:
        """清除所有警告"""
        self.alerts.clear()
        self.logger.info("已清除所有效能警告")
    
    def clear_suggestions(self) -> None:
        """清除所有建議"""
        self.suggestions.clear()
        self.logger.info("已清除所有最佳化建議")
    
    def export_report(self, report: PerformanceReport, format: str = 'json') -> Optional[str]:
        """匯出效能報告"""
        try:
            if format.lower() == 'json':
                report_data = {
                    "report_id": report.report_id,
                    "start_time": report.start_time.isoformat(),
                    "end_time": report.end_time.isoformat(),
                    "overall_score": report.overall_score,
                    "metrics_summary": {
                        k.value if hasattr(k, 'value') else str(k): v 
                        for k, v in report.metrics_summary.items()
                    },
                    "alerts": [
                        {
                            "timestamp": a.timestamp.isoformat(),
                            "resource_type": a.resource_type.value,
                            "level": a.level.value,
                            "message": a.message,
                            "value": a.value,
                            "threshold": a.threshold,
                            "resolved": a.resolved,
                            "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None
                        }
                        for a in report.alerts
                    ],
                    "suggestions": [
                        {
                            "category": s.category,
                            "priority": s.priority,
                            "title": s.title,
                            "description": s.description,
                            "action": s.action,
                            "estimated_impact": s.estimated_impact,
                            "auto_applicable": s.auto_applicable,
                            "applied": s.applied,
                            "applied_at": s.applied_at.isoformat() if s.applied_at else None
                        }
                        for s in report.suggestions
                    ],
                    "trends": report.trends
                }
                
                # 儲存到檔案
                reports_dir = platform_adapter.get_config_dir() / "performance_reports"
                reports_dir.mkdir(exist_ok=True)
                
                report_file = reports_dir / f"{report.report_id}.json"
                with open(report_file, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, indent=2, ensure_ascii=False)
                
                self.logger.info(f"效能報告已匯出: {report_file}")
                return str(report_file)
                
        except Exception as e:
            self.logger.error(f"匯出效能報告失敗: {str(e)}")
            return None


# 全域效能監控器實例
performance_monitor = PerformanceMonitor()


if __name__ == "__main__":
    # 測試程式
    print("=== 效能監控系統測試 ===")
    
    monitor = PerformanceMonitor()
    
    # 啟動監控
    monitor.start_monitoring()
    
    # 等待一段時間收集資料
    time.sleep(10)
    
    # 取得狀態
    status = monitor.get_current_status()
    print(f"監控狀態: {status}")
    
    # 生成報告
    report = monitor.generate_performance_report(hours=1)
    print(f"效能報告: 整體分數 {report.overall_score}")
    
    # 停止監控
    monitor.stop_monitoring()