"""
🗄️ Database - قاعدة البيانات
=============================
SQLite database للذاكرة طويلة المدى.
"""

import sqlite3
import os
import time
from typing import List, Dict, Optional
from contextlib import contextmanager

# مسار قاعدة البيانات
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "jarvis.db")


def get_db_path() -> str:
    """جلب مسار قاعدة البيانات"""
    return DB_PATH


@contextmanager
def get_connection():
    """Context manager للاتصال بقاعدة البيانات"""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # للوصول للأعمدة بالاسم
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def init_database():
    """تهيئة قاعدة البيانات وإنشاء الجداول"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # جدول المحادثات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                user_text TEXT NOT NULL,
                ai_response TEXT,
                intent TEXT,
                success INTEGER DEFAULT 1
            )
        """)
        
        # جدول أحداث النظام
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                event_type TEXT NOT NULL,
                details TEXT,
                target TEXT
            )
        """)
        
        # جدول إحصائيات التطبيقات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_name TEXT UNIQUE NOT NULL,
                open_count INTEGER DEFAULT 1,
                last_used REAL NOT NULL
            )
        """)
        
        # جدول المهام المجدولة
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
        
        # فهارس للبحث السريع
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conv_timestamp ON conversations(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conv_intent ON conversations(intent)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_name ON app_usage(app_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_run_at ON scheduled_tasks(run_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON scheduled_tasks(status)")
        
        print(f"✅ Database initialized: {DB_PATH}")


# ═══════════════════════════════════════════════════════════
# دوال المحادثات
# ═══════════════════════════════════════════════════════════

def save_conversation(user_text: str, ai_response: dict, intent: str = None):
    """حفظ محادثة"""
    import json
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO conversations (timestamp, user_text, ai_response, intent)
            VALUES (?, ?, ?, ?)
        """, (
            time.time(),
            user_text,
            json.dumps(ai_response, ensure_ascii=False) if isinstance(ai_response, dict) else str(ai_response),
            intent
        ))


def search_conversations(query: str, limit: int = 10) -> List[Dict]:
    """بحث في المحادثات"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM conversations 
            WHERE user_text LIKE ? OR ai_response LIKE ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", limit))
        return [dict(row) for row in cursor.fetchall()]


def get_recent_conversations(limit: int = 10) -> List[Dict]:
    """جلب آخر المحادثات"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM conversations 
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]


def get_conversations_by_intent(intent: str, limit: int = 20) -> List[Dict]:
    """جلب المحادثات حسب النية"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM conversations 
            WHERE intent = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (intent, limit))
        return [dict(row) for row in cursor.fetchall()]


# ═══════════════════════════════════════════════════════════
# دوال الأحداث
# ═══════════════════════════════════════════════════════════

def save_event(event_type: str, details: str, target: str = None):
    """حفظ حدث"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO events (timestamp, event_type, details, target)
            VALUES (?, ?, ?, ?)
        """, (time.time(), event_type, details, target))


def get_recent_events(limit: int = 20) -> List[Dict]:
    """جلب آخر الأحداث"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM events 
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]


def get_events_by_type(event_type: str, limit: int = 20) -> List[Dict]:
    """جلب الأحداث حسب النوع"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM events 
            WHERE event_type = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (event_type, limit))
        return [dict(row) for row in cursor.fetchall()]


# ═══════════════════════════════════════════════════════════
# دوال إحصائيات التطبيقات
# ═══════════════════════════════════════════════════════════

def track_app_usage(app_name: str):
    """تتبع استخدام تطبيق"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO app_usage (app_name, open_count, last_used)
            VALUES (?, 1, ?)
            ON CONFLICT(app_name) DO UPDATE SET 
                open_count = open_count + 1,
                last_used = ?
        """, (app_name.lower(), time.time(), time.time()))


def get_most_used_apps(limit: int = 10) -> List[Dict]:
    """جلب أكثر التطبيقات استخداماً"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT app_name, open_count, last_used
            FROM app_usage 
            ORDER BY open_count DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]


def get_recent_apps(limit: int = 10) -> List[Dict]:
    """جلب آخر التطبيقات المستخدمة"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT app_name, open_count, last_used
            FROM app_usage 
            ORDER BY last_used DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]


# ═══════════════════════════════════════════════════════════
# إحصائيات عامة
# ═══════════════════════════════════════════════════════════

def get_stats() -> Dict:
    """جلب إحصائيات عامة"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # عدد المحادثات
        cursor.execute("SELECT COUNT(*) FROM conversations")
        total_conversations = cursor.fetchone()[0]
        
        # عدد الأحداث
        cursor.execute("SELECT COUNT(*) FROM events")
        total_events = cursor.fetchone()[0]
        
        # عدد التطبيقات المستخدمة
        cursor.execute("SELECT COUNT(*) FROM app_usage")
        total_apps = cursor.fetchone()[0]
        
        # أكثر intent استخداماً
        cursor.execute("""
            SELECT intent, COUNT(*) as count 
            FROM conversations 
            WHERE intent IS NOT NULL
            GROUP BY intent 
            ORDER BY count DESC 
            LIMIT 5
        """)
        top_intents = [dict(row) for row in cursor.fetchall()]
        
        return {
            "total_conversations": total_conversations,
            "total_events": total_events,
            "total_apps_used": total_apps,
            "top_intents": top_intents
        }


# تهيئة تلقائية عند الاستيراد
init_database()
