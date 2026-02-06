# core/execution_context.py
import json
from pathlib import Path
from datetime import datetime


class ExecutionContext:
    def __init__(self, base_path):
        self.base_path = Path(base_path).resolve()
        self.cwd = self.base_path
        self.vars = {}
        self.history = []
        self.event_log = []  # ذاكرة الأحداث

    def set_cwd(self, path):
        self.cwd = Path(path).resolve()
        self.history.append(f"cwd -> {self.cwd}")

    def log_event(self, message):
        """تسجيل حدث في الذاكرة"""
        event = {
            "time": datetime.now().isoformat(),
            "message": message
        }
        self.event_log.append(event)

    def save_memory(self, filename="memory_dump.json"):
        """حفظ الذاكرة في ملف"""
        data = {
            "base_path": str(self.base_path),
            "cwd": str(self.cwd),
            "history": self.history,
            "events": self.event_log
        }
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        # print(f"💾 Memory saved to {filename}")

    def get_summary(self):
        """ملخص السياق"""
        return {
            "base": str(self.base_path),
            "cwd": str(self.cwd),
            "actions_count": len(self.history),
            "events_count": len(self.event_log)
        }
