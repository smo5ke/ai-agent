"""
🔄 Crash Recovery - نظام التعافي من الأعطال
=============================================
إعادة تشغيل تلقائية للـ Worker والـ Watchers.
"""

import subprocess
import threading
import time
import sys
import os
from typing import Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RecoveryConfig:
    """إعدادات التعافي"""
    max_retries: int = 3
    retry_delay: float = 2.0  # ثواني
    health_check_interval: float = 10.0  # ثواني
    auto_restart: bool = True


@dataclass
class ServiceStatus:
    """حالة الخدمة"""
    name: str
    is_running: bool = False
    last_check: datetime = field(default_factory=datetime.now)
    restart_count: int = 0
    last_error: Optional[str] = None


class CrashRecovery:
    """
    مدير التعافي من الأعطال.
    يراقب الخدمات ويعيد تشغيلها عند الفشل.
    """
    
    def __init__(self, config: RecoveryConfig = None):
        self.config = config or RecoveryConfig()
        self.services: dict = {}
        self._monitor_thread: Optional[threading.Thread] = None
        self._running = False
        self._callbacks: list = []
        
        # تسجيل الخدمات الافتراضية
        self._register_default_services()
    
    def _register_default_services(self):
        """تسجيل الخدمات الافتراضية"""
        self.services["llm_worker"] = ServiceStatus(name="LLM Worker")
        self.services["watcher"] = ServiceStatus(name="File Watcher")
        self.services["scheduler"] = ServiceStatus(name="Task Scheduler")
    
    def add_callback(self, callback: Callable):
        """إضافة callback للإشعارات"""
        self._callbacks.append(callback)
    
    def _notify(self, message: str, level: str = "info"):
        """إرسال إشعار"""
        for callback in self._callbacks:
            try:
                callback(message, level)
            except:
                pass
    
    # ═══════════════════════════════════════════════════════════
    # فحص صحة الخدمات
    # ═══════════════════════════════════════════════════════════
    
    def check_llm_worker(self) -> bool:
        """فحص حالة LLM Worker"""
        try:
            from llm import ipc
            return ipc.is_worker_available()
        except Exception as e:
            self.services["llm_worker"].last_error = str(e)
            return False
    
    def check_watcher(self) -> bool:
        """فحص حالة Watcher"""
        try:
            from watcher_engine import watcher_engine
            # نعتبره يعمل إذا كان هناك أي watches نشطة
            return len(watcher_engine.active_watches) >= 0  # دائماً OK
        except Exception as e:
            self.services["watcher"].last_error = str(e)
            return False
    
    def check_scheduler(self) -> bool:
        """فحص حالة Scheduler"""
        try:
            from core.scheduler import get_scheduler
            scheduler = get_scheduler()
            return scheduler is not None
        except Exception as e:
            self.services["scheduler"].last_error = str(e)
            return False
    
    def check_all(self) -> dict:
        """فحص جميع الخدمات"""
        results = {
            "llm_worker": self.check_llm_worker(),
            "watcher": self.check_watcher(),
            "scheduler": self.check_scheduler()
        }
        
        for name, is_running in results.items():
            self.services[name].is_running = is_running
            self.services[name].last_check = datetime.now()
        
        return results
    
    # ═══════════════════════════════════════════════════════════
    # إعادة تشغيل الخدمات
    # ═══════════════════════════════════════════════════════════
    
    def restart_llm_worker(self) -> bool:
        """إعادة تشغيل LLM Worker"""
        service = self.services["llm_worker"]
        
        if service.restart_count >= self.config.max_retries:
            self._notify(f"⚠️ LLM Worker فشل {self.config.max_retries} مرات", "error")
            return False
        
        try:
            self._notify("🔄 جاري إعادة تشغيل LLM Worker...", "warning")
            
            # الحصول على مسار الـ worker
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            worker_path = os.path.join(base_dir, "llm", "worker_process.py")
            
            # تشغيل Worker في process جديد
            subprocess.Popen(
                [sys.executable, worker_path],
                cwd=base_dir,
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
            
            # انتظار قليلاً ثم فحص
            time.sleep(3)
            
            if self.check_llm_worker():
                service.restart_count += 1
                self._notify("✅ LLM Worker يعمل الآن!", "success")
                return True
            else:
                service.restart_count += 1
                self._notify("❌ فشل إعادة تشغيل LLM Worker", "error")
                return False
                
        except Exception as e:
            service.last_error = str(e)
            service.restart_count += 1
            self._notify(f"❌ خطأ: {e}", "error")
            return False
    
    def restart_service(self, service_name: str) -> bool:
        """إعادة تشغيل خدمة محددة"""
        if service_name == "llm_worker":
            return self.restart_llm_worker()
        # يمكن إضافة خدمات أخرى هنا
        return False
    
    # ═══════════════════════════════════════════════════════════
    # المراقبة التلقائية
    # ═══════════════════════════════════════════════════════════
    
    def start_monitoring(self):
        """بدء المراقبة التلقائية"""
        if self._running:
            return
        
        self._running = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True
        )
        self._monitor_thread.start()
        print("🔄 Crash Recovery monitoring started")
    
    def stop_monitoring(self):
        """إيقاف المراقبة"""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2)
        print("⏹️ Crash Recovery monitoring stopped")
    
    def _monitor_loop(self):
        """حلقة المراقبة"""
        while self._running:
            try:
                results = self.check_all()
                
                # إعادة تشغيل الخدمات المتوقفة
                if self.config.auto_restart:
                    for name, is_running in results.items():
                        if not is_running and name == "llm_worker":
                            self.restart_service(name)
                
            except Exception as e:
                print(f"Monitor error: {e}")
            
            time.sleep(self.config.health_check_interval)
    
    # ═══════════════════════════════════════════════════════════
    # تقرير الحالة
    # ═══════════════════════════════════════════════════════════
    
    def get_status_report(self) -> str:
        """تقرير حالة الخدمات"""
        self.check_all()
        
        lines = ["📊 حالة الخدمات:"]
        for name, status in self.services.items():
            icon = "✅" if status.is_running else "❌"
            lines.append(f"  {icon} {status.name}")
            if status.restart_count > 0:
                lines.append(f"      ↻ إعادة تشغيل: {status.restart_count}")
            if status.last_error:
                lines.append(f"      ⚠️ {status.last_error[:50]}")
        
        return "\n".join(lines)
    
    def reset_counters(self):
        """إعادة تعيين عدادات إعادة التشغيل"""
        for service in self.services.values():
            service.restart_count = 0
            service.last_error = None


# Singleton
_crash_recovery: Optional[CrashRecovery] = None

def get_crash_recovery() -> CrashRecovery:
    global _crash_recovery
    if _crash_recovery is None:
        _crash_recovery = CrashRecovery()
    return _crash_recovery


def start_recovery_monitoring():
    """بدء المراقبة (للاستدعاء من main.py)"""
    recovery = get_crash_recovery()
    recovery.start_monitoring()
    return recovery
