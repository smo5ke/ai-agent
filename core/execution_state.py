"""
🎯 Execution State Machine - حالة التنفيذ
==========================================
تتبع حالة كل أمر في الوقت الحقيقي.

States:
INIT → POLICY_CHECK → GRAPH_BUILT → NODE_RUNNING → COMPLETED/FAILED/ROLLED_BACK
"""

import threading
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum


class ExecutionState(Enum):
    """حالات التنفيذ"""
    INIT = "init"                    # تم تسجيل الأمر
    PARSING = "parsing"              # جاري التحليل بالـ LLM
    POLICY_CHECK = "policy_check"    # فحص السياسات
    POLICY_BLOCKED = "policy_blocked"  # تم الحظر
    GRAPH_BUILT = "graph_built"      # تم بناء الـ Graph
    NODE_RUNNING = "node_running"    # جاري تنفيذ Node
    NODE_DONE = "node_done"          # اكتمل Node
    PAUSED = "paused"                # متوقف مؤقتاً
    COMPLETED = "completed"          # اكتمل بنجاح
    FAILED = "failed"                # فشل
    CANCELLED = "cancelled"          # تم الإلغاء
    ROLLING_BACK = "rolling_back"    # جاري التراجع
    ROLLED_BACK = "rolled_back"      # تم التراجع


@dataclass
class TimelineEvent:
    """حدث في الـ Timeline"""
    timestamp: datetime
    state: ExecutionState
    message: str
    node_id: Optional[str] = None
    details: Dict = field(default_factory=dict)


@dataclass
class ExecutionStatus:
    """حالة التنفيذ الكاملة"""
    command_id: str
    state: ExecutionState
    current_node: Optional[str] = None
    nodes_total: int = 0
    nodes_completed: int = 0
    progress_percent: int = 0
    last_action: str = ""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    can_pause: bool = False
    can_cancel: bool = True
    can_rollback: bool = False
    timeline: List[TimelineEvent] = field(default_factory=list)


class ExecutionStateMachine:
    """
    State Machine لتتبع حالة التنفيذ.
    
    يوفر:
    - تتبع الحالة في الوقت الحقيقي
    - Timeline للأحداث
    - Control (Pause/Cancel/Rollback)
    """
    
    def __init__(self):
        self._states: Dict[str, ExecutionStatus] = {}
        self._lock = threading.Lock()
        self._subscribers: Dict[str, List[Callable]] = {}
        self._global_subscribers: List[Callable] = []
    
    # ═══════════════════════════════════════════════════════════
    # إنشاء وتحديث الحالة
    # ═══════════════════════════════════════════════════════════
    
    def init(self, command_id: str) -> ExecutionStatus:
        """تهيئة حالة جديدة"""
        status = ExecutionStatus(
            command_id=command_id,
            state=ExecutionState.INIT,
            started_at=datetime.now()
        )
        
        with self._lock:
            self._states[command_id] = status
        
        self._add_event(command_id, ExecutionState.INIT, "تم تسجيل الأمر")
        self._notify(command_id)
        
        return status
    
    def transition(
        self,
        command_id: str,
        new_state: ExecutionState,
        message: str = "",
        node_id: str = None,
        details: Dict = None
    ):
        """انتقال لحالة جديدة"""
        with self._lock:
            if command_id not in self._states:
                return
            
            status = self._states[command_id]
            old_state = status.state
            status.state = new_state
            status.last_action = message or new_state.value
            
            if node_id:
                status.current_node = node_id
            
            # تحديث الـ flags
            if new_state == ExecutionState.NODE_RUNNING:
                status.can_pause = True
            elif new_state in (ExecutionState.COMPLETED, ExecutionState.FAILED, 
                               ExecutionState.CANCELLED, ExecutionState.ROLLED_BACK):
                status.can_pause = False
                status.can_cancel = False
                status.completed_at = datetime.now()
            
            if new_state == ExecutionState.COMPLETED:
                status.can_rollback = True
                status.progress_percent = 100
        
        self._add_event(command_id, new_state, message, node_id, details or {})
        self._notify(command_id)
    
    def update_progress(self, command_id: str, completed: int, total: int, current_node: str = None):
        """تحديث التقدم"""
        with self._lock:
            if command_id not in self._states:
                return
            
            status = self._states[command_id]
            status.nodes_completed = completed
            status.nodes_total = total
            status.progress_percent = int((completed / total) * 100) if total > 0 else 0
            
            if current_node:
                status.current_node = current_node
        
        self._notify(command_id)
    
    def set_error(self, command_id: str, error: str):
        """تسجيل خطأ"""
        with self._lock:
            if command_id in self._states:
                self._states[command_id].error = error
        
        self.transition(command_id, ExecutionState.FAILED, f"خطأ: {error}")
    
    # ═══════════════════════════════════════════════════════════
    # Timeline
    # ═══════════════════════════════════════════════════════════
    
    def _add_event(
        self,
        command_id: str,
        state: ExecutionState,
        message: str,
        node_id: str = None,
        details: Dict = None
    ):
        """إضافة حدث للـ Timeline"""
        event = TimelineEvent(
            timestamp=datetime.now(),
            state=state,
            message=message,
            node_id=node_id,
            details=details or {}
        )
        
        with self._lock:
            if command_id in self._states:
                self._states[command_id].timeline.append(event)
    
    def get_timeline(self, command_id: str) -> List[TimelineEvent]:
        """الحصول على Timeline"""
        with self._lock:
            if command_id in self._states:
                return self._states[command_id].timeline.copy()
        return []
    
    # ═══════════════════════════════════════════════════════════
    # استعلام
    # ═══════════════════════════════════════════════════════════
    
    def get(self, command_id: str) -> Optional[ExecutionStatus]:
        """الحصول على حالة أمر"""
        return self._states.get(command_id)
    
    def get_active(self) -> List[ExecutionStatus]:
        """الحصول على الأوامر النشطة"""
        active_states = (
            ExecutionState.INIT,
            ExecutionState.PARSING,
            ExecutionState.POLICY_CHECK,
            ExecutionState.GRAPH_BUILT,
            ExecutionState.NODE_RUNNING,
            ExecutionState.PAUSED
        )
        return [s for s in self._states.values() if s.state in active_states]
    
    def get_json(self, command_id: str) -> Optional[Dict]:
        """الحصول على حالة كـ JSON"""
        status = self.get(command_id)
        if not status:
            return None
        
        return {
            "command_id": status.command_id,
            "state": status.state.value,
            "current_node": status.current_node,
            "progress": f"{status.nodes_completed}/{status.nodes_total}",
            "progress_percent": status.progress_percent,
            "last_action": status.last_action,
            "can_pause": status.can_pause,
            "can_cancel": status.can_cancel,
            "can_rollback": status.can_rollback,
            "error": status.error
        }
    
    # ═══════════════════════════════════════════════════════════
    # Control (Pause/Cancel/Rollback)
    # ═══════════════════════════════════════════════════════════
    
    def pause(self, command_id: str) -> bool:
        """إيقاف مؤقت"""
        status = self.get(command_id)
        if not status or not status.can_pause:
            return False
        
        self.transition(command_id, ExecutionState.PAUSED, "تم الإيقاف المؤقت")
        return True
    
    def resume(self, command_id: str) -> bool:
        """استئناف"""
        status = self.get(command_id)
        if not status or status.state != ExecutionState.PAUSED:
            return False
        
        self.transition(command_id, ExecutionState.NODE_RUNNING, "تم الاستئناف")
        return True
    
    def cancel(self, command_id: str) -> bool:
        """إلغاء"""
        status = self.get(command_id)
        if not status or not status.can_cancel:
            return False
        
        self.transition(command_id, ExecutionState.CANCELLED, "تم الإلغاء")
        return True
    
    def request_rollback(self, command_id: str) -> bool:
        """طلب Rollback"""
        status = self.get(command_id)
        if not status or not status.can_rollback:
            return False
        
        self.transition(command_id, ExecutionState.ROLLING_BACK, "جاري التراجع")
        return True
    
    def mark_rolled_back(self, command_id: str):
        """تأكيد Rollback"""
        self.transition(command_id, ExecutionState.ROLLED_BACK, "تم التراجع بنجاح")
    
    # ═══════════════════════════════════════════════════════════
    # Subscription (للـ UI)
    # ═══════════════════════════════════════════════════════════
    
    def subscribe(self, command_id: str, callback: Callable):
        """الاشتراك في تحديثات أمر معين"""
        if command_id not in self._subscribers:
            self._subscribers[command_id] = []
        self._subscribers[command_id].append(callback)
    
    def subscribe_all(self, callback: Callable):
        """الاشتراك في كل التحديثات"""
        self._global_subscribers.append(callback)
    
    def unsubscribe(self, command_id: str, callback: Callable):
        """إلغاء الاشتراك"""
        if command_id in self._subscribers:
            try:
                self._subscribers[command_id].remove(callback)
            except ValueError:
                pass
    
    def _notify(self, command_id: str):
        """إرسال إشعار للمشتركين"""
        status = self.get(command_id)
        if not status:
            return
        
        # المشتركين في هذا الأمر
        for callback in self._subscribers.get(command_id, []):
            try:
                callback(status)
            except Exception as e:
                print(f"Subscriber error: {e}")
        
        # المشتركين في كل الأوامر
        for callback in self._global_subscribers:
            try:
                callback(status)
            except Exception as e:
                print(f"Global subscriber error: {e}")
    
    # ═══════════════════════════════════════════════════════════
    # تنسيق للعرض
    # ═══════════════════════════════════════════════════════════
    
    def format_status(self, command_id: str) -> str:
        """تنسيق الحالة للعرض"""
        status = self.get(command_id)
        if not status:
            return f"❓ أمر غير موجود: {command_id}"
        
        state_icons = {
            ExecutionState.INIT: "🆕",
            ExecutionState.PARSING: "🤔",
            ExecutionState.POLICY_CHECK: "🔍",
            ExecutionState.POLICY_BLOCKED: "🚫",
            ExecutionState.GRAPH_BUILT: "📊",
            ExecutionState.NODE_RUNNING: "⚙️",
            ExecutionState.NODE_DONE: "✅",
            ExecutionState.PAUSED: "⏸️",
            ExecutionState.COMPLETED: "✅",
            ExecutionState.FAILED: "❌",
            ExecutionState.CANCELLED: "🚫",
            ExecutionState.ROLLING_BACK: "↩️",
            ExecutionState.ROLLED_BACK: "↩️"
        }
        
        icon = state_icons.get(status.state, "❓")
        progress = f"[{status.nodes_completed}/{status.nodes_total}]" if status.nodes_total > 0 else ""
        
        lines = [
            f"{icon} [{status.command_id}] {status.state.value.upper()}",
            f"   📊 Progress: {status.progress_percent}% {progress}",
        ]
        
        if status.current_node:
            lines.append(f"   🔄 Current: {status.current_node}")
        
        if status.last_action:
            lines.append(f"   📝 Action: {status.last_action}")
        
        if status.error:
            lines.append(f"   ❌ Error: {status.error}")
        
        return "\n".join(lines)
    
    def format_timeline(self, command_id: str) -> str:
        """تنسيق Timeline للعرض"""
        timeline = self.get_timeline(command_id)
        if not timeline:
            return "❓ لا يوجد timeline"
        
        lines = [f"📜 Timeline [{command_id}]"]
        for event in timeline:
            time_str = event.timestamp.strftime("%H:%M:%S")
            lines.append(f"  {time_str} | {event.state.value}: {event.message}")
        
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════════════════

_state_machine: Optional[ExecutionStateMachine] = None

def get_execution_state() -> ExecutionStateMachine:
    global _state_machine
    if _state_machine is None:
        _state_machine = ExecutionStateMachine()
    return _state_machine
