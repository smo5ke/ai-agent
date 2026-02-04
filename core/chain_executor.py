"""
🔗 Advanced Chain Executor - منفذ سلاسل الأوامر المتقدم
========================================================
دعم الأوامر المتسلسلة + الشروط (if/else) + الحلقات (for/repeat)

أمثلة:
1. "أنشئ مجلد X وداخله 5 ملفات"
2. "إذا كان المجلد موجود احذفه وإلا أنشئه"
3. "كرر 3 مرات: أنشئ ملف note_N"
"""

import re
import os
from typing import List, Dict, Optional, Callable, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class StepType(Enum):
    """نوع الخطوة"""
    ACTION = "action"        # أمر تنفيذي
    CONDITION = "condition"  # شرط if/else
    LOOP = "loop"           # حلقة
    VARIABLE = "variable"   # تعيين متغير


@dataclass
class ChainStep:
    """خطوة في السلسلة"""
    step_type: StepType
    intent: str = ""
    params: Dict = field(default_factory=dict)
    status: str = "pending"  # pending, running, done, failed, skipped
    result: str = ""
    depends_on: Optional[int] = None
    # للشروط
    condition: str = ""
    then_steps: List = field(default_factory=list)
    else_steps: List = field(default_factory=list)
    # للحلقات
    loop_count: int = 0
    loop_var: str = ""
    loop_steps: List = field(default_factory=list)


class ContextMemory:
    """ذاكرة السياق المتقدمة"""
    
    def __init__(self):
        self.current_folder: Optional[str] = None
        self.current_file: Optional[str] = None
        self.last_created: Optional[str] = None
        self.variables: Dict[str, Any] = {}
        self.loop_counter: int = 0
        self.results_history: List[Dict] = []
    
    def set_var(self, name: str, value: Any):
        """تعيين متغير"""
        self.variables[name] = value
    
    def get_var(self, name: str, default: Any = None) -> Any:
        """الحصول على متغير"""
        return self.variables.get(name, default)
    
    def update(self, intent: str, target: str, result: str):
        """تحديث السياق بعد تنفيذ خطوة"""
        if intent == "create_folder":
            self.current_folder = target
            self.last_created = target
        elif intent in ("create_file", "write_file"):
            self.current_file = target
            self.last_created = target
        
        # حفظ في التاريخ
        self.results_history.append({
            "intent": intent,
            "target": target,
            "result": result,
            "time": datetime.now().isoformat()
        })
    
    def resolve_template(self, text: str) -> str:
        """حل القوالب والمتغيرات في النص"""
        if not text:
            return text
        
        # حل المتغيرات {var_name}
        for var_name, var_value in self.variables.items():
            text = text.replace(f"{{{var_name}}}", str(var_value))
        
        # حل $N للحلقات
        text = text.replace("$N", str(self.loop_counter))
        text = text.replace("$n", str(self.loop_counter))
        text = text.replace("{i}", str(self.loop_counter))
        
        # حل المراجع
        text = text.replace("{current_folder}", self.current_folder or "")
        text = text.replace("{current_file}", self.current_file or "")
        text = text.replace("{last}", self.last_created or "")
        
        return text
    
    def reset(self):
        """إعادة تعيين السياق"""
        self.current_folder = None
        self.current_file = None
        self.last_created = None
        self.loop_counter = 0


class AdvancedChainExecutor:
    """منفذ سلاسل الأوامر المتقدم"""
    
    # كلمات الربط
    CONNECTORS = [
        "و", "ثم", "بعدها", "وبعدين", "ومن ثم",
        "and", "then", "after that", "next"
    ]
    
    # كلمات الشروط
    CONDITION_KEYWORDS = [
        "إذا", "لو", "if", "اذا",
        "وإلا", "والا", "else", "otherwise"
    ]
    
    # كلمات الحلقات
    LOOP_KEYWORDS = [
        "كرر", "repeat", "for", "loop",
        "مرات", "مرة", "times"
    ]
    
    def __init__(self):
        self.context = ContextMemory()
        self.steps: List[ChainStep] = []
        self.current_step = 0
        self._callbacks: List[Callable] = []
    
    def add_callback(self, callback: Callable):
        """إضافة callback للإشعارات"""
        self._callbacks.append(callback)
    
    def _notify(self, message: str, level: str = "info"):
        """إرسال إشعار"""
        for callback in self._callbacks:
            try:
                callback(message, level)
            except:
                pass
    
    # ═══════════════════════════════════════════════════════════
    # كشف نوع الأمر
    # ═══════════════════════════════════════════════════════════
    
    def is_chain_command(self, text: str) -> bool:
        """هل الأمر يحتوي على سلسلة/شرط/حلقة؟"""
        text_lower = text.lower()
        
        # كشف الحلقات
        if self._is_loop_command(text):
            return True
        
        # كشف الشروط
        if self._is_condition_command(text):
            return True
        
        # كشف السلسلة العادية
        return any(conn in text_lower for conn in self.CONNECTORS)
    
    def _is_loop_command(self, text: str) -> bool:
        """هل يحتوي على حلقة؟"""
        text_lower = text.lower()
        # "كرر X مرات" أو "أنشئ X ملفات"
        patterns = [
            r"كرر\s*(\d+)",
            r"(\d+)\s*مرات?",
            r"repeat\s*(\d+)",
            r"(\d+)\s*times",
            r"أنشئ\s*(\d+)\s*(ملفات?|مجلدات?)",
            r"create\s*(\d+)\s*(files?|folders?)",
        ]
        return any(re.search(p, text_lower) for p in patterns)
    
    def _is_condition_command(self, text: str) -> bool:
        """هل يحتوي على شرط؟"""
        text_lower = text.lower()
        return any(kw in text_lower for kw in ["إذا", "لو", "if", "اذا"])
    
    # ═══════════════════════════════════════════════════════════
    # تحليل الأوامر
    # ═══════════════════════════════════════════════════════════
    
    def parse_chain(self, text: str) -> List[Dict]:
        """تحليل النص واستخراج الأوامر"""
        
        # 1. كشف الحلقات
        loop_match = self._parse_loop(text)
        if loop_match:
            return loop_match
        
        # 2. كشف الشروط
        condition_match = self._parse_condition(text)
        if condition_match:
            return condition_match
        
        # 3. سلسلة عادية
        return self._parse_simple_chain(text)
    
    def _parse_loop(self, text: str) -> Optional[List[Dict]]:
        """تحليل أمر الحلقة"""
        
        # Pattern: "أنشئ 5 ملفات باسم note"
        match = re.search(r"أنشئ\s*(\d+)\s*(ملفات?|مجلدات?)\s*(باسم|اسمها?|اسمه?)?\s*(\S+)?", text)
        if match:
            count = int(match.group(1))
            item_type = match.group(2)
            base_name = match.group(4) or "item"
            
            commands = []
            intent = "create_folder" if "مجلد" in item_type else "create_file"
            
            for i in range(1, count + 1):
                name = f"{base_name}_{i}" if "$" not in base_name else base_name.replace("$N", str(i))
                commands.append({
                    "intent": intent,
                    "target": name,
                    "loc": "desktop",
                    "_loop_index": i
                })
            
            return commands
        
        # Pattern: "كرر 3 مرات: أنشئ ملف"
        match = re.search(r"كرر\s*(\d+)\s*مرات?[:\s]+(.+)", text)
        if match:
            count = int(match.group(1))
            action_text = match.group(2)
            
            commands = []
            for i in range(1, count + 1):
                self.context.loop_counter = i
                sub_commands = self._parse_simple_chain(action_text)
                for cmd in sub_commands:
                    # حل القوالب
                    if "target" in cmd:
                        cmd["target"] = self.context.resolve_template(cmd["target"])
                    cmd["_loop_index"] = i
                    commands.append(cmd)
            
            return commands
        
        # English: "create 5 files named test"
        match = re.search(r"create\s*(\d+)\s*(files?|folders?)\s*(named|called)?\s*(\S+)?", text, re.IGNORECASE)
        if match:
            count = int(match.group(1))
            item_type = match.group(2)
            base_name = match.group(4) or "item"
            
            commands = []
            intent = "create_folder" if "folder" in item_type.lower() else "create_file"
            
            for i in range(1, count + 1):
                commands.append({
                    "intent": intent,
                    "target": f"{base_name}_{i}",
                    "loc": "desktop",
                    "_loop_index": i
                })
            
            return commands
        
        return None
    
    def _parse_condition(self, text: str) -> Optional[List[Dict]]:
        """تحليل أمر شرطي"""
        
        # Pattern: "إذا كان المجلد X موجود احذفه وإلا أنشئه"
        # معقد جداً للتحليل الكامل - نستخدم نسخة مبسطة
        
        match = re.search(r"إذا\s+(كان\s+)?(.+?)\s+(موجود|exists?)\s+(.+?)\s+(وإلا|والا|else)\s+(.+)", text, re.IGNORECASE)
        if match:
            target = match.group(2).strip()
            then_action = match.group(4).strip()
            else_action = match.group(6).strip()
            
            # فحص إذا كان موجود
            return [{
                "intent": "_condition",
                "condition": "exists",
                "target": target,
                "then": self._parse_action(then_action, target),
                "else": self._parse_action(else_action, target)
            }]
        
        return None
    
    def _parse_action(self, text: str, context_target: str = None) -> Dict:
        """تحليل فعل واحد"""
        text_lower = text.lower()
        
        if any(kw in text_lower for kw in ["احذف", "امسح", "delete"]):
            return {"intent": "delete", "target": context_target or ""}
        elif any(kw in text_lower for kw in ["أنشئ", "انشئ", "create"]):
            return {"intent": "create_folder", "target": context_target or ""}
        
        return {"intent": "unknown"}
    
    def _parse_simple_chain(self, text: str) -> List[Dict]:
        """تحليل سلسلة بسيطة"""
        # استخدام الكود القديم
        pattern = "|".join([re.escape(c) for c in self.CONNECTORS])
        parts = re.split(pattern, text, flags=re.IGNORECASE)
        
        commands = []
        for part in parts:
            part = part.strip()
            if part:
                cmd = self._parse_single_command(part)
                if cmd:
                    commands.append(cmd)
        
        return commands
    
    def _parse_single_command(self, text: str) -> Optional[Dict]:
        """تحليل أمر واحد"""
        text_lower = text.lower()
        
        # create_folder
        if any(kw in text_lower for kw in ["أنشئ مجلد", "انشئ مجلد", "أنشئ فولدر", "create folder"]):
            name = self._extract_word_after(text, ["مجلد", "folder"])
            return {
                "intent": "create_folder",
                "target": name or "untitled",
                "loc": self._extract_location(text) or "desktop"
            }
        
        # create_file
        if any(kw in text_lower for kw in ["أنشئ ملف", "انشئ ملف", "create file", "ملف نصي", "داخله ملف"]):
            name = self._extract_word_after(text, ["ملف", "file"])
            if name in ["نصي", "نصى"]:
                name = "note.txt"
            return {
                "intent": "create_file",
                "target": name or "untitled.txt",
                "loc": self._extract_location(text) or self.context.current_folder or "desktop"
            }
        
        # write_file
        if any(kw in text_lower for kw in ["اكتب", "كتابة", "write"]):
            content = self._extract_after(text, ["اكتب", "write"])
            return {
                "intent": "write_file",
                "target": self.context.current_file or "untitled.txt",
                "param": content or "",
                "loc": self.context.current_folder or "desktop"
            }
        
        # delete
        if any(kw in text_lower for kw in ["احذف", "حذف", "delete"]):
            target = self._extract_after(text, ["احذف", "حذف", "delete"])
            return {
                "intent": "delete",
                "target": target,
                "loc": self._extract_location(text) or "desktop"
            }
        
        return None
    
    def _extract_word_after(self, text: str, keywords: List[str]) -> Optional[str]:
        """استخراج كلمة واحدة بعد الكلمة المفتاحية"""
        for kw in keywords:
            if kw in text.lower():
                idx = text.lower().find(kw) + len(kw)
                rest = text[idx:].strip()
                skip_words = ["اسمه", "باسم", "على", "في", "من", "اسمها"]
                words = rest.split()
                for word in words:
                    clean = word.strip("،,.")
                    if clean and clean not in skip_words and len(clean) > 1:
                        return clean
        return None
    
    def _extract_after(self, text: str, keywords: List[str]) -> Optional[str]:
        """استخراج النص بعد كلمة مفتاحية"""
        for kw in keywords:
            if kw in text.lower():
                idx = text.lower().find(kw) + len(kw)
                return text[idx:].strip()
        return None
    
    def _extract_location(self, text: str) -> Optional[str]:
        """استخراج الموقع"""
        locations = {
            "سطح المكتب": "desktop",
            "desktop": "desktop",
            "التنزيلات": "downloads",
            "downloads": "downloads",
            "المستندات": "documents",
            "documents": "documents",
        }
        
        text_lower = text.lower()
        for loc_name, loc_value in locations.items():
            if loc_name in text_lower:
                return loc_value
        
        return None
    
    # ═══════════════════════════════════════════════════════════
    # التنفيذ
    # ═══════════════════════════════════════════════════════════
    
    def execute_chain(self, commands: List[Dict], executor_func: Callable) -> List[Dict]:
        """تنفيذ سلسلة الأوامر"""
        results = []
        
        for i, cmd in enumerate(commands):
            # التعامل مع الشروط
            if cmd.get("intent") == "_condition":
                result = self._execute_condition(cmd, executor_func)
                results.append(result)
                continue
            
            # حل القوالب
            cmd = self._resolve_command_templates(cmd)
            
            # تحديث الموقع من السياق
            if cmd.get("loc") == "داخله" and self.context.current_folder:
                cmd["loc"] = self.context.current_folder
            
            # تنفيذ
            try:
                loop_info = f" (#{cmd.get('_loop_index', '')})" if "_loop_index" in cmd else ""
                self._notify(f"⚙️ تنفيذ: {cmd.get('intent')} {cmd.get('target')}{loop_info}", "thought")
                
                result = executor_func(cmd)
                results.append({
                    "step": i + 1,
                    "intent": cmd.get("intent"),
                    "target": cmd.get("target"),
                    "success": True,
                    "result": result
                })
                
                # تحديث السياق
                self.context.update(
                    cmd.get("intent", ""),
                    cmd.get("target", ""),
                    result
                )
                
            except Exception as e:
                results.append({
                    "step": i + 1,
                    "intent": cmd.get("intent"),
                    "success": False,
                    "error": str(e)
                })
                # لا نتوقف عند الخطأ في الحلقات
                if "_loop_index" not in cmd:
                    break
        
        return results
    
    def _execute_condition(self, cmd: Dict, executor_func: Callable) -> Dict:
        """تنفيذ شرط"""
        target = cmd.get("target", "")
        condition = cmd.get("condition", "")
        
        # فحص الشرط
        condition_result = False
        
        if condition == "exists":
            # فحص إذا كان الملف/المجلد موجود
            from actions.file_ops import resolve_path
            path = resolve_path(target, "desktop")
            condition_result = os.path.exists(path)
        
        # تنفيذ الفرع المناسب
        if condition_result:
            action = cmd.get("then", {})
            branch = "then"
        else:
            action = cmd.get("else", {})
            branch = "else"
        
        try:
            result = executor_func(action)
            return {
                "intent": "_condition",
                "condition": condition,
                "target": target,
                "branch": branch,
                "success": True,
                "result": result
            }
        except Exception as e:
            return {
                "intent": "_condition",
                "success": False,
                "error": str(e)
            }
    
    def _resolve_command_templates(self, cmd: Dict) -> Dict:
        """حل القوالب في الأمر"""
        resolved = cmd.copy()
        
        for key in ["target", "param", "loc"]:
            if key in resolved and isinstance(resolved[key], str):
                resolved[key] = self.context.resolve_template(resolved[key])
        
        return resolved
    
    def format_results(self, results: List[Dict]) -> str:
        """تنسيق النتائج للعرض"""
        lines = [f"📋 نتائج السلسلة ({len(results)} خطوة):"]
        
        for r in results:
            step = r.get("step", "?")
            if r.get("success"):
                target = r.get("target", "")
                lines.append(f"  {step}️⃣ ✅ {r.get('result', '')}")
            else:
                lines.append(f"  {step}️⃣ ❌ {r.get('error', 'خطأ')}")
        
        return "\n".join(lines)


# Singleton
_advanced_executor: Optional[AdvancedChainExecutor] = None

def get_advanced_chain_executor() -> AdvancedChainExecutor:
    global _advanced_executor
    if _advanced_executor is None:
        _advanced_executor = AdvancedChainExecutor()
    return _advanced_executor


# للتوافق مع الكود القديم
def get_chain_executor():
    return get_advanced_chain_executor()
