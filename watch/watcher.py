# watch/watcher.py
"""
👀 File Watcher - مراقبة الملفات
يرسل الأحداث للـ EventBus بدلاً من المعالجة المباشرة
"""
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from typing import Callable, Optional


class AgentWatcher(FileSystemEventHandler):
    def __init__(self, event_callback: Callable[[str, str], None]):
        self.callback = event_callback

    def on_created(self, event):
        if not event.is_directory:
            self.callback("created", event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self.callback("modified", event.src_path)

    def on_deleted(self, event):
        if not event.is_directory:
            self.callback("deleted", event.src_path)


class SystemMonitor:
    def __init__(self, path_to_watch: str, use_event_bus: bool = True):
        self.path = path_to_watch
        self.use_event_bus = use_event_bus
        self.observer: Optional[Observer] = None
        self.running = False
        self._custom_callback: Optional[Callable] = None

    def set_callback(self, callback: Callable[[str, str], None]):
        """تعيين callback مخصص (بديل عن EventBus)"""
        self._custom_callback = callback

    def _handle_event(self, event_type: str, path: str):
        """معالجة الحدث - إرساله للـ EventBus أو callback"""
        if self.use_event_bus:
            from core.event_bus import get_event_bus
            get_event_bus().push(event_type, path)
        elif self._custom_callback:
            self._custom_callback(event_type, path)
        else:
            print(f"🔔 [{event_type}]: {path}")

    def start(self):
        """بدء المراقبة"""
        if self.running:
            return
        
        event_handler = AgentWatcher(self._handle_event)
        self.observer = Observer()
        self.observer.schedule(event_handler, self.path, recursive=True)
        self.observer.start()
        self.running = True
        print(f"👀 Watcher started on: {self.path}")

    def stop(self):
        """إيقاف المراقبة"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.running = False
            print("🛑 Watcher stopped")


# للتوافق مع الكود القديم
class WatchHandler(FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback

    def on_created(self, event):
        self.callback(event)


def start_watch(path, callback):
    observer = Observer()
    handler = WatchHandler(callback)
    observer.schedule(handler, path, recursive=False)
    observer.start()
    return observer
