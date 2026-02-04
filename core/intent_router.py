"""
🔀 Intent Router - موجّه الأوامر
=================================
توجيه الأوامر للـ Executor المناسب.
"""

from typing import Dict, Callable, Optional
from enum import Enum


class IntentCategory(Enum):
    """تصنيفات الأوامر"""
    APP = "app"           # فتح تطبيقات
    FILE = "file"         # عمليات ملفات
    WEB = "web"           # عمليات ويب
    SYSTEM = "system"     # أوامر نظام
    SCHEDULE = "schedule" # جدولة
    WATCH = "watch"       # مراقبة


# تصنيف كل intent
INTENT_CATEGORIES: Dict[str, IntentCategory] = {
    # APP
    "open": IntentCategory.APP,
    
    # FILE
    "open_file": IntentCategory.FILE,
    "create_folder": IntentCategory.FILE,
    "create_file": IntentCategory.FILE,
    "write_file": IntentCategory.FILE,
    "delete": IntentCategory.FILE,
    "rename": IntentCategory.FILE,
    "copy": IntentCategory.FILE,
    "move": IntentCategory.FILE,
    "clean": IntentCategory.FILE,
    
    # WEB
    "macro": IntentCategory.WEB,
    
    # SCHEDULE
    "schedule": IntentCategory.SCHEDULE,
    "reminder": IntentCategory.SCHEDULE,
    
    # WATCH
    "watch": IntentCategory.WATCH,
    "stop_watch": IntentCategory.WATCH,
}


class IntentRouter:
    """موجّه الأوامر"""
    
    def __init__(self):
        self._handlers: Dict[str, Callable] = {}
        self._category_handlers: Dict[IntentCategory, Callable] = {}
    
    def register_intent(self, intent: str, handler: Callable):
        """تسجيل handler لـ intent معين"""
        self._handlers[intent] = handler
    
    def register_category(self, category: IntentCategory, handler: Callable):
        """تسجيل handler لتصنيف كامل"""
        self._category_handlers[category] = handler
    
    def get_category(self, intent: str) -> Optional[IntentCategory]:
        """جلب تصنيف الـ intent"""
        return INTENT_CATEGORIES.get(intent)
    
    def route(self, command: dict) -> Optional[Callable]:
        """
        توجيه الأمر للـ handler المناسب.
        
        Returns:
            الـ handler المناسب أو None
        """
        intent = command.get("intent", "unknown")
        
        # 1. البحث عن handler محدد للـ intent
        if intent in self._handlers:
            return self._handlers[intent]
        
        # 2. البحث عن handler للتصنيف
        category = self.get_category(intent)
        if category and category in self._category_handlers:
            return self._category_handlers[category]
        
        return None
    
    def get_intent_info(self, intent: str) -> dict:
        """معلومات عن intent"""
        return {
            "intent": intent,
            "category": self.get_category(intent),
            "has_handler": intent in self._handlers,
        }


# Singleton
_router = None

def get_router() -> IntentRouter:
    global _router
    if _router is None:
        _router = IntentRouter()
    return _router
