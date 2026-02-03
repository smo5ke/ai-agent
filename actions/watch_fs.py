import os
import shutil
import winreg
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

class FileSystemManager:
    def __init__(self):
        self.observer = Observer()
        self.watched_paths = []
        # هنا سنحتاج لتمرير "callback" لإبلاغ الواجهة عند حدوث شيء
        self.callback = None 

    def get_real_path(self, name):
        """نفس دالة جلب المسار من الريجستري"""
        name = name.lower() if name else "desktop"
        key_map = {
            "desktop": "Desktop", "سطح المكتب": "Desktop",
            "downloads": "{374DE290-123F-4565-9164-39C4925E467B}", "التنزيلات": "{374DE290-123F-4565-9164-39C4925E467B}",
            "documents": "Personal", "المستندات": "Personal"
        }
        if name in key_map:
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders")
                path, _ = winreg.QueryValueEx(key, key_map[name])
                return os.path.expandvars(path)
            except: pass
        return os.path.join(os.path.expanduser("~"), "Desktop")

    def clean_folder(self, source, filter_key, dest_name="Documents"):
        src = self.get_real_path(source)
        dest = os.path.join(self.get_real_path(dest_name), "Cleaned")
        os.makedirs(dest, exist_ok=True)
        
        count = 0
        if os.path.exists(src):
            for item in os.listdir(src):
                if filter_key and filter_key not in item: continue
                try:
                    shutil.move(os.path.join(src, item), os.path.join(dest, item))
                    count += 1
                except: pass
        return f"تم نقل {count} ملفات."

    def start_watch(self, folder, filter_key, action_type, ui_callback):
        self.callback = ui_callback
        path = self.get_real_path(folder)
        
        event_handler = Handler(self.callback, filter_key, action_type)
        self.observer.schedule(event_handler, path, recursive=False)
        if not self.observer.is_alive():
            self.observer.start()
        
        return f"تم تفعيل المراقبة على {path}"

class Handler(FileSystemEventHandler):
    def __init__(self, callback, filter_key, action_type):
        self.callback = callback
        self.filter = filter_key
        self.action = action_type
        self.last_event = 0

    def on_created(self, event):
        if event.is_directory: return
        if time.time() - self.last_event < 2: return # Debounce
        self.last_event = time.time()

        filename = os.path.basename(event.src_path)
        
        if self.filter and self.filter not in filename: return
        
        if self.callback:
            self.callback(f"تم رصد ملف: {filename}", "warning")
            # هنا يمكن إضافة منطق النقل الآلي إذا كان action == move