from enum import Enum

class SecurityLevel(Enum):
    SAFE = 1      # نفذ فوراً (بحث، قراءة)
    WARNING = 2   # يحتاج انتباه (مراقبة)
    CRITICAL = 3  # يحتاج موافقة صريحة (حذف، نقل، تشغيل ملفات exe)

# خريطة الصلاحيات
ACTION_POLICY = {
    "open": SecurityLevel.SAFE,
    "clean": SecurityLevel.CRITICAL, # التنظيف ينقل ملفات، لازم إذن
    "watch": SecurityLevel.WARNING,
    "macro": SecurityLevel.SAFE,
    "hello": SecurityLevel.SAFE,
    "chat": SecurityLevel.SAFE,
}

def check_permission(intent: str) -> SecurityLevel:
    return ACTION_POLICY.get(intent, SecurityLevel.CRITICAL)