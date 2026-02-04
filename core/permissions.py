from enum import Enum

class SecurityLevel(Enum):
    SAFE = 1      # نفذ فوراً (بحث، قراءة)
    WARNING = 2   # يحتاج انتباه (مراقبة)
    CRITICAL = 3  # يحتاج موافقة صريحة (حذف، نقل، تشغيل ملفات exe)

# خريطة الصلاحيات
ACTION_POLICY = {
    "open": SecurityLevel.SAFE,
    "open_file": SecurityLevel.SAFE,
    "clean": SecurityLevel.CRITICAL,
    "watch": SecurityLevel.WARNING,
    "stop_watch": SecurityLevel.SAFE,
    "macro": SecurityLevel.SAFE,
    "schedule": SecurityLevel.SAFE,
    "reminder": SecurityLevel.SAFE,
    "hello": SecurityLevel.SAFE,
    "chat": SecurityLevel.SAFE,
}

def check_permission(intent: str) -> SecurityLevel:
    return ACTION_POLICY.get(intent, SecurityLevel.CRITICAL)