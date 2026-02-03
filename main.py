import tkinter as tk
from tkinter import scrolledtext
import os
import sys

# التأكد من أن بايثون يرى المجلدات الداخلية
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# مكتبات اللغة العربية
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
except ImportError: pass

from core.orchestrator import Orchestrator

# ألوان التصميم
BG_COLOR = "#1e1e1e"
FG_COLOR = "#00ff41" # الأخضر الهاكر
ACCENT_COLOR = "#00ADB5"

class JarvisApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Jarvis AI: Enterprise Edition 🏢")
        self.root.geometry("950x650")
        self.root.configure(bg=BG_COLOR)

        # 1. تهيئة النظام
        # تأكد من وضع ملف الموديل داخل مجلد llm أو بجانب main.py
        model_name = "Meta-Llama-3.1-8B-Instruct-Q6_K_L.gguf"
        model_path = os.path.join("llm", model_name)
        
        if not os.path.exists(model_path):
             # محاولة البحث في المجلد الرئيسي
             if os.path.exists(model_name):
                 model_path = model_name
             else:
                 print(f"❌ Error: Model not found at {model_path}")

        self.orchestrator = Orchestrator(model_path)
        self.orchestrator.ui_callback = self.update_log # ربط الواجهة
        self.orchestrator.start_brain()

        # 2. بناء الواجهة
        self.setup_ui()

    def setup_ui(self):
        header = tk.Label(self.root, text="J.A.R.V.I.S  |  SYSTEM ONLINE", bg=BG_COLOR, fg=ACCENT_COLOR, font=("Segoe UI", 16, "bold"))
        header.pack(pady=15)

        self.log_area = scrolledtext.ScrolledText(self.root, bg="#121212", fg=FG_COLOR, font=("Consolas", 12), height=20, borderwidth=0)
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        self.log_area.tag_config('right', justify='right')
        self.log_area.config(state=tk.DISABLED)

        input_frame = tk.Frame(self.root, bg=BG_COLOR)
        input_frame.pack(fill=tk.X, padx=20, pady=15)

        self.entry = tk.Entry(input_frame, bg="#2C2C2C", fg="white", font=("Arial", 12), insertbackground="white", justify='right')
        self.entry.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        self.entry.bind("<Return>", self.send_command)

        btn = tk.Button(input_frame, text="Execute", command=self.send_command_click, bg=ACCENT_COLOR, fg="white", font=("Segoe UI", 10, "bold"), relief="flat", padx=15)
        btn.pack(side=tk.LEFT)

    def fix_arabic(self, text):
        try: return get_display(arabic_reshaper.reshape(text))
        except: return text

    def update_log(self, message, msg_type="info"):
        self.root.after(0, lambda: self._log_thread_safe(message, msg_type))

    def _log_thread_safe(self, message, msg_type):
        fixed_msg = self.fix_arabic(message)
        self.log_area.config(state=tk.NORMAL)
        
        prefix = "🤖"
        color = FG_COLOR
        if msg_type == "thought": prefix = "🧠"; color = "#888888"
        elif msg_type == "warning": prefix = "🛡️"; color = "#FFC107"
        elif msg_type == "success": prefix = "✅"; color = "#4CAF50"
        elif msg_type == "error": prefix = "❌"; color = "#FF5252"

        self.log_area.insert(tk.END, f"{prefix} {fixed_msg}\n", ('right', msg_type))
        self.log_area.tag_config(msg_type, foreground=color)
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)

    def send_command_click(self): self.send_command(None)

    def send_command(self, event):
        text = self.entry.get().strip()
        if not text: return
        self.entry.delete(0, tk.END)
        self.update_log(f"أنت: {text}", "info")
        self.orchestrator.process_request(text)

if __name__ == "__main__":
    root = tk.Tk()
    app = JarvisApp(root)
    root.mainloop()