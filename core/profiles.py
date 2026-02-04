"""
👤 Profiles - أوضاع التشغيل
============================
Safe Mode, Power Mode, Silent Mode
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class ProfileType(Enum):
    """أنواع الأوضاع"""
    SAFE = "safe"       # آمن - تأكيد لكل شيء
    POWER = "power"     # قوي - بدون تأكيد
    SILENT = "silent"   # صامت - بدون إشعارات


@dataclass
class ProfileSettings:
    """إعدادات الوضع"""
    name: str
    confirm_high_risk: bool = True      # طلب تأكيد للعمليات الخطرة
    confirm_medium_risk: bool = False   # طلب تأكيد للعمليات المتوسطة
    dry_run_enabled: bool = True        # محاكاة قبل التنفيذ
    notifications_enabled: bool = True  # إشعارات Toast
    sound_enabled: bool = True          # أصوات
    voice_feedback: bool = False        # رد صوتي
    log_to_console: bool = True         # طباعة للـ console


# الأوضاع المحددة مسبقاً
PREDEFINED_PROFILES = {
    ProfileType.SAFE: ProfileSettings(
        name="🛡️ Safe Mode",
        confirm_high_risk=True,
        confirm_medium_risk=True,
        dry_run_enabled=True,
        notifications_enabled=True,
        sound_enabled=True,
        voice_feedback=False,
        log_to_console=True
    ),
    ProfileType.POWER: ProfileSettings(
        name="⚡ Power Mode",
        confirm_high_risk=True,      # لا زال يطلب للخطير
        confirm_medium_risk=False,
        dry_run_enabled=False,
        notifications_enabled=True,
        sound_enabled=True,
        voice_feedback=False,
        log_to_console=True
    ),
    ProfileType.SILENT: ProfileSettings(
        name="🔇 Silent Mode",
        confirm_high_risk=True,
        confirm_medium_risk=False,
        dry_run_enabled=True,
        notifications_enabled=False,
        sound_enabled=False,
        voice_feedback=False,
        log_to_console=False
    ),
}


class ProfileManager:
    """مدير الأوضاع"""
    
    def __init__(self):
        self._current: ProfileType = ProfileType.SAFE
        self._custom_settings: Optional[ProfileSettings] = None
    
    @property
    def current_profile(self) -> ProfileType:
        return self._current
    
    @property
    def settings(self) -> ProfileSettings:
        """جلب إعدادات الوضع الحالي"""
        if self._custom_settings:
            return self._custom_settings
        return PREDEFINED_PROFILES[self._current]
    
    def switch_to(self, profile: ProfileType):
        """التبديل لوضع آخر"""
        self._current = profile
        self._custom_settings = None
        print(f"🔄 تم التبديل إلى: {self.settings.name}")
    
    def set_custom(self, settings: ProfileSettings):
        """تعيين إعدادات مخصصة"""
        self._custom_settings = settings
    
    def should_confirm(self, risk_level: str) -> bool:
        """هل يجب طلب تأكيد لهذا المستوى؟"""
        settings = self.settings
        
        if risk_level in ("HIGH", "CRITICAL"):
            return settings.confirm_high_risk
        elif risk_level == "MEDIUM":
            return settings.confirm_medium_risk
        
        return False
    
    def should_notify(self) -> bool:
        """هل الإشعارات مفعلة؟"""
        return self.settings.notifications_enabled
    
    def should_dry_run(self, risk_level: str) -> bool:
        """هل يجب المحاكاة؟"""
        if not self.settings.dry_run_enabled:
            return False
        return risk_level in ("HIGH", "CRITICAL")
    
    def get_all_profiles(self) -> list:
        """جلب كل الأوضاع المتاحة"""
        return [
            {
                "type": p.value,
                "name": PREDEFINED_PROFILES[p].name,
                "active": p == self._current
            }
            for p in ProfileType
        ]


# Singleton
_manager = None

def get_profile_manager() -> ProfileManager:
    global _manager
    if _manager is None:
        _manager = ProfileManager()
    return _manager
