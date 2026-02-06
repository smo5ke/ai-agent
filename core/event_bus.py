# core/event_bus.py
"""
🔔 Event Bus - الحلقة التفاعلية
يفصل بين سرعة النظام وبطء الـ LLM مع Debouncing
"""
import queue
import threading
import time
from typing import Callable, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Event:
    """حدث في النظام"""
    event_type: str      # created, modified, deleted
    path: str            # مسار الملف
    timestamp: float     # وقت الحدث
    source: str = "watcher"  # مصدر الحدث


class EventBus:
    def __init__(self, debounce_seconds: float = 1.0):
        self.queue: queue.Queue[Event] = queue.Queue()
        self.debounce_seconds = debounce_seconds
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.callback: Optional[Callable[[Event], None]] = None
        
        # للـ Debouncing: آخر حدث لكل مسار
        self._last_events: dict[str, Event] = {}
        self._lock = threading.Lock()

    def set_callback(self, callback: Callable[[Event], None]):
        """تعيين الدالة التي تُستدعى عند حدث مستقر"""
        self.callback = callback

    def push(self, event_type: str, path: str):
        """إضافة حدث للطابور"""
        event = Event(
            event_type=event_type,
            path=path,
            timestamp=time.time()
        )
        
        with self._lock:
            # تخزين آخر حدث لهذا المسار (للـ Debouncing)
            self._last_events[path] = event
        
        self.queue.put(event)

    def start(self):
        """تشغيل الـ EventBus في Thread منفصل"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._process_loop, daemon=True)
        self.thread.start()
        print("🔔 EventBus started")

    def stop(self):
        """إيقاف الـ EventBus"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        print("🔔 EventBus stopped")

    def _process_loop(self):
        """الحلقة الرئيسية للمعالجة"""
        processed_paths: set[str] = set()
        
        while self.running:
            try:
                # انتظار حدث مع timeout
                event = self.queue.get(timeout=0.5)
                
                # انتظار Debounce
                time.sleep(self.debounce_seconds)
                
                with self._lock:
                    # تحقق إذا هذا هو آخر حدث لهذا المسار
                    last_event = self._last_events.get(event.path)
                    
                    if last_event and last_event.timestamp == event.timestamp:
                        # هذا هو آخر حدث، نعالجه
                        if self.callback and event.path not in processed_paths:
                            try:
                                self.callback(last_event)
                                processed_paths.add(event.path)
                                
                                # نمسح بعد فترة
                                threading.Timer(
                                    5.0, 
                                    lambda p=event.path: processed_paths.discard(p)
                                ).start()
                            except Exception as e:
                                print(f"⚠️ EventBus callback error: {e}")
                        
                        # حذف من القائمة
                        del self._last_events[event.path]
                
                self.queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"⚠️ EventBus error: {e}")


# Singleton instance
_event_bus: Optional[EventBus] = None

def get_event_bus() -> EventBus:
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus
