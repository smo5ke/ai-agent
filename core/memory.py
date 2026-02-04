"""
🧠 Memory - الذاكرة
====================
نظام الذاكرة مع دعم SQLite للتخزين طويل المدى.
"""

import time
from datetime import datetime
from typing import List, Dict, Optional
from core import database as db

# استيراد التشفير
try:
    from core.encryption import encrypt, decrypt
    ENCRYPTION_ENABLED = True
except ImportError:
    ENCRYPTION_ENABLED = False
    encrypt = lambda x: x
    decrypt = lambda x: x


class Memory:
    def __init__(self):
        # ذاكرة RAM للجلسة الحالية (سريعة)
        self.session_history = []
        self.session_events = []
        
        # تأكيد تهيئة قاعدة البيانات
        db.init_database()
        
        if ENCRYPTION_ENABLED:
            print("🔐 تشفير البيانات مفعّل")
    
    # ═══════════════════════════════════════════════════════════
    # المحادثات
    # ═══════════════════════════════════════════════════════════

    def add_interaction(self, user_text: str, ai_response: dict):
        """حفظ محادثة في RAM و SQLite (مع تشفير)"""
        timestamp = time.time()
        intent = ai_response.get("intent") if isinstance(ai_response, dict) else None
        
        # حفظ في RAM للوصول السريع (بدون تشفير)
        entry = {
            "timestamp": timestamp,
            "user": user_text,
            "ai": ai_response
        }
        self.session_history.append(entry)
        
        # حد أقصى 50 في RAM
        if len(self.session_history) > 50:
            self.session_history.pop(0)
        
        # تشفير النص قبل الحفظ
        encrypted_text = encrypt(user_text)
        
        # حفظ في SQLite للتخزين الدائم
        try:
            db.save_conversation(encrypted_text, ai_response, intent)
        except Exception as e:
            print(f"⚠️ Database save error: {e}")

    def get_recent_context(self, count: int = 5) -> List[Dict]:
        """جلب آخر الأوامر من الجلسة الحالية"""
        return self.session_history[-count:]

    def search_history(self, query: str, limit: int = 10) -> List[Dict]:
        """بحث في المحادثات المحفوظة"""
        return db.search_conversations(query, limit)

    def get_history_by_intent(self, intent: str, limit: int = 20) -> List[Dict]:
        """جلب المحادثات حسب النية"""
        return db.get_conversations_by_intent(intent, limit)

    def get_all_history(self, limit: int = 100) -> List[Dict]:
        """جلب كل المحادثات من قاعدة البيانات"""
        return db.get_recent_conversations(limit)

    # ═══════════════════════════════════════════════════════════
    # أحداث النظام
    # ═══════════════════════════════════════════════════════════

    def add_system_event(self, event_type: str, details: str, target: str = None):
        """حفظ حدث نظام"""
        entry = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "type": event_type,
            "details": details
        }
        self.session_events.append(entry)
        
        # حفظ في SQLite
        try:
            db.save_event(event_type, details, target)
            
            # تتبع استخدام التطبيقات
            if event_type == "open" and target:
                db.track_app_usage(target)
        except Exception as e:
            print(f"⚠️ Event save error: {e}")

    def get_recent_events(self, limit: int = 20) -> List[Dict]:
        """جلب آخر الأحداث"""
        return db.get_recent_events(limit)

    def get_events_by_type(self, event_type: str, limit: int = 20) -> List[Dict]:
        """جلب الأحداث حسب النوع"""
        return db.get_events_by_type(event_type, limit)

    # ═══════════════════════════════════════════════════════════
    # إحصائيات التطبيقات
    # ═══════════════════════════════════════════════════════════

    def track_app(self, app_name: str):
        """تتبع استخدام تطبيق"""
        db.track_app_usage(app_name)

    def get_most_used_apps(self, limit: int = 10) -> List[Dict]:
        """أكثر التطبيقات استخداماً"""
        return db.get_most_used_apps(limit)

    def get_recent_apps(self, limit: int = 10) -> List[Dict]:
        """آخر التطبيقات المستخدمة"""
        return db.get_recent_apps(limit)

    # ═══════════════════════════════════════════════════════════
    # إحصائيات عامة
    # ═══════════════════════════════════════════════════════════

    def get_stats(self) -> Dict:
        """جلب إحصائيات عامة"""
        stats = db.get_stats()
        stats["session_commands"] = len(self.session_history)
        stats["session_events"] = len(self.session_events)
        return stats

    def get_context_for_llm(self, count: int = 5) -> str:
        """
        تجهيز سياق للـ LLM من آخر المحادثات.
        يمكن استخدامه لتحسين فهم السياق.
        """
        recent = self.get_recent_context(count)
        if not recent:
            return ""
        
        context_lines = []
        for item in recent:
            user_text = item.get("user", "")
            ai_resp = item.get("ai", {})
            intent = ai_resp.get("intent", "unknown") if isinstance(ai_resp, dict) else "unknown"
            context_lines.append(f"User: {user_text} -> Intent: {intent}")
        
        return "\n".join(context_lines)