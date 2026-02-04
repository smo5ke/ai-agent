"""
⌨️ Hotkeys - اختصارات لوحة المفاتيح
====================================
نظام اختصارات لوحة المفاتيح العامة.
"""

import threading
from typing import Callable, Dict, Optional

# محاولة استيراد المكتبة
try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
    print("⚠️ keyboard not installed. Run: pip install keyboard")


class HotkeyManager:
    """مدير اختصارات لوحة المفاتيح"""
    
    # الاختصارات الافتراضية
    DEFAULT_HOTKEYS = {
        "voice": "ctrl+shift+v",      # تفعيل الصوت
        "focus": "ctrl+shift+j",      # التركيز على Jarvis
    }
    
    def __init__(self):
        self._callbacks: Dict[str, Callable] = {}
        self._registered: Dict[str, str] = {}
        self._enabled = True
    
    def is_available(self) -> bool:
        """فحص توفر المكتبة"""
        return KEYBOARD_AVAILABLE
    
    def register(self, name: str, hotkey: str, callback: Callable):
        """
        تسجيل اختصار جديد.
        
        Args:
            name: اسم الاختصار (voice, focus, etc)
            hotkey: الاختصار (ctrl+shift+v)
            callback: الدالة التي تُنفذ
        """
        if not KEYBOARD_AVAILABLE:
            return False
        
        try:
            # إلغاء الاختصار القديم إذا كان موجوداً
            if name in self._registered:
                keyboard.remove_hotkey(self._registered[name])
            
            # تسجيل الاختصار الجديد
            keyboard.add_hotkey(hotkey, lambda: self._handle_hotkey(name))
            
            self._callbacks[name] = callback
            self._registered[name] = hotkey
            
            print(f"⌨️ Hotkey registered: {name} → {hotkey}")
            return True
            
        except Exception as e:
            print(f"❌ Hotkey error: {e}")
            return False
    
    def _handle_hotkey(self, name: str):
        """معالجة ضغط اختصار"""
        if not self._enabled:
            return
        
        if name in self._callbacks:
            # تنفيذ في thread منفصل لمنع الـ blocking
            threading.Thread(
                target=self._callbacks[name],
                daemon=True
            ).start()
    
    def unregister(self, name: str):
        """إلغاء تسجيل اختصار"""
        if name in self._registered:
            try:
                keyboard.remove_hotkey(self._registered[name])
                del self._registered[name]
                del self._callbacks[name]
            except:
                pass
    
    def enable(self):
        """تفعيل الاختصارات"""
        self._enabled = True
    
    def disable(self):
        """تعطيل الاختصارات"""
        self._enabled = False
    
    def get_hotkey(self, name: str) -> Optional[str]:
        """جلب اختصار معين"""
        return self._registered.get(name) or self.DEFAULT_HOTKEYS.get(name)
    
    def cleanup(self):
        """تنظيف كل الاختصارات"""
        if KEYBOARD_AVAILABLE:
            for name in list(self._registered.keys()):
                self.unregister(name)


# Singleton
_manager = None

def get_hotkey_manager() -> HotkeyManager:
    """جلب مدير الاختصارات"""
    global _manager
    if _manager is None:
        _manager = HotkeyManager()
    return _manager
