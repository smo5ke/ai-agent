import os
import subprocess
import webbrowser
import difflib # مكتبة للمقارنة الذكية بين النصوص
from .base import BaseAction

class OpenAppAction(BaseAction):
    def __init__(self):
        self.apps_index = {} # الذاكرة التي سنحفظ فيها أماكن البرامج
        self.common_aliases = {
            "google": "chrome",
            "max": "3ds max",
            "word": "word",
            "excel": "excel",
            "calculator": "calc",
            "الحاسبة": "calc",
            "الرسام": "mspaint",
            "notepad": "notepad",
            "telegram": "telegram desktop"
        }
        # تشغيل الفهرسة فوراً عند الإقلاع
        self.index_installed_apps()

    def index_installed_apps(self):
        """
        دالة تقوم بمسح شامل لقائمة إبدأ (Start Menu)
        وتسجيل موقع كل ملف .lnk
        """
        print("📂 جاري فهرسة برامج الويندوز (.lnk)...")
        
        # مسارات قائمة إبدأ (للمستخدم الحالي ولكل المستخدمين)
        start_menu_paths = [
            os.path.join(os.getenv('APPDATA'), r"Microsoft\Windows\Start Menu\Programs"),
            os.path.join(os.getenv('PROGRAMDATA'), r"Microsoft\Windows\Start Menu\Programs")
        ]

        count = 0
        for path in start_menu_paths:
            if not os.path.exists(path): continue
            
            for root, dirs, files in os.walk(path):
                for file in files:
                    # هنا السر: البحث عن ملفات .lnk
                    if file.lower().endswith(".lnk"):
                        # تنظيف الاسم: Google Chrome.lnk -> google chrome
                        clean_name = file.lower().replace(".lnk", "")
                        full_path = os.path.join(root, file)
                        self.apps_index[clean_name] = full_path
                        count += 1
        
        print(f"✅ تم العثور على {count} تطبيق مثبت.")

    def find_best_match(self, target):
        """
        دالة البحث الذكي: تحاول إيجاد أقرب اسم برنامج للطلب
        """
        target = target.lower()
        
        # 1. التحقق من الأسماء المستعارة (مثلاً قال "max" -> نبحث عن "3ds max")
        target = self.common_aliases.get(target, target)

        # 2. بحث دقيق مباشر
        if target in self.apps_index:
            return self.apps_index[target]

        # 3. بحث جزئي (هل الكلمة جزء من اسم البرنامج؟)
        # مثلاً: "chrome" موجودة داخل "google chrome"
        matches = []
        for app_name, path in self.apps_index.items():
            if target in app_name:
                matches.append((app_name, path))
        
        if matches:
            # نأخذ أقصر اسم لأنه عادة الأصح (chrome أفضل من chrome uninstall)
            matches.sort(key=lambda x: len(x[0]))
            return matches[0][1]

        # 4. بحث ضبابي (Fuzzy Search) لو كتب الاسم غلط بحرف
        # يبحث عن أقرب كلمة تشبه اللي كتبته
        close_matches = difflib.get_close_matches(target, self.apps_index.keys(), n=1, cutoff=0.6)
        if close_matches:
            return self.apps_index[close_matches[0]]

        return None

    def run(self, target):
        print(f"🚀 جاري البحث عن: {target}")
        
        # البحث في الفهرس الذي بنيناه
        app_path = self.find_best_match(target)

        if app_path:
            try:
                print(f"✅ تم العثور عليه: {app_path}")
                # os.startfile هي الطريقة الصحيحة لفتح ملفات .lnk في ويندوز
                os.startfile(app_path)
                return f"تم تشغيل {os.path.basename(app_path).replace('.lnk', '')}"
            except Exception as e:
                return f"وجدت البرنامج لكن فشل التشغيل: {e}"

        # خطة بديلة: أوامر الويندوز المباشرة (مثل calc, notepad)
        try:
            subprocess.Popen(target)
            return f"تم تشغيل {target} (أمر مباشر)"
        except: pass

        # خطة بديلة 2: فتح موقع
        if "." in target: # مثل youtube.com
             webbrowser.open(f"https://{target}")
             return f"تم فتح الموقع {target}"

        return f"❌ لم أجد برنامجاً باسم '{target}' في جهازك."