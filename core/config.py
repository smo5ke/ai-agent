"""
⚙️ Config Manager - إدارة الإعدادات
====================================
حفظ وتحميل الإعدادات من ملف JSON.
"""

import os
import json
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict


# مسار ملف الإعدادات
CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")


@dataclass
class JarvisConfig:
    """إعدادات Jarvis الرئيسية"""
    
    # الوضع الافتراضي
    default_profile: str = "safe"
    
    # LLM
    llm_host: str = "localhost"
    llm_port: int = 6000
    llm_timeout: int = 30
    
    # الواجهة
    theme: str = "dark"
    language: str = "ar"
    font_size: int = 12
    
    # الصوت
    voice_enabled: bool = True
    voice_language: str = "ar-SA"
    
    # الإشعارات
    notifications_enabled: bool = True
    sound_enabled: bool = True
    
    # الأمان
    confirm_high_risk: bool = True
    dry_run_by_default: bool = True
    
    # Telegram
    telegram_enabled: bool = False
    telegram_token: str = ""
    telegram_allowed_users: list = None
    
    # Hotkeys
    hotkey_voice: str = "ctrl+shift+v"
    hotkey_focus: str = "ctrl+shift+j"
    
    # المراقبة
    max_watches: int = 10
    
    # السجلات
    max_log_entries: int = 100
    
    def __post_init__(self):
        if self.telegram_allowed_users is None:
            self.telegram_allowed_users = []


class ConfigManager:
    """مدير الإعدادات"""
    
    def __init__(self):
        self._config: Optional[JarvisConfig] = None
        self._load()
    
    def _load(self):
        """تحميل الإعدادات من الملف"""
        # التأكد من وجود المجلد
        os.makedirs(CONFIG_DIR, exist_ok=True)
        
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._config = JarvisConfig(**data)
            except Exception as e:
                print(f"⚠️ Config load error: {e}")
                self._config = JarvisConfig()
        else:
            self._config = JarvisConfig()
            self._save()
    
    def _save(self):
        """حفظ الإعدادات للملف"""
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(asdict(self._config), f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Config save error: {e}")
    
    @property
    def config(self) -> JarvisConfig:
        return self._config
    
    def get(self, key: str, default: Any = None) -> Any:
        """جلب قيمة إعداد"""
        return getattr(self._config, key, default)
    
    def set(self, key: str, value: Any):
        """تعيين قيمة إعداد"""
        if hasattr(self._config, key):
            setattr(self._config, key, value)
            self._save()
    
    def update(self, **kwargs):
        """تحديث عدة إعدادات"""
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
        self._save()
    
    def reset(self):
        """إعادة تعيين للإعدادات الافتراضية"""
        self._config = JarvisConfig()
        self._save()
    
    def to_dict(self) -> Dict:
        """تحويل لقاموس"""
        return asdict(self._config)


# Singleton
_manager = None

def get_config() -> ConfigManager:
    global _manager
    if _manager is None:
        _manager = ConfigManager()
    return _manager
