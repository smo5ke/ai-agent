import os
import sys
import json
import time
import queue
import shutil
import threading
import schedule
import webbrowser
import subprocess
import tkinter as tk
from tkinter import scrolledtext, messagebox, Listbox
import winreg

# --- مكتبات الأتمتة ---
try:
    import pyautogui
    import pyperclip
except ImportError: pass

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.5

# --- مكتبات تصحيح العربية ---
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
except ImportError: pass

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from llama_cpp import Llama
from dynamic_resolver import DynamicResolver

BG_COLOR = "#0f0f0f"
FG_COLOR = "#00ff41"
TXT_FONT = ("Consolas", 11)

class AutoAgent:
    def type_text(self, text):
        pyperclip.copy(text)
        time.sleep(0.1)
        pyautogui.hotkey('ctrl', 'v')

    def open_notepad_and_write(self, text):
        subprocess.Popen("notepad.exe")
        time.sleep(1)
        self.type_text(text)

    def google_search(self, query):
        url = f"https://www.google.com/search?q={query}"
        webbrowser.open(url)

    def youtube_search(self, query):
        url = f"https://www.youtube.com/results?search_query={query}"
        webbrowser.open(url)

class JarvisGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Jarvis AI: Ultimate Fix 🛠️")
        self.root.geometry("1000x700")
        self.root.configure(bg=BG_COLOR)

        self.event_queue = queue.Queue()
        self.brain_lock = threading.Lock()
        self.llm = None
        self.resolver = None
        self.observer = Observer()
        self.active_missions = []
        self.watched_paths = []
        self.processed_cache = {}
        
        self.automator = AutoAgent()
        self.build_ui()
        
        self.log("🚀 جاري تحميل النظام...")
        threading.Thread(target=self.start_backend, daemon=True).start()
        self.root.after(100, self.check_queue)

    def build_ui(self):
        main_frame = tk.Frame(self.root, bg=BG_COLOR)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        left_frame = tk.Frame(main_frame, bg=BG_COLOR)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.log_area = scrolledtext.ScrolledText(left_frame, bg="#1a1a1a", fg=FG_COLOR, font=TXT_FONT, height=20, borderwidth=0)
        self.log_area.pack(fill=tk.BOTH, expand=True, pady=10)
        self.log_area.tag_config('right', justify='right')
        self.log_area.config(state=tk.DISABLED)
        
        input_frame = tk.Frame(left_frame, bg=BG_COLOR)
        input_frame.pack(fill=tk.X, pady=5)
        
        self.cmd_entry = tk.Entry(input_frame, bg="#333", fg="white", font=("Arial", 12), justify='right', insertbackground='white')
        self.cmd_entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        self.cmd_entry.bind("<Return>", self.send_command)
        
        btn_send = tk.Button(input_frame, text="تنفيذ", command=self.send_command_click, bg="#2962ff", fg="white")
        btn_send.pack(side=tk.LEFT)

        right_frame = tk.Frame(main_frame, bg=BG_COLOR, width=300)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(15, 0))
        
        self.task_list = Listbox(right_frame, bg="#1a1a1a", fg="white", font=("Segoe UI", 11), height=25, justify='right', borderwidth=0)
        self.task_list.pack(fill=tk.BOTH, expand=True, pady=10)
        
        btn_stop = tk.Button(right_frame, text="حذف المهمة", command=self.stop_mission, bg="#d50000", fg="white")
        btn_stop.pack(fill=tk.X)

    def fix_arabic(self, text):
        try: return get_display(arabic_reshaper.reshape(text))
        except: return text

    def log(self, text, is_thought=False):
        fixed_text = self.fix_arabic(text)
        self.log_area.config(state=tk.NORMAL)
        prefix = "🤔 " if is_thought else "🤖 "
        color = "#888888" if is_thought else FG_COLOR
        self.log_area.insert(tk.END, f"{prefix}{fixed_text}\n", ('right', 'color'))
        self.log_area.tag_config('color', foreground=color)
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)

    def log_queue(self, text, is_thought=False):
        self.root.after(0, lambda: self.log(text, is_thought))

    def start_backend(self):
        try: self.resolver = DynamicResolver()
        except: self.resolver = None
        self.handler = self.create_handler()
        self.init_defaults()
        self.observer.start()
        threading.Thread(target=self.watcher_loop, daemon=True).start()
        threading.Thread(target=self.scheduler_loop, daemon=True).start()
        
        model_name = "Meta-Llama-3.1-8B-Instruct-Q6_K_L.gguf"
        if os.path.exists(model_name):
            try:
                self.llm = Llama(model_path=model_name, n_ctx=8192, n_gpu_layers=0, verbose=False)
                self.log_queue("✅ النظام جاهز.")
            except Exception as e: self.log_queue(f"❌ خطأ: {e}")
        else: self.log_queue("❌ الموديل غير موجود!")

    def send_command_click(self): self.send_command(None)

    def send_command(self, event):
        text = self.cmd_entry.get().strip()
        if not text: return
        self.cmd_entry.delete(0, tk.END)
        self.log(f"👤 {text}")
        if self.llm is None: return
        threading.Thread(target=self._smart_think, args=(text,), daemon=True).start()

    def _smart_think(self, user_input):
        known_apps = list(self.resolver.system_apps.keys())[:20] if self.resolver else []
        
        # برومبت محسن جداً للفصل بين البحث والفتح
        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are an advanced AI OS Controller.

CONTEXT:
- Apps: {', '.join(known_apps)}

COMMAND TYPES:
1. **MACRO**: 
   - Use `web_search` for Google.
   - Use `Youtube` ONLY if user asks to "search" or "find" IN YouTube.
   - Use `write_note` for writing text.

2. **SYSTEM**:
   - Use `open` to launch apps or websites (like "Open YouTube", "Open Paint").
   - Use `watch` to monitor folders.
   - Use `clean` to organize files.

CRITICAL RULES:
1. **Translation**: "الرسام" -> "mspaint", "الحاسبة" -> "calc", "يوتيوب" -> "youtube.com".
2. **Distinction**:
   - "Open YouTube" -> SYSTEM intent (open website).
   - "Search python in YouTube" -> MACRO intent (youtube_search).
3. **Watch**: Default action is 'alert'.

EXAMPLES:
User: "ابحث عن بايثون في يوتيوب" -> {{"intent": "macro", "cmd": "youtube_search", "param": "python"}}
User: "افتح يوتيوب" -> {{"intent": "open", "target": "youtube.com"}}
User: "افتح الرسام" -> {{"intent": "open", "target": "mspaint"}}
User: "راقب سطح المكتب" -> {{"intent": "watch", "loc": "Desktop", "filter": null, "act": "alert", "dest": "Documents"}}

<|eot_id|><|start_header_id|>user<|end_header_id|>
{user_input}
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""
        try:
            with self.brain_lock:
                output = self.llm(prompt, max_tokens=256, temperature=0.1, stop=["<|eot_id|>"])
            
            response_text = output['choices'][0]['text'].strip()
            if "{" in response_text:
                json_str = response_text[response_text.find('{'):response_text.rfind('}')+1]
                thought = response_text.split('{')[0].strip()
                if thought: self.log_queue(f"تحليل: {thought}", is_thought=True)
                
                data = json.loads(json_str)
                self.root.after(0, lambda: self.execute_action(data))
            else:
                self.log_queue("⚠️ لم أفهم الطلب.")
        except Exception as e: self.log_queue(f"⚠️ خطأ: {e}")

    def execute_action(self, data):
        intent = data.get('intent')

        if intent == 'macro':
            cmd = data.get('cmd')
            param = data.get('param')
            self.log(f"⚡ تشغيل آلي: {cmd}")
            if cmd == "web_search": self.automator.google_search(param)
            elif cmd == "youtube_search": self.automator.youtube_search(param)
            elif cmd == "write_note": threading.Thread(target=self.automator.open_notepad_and_write, args=(param,)).start()

        elif intent == 'open':
            target = data.get('target').lower()
            self.log(f"🚀 تشغيل: {target}")
            
            # --- القائمة الذهبية (تمنع الهلوسة) ---
            # هنا نثبت أسماء البرامج الشائعة يدوياً لضمان فتحها 100%
            app_map = {
                "paint": "mspaint", "الرسام": "mspaint", "mspaint": "mspaint",
                "word": "winword", "وورد": "winword",
                "excel": "excel", "اكسل": "excel",
                "calc": "calc", "الحاسبة": "calc", "الالة الحاسبة": "calc",
                "notepad": "notepad", "المفكرة": "notepad",
                "chrome": "chrome", "كروم": "chrome",
                "edge": "msedge",
                "telegram": "telegram", "تيليجرام": "telegram",
                "youtube": "youtube.com", "يوتيوب": "youtube.com" # فتح يوتيوب كـ موقع
            }
            
            # التحقق من القائمة الذهبية أولاً
            real_target = app_map.get(target, target)
            
            # إذا كان موقع إلكتروني
            if "." in real_target and not real_target.endswith(".exe"):
                webbrowser.open(f"https://{real_target}" if "http" not in real_target else real_target)
                return

            # محاولة التشغيل المباشر
            try: 
                subprocess.Popen(real_target)
                return
            except: pass
            
            # المحاولة الأخيرة عبر Resolver
            if self.resolver:
                res = self.resolver.resolve(target)
                if res:
                    if res['type'] == 'app':
                        path = res['target']
                        if "!" in path or not os.path.exists(path):
                             subprocess.run(f'explorer.exe shell:AppsFolder\\{path}', shell=True)
                        else: subprocess.Popen(path)

        elif intent == 'clean':
            src = self.get_real_path(data.get('target', 'Desktop'))
            flt = data.get('filter')
            self.log(f"🧹 تنظيف {os.path.basename(src)}")
            self.smart_move(src, data.get('dest', 'Documents'), filter_rule=flt)

        elif intent == 'watch':
            src = self.get_real_path(data.get('loc', 'Desktop'))
            act = data.get('act', 'alert')
            if act == 'move' and not data.get('filter'):
                act = 'alert'
                self.log("🛡️ تم تحويل النقل إلى تنبيه للأمان.")

            if self.add_watch_path(src):
                mission = {'intent': 'watch', 'loc': src, 'filter': data.get('filter'), 'act': act, 'dest': data.get('dest', 'Documents')}
                self.active_missions.append(mission)
                desc = f"👀 {os.path.basename(src)}" + (f" -> {mission['filter']}" if mission['filter'] else "")
                self.task_list.insert(tk.END, self.fix_arabic(desc))
                self.log(f"✅ بدأت المراقبة: {desc}")
            else:
                self.log(f"❌ لم أعثر على المجلد: {src}")

    # --- دوال المسارات والمراقبة ---
    def get_real_path(self, name):
        name = name.lower()
        if name in ["desktop", "سطح المكتب", "downloads", "التنزيلات", "documents", "المستندات", "pictures", "الصور"]:
            try:
                key_map = {
                    "desktop": "Desktop", "سطح المكتب": "Desktop",
                    "downloads": "{374DE290-123F-4565-9164-39C4925E467B}", "التنزيلات": "{374DE290-123F-4565-9164-39C4925E467B}",
                    "documents": "Personal", "المستندات": "Personal",
                    "pictures": "My Pictures", "الصور": "My Pictures"
                }
                reg_key = key_map.get(name)
                if reg_key:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders")
                    path, _ = winreg.QueryValueEx(key, reg_key)
                    return os.path.expandvars(path)
            except: pass
        
        mapping = {"سطح المكتب": "Desktop", "التنزيلات": "Downloads", "المستندات": "Documents", "الصور": "Pictures"}
        return os.path.join(os.path.expanduser("~"), mapping.get(name, name))

    def smart_move(self, source, dest_name, filter_rule=None):
        dest_path = os.path.join(self.get_real_path(dest_name), "Cleaned")
        os.makedirs(dest_path, exist_ok=True)
        if not os.path.exists(source): return
        count = 0
        for item in os.listdir(source):
            full_path = os.path.join(source, item)
            if not os.path.isfile(full_path) or item.startswith('.'): continue
            
            is_match = True
            if filter_rule:
                if filter_rule.lower() not in item.lower(): is_match = False
            
            if is_match:
                try: shutil.move(full_path, os.path.join(dest_path, item)); count += 1
                except: pass
        self.log_queue(f"✨ تم نقل {count} ملفات." if count > 0 else "✨ لم أجد ملفات.")

    def create_handler(self):
        class Handler(FileSystemEventHandler):
            def on_created(nested_self, event):
                if not event.is_directory: self.event_queue.put(event)
        return Handler()

    def init_defaults(self):
        for p in ["Desktop", "Downloads"]: self.add_watch_path(self.get_real_path(p), silent=True)

    def add_watch_path(self, path, silent=False):
        if not path or not os.path.exists(path) or path in self.watched_paths: return False
        try:
            self.observer.schedule(self.handler, path, recursive=True)
            self.watched_paths.append(path)
            if not silent: self.log_queue(f"👀 تفعيل المراقبة: {path}")
            return True
        except: return False

    def watcher_loop(self):
        while True:
            try:
                event = self.event_queue.get()
                fname = os.path.basename(event.src_path)
                fpath = os.path.abspath(event.src_path)
                now = time.time()
                if now - self.processed_cache.get(fpath, 0) < 3:
                    self.event_queue.task_done(); continue
                
                for m in self.active_missions:
                    if m['intent'] == 'watch' and os.path.abspath(m['loc']) in fpath:
                        if fname.endswith(('.tmp', '.crdownload')): continue
                        is_match = True
                        if m['filter'] and m['filter'].lower() not in fname.lower(): is_match = False
                        
                        if is_match:
                            act = m.get('act', 'alert')
                            if act == 'move':
                                self.log_queue(f"⚡ نقل آلي: {fname}")
                                self.processed_cache[fpath] = now
                                time.sleep(1)
                                self.smart_move(os.path.dirname(fpath), m['dest'], filter_rule=m['filter'])
                            else:
                                self.log_queue(f"🔔 تنبيه: ملف جديد {fname}")
                                self.processed_cache[fpath] = now
                self.event_queue.task_done()
            except: pass

    def scheduler_loop(self):
        while True: schedule.run_pending(); time.sleep(1)
    
    def check_queue(self): self.root.after(100, self.check_queue)
    
    def stop_mission(self):
        sel = self.task_list.curselection()
        if sel:
            idx = sel[0]; self.task_list.delete(idx)
            if idx < len(self.active_missions): self.active_missions.pop(idx)
            self.log("🛑 تم الحذف.")

if __name__ == "__main__":
    root = tk.Tk()
    app = JarvisGUI(root)
    root.mainloop()