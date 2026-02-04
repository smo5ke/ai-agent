"""
🆔 Command Registry - سجل الأوامر
==================================
توليد Command ID فريد وتسجيل الأوامر.

Format: CMD-YYYYMMDD-XXXX
Example: CMD-20260204-8F3A
"""

import uuid
import threading
from datetime import datetime
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, field
from enum import Enum


class CommandStatus(Enum):
    """حالة الأمر"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ROLLED_BACK = "rolled_back"


@dataclass
class CommandRecord:
    """سجل الأمر"""
    command_id: str
    raw_input: str
    intent: str = ""
    params: Dict = field(default_factory=dict)
    status: CommandStatus = CommandStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None
    nodes_count: int = 0
    rollback_available: bool = False


class CommandRegistry:
    """
    سجل الأوامر المركزي.
    
    يُولّد Command ID فريد لكل أمر ويتتبع حالته.
    """
    
    def __init__(self, max_history: int = 1000):
        self._registry: Dict[str, CommandRecord] = {}
        self._lock = threading.Lock()
        self._max_history = max_history
        self._counter = 0
    
    # ═══════════════════════════════════════════════════════════
    # توليد Command ID
    # ═══════════════════════════════════════════════════════════
    
    def generate_id(self) -> str:
        """توليد Command ID فريد"""
        with self._lock:
            self._counter += 1
            date_part = datetime.now().strftime("%Y%m%d")
            unique_part = uuid.uuid4().hex[:4].upper()
            return f"CMD-{date_part}-{unique_part}"
    
    # ═══════════════════════════════════════════════════════════
    # تسجيل الأوامر
    # ═══════════════════════════════════════════════════════════
    
    def register(self, raw_input: str, intent: str = "", params: Dict = None) -> str:
        """تسجيل أمر جديد"""
        command_id = self.generate_id()
        
        record = CommandRecord(
            command_id=command_id,
            raw_input=raw_input,
            intent=intent,
            params=params or {}
        )
        
        with self._lock:
            self._registry[command_id] = record
            self._cleanup_old()
        
        return command_id
    
    def _cleanup_old(self):
        """حذف السجلات القديمة"""
        if len(self._registry) > self._max_history:
            # حذف أقدم 100 سجل
            sorted_ids = sorted(
                self._registry.keys(),
                key=lambda x: self._registry[x].created_at
            )
            for old_id in sorted_ids[:100]:
                del self._registry[old_id]
    
    # ═══════════════════════════════════════════════════════════
    # تحديث الحالة
    # ═══════════════════════════════════════════════════════════
    
    def update_status(self, command_id: str, status: CommandStatus, 
                      result: Any = None, error: str = None):
        """تحديث حالة الأمر"""
        with self._lock:
            if command_id in self._registry:
                record = self._registry[command_id]
                record.status = status
                
                if status in (CommandStatus.COMPLETED, CommandStatus.FAILED):
                    record.completed_at = datetime.now()
                
                if result is not None:
                    record.result = result
                if error:
                    record.error = error
    
    def set_intent(self, command_id: str, intent: str, params: Dict = None):
        """تعيين intent و params"""
        with self._lock:
            if command_id in self._registry:
                record = self._registry[command_id]
                record.intent = intent
                if params:
                    record.params = params
    
    def set_nodes_count(self, command_id: str, count: int):
        """تعيين عدد الـ nodes"""
        with self._lock:
            if command_id in self._registry:
                self._registry[command_id].nodes_count = count
    
    def set_rollback_available(self, command_id: str, available: bool = True):
        """تعيين قابلية الـ rollback"""
        with self._lock:
            if command_id in self._registry:
                self._registry[command_id].rollback_available = available
    
    # ═══════════════════════════════════════════════════════════
    # استعلام
    # ═══════════════════════════════════════════════════════════
    
    def get(self, command_id: str) -> Optional[CommandRecord]:
        """الحصول على سجل أمر"""
        return self._registry.get(command_id)
    
    def get_recent(self, count: int = 10) -> List[CommandRecord]:
        """الحصول على آخر N أوامر"""
        sorted_records = sorted(
            self._registry.values(),
            key=lambda x: x.created_at,
            reverse=True
        )
        return sorted_records[:count]
    
    def get_by_status(self, status: CommandStatus) -> List[CommandRecord]:
        """الحصول على الأوامر حسب الحالة"""
        return [r for r in self._registry.values() if r.status == status]
    
    def get_rollbackable(self) -> List[CommandRecord]:
        """الحصول على الأوامر القابلة للـ rollback"""
        return [
            r for r in self._registry.values() 
            if r.rollback_available and r.status == CommandStatus.COMPLETED
        ]
    
    # ═══════════════════════════════════════════════════════════
    # إحصائيات
    # ═══════════════════════════════════════════════════════════
    
    def get_stats(self) -> Dict:
        """إحصائيات السجل"""
        total = len(self._registry)
        by_status = {}
        
        for record in self._registry.values():
            status = record.status.value
            by_status[status] = by_status.get(status, 0) + 1
        
        return {
            "total": total,
            "by_status": by_status,
            "rollbackable": len(self.get_rollbackable())
        }
    
    def format_record(self, record: CommandRecord) -> str:
        """تنسيق السجل للعرض"""
        status_icons = {
            CommandStatus.PENDING: "⏳",
            CommandStatus.PROCESSING: "⚙️",
            CommandStatus.COMPLETED: "✅",
            CommandStatus.FAILED: "❌",
            CommandStatus.CANCELLED: "🚫",
            CommandStatus.ROLLED_BACK: "↩️"
        }
        
        icon = status_icons.get(record.status, "❓")
        time_str = record.created_at.strftime("%H:%M:%S")
        
        return f"{icon} [{record.command_id}] {time_str} - {record.intent or record.raw_input[:30]}"


# ═══════════════════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════════════════

_registry: Optional[CommandRegistry] = None

def get_command_registry() -> CommandRegistry:
    global _registry
    if _registry is None:
        _registry = CommandRegistry()
    return _registry
