"""
🔔 Notifications - الإشعارات
=============================
نظام إشعارات Windows Toast.
"""

import os
import threading
from typing import Optional

# محاولة استيراد winotify
try:
    from winotify import Notification, audio
    WINOTIFY_AVAILABLE = True
except ImportError:
    WINOTIFY_AVAILABLE = False
    print("⚠️ winotify not installed. Run: pip install winotify")


# إعدادات الإشعارات
APP_ID = "Jarvis AI"
ICON_PATH = None  # يمكن تحديد أيقونة لاحقاً


class NotificationManager:
    """مدير إشعارات Windows"""
    
    def __init__(self):
        self.enabled = True
        self._check_availability()
    
    def _check_availability(self):
        """فحص توفر نظام الإشعارات"""
        if not WINOTIFY_AVAILABLE:
            print("⚠️ Windows Toast notifications not available")
            self.enabled = False
    
    def send(
        self, 
        title: str, 
        message: str, 
        icon: str = None,
        duration: str = "short",
        sound: bool = True
    ) -> bool:
        """
        إرسال إشعار Windows Toast.
        
        Args:
            title: عنوان الإشعار
            message: نص الإشعار
            icon: مسار الأيقونة (اختياري)
            duration: "short" أو "long"
            sound: تشغيل صوت
            
        Returns:
            bool: نجاح الإرسال
        """
        if not self.enabled or not WINOTIFY_AVAILABLE:
            print(f"🔔 [Notification]: {title} - {message}")
            return False
        
        try:
            toast = Notification(
                app_id=APP_ID,
                title=title,
                msg=message,
                duration=duration,
                icon=icon or ICON_PATH or ""
            )
            
            if sound:
                toast.set_audio(audio.Default, loop=False)
            
            # إرسال في thread منفصل لتجنب التعليق
            threading.Thread(target=toast.show, daemon=True).start()
            return True
            
        except Exception as e:
            print(f"⚠️ Notification error: {e}")
            return False
    
    # ═══════════════════════════════════════════════════════════
    # إشعارات جاهزة
    # ═══════════════════════════════════════════════════════════
    
    def file_detected(self, filename: str, folder: str = ""):
        """إشعار اكتشاف ملف جديد"""
        self.send(
            title="👁️ ملف جديد!",
            message=f"تم رصد: {filename}" + (f"\nفي: {folder}" if folder else "")
        )
    
    def app_opened(self, app_name: str):
        """إشعار فتح تطبيق"""
        self.send(
            title="🚀 تم التشغيل",
            message=f"تم فتح: {app_name}",
            duration="short"
        )
    
    def watch_started(self, folder: str, watch_id: str):
        """إشعار بدء المراقبة"""
        self.send(
            title="👁️ بدأت المراقبة",
            message=f"المجلد: {folder}\nID: {watch_id}"
        )
    
    def watch_stopped(self, folder: str):
        """إشعار إيقاف المراقبة"""
        self.send(
            title="🛑 توقفت المراقبة",
            message=f"المجلد: {folder}"
        )
    
    def error(self, message: str):
        """إشعار خطأ"""
        self.send(
            title="❌ خطأ",
            message=message,
            duration="long"
        )
    
    def success(self, message: str):
        """إشعار نجاح"""
        self.send(
            title="✅ تم",
            message=message
        )


# Singleton instance
_notifier = None

def get_notifier() -> NotificationManager:
    """جلب مدير الإشعارات (Singleton)"""
    global _notifier
    if _notifier is None:
        _notifier = NotificationManager()
    return _notifier


# دوال مختصرة للاستخدام السريع
def notify(title: str, message: str, **kwargs):
    """إرسال إشعار سريع"""
    get_notifier().send(title, message, **kwargs)

def notify_file(filename: str, folder: str = ""):
    """إشعار ملف جديد"""
    get_notifier().file_detected(filename, folder)

def notify_error(message: str):
    """إشعار خطأ"""
    get_notifier().error(message)

def notify_success(message: str):
    """إشعار نجاح"""
    get_notifier().success(message)
