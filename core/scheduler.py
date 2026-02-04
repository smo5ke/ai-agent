"""
⏰ Scheduler - المهام المجدولة
==============================
نظام جدولة الأوامر للتنفيذ في وقت لاحق.
"""

import time
import threading
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Callable
import re

from core.database import get_connection


class Scheduler:
    """مدير المهام المجدولة"""
    
    def __init__(self):
        self._running = False
        self._thread = None
        self._executor = None  # دالة تنفيذ الأوامر
        self._ui_callback = None
        self._lock = threading.Lock()
        
        # تهيئة الجدول
        self._init_table()
    
    def _init_table(self):
        """تأكيد وجود جدول المهام"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scheduled_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_at REAL NOT NULL,
                    command TEXT NOT NULL,
                    command_data TEXT,
                    repeat TEXT DEFAULT 'once',
                    status TEXT DEFAULT 'pending',
                    created_at REAL NOT NULL,
                    executed_at REAL
                )
            """)
    
    def set_executor(self, executor: Callable):
        """تعيين دالة تنفيذ الأوامر"""
        self._executor = executor
    
    def set_ui_callback(self, callback: Callable):
        """تعيين callback للـ UI"""
        self._ui_callback = callback
    
    # ═══════════════════════════════════════════════════════════
    # إضافة المهام
    # ═══════════════════════════════════════════════════════════
    
    def add_task(
        self, 
        command: str, 
        run_at: float = None,
        delay_seconds: int = None,
        time_str: str = None,
        repeat: str = "once",
        command_data: dict = None
    ) -> int:
        """
        إضافة مهمة مجدولة.
        
        Args:
            command: الأمر للتنفيذ (open, reminder, etc.)
            run_at: Timestamp للتنفيذ
            delay_seconds: تأخير بالثواني (بديل عن run_at)
            time_str: وقت بصيغة "HH:MM" (بديل عن run_at)
            repeat: "once", "daily", "hourly"
            command_data: بيانات إضافية للأمر
            
        Returns:
            int: معرف المهمة
        """
        # حساب وقت التنفيذ
        if run_at is None:
            if delay_seconds:
                run_at = time.time() + delay_seconds
            elif time_str:
                run_at = self._parse_time_str(time_str)
            else:
                run_at = time.time() + 60  # افتراضي: دقيقة واحدة
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO scheduled_tasks 
                (run_at, command, command_data, repeat, status, created_at)
                VALUES (?, ?, ?, ?, 'pending', ?)
            """, (
                run_at,
                command,
                json.dumps(command_data, ensure_ascii=False) if command_data else None,
                repeat,
                time.time()
            ))
            task_id = cursor.lastrowid
        
        self._log(f"⏰ تمت جدولة مهمة #{task_id}: {command}")
        return task_id
    
    def add_reminder(self, message: str, delay_seconds: int) -> int:
        """إضافة تذكير"""
        return self.add_task(
            command="reminder",
            delay_seconds=delay_seconds,
            command_data={"message": message}
        )
    
    def schedule_app_open(self, app_name: str, time_str: str, repeat: str = "once") -> int:
        """جدولة فتح تطبيق"""
        return self.add_task(
            command="open",
            time_str=time_str,
            repeat=repeat,
            command_data={"target": app_name}
        )
    
    # ═══════════════════════════════════════════════════════════
    # إدارة المهام
    # ═══════════════════════════════════════════════════════════
    
    def cancel_task(self, task_id: int) -> bool:
        """إلغاء مهمة"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE scheduled_tasks 
                SET status = 'cancelled' 
                WHERE id = ? AND status = 'pending'
            """, (task_id,))
            success = cursor.rowcount > 0
        
        if success:
            self._log(f"🛑 تم إلغاء المهمة #{task_id}")
        return success
    
    def get_pending_tasks(self) -> List[Dict]:
        """جلب المهام المعلقة"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM scheduled_tasks 
                WHERE status = 'pending'
                ORDER BY run_at ASC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_tasks(self, limit: int = 50) -> List[Dict]:
        """جلب جميع المهام"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM scheduled_tasks 
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_tasks_for_ui(self) -> List[Dict]:
        """جلب المهام بصيغة مناسبة للعرض"""
        tasks = self.get_pending_tasks()
        result = []
        for task in tasks:
            run_time = datetime.fromtimestamp(task['run_at'])
            result.append({
                "id": task['id'],
                "command": task['command'],
                "time": run_time.strftime("%H:%M"),
                "date": run_time.strftime("%Y-%m-%d"),
                "repeat": task['repeat'],
                "remaining": self._format_remaining(task['run_at'])
            })
        return result
    
    # ═══════════════════════════════════════════════════════════
    # الحلقة الرئيسية
    # ═══════════════════════════════════════════════════════════
    
    def start(self):
        """بدء مراقبة المهام"""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        print("⏰ Scheduler started")
    
    def stop(self):
        """إيقاف المراقبة"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
    
    def _run_loop(self):
        """حلقة التحقق من المهام"""
        while self._running:
            try:
                self._check_and_execute()
            except Exception as e:
                print(f"Scheduler error: {e}")
            time.sleep(5)  # فحص كل 5 ثواني
    
    def _check_and_execute(self):
        """فحص وتنفيذ المهام المستحقة"""
        now = time.time()
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM scheduled_tasks 
                WHERE status = 'pending' AND run_at <= ?
            """, (now,))
            due_tasks = [dict(row) for row in cursor.fetchall()]
        
        for task in due_tasks:
            self._execute_task(task)
    
    def _execute_task(self, task: dict):
        """تنفيذ مهمة واحدة"""
        task_id = task['id']
        command = task['command']
        data = json.loads(task['command_data']) if task['command_data'] else {}
        repeat = task['repeat']
        
        try:
            # تنفيذ الأمر
            if command == "reminder":
                self._send_reminder(data.get('message', 'تذكير!'))
            elif command == "open" and self._executor:
                self._executor(f"افتح {data.get('target', '')}")
            elif self._executor:
                self._executor(command)
            
            self._log(f"✅ تم تنفيذ المهمة #{task_id}: {command}")
            
            # تحديث الحالة
            with get_connection() as conn:
                cursor = conn.cursor()
                
                if repeat == "once":
                    cursor.execute("""
                        UPDATE scheduled_tasks 
                        SET status = 'done', executed_at = ?
                        WHERE id = ?
                    """, (time.time(), task_id))
                else:
                    # جدولة التكرار
                    next_run = self._calculate_next_run(task['run_at'], repeat)
                    cursor.execute("""
                        UPDATE scheduled_tasks 
                        SET run_at = ?, executed_at = ?
                        WHERE id = ?
                    """, (next_run, time.time(), task_id))
                    
        except Exception as e:
            self._log(f"❌ فشل تنفيذ المهمة #{task_id}: {e}")
    
    def _send_reminder(self, message: str):
        """إرسال تذكير"""
        try:
            from core.notifications import notify
            notify("⏰ تذكير", message)
        except:
            pass
        
        if self._ui_callback:
            self._ui_callback(f"⏰ تذكير: {message}", "warning")
    
    # ═══════════════════════════════════════════════════════════
    # دوال مساعدة
    # ═══════════════════════════════════════════════════════════
    
    def _parse_time_str(self, time_str: str) -> float:
        """تحويل نص الوقت إلى timestamp"""
        now = datetime.now()
        
        # محاولة تحليل الوقت
        try:
            # صيغة HH:MM
            if ':' in time_str:
                parts = time_str.split(':')
                hour = int(parts[0])
                minute = int(parts[1]) if len(parts) > 1 else 0
                
                target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                # إذا كان الوقت قد مر، نجدوله لليوم التالي
                if target <= now:
                    target += timedelta(days=1)
                
                return target.timestamp()
        except:
            pass
        
        # افتراضي: بعد دقيقة
        return time.time() + 60
    
    def _calculate_next_run(self, last_run: float, repeat: str) -> float:
        """حساب وقت التنفيذ التالي"""
        if repeat == "hourly":
            return last_run + 3600
        elif repeat == "daily":
            return last_run + 86400
        elif repeat == "weekly":
            return last_run + 604800
        else:
            return last_run + 86400  # افتراضي: يومي
    
    def _format_remaining(self, run_at: float) -> str:
        """تنسيق الوقت المتبقي"""
        remaining = run_at - time.time()
        
        if remaining <= 0:
            return "الآن"
        elif remaining < 60:
            return f"{int(remaining)} ثانية"
        elif remaining < 3600:
            return f"{int(remaining / 60)} دقيقة"
        elif remaining < 86400:
            return f"{int(remaining / 3600)} ساعة"
        else:
            return f"{int(remaining / 86400)} يوم"
    
    def _log(self, message: str):
        """تسجيل رسالة"""
        print(message)
        if self._ui_callback:
            self._ui_callback(message, "info")


# ═══════════════════════════════════════════════════════════
# دوال تحليل الأوامر
# ═══════════════════════════════════════════════════════════

def parse_delay(text: str) -> Optional[int]:
    """
    تحليل التأخير من النص.
    مثال: "5 دقائق" -> 300
    """
    patterns = [
        (r'(\d+)\s*(ثانية|ثواني|sec|second)', 1),
        (r'(\d+)\s*(دقيقة|دقائق|min|minute)', 60),
        (r'(\d+)\s*(ساعة|ساعات|hour)', 3600),
    ]
    
    for pattern, multiplier in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1)) * multiplier
    
    return None


def parse_time(text: str) -> Optional[str]:
    """
    استخراج الوقت من النص.
    مثال: "الساعة 9" -> "09:00"
    """
    patterns = [
        r'(\d{1,2}):(\d{2})',  # 9:00
        r'(\d{1,2})\s*صباحا?',  # 9 صباحا
        r'(\d{1,2})\s*مساء?',  # 9 مساء
        r'الساعة\s*(\d{1,2})',  # الساعة 9
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            hour = int(match.group(1))
            if 'مساء' in text and hour < 12:
                hour += 12
            return f"{hour:02d}:00"
    
    return None


# Singleton
_scheduler = None

def get_scheduler() -> Scheduler:
    """جلب مدير الجدولة"""
    global _scheduler
    if _scheduler is None:
        _scheduler = Scheduler()
        _scheduler.start()
    return _scheduler
