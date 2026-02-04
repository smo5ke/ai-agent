"""
🧠 Brain - الدماغ
==================
واجهة موحدة للتفكير. يستخدم IPC للتواصل مع LLM Worker المستقل.

التغيير الرئيسي:
- قبل: الموديل يعمل في نفس الـ Process
- الآن: الموديل في Worker منفصل عبر TCP Socket
"""

import json
from core.schemas import Command
from llm import ipc


class Brain:
    def __init__(self, model_path=None):
        """
        Args:
            model_path: لم يعد مستخدماً (للتوافق فقط)
                       الموديل يُحمّل في worker_process.py
        """
        self.model_path = model_path
        self._worker_available = False
    
    def load(self) -> bool:
        """
        فحص توفر الـ Worker بدلاً من تحميل الموديل.
        """
        print("🧠 Checking LLM Worker connection...")
        
        if ipc.is_worker_available():
            print("✅ LLM Worker is connected!")
            self._worker_available = True
            return True
        else:
            print("⚠️ LLM Worker not available!")
            print("💡 Start it with: python llm/worker_process.py")
            self._worker_available = False
            return False
    
    def think(self, user_input: str, app_context: str):
        """
        إرسال الطلب للـ Worker عبر IPC.
        
        Args:
            user_input: ما كتبه المستخدم
            app_context: قائمة التطبيقات المتاحة
            
        Returns:
            Command أو List[dict]: الأمر المحلل أو قائمة أوامر
        """
        
        # فحص سريع للاتصال
        if not ipc.is_worker_available():
            print("❌ LLM Worker disconnected!")
            return Command(intent="unknown")
        
        # إرسال للـ Worker
        result = ipc.think(
            prompt=user_input,
            app_context=app_context,
            timeout=30
        )
        
        # معالجة النتيجة
        if result.get("success"):
            try:
                data = result.get("response")
                
                # إذا كانت قائمة أوامر
                if isinstance(data, list):
                    return data  # إرجاع القائمة كما هي
                
                # إذا كان كائن واحد
                return Command(**data)
                
            except Exception as e:
                print(f"⚠️ Command parsing error: {e}")
                return Command(intent="unknown")
        else:
            error = result.get("error", "Unknown error")
            print(f"⚠️ LLM Error: {error}")
            return Command(intent="unknown")
    
    def is_ready(self) -> bool:
        """فحص جاهزية الـ Worker"""
        return ipc.is_worker_available()