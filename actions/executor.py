import os
import shutil
import subprocess
import webbrowser
import winreg
import time

class Executor:
    def __init__(self):
        # القائمة الذهبية للتطبيقات
        self.app_map = {
            "paint": "mspaint", "الرسام": "mspaint",
            "notepad": "notepad", "المفكرة": "notepad",
            "calc": "calc", "الحاسبة": "calc",
            "word": "winword", "excel": "excel",
            "chrome": "chrome", "edge": "msedge",
            "telegram": "telegram", "تيليجرام": "telegram", # سيتم معالجته في الدالة بالأسفل
            "youtube": "youtube.com"
        }

    def get_real_path(self, name):
        """جلب المسار الحقيقي (يدعم OneDrive)"""
        name = name.lower() if name else "desktop"
        key_map = {
            "desktop": "Desktop", "سطح المكتب": "Desktop",
            "downloads": "{374DE290-123F-4565-9164-39C4925E467B}", "التنزيلات": "{374DE290-123F-4565-9164-39C4925E467B}",
            "documents": "Personal", "المستندات": "Personal",
            "pictures": "My Pictures", "الصور": "My Pictures"
        }
        
        if name in key_map:
            try:
                reg_key = key_map.get(name)
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders")
                path, _ = winreg.QueryValueEx(key, reg_key)
                return os.path.expandvars(path)
            except: pass
        
        mapping = {"سطح المكتب": "Desktop", "التنزيلات": "Downloads", "المستندات": "Documents", "الصور": "Pictures"}
        clean_name = mapping.get(name, name)
        return os.path.join(os.path.expanduser("~"), clean_name)

    def find_telegram(self):
        """محاولة إيجاد مسار تيليجرام في الأماكن المشهورة"""
        user_home = os.path.expanduser("~")
        possible_paths = [
            os.path.join(user_home, "AppData", "Roaming", "Telegram Desktop", "Telegram.exe"),
            r"C:\Program Files\Telegram Desktop\Telegram.exe",
            r"C:\Program Files (x86)\Telegram Desktop\Telegram.exe"
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None

    def open_app(self, target):
        """فتح التطبيقات والمواقع بذكاء"""
        target = target.lower()
        real_target = self.app_map.get(target, target)

        print(f"🚀 Action: Opening {real_target}")

        # 1. موقع إلكتروني
        if "." in real_target and not real_target.endswith(".exe"):
            webbrowser.open(f"https://{real_target}" if "http" not in real_target else real_target)
            return f"تم فتح الموقع: {real_target}"

        # 3. تطبيق عادي
        try:
            subprocess.Popen(real_target)
            return f"تم تشغيل {real_target}"
        except:
            # محاولة البحث عنه في جوجل إذا فشل كل شيء
            webbrowser.open(f"https://google.com/search?q={target}")
            return f"لم أتمكن من العثور على {target}، قمت بالبحث عنه في المتصفح."

    def clean_folder(self, source_name, filter_key, dest_name="Documents"):
        """نقل الملفات (التنظيف)"""
        src = self.get_real_path(source_name)
        dest_base = self.get_real_path(dest_name)
        dest = os.path.join(dest_base, "Cleaned")
        os.makedirs(dest, exist_ok=True)

        if not os.path.exists(src):
            return f"المجلد غير موجود: {src}"

        count = 0
        for item in os.listdir(src):
            full_path = os.path.join(src, item)
            
            if not os.path.isfile(full_path) or item.startswith('.'): continue
            
            should_move = True
            if filter_key:
                if filter_key.lower() not in item.lower(): should_move = False
            
            if should_move:
                try:
                    shutil.move(full_path, os.path.join(dest, item))
                    count += 1
                except: pass
        
        return f"تم نقل {count} ملفات من {source_name}."