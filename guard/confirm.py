"""
✋ Confirmation Manager - مدير التأكيد
======================================
طلب تأكيد المستخدم للعمليات الخطرة.
"""

from typing import Callable, Optional
from .risk import RiskLevel


class ConfirmationManager:
    """مدير التأكيد"""
    
    def __init__(self):
        self._pending_command = None
        self._confirm_callback: Optional[Callable] = None
        self._cancel_callback: Optional[Callable] = None
    
    def needs_confirmation(self, risk_level: RiskLevel) -> bool:
        """هل يحتاج الأمر تأكيد؟"""
        return risk_level.value >= RiskLevel.HIGH.value
    
    def request_confirmation(
        self, 
        command: dict, 
        dry_run_result: str,
        on_confirm: Callable,
        on_cancel: Callable = None
    ):
        """
        طلب تأكيد من المستخدم.
        
        Args:
            command: الأمر المطلوب تنفيذه
            dry_run_result: نتيجة المحاكاة
            on_confirm: callback عند التأكيد
            on_cancel: callback عند الإلغاء
        """
        self._pending_command = command
        self._confirm_callback = on_confirm
        self._cancel_callback = on_cancel
        
        # سيتم عرض UI للتأكيد
        return {
            "pending": True,
            "command": command,
            "message": dry_run_result,
            "actions": ["confirm", "cancel"]
        }
    
    def confirm(self):
        """تأكيد العملية"""
        if self._pending_command and self._confirm_callback:
            self._confirm_callback(self._pending_command)
            self._clear()
    
    def cancel(self):
        """إلغاء العملية"""
        if self._cancel_callback:
            self._cancel_callback()
        self._clear()
    
    def _clear(self):
        """مسح الحالة"""
        self._pending_command = None
        self._confirm_callback = None
        self._cancel_callback = None
    
    def has_pending(self) -> bool:
        """هل يوجد أمر معلق؟"""
        return self._pending_command is not None


def needs_confirmation(risk_level: RiskLevel) -> bool:
    """دالة مختصرة"""
    manager = ConfirmationManager()
    return manager.needs_confirmation(risk_level)
