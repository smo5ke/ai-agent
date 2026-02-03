import os
import json
import subprocess
import difflib

class DynamicResolver:
    def __init__(self):
        self.system_apps = {}
        
        # 1. المترادفات (Aliases)
        self.aliases = {
            "وورد": "word", "word": "word",
            "اكسل": "excel", "excel": "excel",
            "بوربوينت": "powerpoint",
            "نوت": "notepad", "مفكرة": "notepad",
            "رسام": "paint",
            "حاسبة": "calculator",
            "blender": "blender",
            "تلغرام": "telegram", "telegram": "telegram",
            "فوتوشوب": "photoshop",
            "كود": "visual studio code",
            "كروم": "google chrome", "chrome": "google chrome"
        }
        
        self.refresh_system_apps()

    def normalize_text(self, text):
        text = text.lower().strip()
        if text.startswith("ال") and len(text) > 3:
            text = text[2:]
        return text

    def _scan_desktop_shortcuts(self):
        """مسح أيقونات سطح المكتب (لحل مشكلة البرامج غير المسجلة مثل Blender)"""
        desktop_paths = [
            os.path.join(os.path.expanduser("~"), "Desktop"),
            os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")
        ]
        
        found_shortcuts = {}
        for path in desktop_paths:
            if os.path.exists(path):
                try:
                    for item in os.listdir(path):
                        if item.lower().endswith(('.lnk', '.exe')):
                            name = item.lower().replace('.lnk', '').replace('.exe', '').strip()
                            full_path = os.path.join(path, item)
                            found_shortcuts[name] = full_path
                except: pass
        return found_shortcuts

    def refresh_system_apps(self):
        print("⚡ جاري مسح تطبيقات النظام + سطح المكتب...")
        self.system_apps = {}
        
        # 1. المصدر الأول: PowerShell
        ps_command = "Get-StartApps | ConvertTo-Json"
        try:
            result = subprocess.run(["powershell", "-Command", ps_command], capture_output=True, text=True)
            apps_list = json.loads(result.stdout)
            if isinstance(apps_list, dict): apps_list = [apps_list]
            
            for app in apps_list:
                name = app['Name'].lower().strip()
                self.system_apps[name] = {
                    "type": "store_app",
                    "target": app['AppID']
                }
        except: pass

        # 2. المصدر الثاني: سطح المكتب
        desktop_apps = self._scan_desktop_shortcuts()
        for name, path in desktop_apps.items():
            self.system_apps[name] = {
                "type": "desktop_shortcut",
                "target": path
            }
        
        print(f"✅ تم الفهرسة: {len(self.system_apps)} تطبيق.")

    def resolve(self, query):
        original = query
        query = query.replace("افتح", "").replace("شغل", "").strip()
        clean_query = self.normalize_text(query)
        
        search_term = self.aliases.get(clean_query, clean_query)

        # 1. التطابق التام
        if search_term in self.system_apps:
            return self._build_response(search_term)

        # 2. الاحتواء الذكي
        candidates = []
        for app_name in self.system_apps.keys():
            if search_term in app_name:
                candidates.append(app_name)
        
        if candidates:
            best_candidate = min(candidates, key=len)
            return self._build_response(best_candidate)

        # 3. البحث الضبابي
        matches = difflib.get_close_matches(search_term, self.system_apps.keys(), n=1, cutoff=0.8)
        if matches:
            return self._build_response(matches[0])

        # 4. مواقع
        if clean_query in ["يوتيوب", "youtube"]:
             return {"type": "website", "target": "https://youtube.com", "action": "open_browser"}
        
        return {"type": "search", "target": original, "action": "google_search"}

    def _build_response(self, app_name):
        app_info = self.system_apps[app_name]
        return {
            "type": "app",
            "name": app_name,
            "target": app_info['target'],
            "method": app_info['type'],
            "action": "launch_app"
        }