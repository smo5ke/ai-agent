"""
🌍 World Model - نموذج العالم
============================
Jarvis يعرف الافتراضيات الذكية للأوامر.

بدل "أين؟" → يعرف.
بدل "ما اسمه؟" → يعرف.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DefaultContext:
    """السياق الافتراضي"""
    location: str = ""
    name: str = ""
    extension: str = ""
    params: Dict = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════
# 🌍 الافتراضيات الذكية
# ═══════════════════════════════════════════════════════════

DEFAULTS = {
    # إنشاء ملف
    "create_file": DefaultContext(
        location="desktop",
        name="ملف_جديد",
        extension=".txt"
    ),
    
    # إنشاء مجلد
    "create_folder": DefaultContext(
        location="desktop",
        name="مجلد_جديد"
    ),
    
    # المراقبة
    "watch": DefaultContext(
        location="downloads"
    ),
    
    # التنظيف
    "clean": DefaultContext(
        location="downloads"
    ),
    
    # فتح تطبيق
    "open": DefaultContext(
        name="chrome"
    ),
}


# ═══════════════════════════════════════════════════════════
# 🧠 أنماط الربط الذكي
# ═══════════════════════════════════════════════════════════

# إذا الأمر السابق كان X، الـ location التالي يكون Y
CONTEXT_INHERITANCE = {
    "watch": {
        # إذا راقبت downloads، الأمر التالي يكون داخل downloads
        "create_folder": lambda ctx: ctx.get("watch_target", "desktop"),
        "create_file": lambda ctx: ctx.get("watch_target", "desktop"),
    }
}


# أنماط اللغة الطبيعية → location
LOCATION_PATTERNS = {
    # عربي
    "تنزيلات": "downloads",
    "التنزيلات": "downloads",
    "downloads": "downloads",
    "سطح المكتب": "desktop",
    "المكتب": "desktop",
    "desktop": "desktop",
    "مستندات": "documents",
    "documents": "documents",
    
    # OneDrive paths
    "onedrive": os.path.expanduser("~/OneDrive"),
}


# ═══════════════════════════════════════════════════════════
# 📍 Location Resolver
# ═══════════════════════════════════════════════════════════

def resolve_location(loc: str) -> str:
    """تحويل location لمسار حقيقي"""
    if not loc:
        return ""
    
    # تحقق من الأنماط المعروفة
    loc_lower = loc.lower().strip()
    
    if loc_lower in LOCATION_PATTERNS:
        loc = LOCATION_PATTERNS[loc_lower]
    
    # المسارات المعروفة
    known_paths = {
        "desktop": get_desktop_path(),
        "downloads": get_downloads_path(),
        "documents": os.path.expanduser("~/Documents"),
    }
    
    return known_paths.get(loc, loc)


def get_desktop_path() -> str:
    """الحصول على مسار سطح المكتب"""
    onedrive_desktop = os.path.expanduser("~/OneDrive/سطح المكتب")
    if os.path.exists(onedrive_desktop):
        return onedrive_desktop
    return os.path.expanduser("~/Desktop")


def get_downloads_path() -> str:
    """الحصول على مسار التنزيلات"""
    return os.path.expanduser("~/Downloads")


# ═══════════════════════════════════════════════════════════
# 🤖 World Model Class
# ═══════════════════════════════════════════════════════════

class WorldModel:
    """
    نموذج العالم - يعرف كيف يكمل الناقص.
    """
    
    def __init__(self):
        self.defaults = DEFAULTS.copy()
        self.context: Dict[str, Any] = {}
        self.last_intent: Optional[str] = None
        self.last_location: Optional[str] = None
    
    def get_default(self, intent: str) -> DefaultContext:
        """الحصول على الافتراضي لـ intent"""
        return self.defaults.get(intent, DefaultContext())
    
    def update_context(self, key: str, value: Any):
        """تحديث السياق"""
        self.context[key] = value
    
    def set_last_action(self, intent: str, location: str = None):
        """تسجيل آخر عملية"""
        self.last_intent = intent
        if location:
            self.last_location = location
            self.context["last_location"] = location
    
    def infer_location(self, intent: str, explicit_loc: str = None) -> str:
        """
        استنتاج الـ location بذكاء.
        
        الأولوية:
        1. الموقع المحدد صراحة
        2. السياق من العملية السابقة
        3. الافتراضي للـ intent
        """
        # 1. إذا محدد صراحة
        if explicit_loc:
            return resolve_location(explicit_loc)
        
        # 2. وراثة من السياق
        if self.last_intent and self.last_intent in CONTEXT_INHERITANCE:
            inheritance = CONTEXT_INHERITANCE[self.last_intent]
            if intent in inheritance:
                inherited = inheritance[intent](self.context)
                if inherited:
                    return resolve_location(inherited)
        
        # 3. آخر موقع مستخدم
        if self.last_location and intent in ["create_folder", "create_file"]:
            return self.last_location
        
        # 4. الافتراضي
        default = self.get_default(intent)
        return resolve_location(default.location)
    
    def infer_name(self, intent: str, explicit_name: str = None) -> str:
        """استنتاج الاسم بذكاء"""
        if explicit_name:
            return explicit_name
        
        default = self.get_default(intent)
        
        # إضافة timestamp للتفرد
        timestamp = datetime.now().strftime("%H%M")
        base_name = default.name or "item"
        
        if intent == "create_file":
            ext = default.extension
            return f"{base_name}_{timestamp}{ext}"
        
        return f"{base_name}_{timestamp}"
    
    def complete_command(self, command: dict) -> dict:
        """
        إكمال الأمر الناقص بذكاء.
        
        Returns:
            الأمر المُكمل
        """
        intent = command.get("intent", "")
        target = command.get("target")
        loc = command.get("loc")
        
        completed = command.copy()
        
        # إكمال الـ location
        if not loc or loc in ["", None, "?"]:
            inferred_loc = self.infer_location(intent, None)
            if inferred_loc:
                completed["loc"] = inferred_loc
                completed["_inferred_loc"] = True
        
        # إكمال الـ target
        if not target or target in ["", None, "?"]:
            inferred_name = self.infer_name(intent, None)
            if inferred_name:
                completed["target"] = inferred_name
                completed["_inferred_target"] = True
        
        # تسجيل للسياق
        self.set_last_action(intent, completed.get("loc"))
        
        return completed
    
    def format_inference(self, command: dict) -> str:
        """تنسيق ما تم استنتاجه"""
        parts = []
        
        if command.get("_inferred_loc"):
            parts.append(f"📍 الموقع: {command.get('loc')} (افتراضي)")
        
        if command.get("_inferred_target"):
            parts.append(f"📝 الاسم: {command.get('target')} (افتراضي)")
        
        return " | ".join(parts) if parts else ""


# ═══════════════════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════════════════

_world_model: Optional[WorldModel] = None

def get_world_model() -> WorldModel:
    global _world_model
    if _world_model is None:
        _world_model = WorldModel()
    return _world_model
