"""
🔍 Condition Pre-processor - معالج الشروط
==========================================
يفحص الشروط قبل إرسال الأمر للـ LLM.

مثال:
"إذا كان مجلد X ليس موجود أنشئ ملف Y"
↓
1. كشف الشرط: exists/not_exists
2. فحص الحالة الفعلية
3. إرجاع الأمر المناسب
"""

import re
import os
from typing import Optional, Tuple, Dict
from dataclasses import dataclass


@dataclass
class ConditionResult:
    """نتيجة تحليل الشرط"""
    has_condition: bool = False
    condition_type: str = ""      # exists, not_exists
    target: str = ""              # المجلد/الملف المستهدف
    target_location: str = ""     # الموقع (desktop, downloads)
    then_command: str = ""        # الأمر إذا تحقق الشرط
    else_command: str = ""        # الأمر إذا لم يتحقق
    condition_met: bool = False   # هل تحقق الشرط؟
    final_command: str = ""       # الأمر النهائي للـ LLM


class ConditionPreprocessor:
    """معالج الشروط قبل الـ LLM"""
    
    # ترجمة المواقع
    LOCATIONS = {
        "سطح المكتب": "desktop",
        "desktop": "desktop",
        "التنزيلات": "downloads",
        "downloads": "downloads",
        "المستندات": "documents",
        "documents": "documents",
    }
    
    def __init__(self):
        self.desktop_path = self._get_desktop_path()
    
    def _get_desktop_path(self) -> str:
        """الحصول على مسار سطح المكتب"""
        # OneDrive Desktop
        onedrive = os.path.expanduser("~/OneDrive/سطح المكتب")
        if os.path.exists(onedrive):
            return onedrive
        
        # Desktop العادي
        return os.path.expanduser("~/Desktop")
    
    def _resolve_path(self, target: str, location: str) -> str:
        """تحويل الاسم لمسار كامل"""
        base_paths = {
            "desktop": self.desktop_path,
            "downloads": os.path.expanduser("~/Downloads"),
            "documents": os.path.expanduser("~/Documents"),
        }
        
        base = base_paths.get(location, self.desktop_path)
        return os.path.join(base, target)
    
    # ═══════════════════════════════════════════════════════════
    # كشف وتحليل الشروط
    # ═══════════════════════════════════════════════════════════
    
    def process(self, text: str) -> ConditionResult:
        """معالجة النص واستخراج الشرط"""
        result = ConditionResult()
        
        # كشف إذا كان هناك شرط
        if not self._has_condition(text):
            result.has_condition = False
            result.final_command = text
            return result
        
        result.has_condition = True
        
        # تحليل الشرط
        parsed = self._parse_condition(text)
        if not parsed:
            result.final_command = text
            return result
        
        result.condition_type = parsed["type"]
        result.target = parsed["target"]
        result.target_location = parsed["location"]
        result.then_command = parsed["then"]
        result.else_command = parsed.get("else", "")
        
        # فحص الحالة الفعلية
        path = self._resolve_path(result.target, result.target_location)
        exists = os.path.exists(path)
        
        # تحديد إذا تحقق الشرط
        if result.condition_type == "exists":
            result.condition_met = exists
        elif result.condition_type == "not_exists":
            result.condition_met = not exists
        
        # تحديد الأمر النهائي
        if result.condition_met:
            result.final_command = result.then_command
        elif result.else_command:
            result.final_command = result.else_command
        else:
            result.final_command = ""  # لا شيء للتنفيذ
        
        return result
    
    def _has_condition(self, text: str) -> bool:
        """هل النص يحتوي على شرط؟"""
        keywords = ["إذا", "اذا", "لو", "if"]
        return any(kw in text.lower() for kw in keywords)
    
    def _parse_condition(self, text: str) -> Optional[Dict]:
        """تحليل الشرط واستخراج مكوناته"""
        
        # === Pattern 1: إذا كان مجلد X ليس موجود ===
        # إذا كان مجلد تجربة ليس موجود على سطح المكتب انشء ملف a.txt
        pattern1 = r"(?:إذا|اذا|لو)\s+(?:كان\s+)?(مجلد|ملف|folder|file)\s+(\S+)\s+(?:ليس\s+)?(?:غير\s+)?(?:موجود|مش\s+موجود|not\s+exist)"
        match = re.search(pattern1, text, re.IGNORECASE)
        
        if match:
            item_type = match.group(1)
            target = match.group(2)
            
            # البحث عن الموقع
            location = "desktop"
            for loc_ar, loc_en in self.LOCATIONS.items():
                if loc_ar in text.lower():
                    location = loc_en
                    break
            
            # استخراج الأمر (ما بعد الشرط والموقع)
            # Pattern: موجود على سطح المكتب [أمر] أو موجود [أمر]
            action_match = re.search(
                r"(?:موجود|exist)[s]?\s+(?:على\s+سطح\s+المكتب\s+)?(.+)", 
                text, 
                re.IGNORECASE
            )
            then_command = ""
            if action_match:
                then_command = action_match.group(1).strip()
                # حذف الموقع من الأمر إذا وجد
                then_command = re.sub(r"^على\s+سطح\s+المكتب\s+", "", then_command)
                
                # استبدال المراجع مثل "داخل المجلد" باسم المجلد الفعلي
                then_command = re.sub(r"داخل\s+المجلد", f"داخل مجلد {target}", then_command)
                then_command = re.sub(r"داخله", f"داخل مجلد {target}", then_command)
                then_command = re.sub(r"فيه", f"في مجلد {target}", then_command)
            
            # تحديد نوع الشرط
            is_negated = any(kw in text for kw in ["ليس", "غير", "مش", "not"])
            condition_type = "not_exists" if is_negated else "exists"
            
            return {
                "type": condition_type,
                "target": target,
                "location": location,
                "then": then_command,
                "else": ""
            }
        
        # === Pattern 2: إذا كان X موجود احذفه وإلا أنشئه ===
        pattern2 = r"(?:إذا|اذا|لو)\s+(?:كان\s+)?(مجلد|ملف)?\s*(\S+)\s+موجود\s+(.+?)\s+(?:وإلا|والا|else)\s+(.+)"
        match = re.search(pattern2, text, re.IGNORECASE)
        
        if match:
            target = match.group(2)
            then_action = match.group(3).strip()
            else_action = match.group(4).strip()
            
            return {
                "type": "exists",
                "target": target,
                "location": "desktop",
                "then": then_action,
                "else": else_action
            }
        
        # === Pattern 3: if folder X exists ===
        pattern3 = r"if\s+(?:folder|file)?\s*(\S+)\s+(?:does\s+)?(?:not\s+)?exists?\s+(.+)"
        match = re.search(pattern3, text, re.IGNORECASE)
        
        if match:
            target = match.group(1)
            then_command = match.group(2)
            is_negated = "not" in text.lower()
            
            return {
                "type": "not_exists" if is_negated else "exists",
                "target": target,
                "location": "desktop",
                "then": then_command,
                "else": ""
            }
        
        return None
    
    def get_status_message(self, result: ConditionResult) -> str:
        """رسالة توضيحية للمستخدم"""
        if not result.has_condition:
            return ""
        
        target = result.target
        exists_text = "موجود ✅" if result.condition_met else "غير موجود ❌"
        
        if result.condition_type == "not_exists":
            # الشرط معكوس
            check = "ليس موجود"
        else:
            check = "موجود"
        
        if result.condition_met:
            action = f"→ سيتم تنفيذ: {result.then_command}"
        elif result.else_command:
            action = f"→ سيتم تنفيذ: {result.else_command}"
        else:
            action = "→ لن يتم تنفيذ شيء"
        
        return f"🔍 فحص: {target} ({exists_text})\n{action}"


# Singleton
_preprocessor: Optional[ConditionPreprocessor] = None

def get_condition_preprocessor() -> ConditionPreprocessor:
    global _preprocessor
    if _preprocessor is None:
        _preprocessor = ConditionPreprocessor()
    return _preprocessor
