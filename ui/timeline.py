"""
📊 Execution Timeline - واجهة التنفيذ المرئية
=============================================
تُظهر لك ما يحدث داخل Jarvis في الوقت الحقيقي.

Components:
- TimelineEvent: حدث واحد
- TimelineRenderer: يرسم الـ timeline
- TimelinePanel: Tkinter widget
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading


# ═══════════════════════════════════════════════════════════
# 🎨 Timeline Status & Colors
# ═══════════════════════════════════════════════════════════

class TimelineStatus(Enum):
    """حالة الحدث"""
    PENDING = "pending"       # ⏳ في الانتظار
    RUNNING = "running"       # ▶️ قيد التنفيذ
    COMPLETED = "completed"   # ✅ مكتمل
    FAILED = "failed"         # ❌ فشل
    PAUSED = "paused"         # ⏸ متوقف
    CANCELLED = "cancelled"   # ⛔ ملغي
    ROLLED_BACK = "rolled_back"  # ↩️ تم التراجع


STATUS_COLORS = {
    TimelineStatus.PENDING: "#6B7280",      # رمادي
    TimelineStatus.RUNNING: "#3B82F6",      # أزرق
    TimelineStatus.COMPLETED: "#10B981",    # أخضر
    TimelineStatus.FAILED: "#EF4444",       # أحمر
    TimelineStatus.PAUSED: "#F59E0B",       # برتقالي
    TimelineStatus.CANCELLED: "#6B7280",    # رمادي
    TimelineStatus.ROLLED_BACK: "#8B5CF6",  # بنفسجي
}

STATUS_ICONS = {
    TimelineStatus.PENDING: "⏳",
    TimelineStatus.RUNNING: "▶️",
    TimelineStatus.COMPLETED: "✅",
    TimelineStatus.FAILED: "❌",
    TimelineStatus.PAUSED: "⏸",
    TimelineStatus.CANCELLED: "⛔",
    TimelineStatus.ROLLED_BACK: "↩️",
}


# ═══════════════════════════════════════════════════════════
# 📝 Timeline Event
# ═══════════════════════════════════════════════════════════

@dataclass
class TimelineEvent:
    """حدث في الـ timeline"""
    id: str
    title: str
    status: TimelineStatus = TimelineStatus.PENDING
    timestamp: str = ""
    duration_ms: int = 0
    details: str = ""
    progress: float = 0.0  # 0-1
    children: List['TimelineEvent'] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().strftime("%H:%M:%S")
    
    @property
    def icon(self) -> str:
        return STATUS_ICONS.get(self.status, "•")
    
    @property
    def color(self) -> str:
        return STATUS_COLORS.get(self.status, "#6B7280")
    
    def update_status(self, status: TimelineStatus):
        """تحديث الحالة"""
        self.status = status
        if status in [TimelineStatus.COMPLETED, TimelineStatus.FAILED]:
            self.progress = 1.0
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status.value,
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms,
            "details": self.details,
            "progress": self.progress
        }


# ═══════════════════════════════════════════════════════════
# 📊 Timeline Manager
# ═══════════════════════════════════════════════════════════

class TimelineManager:
    """
    مدير الـ Timeline.
    
    يتتبع أحداث التنفيذ ويُبلغ الـ UI.
    """
    
    def __init__(self):
        self.events: Dict[str, TimelineEvent] = {}
        self.root_events: List[str] = []  # IDs of root events
        self._listeners: List[Callable] = []
        self._lock = threading.Lock()
    
    def add_event(self, event: TimelineEvent, parent_id: str = None):
        """إضافة حدث"""
        with self._lock:
            self.events[event.id] = event
            if parent_id and parent_id in self.events:
                self.events[parent_id].children.append(event)
            else:
                self.root_events.append(event.id)
        self._notify_listeners()
    
    def update_event(self, event_id: str, 
                     status: TimelineStatus = None,
                     progress: float = None,
                     details: str = None):
        """تحديث حدث"""
        with self._lock:
            if event_id in self.events:
                event = self.events[event_id]
                if status:
                    event.update_status(status)
                if progress is not None:
                    event.progress = progress
                if details:
                    event.details = details
        self._notify_listeners()
    
    def get_event(self, event_id: str) -> Optional[TimelineEvent]:
        """جلب حدث"""
        return self.events.get(event_id)
    
    def get_all_events(self) -> List[TimelineEvent]:
        """جلب كل الأحداث بالترتيب"""
        result = []
        for event_id in self.root_events:
            if event_id in self.events:
                result.append(self.events[event_id])
        return result
    
    def clear(self):
        """مسح كل الأحداث"""
        with self._lock:
            self.events.clear()
            self.root_events.clear()
        self._notify_listeners()
    
    def add_listener(self, callback: Callable):
        """إضافة مستمع للتغييرات"""
        self._listeners.append(callback)
    
    def _notify_listeners(self):
        """إبلاغ المستمعين"""
        for callback in self._listeners:
            try:
                callback()
            except:
                pass
    
    # ═══════════════════════════════════════════════════════════
    # Helpers للتنفيذ
    # ═══════════════════════════════════════════════════════════
    
    def start_command(self, cmd_id: str, title: str) -> TimelineEvent:
        """بدء أمر جديد"""
        event = TimelineEvent(
            id=cmd_id,
            title=title,
            status=TimelineStatus.RUNNING
        )
        self.add_event(event)
        return event
    
    def add_step(self, cmd_id: str, step_id: str, title: str) -> TimelineEvent:
        """إضافة خطوة لأمر"""
        step = TimelineEvent(
            id=step_id,
            title=title,
            status=TimelineStatus.PENDING
        )
        self.add_event(step, parent_id=cmd_id)
        return step
    
    def complete_step(self, step_id: str, success: bool = True):
        """إكمال خطوة"""
        status = TimelineStatus.COMPLETED if success else TimelineStatus.FAILED
        self.update_event(step_id, status=status)
    
    def complete_command(self, cmd_id: str, success: bool = True):
        """إكمال أمر"""
        status = TimelineStatus.COMPLETED if success else TimelineStatus.FAILED
        self.update_event(cmd_id, status=status)


# ═══════════════════════════════════════════════════════════
# 🎨 Timeline Panel (Tkinter)
# ═══════════════════════════════════════════════════════════

class TimelinePanel(tk.Frame):
    """
    لوحة Timeline في Tkinter.
    
    تعرض الأحداث بشكل مرئي.
    """
    
    def __init__(self, parent, manager: TimelineManager = None):
        super().__init__(parent, bg="#1F2937")
        
        self.manager = manager or TimelineManager()
        self.manager.add_listener(self._on_update)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """إعداد الواجهة"""
        # Header
        header = tk.Frame(self, bg="#111827")
        header.pack(fill="x", padx=5, pady=5)
        
        tk.Label(
            header, 
            text="📊 Execution Timeline", 
            font=("Segoe UI", 12, "bold"),
            bg="#111827", fg="white"
        ).pack(side="left", padx=10)
        
        # Controls
        controls = tk.Frame(header, bg="#111827")
        controls.pack(side="right", padx=10)
        
        self.pause_btn = tk.Button(
            controls, text="⏸", width=3, 
            command=self._on_pause,
            bg="#374151", fg="white", relief="flat"
        )
        self.pause_btn.pack(side="left", padx=2)
        
        self.cancel_btn = tk.Button(
            controls, text="⛔", width=3,
            command=self._on_cancel,
            bg="#374151", fg="white", relief="flat"
        )
        self.cancel_btn.pack(side="left", padx=2)
        
        self.clear_btn = tk.Button(
            controls, text="🗑️", width=3,
            command=self._on_clear,
            bg="#374151", fg="white", relief="flat"
        )
        self.clear_btn.pack(side="left", padx=2)
        
        # Timeline area (scrollable)
        container = tk.Frame(self, bg="#1F2937")
        container.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.canvas = tk.Canvas(container, bg="#1F2937", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        
        self.timeline_frame = tk.Frame(self.canvas, bg="#1F2937")
        
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.timeline_frame, anchor="nw"
        )
        
        self.timeline_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        # Initial render
        self._render_timeline()
    
    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)
    
    def _render_timeline(self):
        """رسم الـ Timeline"""
        # Clear existing
        for widget in self.timeline_frame.winfo_children():
            widget.destroy()
        
        events = self.manager.get_all_events()
        
        if not events:
            tk.Label(
                self.timeline_frame,
                text="No events yet...",
                font=("Segoe UI", 10),
                bg="#1F2937", fg="#6B7280"
            ).pack(pady=20)
            return
        
        for event in events:
            self._render_event(event)
    
    def _render_event(self, event: TimelineEvent, indent: int = 0):
        """رسم حدث واحد"""
        frame = tk.Frame(self.timeline_frame, bg="#1F2937")
        frame.pack(fill="x", padx=(10 + indent * 20, 10), pady=3)
        
        # Left side: icon + line
        left = tk.Frame(frame, bg="#1F2937", width=30)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        
        tk.Label(
            left, 
            text=event.icon, 
            font=("Segoe UI Emoji", 14),
            bg="#1F2937"
        ).pack()
        
        # Main content
        content = tk.Frame(frame, bg="#374151", relief="flat")
        content.pack(side="left", fill="x", expand=True, padx=5)
        
        # Title row
        title_row = tk.Frame(content, bg="#374151")
        title_row.pack(fill="x", padx=10, pady=5)
        
        tk.Label(
            title_row,
            text=event.title,
            font=("Segoe UI", 10, "bold"),
            bg="#374151", fg="white"
        ).pack(side="left")
        
        tk.Label(
            title_row,
            text=event.timestamp,
            font=("Segoe UI", 8),
            bg="#374151", fg="#9CA3AF"
        ).pack(side="right")
        
        # Progress bar (if running)
        if event.status == TimelineStatus.RUNNING:
            progress_frame = tk.Frame(content, bg="#374151")
            progress_frame.pack(fill="x", padx=10, pady=(0, 5))
            
            progress_bg = tk.Frame(progress_frame, bg="#4B5563", height=4)
            progress_bg.pack(fill="x")
            
            progress_fill = tk.Frame(progress_bg, bg=event.color, height=4)
            progress_fill.place(relwidth=event.progress, relheight=1)
        
        # Details (if any)
        if event.details:
            tk.Label(
                content,
                text=event.details,
                font=("Segoe UI", 9),
                bg="#374151", fg="#9CA3AF",
                wraplength=300, justify="left"
            ).pack(fill="x", padx=10, pady=(0, 5))
        
        # Children
        for child in event.children:
            self._render_event(child, indent + 1)
    
    def _on_update(self):
        """عند تحديث الـ timeline"""
        # Schedule on main thread
        self.after(0, self._render_timeline)
    
    def _on_pause(self):
        """إيقاف مؤقت"""
        for event in self.manager.get_all_events():
            if event.status == TimelineStatus.RUNNING:
                self.manager.update_event(event.id, status=TimelineStatus.PAUSED)
    
    def _on_cancel(self):
        """إلغاء"""
        for event in self.manager.get_all_events():
            if event.status in [TimelineStatus.RUNNING, TimelineStatus.PAUSED]:
                self.manager.update_event(event.id, status=TimelineStatus.CANCELLED)
    
    def _on_clear(self):
        """مسح"""
        self.manager.clear()


# ═══════════════════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════════════════

_timeline_manager: Optional[TimelineManager] = None

def get_timeline_manager() -> TimelineManager:
    global _timeline_manager
    if _timeline_manager is None:
        _timeline_manager = TimelineManager()
    return _timeline_manager


# ═══════════════════════════════════════════════════════════
# Demo
# ═══════════════════════════════════════════════════════════

def demo():
    """عرض توضيحي"""
    root = tk.Tk()
    root.title("Jarvis Timeline")
    root.geometry("400x500")
    root.configure(bg="#1F2937")
    
    manager = get_timeline_manager()
    panel = TimelinePanel(root, manager)
    panel.pack(fill="both", expand=True)
    
    # Add demo events
    def add_demo_events():
        import time
        
        cmd = manager.start_command("CMD-001", "أنشئ مجلد test")
        time.sleep(0.5)
        
        step1 = manager.add_step("CMD-001", "step-1", "تحليل الأمر")
        manager.update_event("step-1", status=TimelineStatus.RUNNING)
        time.sleep(0.3)
        manager.complete_step("step-1")
        
        step2 = manager.add_step("CMD-001", "step-2", "فحص السياسات")
        manager.update_event("step-2", status=TimelineStatus.RUNNING)
        time.sleep(0.3)
        manager.complete_step("step-2")
        
        step3 = manager.add_step("CMD-001", "step-3", "تنفيذ الأمر")
        manager.update_event("step-3", status=TimelineStatus.RUNNING)
        time.sleep(0.5)
        manager.complete_step("step-3")
        
        manager.complete_command("CMD-001")
    
    threading.Thread(target=add_demo_events, daemon=True).start()
    
    root.mainloop()


if __name__ == "__main__":
    demo()
