import time
from datetime import datetime

class Memory:
    def __init__(self):
        self.history = [] # سجل المحادثات
        self.events = []  # سجل أحداث النظام (نقل ملف، فتح برنامج)

    def add_interaction(self, user_text, ai_response):
        """حفظ المحادثة"""
        entry = {
            "timestamp": time.time(),
            "user": user_text,
            "ai": ai_response
        }
        self.history.append(entry)
        # نحتفظ بآخر 50 محادثة فقط لتوفير الرام
        if len(self.history) > 50:
            self.history.pop(0)

    def add_system_event(self, event_type, details):
        """حفظ ما فعله النظام"""
        entry = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "type": event_type,
            "details": details
        }
        self.events.append(entry)

    def get_recent_context(self):
        """جلب آخر الأوامر ليفهم السياق (مستقبلاً)"""
        return self.history[-5:]