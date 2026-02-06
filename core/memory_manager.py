# core/memory_manager.py
"""
🧠 Memory Manager - الذاكرة الذكية
يحفظ التفضيلات والحقائق في knowledge_base.json
"""
import json
from pathlib import Path
from typing import Any, Optional
from datetime import datetime


class MemoryManager:
    def __init__(self, memory_file: str = "knowledge_base.json"):
        self.memory_file = Path(memory_file)
        self.data = {
            "preferences": {},
            "facts": [],
            "history": []
        }
        self._load()

    def _load(self):
        """تحميل الذاكرة من الملف"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                print(f"🧠 Memory loaded from {self.memory_file}")
            except Exception as e:
                print(f"⚠️ Failed to load memory: {e}")

    def _save(self):
        """حفظ الذاكرة للملف"""
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    # ===== التفضيلات =====
    
    def set_preference(self, key: str, value: Any):
        """حفظ تفضيل"""
        self.data["preferences"][key] = value
        self._save()
        print(f"💾 Preference saved: {key} = {value}")

    def get_preference(self, key: str, default: Any = None) -> Any:
        """جلب تفضيل"""
        return self.data["preferences"].get(key, default)

    # ===== الحقائق =====
    
    def store(self, fact: str):
        """حفظ حقيقة جديدة"""
        if fact not in self.data["facts"]:
            self.data["facts"].append(fact)
            self._save()
            print(f"📝 Fact stored: {fact}")

    def retrieve(self, query: str) -> list[str]:
        """البحث عن حقائق ذات صلة"""
        query_lower = query.lower()
        results = [
            fact for fact in self.data["facts"]
            if any(word in fact.lower() for word in query_lower.split())
        ]
        return results

    def get_all_facts(self) -> list[str]:
        """جلب كل الحقائق"""
        return self.data["facts"]

    # ===== السجل =====
    
    def log_action(self, action: str, details: dict = None):
        """تسجيل عملية في السجل"""
        entry = {
            "time": datetime.now().isoformat(),
            "action": action,
            "details": details or {}
        }
        self.data["history"].append(entry)
        
        # الاحتفاظ بآخر 100 عملية فقط
        if len(self.data["history"]) > 100:
            self.data["history"] = self.data["history"][-100:]
        
        self._save()

    # ===== السياق للـ LLM =====
    
    def get_context_for_llm(self, query: str = "") -> str:
        """تجهيز سياق للـ LLM"""
        context_parts = []
        
        # التفضيلات
        if self.data["preferences"]:
            prefs = ", ".join(f"{k}: {v}" for k, v in self.data["preferences"].items())
            context_parts.append(f"User preferences: {prefs}")
        
        # الحقائق ذات الصلة
        if query:
            relevant = self.retrieve(query)
            if relevant:
                context_parts.append(f"Relevant facts: {'; '.join(relevant)}")
        
        # آخر 3 عمليات
        recent = self.data["history"][-3:] if self.data["history"] else []
        if recent:
            actions = [h["action"] for h in recent]
            context_parts.append(f"Recent actions: {', '.join(actions)}")
        
        return "\n".join(context_parts) if context_parts else ""


# Singleton instance
_memory: Optional[MemoryManager] = None

def get_memory() -> MemoryManager:
    global _memory
    if _memory is None:
        _memory = MemoryManager()
    return _memory
