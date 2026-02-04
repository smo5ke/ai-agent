"""
📤 Post Execution - ما بعد التنفيذ
===================================
معالجة نتائج التنفيذ (إشعارات، ذاكرة، أخطاء).
"""

from typing import Optional, Callable
from dataclasses import dataclass


@dataclass
class PostExecutionConfig:
    """إعدادات ما بعد التنفيذ"""
    notify_on_success: bool = True
    notify_on_error: bool = True
    save_to_memory: bool = True
    log_to_console: bool = True


class PostExecutionHandler:
    """معالج ما بعد التنفيذ"""
    
    def __init__(self, config: PostExecutionConfig = None):
        self.config = config or PostExecutionConfig()
        self._ui_callback: Optional[Callable] = None
        self._memory = None
    
    def set_ui_callback(self, callback: Callable):
        """ربط callback للواجهة"""
        self._ui_callback = callback
    
    def set_memory(self, memory):
        """ربط نظام الذاكرة"""
        self._memory = memory
    
    def handle(self, result, command: dict):
        """
        معالجة نتيجة التنفيذ.
        
        Args:
            result: ExecutionResult
            command: الأمر الأصلي
        """
        # 1. إشعار الواجهة
        if self._ui_callback:
            if result.success and self.config.notify_on_success:
                self._ui_callback(f"✅ {result.message}", "success")
            elif not result.success and self.config.notify_on_error:
                self._ui_callback(f"❌ {result.message}", "error")
        
        # 2. حفظ في الذاكرة
        if self._memory and self.config.save_to_memory:
            self._memory.add_system_event(
                event_type=result.intent,
                details=result.message,
                target=command.get("target")
            )
        
        # 3. طباعة للـ Console
        if self.config.log_to_console:
            status = "✓" if result.success else "✗"
            print(f"[{status}] {result.intent}: {result.message} ({result.duration_ms:.1f}ms)")
        
        # 4. إشعار Toast للعمليات المهمة
        if result.success and result.intent in ["reminder", "schedule"]:
            self._send_toast(result)
    
    def _send_toast(self, result):
        """إرسال إشعار Toast"""
        try:
            from core.notifications import get_notification_manager
            notifier = get_notification_manager()
            notifier.send(
                title="Jarvis",
                message=result.message,
                icon="info"
            )
        except:
            pass


# Singleton
_handler = None

def get_post_handler() -> PostExecutionHandler:
    global _handler
    if _handler is None:
        _handler = PostExecutionHandler()
    return _handler
