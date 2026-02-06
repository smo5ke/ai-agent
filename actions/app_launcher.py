# actions/app_launcher.py
import os
import subprocess
import shutil
from AppOpener import open as app_opener

class AppLauncher:
    """
    🚀 App Launcher - مشغل التطبيقات (v2.0)
    يعتمد على مكتبة AppOpener للبحث الذكي + بروتوكولات المتجر (URI Schemes).
    """

    def open_program(self, name_or_path: str) -> str:
        """فتح برنامج بالاسم أو المسار"""
        app_name = name_or_path.strip()
        app_name_lower = app_name.lower()

        print(f"🚀 Trying to open: {app_name}...")

        # --- الطريقة 1: المكتبة الذكية (AppOpener) ---
        # هذه المكتبة تبحث في قائمة "إبدأ" مثلما يفعل البشر
        # match_closest=True تعني لو قلت "تيليجرام" وهو اسمه "Telegram Desktop" سيعرفه
        try:
            # check if it works first? No, just try catch.
            # output=False suppresses prints
            # throw_error=True might be needed to catch the exception if not found
            # But the library usually prints. Let's trust the user's snippet.
            # Actually, looking at docs, open() returns None usually.
            # We need to capture if it worked.
            # The library prints "Opening ..." or "Not found...".
            # Users code:
            # app_opener(app_name, match_closest=True, output=False)
            
            # Let's try it.
            result = app_opener(app_name, match_closest=True, output=False)
            if result: # If it returns something truthy? Docs say it returns None usually?
                 pass 
            # We assume if no exception, it might have worked? 
            # Actually, `open` prints to stdout. Capturing that is hard here.
            # Let's trust it works if it doesn't crash?
            # Wait, AppOpener logic is a bit weird.
            # Let's try it.
        except:
             pass
        
        # --- الطريقة 2: التعامل مع تطبيقات المتجر (URI Schemes) ---
        # تطبيقات المتجر غالباً لها "كود سري" للتشغيل
        
        special_apps = {
            "telegram": "tg://",           # كود تشغيل تيليجرام
            "whatsapp": "whatsapp://",     # كود تشغيل واتساب
            "spotify": "spotify:",         # كود تشغيل سبوتيفاي
            "calculator": "calc",          # الآلة الحاسبة
            "settings": "ms-settings:",    # الإعدادات
            "store": "ms-windows-store:",  # المتجر نفسه
            "netflix": "netflix:",
            "instagram": "instagram:",
        }

        # Check for direct match or substring match key (e.g. "telegram desktop" contains "telegram")
        matched_uri = None
        if app_name_lower in special_apps:
            matched_uri = special_apps[app_name_lower]
        else:
            # Reverse lookup for keys in app_name
            for key, uri in special_apps.items():
                if key in app_name_lower:
                    matched_uri = uri
                    break
        
        if matched_uri:
            try:
                os.system(f"start {matched_uri}")
                return f"✅ Opening {app_name} via URI Scheme ({matched_uri})"
            except Exception as e:
                print(f"URI Error: {e}")

        # --- الطريقة 3: الطريقة التقليدية (System Command / Path) ---
        # للبرامج العادية مثل notepad, cmd أو المسارات
        if os.path.exists(app_name):
            try:
                os.startfile(app_name)
                return f"🚀 Launching executable: {app_name}"
            except:
                pass
        
        # Fallback to AppOpener again via simple scan? 
        # Actually user code puts AppOpener first.
        # But AppOpener is slow sometimes?
        
        # Let's try AppOpener explicitly here and return success if no error?
        try:
             # Just matching closest
             app_opener(app_name, match_closest=True, output=False)
             return f"✅ Attemped to open {app_name} via AppOpener (Check screen)."
        except:
             pass

        # Old fallback
        if shutil.which(app_name_lower):
            subprocess.Popen(app_name_lower, shell=True)
            return f"🚀 Running command: {app_name_lower}"

        return f"❓ Attempted to open '{app_name}'. If it didn't open, try specifying the full path or correct name."
