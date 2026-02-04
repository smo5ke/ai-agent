"""
👁️ File System Manager + Watch Manager
=======================================
إدارة مراقبة المجلدات + تنظيف الملفات + فتح الملفات.
"""

import os
import shutil
import winreg
import uuid
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time


class FileSystemManager:
    def __init__(self):
        self.observer = Observer()
        self.callback = None
        
        # نظام تتبع المهام النشطة
        self.active_watches = {}  # {watch_id: {"path": ..., "handler": ..., "watch": ...}}
        self._lock = threading.Lock()
        
        # Callback لتحديث UI عند تغير المهام
        self.on_watches_changed = None

    def get_real_path(self, name):
        """جلب المسار الحقيقي من الريجستري"""
        name = name.lower() if name else "desktop"
        key_map = {
            "desktop": "Desktop", "سطح المكتب": "Desktop",
            "downloads": "{374DE290-123F-4565-9164-39C4925E467B}", "التنزيلات": "{374DE290-123F-4565-9164-39C4925E467B}",
            "documents": "Personal", "المستندات": "Personal",
            "pictures": "My Pictures", "الصور": "My Pictures"
        }
        if name in key_map:
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders")
                path, _ = winreg.QueryValueEx(key, key_map[name])
                return os.path.expandvars(path)
            except: pass
        return os.path.join(os.path.expanduser("~"), "Desktop")

    # ═══════════════════════════════════════════════════════════
    # إدارة المراقبة
    # ═══════════════════════════════════════════════════════════

    def start_watch(self, folder, filter_key, action_type, ui_callback, 
                     on_change_action=None, on_change_callback=None) -> str:
        """
        بدء مراقبة مجلد مع دعم on_change.
        
        Args:
            folder: اسم المجلد (desktop, downloads, etc)
            filter_key: فلتر اسم الملف (اختياري)
            action_type: نوع الإجراء
            ui_callback: callback لتحديث UI
            on_change_action: الأمر المراد تنفيذه عند التغيير (dict)
            on_change_callback: الدالة التي تنفذ الأمر
        
        Returns:
            str: رسالة التأكيد مع watch_id
        """
        self.callback = ui_callback
        path = self.get_real_path(folder)
        
        # إنشاء معرف فريد للمهمة
        watch_id = str(uuid.uuid4())[:8]
        
        # إنشاء المعالج مع دعم on_change
        event_handler = Handler(
            callback=self.callback, 
            filter_key=filter_key, 
            action_type=action_type, 
            watch_id=watch_id,
            on_change_callback=on_change_callback,
            on_change_action=on_change_action
        )
        
        # جدولة المراقبة
        watch = self.observer.schedule(event_handler, path, recursive=False)
        
        # بدء الـ Observer إذا لم يكن يعمل
        if not self.observer.is_alive():
            self.observer.start()
        
        # حفظ المهمة
        with self._lock:
            self.active_watches[watch_id] = {
                "path": path,
                "folder_name": folder,
                "filter": filter_key,
                "action": action_type,
                "handler": event_handler,
                "watch": watch,
                "started_at": time.strftime("%H:%M:%S"),
                "on_change_action": on_change_action  # 🆕 حفظ الأمر
            }
        
        # إبلاغ UI
        self._notify_watches_changed()
        
        # رسالة مع تفاصيل on_change
        msg = f"تم تفعيل المراقبة على {path} (ID: {watch_id})"
        if on_change_action:
            msg += f"\n   ⚡ on_change: {on_change_action.get('intent')} → {on_change_action.get('target')}"
        
        return msg

    def stop_watch(self, watch_id: str) -> str:
        """إيقاف مهمة مراقبة محددة"""
        with self._lock:
            if watch_id not in self.active_watches:
                return f"مهمة المراقبة {watch_id} غير موجودة"
            
            watch_info = self.active_watches[watch_id]
            
            # إلغاء جدولة المراقبة
            try:
                self.observer.unschedule(watch_info["watch"])
            except Exception as e:
                print(f"Error unscheduling: {e}")
            
            # حذف من القائمة
            del self.active_watches[watch_id]
        
        # إبلاغ UI
        self._notify_watches_changed()
        
        return f"تم إيقاف المراقبة: {watch_info.get('folder_name', watch_id)}"

    def stop_all_watches(self) -> str:
        """إيقاف جميع المهام"""
        with self._lock:
            for watch_id, watch_info in list(self.active_watches.items()):
                try:
                    self.observer.unschedule(watch_info["watch"])
                except: pass
            self.active_watches.clear()
        
        self._notify_watches_changed()
        return "تم إيقاف جميع مهام المراقبة"

    def get_active_watches(self) -> list:
        """جلب قائمة المهام النشطة"""
        with self._lock:
            return [
                {
                    "id": watch_id,
                    "path": info["path"],
                    "folder": info.get("folder_name", "Unknown"),
                    "filter": info.get("filter"),
                    "started_at": info.get("started_at", "")
                }
                for watch_id, info in self.active_watches.items()
            ]

    def _notify_watches_changed(self):
        """إبلاغ UI بتغير المهام"""
        if self.on_watches_changed:
            self.on_watches_changed(self.get_active_watches())

    # ═══════════════════════════════════════════════════════════
    # تنظيف الملفات
    # ═══════════════════════════════════════════════════════════

    def clean_folder(self, source, filter_key, dest_name="Documents"):
        """نقل الملفات من مجلد لآخر"""
        src = self.get_real_path(source)
        dest = os.path.join(self.get_real_path(dest_name), "Cleaned")
        os.makedirs(dest, exist_ok=True)
        
        count = 0
        if os.path.exists(src):
            for item in os.listdir(src):
                if filter_key and filter_key.lower() not in item.lower(): 
                    continue
                try:
                    shutil.move(os.path.join(src, item), os.path.join(dest, item))
                    count += 1
                except: pass
        return f"تم نقل {count} ملفات."

    # ═══════════════════════════════════════════════════════════
    # فتح الملفات
    # ═══════════════════════════════════════════════════════════

    def open_file(self, filename: str, folder: str = "desktop") -> str:
        """فتح ملف من مجلد معين"""
        path = self.get_real_path(folder)
        
        if not os.path.exists(path):
            return f"المجلد غير موجود: {path}"
        
        # البحث عن الملف
        matches = []
        for item in os.listdir(path):
            if filename.lower() in item.lower():
                matches.append(item)
        
        if not matches:
            return f"لم يتم العثور على ملف يحتوي على '{filename}' في {folder}"
        
        # فتح أول تطابق
        file_path = os.path.join(path, matches[0])
        try:
            os.startfile(file_path)
            return f"تم فتح: {matches[0]}"
        except Exception as e:
            return f"فشل فتح الملف: {e}"


class Handler(FileSystemEventHandler):
    """معالج أحداث نظام الملفات مع دعم on_change callback"""
    
    def __init__(self, callback, filter_key, action_type, watch_id, on_change_callback=None, on_change_action=None):
        self.callback = callback
        self.filter = filter_key
        self.action = action_type
        self.watch_id = watch_id
        self.last_event = 0
        
        # 🆕 الـ callback لتنفيذ أمر عند التغيير
        self.on_change_callback = on_change_callback
        self.on_change_action = on_change_action  # {"intent": "create_folder", "target": "تجربة", ...}

    def on_created(self, event):
        if event.is_directory: 
            return
        if time.time() - self.last_event < 2:  # Debounce
            return
        self.last_event = time.time()

        filename = os.path.basename(event.src_path)
        folder = os.path.dirname(event.src_path)
        
        # فلترة
        if self.filter and self.filter.lower() not in filename.lower(): 
            return
        
        # إبلاغ UI
        if self.callback:
            self.callback(f"👁️ [{self.watch_id}] تم رصد: {filename}", "warning")
        
        # 🆕 تنفيذ on_change action إذا موجود
        if self.on_change_callback and self.on_change_action:
            try:
                # إضافة context من الحدث
                action = self.on_change_action.copy()
                action["_trigger_file"] = filename
                action["_trigger_folder"] = folder
                action["_watch_id"] = self.watch_id
                
                if self.callback:
                    self.callback(f"⚡ [{self.watch_id}] تنفيذ: {action.get('intent')} → {action.get('target')}", "info")
                
                # تنفيذ الـ callback
                self.on_change_callback(action)
                
            except Exception as e:
                if self.callback:
                    self.callback(f"❌ [{self.watch_id}] خطأ في on_change: {e}", "error")
        
        # إرسال Windows Toast
        try:
            from core.notifications import notify_file
            notify_file(filename, folder)
        except Exception as e:
            print(f"Toast error: {e}")