"""
🤖 Jarvis AI - Main Application
================================
الواجهة الرسومية الرئيسية مع قائمة جانبية لمهام المراقبة.
"""

import tkinter as tk
from tkinter import scrolledtext, ttk
import os
import sys

# التأكد من أن بايثون يرى المجلدات الداخلية
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# مكتبات اللغة العربية
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
except ImportError: 
    arabic_reshaper = None
    get_display = None

from core.orchestrator import Orchestrator

# ═══════════════════════════════════════════════════════════
# ألوان التصميم
# ═══════════════════════════════════════════════════════════
BG_COLOR = "#1e1e1e"
SIDEBAR_BG = "#252526"
FG_COLOR = "#00ff41"  # الأخضر الهاكر
ACCENT_COLOR = "#00ADB5"
WARNING_COLOR = "#FFC107"
ERROR_COLOR = "#FF5252"
SUCCESS_COLOR = "#4CAF50"


class JarvisApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Jarvis AI: Enterprise Edition 🏢")
        self.root.geometry("1100x700")
        self.root.configure(bg=BG_COLOR)
        self.root.minsize(900, 500)

        # تهيئة النظام
        model_name = "Meta-Llama-3.1-8B-Instruct-Q6_K_L.gguf"
        model_path = os.path.join("llm", model_name)
        
        if not os.path.exists(model_path):
            if os.path.exists(model_name):
                model_path = model_name
            else:
                print(f"❌ Error: Model not found at {model_path}")

        self.orchestrator = Orchestrator(model_path)
        self.orchestrator.ui_callback = self.update_log
        self.orchestrator.set_watches_callback(self.update_watches_list)
        self.orchestrator.start_brain()

        # 🔄 تشغيل Crash Recovery
        self._init_crash_recovery()

        # تشغيل Telegram Bot (إذا كان مُعدّ)
        self._init_telegram_bot()

        # بناء الواجهة
        self.setup_ui()
        
        # تسجيل اختصارات لوحة المفاتيح
        self._init_hotkeys()

    def _init_telegram_bot(self):
        """تهيئة Telegram Bot"""
        try:
            from integrations.telegram_config import TELEGRAM_BOT_TOKEN, ALLOWED_USERS
            if TELEGRAM_BOT_TOKEN:
                from integrations.telegram_bot import init_telegram
                init_telegram(TELEGRAM_BOT_TOKEN, self.orchestrator, ALLOWED_USERS)
                print("🤖 Telegram Bot: متصل")
        except ImportError:
            pass  # الملف غير موجود
        except Exception as e:
            print(f"⚠️ Telegram Bot error: {e}")

    def _init_crash_recovery(self):
        """تهيئة نظام التعافي من الأعطال"""
        try:
            from core.crash_recovery import get_crash_recovery
            self.crash_recovery = get_crash_recovery()
            self.crash_recovery.add_callback(self.update_log)
            self.crash_recovery.start_monitoring()
            print("🔄 Crash Recovery: مفعّل")
        except ImportError:
            self.crash_recovery = None
        except Exception as e:
            print(f"⚠️ Crash Recovery error: {e}")
            self.crash_recovery = None

    def _init_hotkeys(self):
        """تهيئة اختصارات لوحة المفاتيح"""
        try:
            from core.hotkeys import get_hotkey_manager
            self.hotkey_manager = get_hotkey_manager()
            
            if self.hotkey_manager.is_available():
                # اختصار تفعيل الصوت: Ctrl+Shift+V
                self.hotkey_manager.register(
                    "voice",
                    "ctrl+shift+v",
                    self._hotkey_voice
                )
                
                # اختصار التركيز على النافذة: Ctrl+Shift+J
                self.hotkey_manager.register(
                    "focus",
                    "ctrl+shift+j",
                    self._hotkey_focus
                )
                
                print("⌨️ Hotkeys: Ctrl+Shift+V (صوت), Ctrl+Shift+J (تركيز)")
        except Exception as e:
            print(f"⚠️ Hotkeys error: {e}")

    def _hotkey_voice(self):
        """اختصار تفعيل الصوت"""
        self.root.after(0, self.start_voice_input)

    def _hotkey_focus(self):
        """اختصار التركيز على النافذة"""
        def focus():
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
            self.entry.focus_set()
        self.root.after(0, focus)

    def setup_ui(self):
        """بناء الواجهة الرسومية"""
        
        # ═══════════════════════════════════════════════════════════
        # Header
        # ═══════════════════════════════════════════════════════════
        header = tk.Label(
            self.root, 
            text="J.A.R.V.I.S  |  SYSTEM ONLINE", 
            bg=BG_COLOR, 
            fg=ACCENT_COLOR, 
            font=("Segoe UI", 16, "bold")
        )
        header.pack(pady=10)

        # ═══════════════════════════════════════════════════════════
        # Main Container (Sidebar + Log)
        # ═══════════════════════════════════════════════════════════
        main_container = tk.Frame(self.root, bg=BG_COLOR)
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        # --- Sidebar (القائمة الجانبية) ---
        sidebar = tk.Frame(main_container, bg=SIDEBAR_BG, width=250)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        sidebar.pack_propagate(False)

        # ═══════════════════════════════════════════════════════════
        # قسم مهام المراقبة
        # ═══════════════════════════════════════════════════════════
        sidebar_title = tk.Label(
            sidebar, 
            text="📋 مهام المراقبة", 
            bg=SIDEBAR_BG, 
            fg=ACCENT_COLOR,
            font=("Segoe UI", 12, "bold"),
            anchor="w"
        )
        sidebar_title.pack(pady=10, padx=10, anchor="w")

        # قائمة المهام
        self.watches_frame = tk.Frame(sidebar, bg=SIDEBAR_BG)
        self.watches_frame.pack(fill=tk.X, padx=5)

        # رسالة عدم وجود مهام
        self.no_watches_label = tk.Label(
            self.watches_frame,
            text="لا توجد مهام نشطة",
            bg=SIDEBAR_BG,
            fg="#666666",
            font=("Segoe UI", 10)
        )
        self.no_watches_label.pack(pady=10)

        # زر إيقاف الكل
        stop_all_btn = tk.Button(
            sidebar,
            text="🛑 إيقاف الكل",
            command=self.stop_all_watches,
            bg="#333333",
            fg="white",
            font=("Segoe UI", 9),
            relief="flat",
            cursor="hand2"
        )
        stop_all_btn.pack(pady=5, padx=10, fill=tk.X)

        # زر الإعدادات ⚙️
        settings_btn = tk.Button(
            sidebar,
            text="⚙️ الإعدادات",
            command=self.open_settings,
            bg=ACCENT_COLOR,
            fg="white",
            font=("Segoe UI", 9),
            relief="flat",
            cursor="hand2"
        )
        settings_btn.pack(pady=5, padx=10, fill=tk.X)

        # ═══════════════════════════════════════════════════════════
        # قسم المهام المجدولة
        # ═══════════════════════════════════════════════════════════
        separator = tk.Frame(sidebar, bg="#444444", height=1)
        separator.pack(fill=tk.X, pady=15, padx=10)

        scheduled_title = tk.Label(
            sidebar, 
            text="⏰ المهام المجدولة", 
            bg=SIDEBAR_BG, 
            fg=ACCENT_COLOR,
            font=("Segoe UI", 12, "bold"),
            anchor="w"
        )
        scheduled_title.pack(padx=10, anchor="w")

        # قائمة المهام المجدولة
        self.scheduled_frame = tk.Frame(sidebar, bg=SIDEBAR_BG)
        self.scheduled_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # رسالة عدم وجود مهام مجدولة
        self.no_scheduled_label = tk.Label(
            self.scheduled_frame,
            text="لا توجد مهام",
            bg=SIDEBAR_BG,
            fg="#666666",
            font=("Segoe UI", 10)
        )
        self.no_scheduled_label.pack(pady=10)

        # بدء التحديث الدوري للمهام المجدولة
        self.update_scheduled_tasks()

        # --- Log Area ---
        log_frame = tk.Frame(main_container, bg=BG_COLOR)
        log_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.log_area = scrolledtext.ScrolledText(
            log_frame, 
            bg="#121212", 
            fg=FG_COLOR, 
            font=("Consolas", 11), 
            borderwidth=0,
            wrap=tk.WORD
        )
        self.log_area.pack(fill=tk.BOTH, expand=True)
        self.log_area.tag_config('right', justify='right')
        self.log_area.config(state=tk.DISABLED)
        
        # ═══════════════════════════════════════════════════════════
        # Timeline Sidebar (Right)
        # ═══════════════════════════════════════════════════════════
        try:
            from ui.timeline import TimelinePanel, get_timeline_manager
            
            # فاصل
            tk.Frame(main_container, bg="#444", width=1).pack(side=tk.LEFT, fill=tk.Y, padx=5)
            
            timeline_container = tk.Frame(main_container, bg="#1F2937", width=300)
            timeline_container.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
            timeline_container.pack_propagate(False)
            
            self.timeline_panel = TimelinePanel(timeline_container, get_timeline_manager())
            self.timeline_panel.pack(fill=tk.BOTH, expand=True)
            
        except ImportError:
            print("⚠️ Timeline module not found")
        except Exception as e:
            print(f"⚠️ Timeline setup error: {e}")

        # ═══════════════════════════════════════════════════════════
        # Smart Suggestions - اقتراحات ذكية
        # ═══════════════════════════════════════════════════════════
        self.suggestions_frame = tk.Frame(self.root, bg=BG_COLOR)
        self.suggestions_frame.pack(fill=tk.X, padx=15, pady=(5, 0))
        
        # تحميل الاقتراحات
        self._load_suggestions()

        # ═══════════════════════════════════════════════════════════
        # Input Area
        # ═══════════════════════════════════════════════════════════
        input_frame = tk.Frame(self.root, bg=BG_COLOR)
        input_frame.pack(fill=tk.X, padx=15, pady=10)

        self.entry = tk.Entry(
            input_frame, 
            bg="#2C2C2C", 
            fg="white", 
            font=("Arial", 12), 
            insertbackground="white", 
            justify='right'
        )
        self.entry.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        self.entry.bind("<Return>", self.send_command)
        self.entry.focus()

        btn = tk.Button(
            input_frame, 
            text="Execute", 
            command=self.send_command_click, 
            bg=ACCENT_COLOR, 
            fg="white", 
            font=("Segoe UI", 10, "bold"), 
            relief="flat", 
            padx=15,
            cursor="hand2"
        )
        btn.pack(side=tk.LEFT)

        # زر الميكروفون
        self.mic_btn = tk.Button(
            input_frame, 
            text="🎤", 
            command=self.start_voice_input, 
            bg="#333333", 
            fg="white", 
            font=("Segoe UI", 12), 
            relief="flat", 
            padx=10,
            cursor="hand2"
        )
        self.mic_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # ═══════════════════════════════════════════════════════════
        # Auto-complete للتطبيقات
        # ═══════════════════════════════════════════════════════════
        self.autocomplete_list = tk.Listbox(
            self.root,
            bg="#2d2d2d",
            fg=ACCENT_COLOR,
            font=("Consolas", 10),
            selectbackground=ACCENT_COLOR,
            selectforeground="white",
            height=5,
            borderwidth=0,
            highlightthickness=1,
            highlightbackground="#444444"
        )
        # سيتم إظهاره فوق الـ input عند الحاجة
        self.autocomplete_visible = False
        
        # ربط أحداث الكتابة
        self.entry.bind("<KeyRelease>", self._on_entry_change)
        self.entry.bind("<Down>", self._focus_autocomplete)
        self.entry.bind("<Escape>", self._hide_autocomplete)
        self.autocomplete_list.bind("<Return>", self._select_autocomplete)
        self.autocomplete_list.bind("<Double-Button-1>", self._select_autocomplete)
        self.autocomplete_list.bind("<Escape>", self._hide_autocomplete)
        
        # تهيئة نظام الصوت
        self._setup_voice()

    # ═══════════════════════════════════════════════════════════
    # إدارة قائمة المراقبة
    # ═══════════════════════════════════════════════════════════

    def update_watches_list(self, watches: list):
        """تحديث قائمة مهام المراقبة في الـ Sidebar"""
        self.root.after(0, lambda: self._update_watches_thread_safe(watches))

    def _update_watches_thread_safe(self, watches: list):
        """تحديث القائمة (thread-safe)"""
        # حذف العناصر القديمة
        for widget in self.watches_frame.winfo_children():
            widget.destroy()

        if not watches:
            # عرض رسالة عدم وجود مهام
            self.no_watches_label = tk.Label(
                self.watches_frame,
                text="لا توجد مهام نشطة",
                bg=SIDEBAR_BG,
                fg="#666666",
                font=("Segoe UI", 10)
            )
            self.no_watches_label.pack(pady=20)
            return

        # إنشاء عنصر لكل مهمة
        for watch in watches:
            self._create_watch_item(watch)

    def _create_watch_item(self, watch: dict):
        """إنشاء عنصر مهمة في القائمة"""
        item_frame = tk.Frame(self.watches_frame, bg="#333333", pady=5)
        item_frame.pack(fill=tk.X, pady=3)

        # معلومات المهمة
        info_frame = tk.Frame(item_frame, bg="#333333")
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        folder_label = tk.Label(
            info_frame,
            text=f"👁️ {watch.get('folder', 'Unknown')}",
            bg="#333333",
            fg=WARNING_COLOR,
            font=("Segoe UI", 10, "bold"),
            anchor="w"
        )
        folder_label.pack(anchor="w")

        id_label = tk.Label(
            info_frame,
            text=f"ID: {watch.get('id', '')} | {watch.get('started_at', '')}",
            bg="#333333",
            fg="#888888",
            font=("Consolas", 8),
            anchor="w"
        )
        id_label.pack(anchor="w")

        # زر الإيقاف
        stop_btn = tk.Button(
            item_frame,
            text="✕",
            command=lambda wid=watch.get('id'): self.stop_watch(wid),
            bg=ERROR_COLOR,
            fg="white",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            width=3,
            cursor="hand2"
        )
        stop_btn.pack(side=tk.RIGHT, padx=5)

    def stop_watch(self, watch_id: str):
        """إيقاف مهمة مراقبة"""
        if watch_id:
            self.orchestrator.stop_watch_by_id(watch_id)

    def stop_all_watches(self):
        """إيقاف جميع المهام"""
        from actions import fs_manager
        result = fs_manager.stop_all_watches()
        self.update_log(f"🛑 {result}", "warning")

    # ═══════════════════════════════════════════════════════════
    # إدارة المهام المجدولة
    # ═══════════════════════════════════════════════════════════

    def update_scheduled_tasks(self):
        """تحديث قائمة المهام المجدولة (دوري كل 5 ثواني)"""
        try:
            from core.scheduler import get_scheduler
            scheduler = get_scheduler()
            tasks = scheduler.get_tasks_for_ui()
            self._update_scheduled_ui(tasks)
        except Exception as e:
            print(f"Scheduler UI error: {e}")
        
        # إعادة التحديث بعد 5 ثواني
        self.root.after(5000, self.update_scheduled_tasks)

    def _update_scheduled_ui(self, tasks: list):
        """تحديث واجهة المهام المجدولة"""
        # حذف العناصر القديمة
        for widget in self.scheduled_frame.winfo_children():
            widget.destroy()

        if not tasks:
            # عرض رسالة عدم وجود مهام
            no_tasks = tk.Label(
                self.scheduled_frame,
                text="لا توجد مهام",
                bg=SIDEBAR_BG,
                fg="#666666",
                font=("Segoe UI", 10)
            )
            no_tasks.pack(pady=10)
            return

        # إنشاء عنصر لكل مهمة
        for task in tasks:
            self._create_scheduled_item(task)

    def _create_scheduled_item(self, task: dict):
        """إنشاء عنصر مهمة مجدولة"""
        item_frame = tk.Frame(self.scheduled_frame, bg="#2d2d2d", pady=5)
        item_frame.pack(fill=tk.X, pady=3)

        # معلومات المهمة
        info_frame = tk.Frame(item_frame, bg="#2d2d2d")
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # الأمر
        cmd_text = task.get('command', 'unknown')
        if cmd_text == 'reminder':
            cmd_text = '🔔 تذكير'
        elif cmd_text == 'open':
            cmd_text = f"🚀 فتح"

        cmd_label = tk.Label(
            info_frame,
            text=cmd_text,
            bg="#2d2d2d",
            fg=WARNING_COLOR,
            font=("Segoe UI", 9, "bold"),
            anchor="w"
        )
        cmd_label.pack(anchor="w")

        # الوقت المتبقي
        remaining = task.get('remaining', '')
        time_label = tk.Label(
            info_frame,
            text=f"⏳ {remaining}",
            bg="#2d2d2d",
            fg="#888888",
            font=("Consolas", 8),
            anchor="w"
        )
        time_label.pack(anchor="w")

        # زر الإلغاء
        cancel_btn = tk.Button(
            item_frame,
            text="✕",
            command=lambda tid=task.get('id'): self.cancel_scheduled_task(tid),
            bg=ERROR_COLOR,
            fg="white",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            width=3,
            cursor="hand2"
        )
        cancel_btn.pack(side=tk.RIGHT, padx=5)

    def cancel_scheduled_task(self, task_id: int):
        """إلغاء مهمة مجدولة"""
        if task_id:
            try:
                from core.scheduler import get_scheduler
                scheduler = get_scheduler()
                if scheduler.cancel_task(task_id):
                    self.update_log(f"🛑 تم إلغاء المهمة #{task_id}", "warning")
                else:
                    self.update_log(f"⚠️ لم يتم العثور على المهمة #{task_id}", "error")
            except Exception as e:
                self.update_log(f"❌ خطأ في إلغاء المهمة: {e}", "error")

    # ═══════════════════════════════════════════════════════════
    # الدوال الأساسية
    # ═══════════════════════════════════════════════════════════

    def fix_arabic(self, text):
        """إصلاح عرض النص العربي"""
        if arabic_reshaper and get_display:
            try: 
                return get_display(arabic_reshaper.reshape(text))
            except: 
                pass
        return text

    def update_log(self, message, msg_type="info"):
        """تحديث سجل الرسائل"""
        self.root.after(0, lambda: self._log_thread_safe(message, msg_type))

    def _log_thread_safe(self, message, msg_type):
        """كتابة في السجل (thread-safe)"""
        fixed_msg = self.fix_arabic(message)
        self.log_area.config(state=tk.NORMAL)
        
        prefix = "🤖"
        color = FG_COLOR
        
        if msg_type == "thought": 
            prefix = "🧠"
            color = "#888888"
        elif msg_type == "warning": 
            prefix = "🛡️"
            color = WARNING_COLOR
        elif msg_type == "success": 
            prefix = "✅"
            color = SUCCESS_COLOR
        elif msg_type == "error": 
            prefix = "❌"
            color = ERROR_COLOR

        self.log_area.insert(tk.END, f"{prefix} {fixed_msg}\n", ('right', msg_type))
        self.log_area.tag_config(msg_type, foreground=color)
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)

    def send_command_click(self): 
        self.send_command(None)

    def send_command(self, event):
        """إرسال أمر للمعالجة"""
        text = self.entry.get().strip()
        if not text: 
            return
        self.entry.delete(0, tk.END)
        self.update_log(f"أنت: {text}", "info")
        self.orchestrator.process_request(text)

    # ═══════════════════════════════════════════════════════════
    # Smart Suggestions
    # ═══════════════════════════════════════════════════════════

    def _load_suggestions(self):
        """تحميل وعرض الاقتراحات الذكية"""
        try:
            from core.suggestions import get_suggestions
            sugg_manager = get_suggestions()
            
            # عرض التحية
            greeting = sugg_manager.get_greeting()
            greeting_label = tk.Label(
                self.suggestions_frame,
                text=greeting,
                bg=BG_COLOR,
                fg=ACCENT_COLOR,
                font=("Segoe UI", 10)
            )
            greeting_label.pack(side=tk.RIGHT, padx=5)
            
            # جلب الاقتراحات
            suggestions = sugg_manager.get_all_suggestions(5)
            
            for sugg in suggestions:
                self._create_suggestion_btn(sugg)
                
        except Exception as e:
            print(f"Suggestions error: {e}")

    def _create_suggestion_btn(self, suggestion: dict):
        """إنشاء زر اقتراح"""
        btn_text = f"{suggestion.get('icon', '💡')} {suggestion.get('text', '')}"
        
        btn = tk.Button(
            self.suggestions_frame,
            text=btn_text,
            command=lambda s=suggestion['text']: self._run_suggestion(s),
            bg="#2d2d2d",
            fg=ACCENT_COLOR,
            font=("Segoe UI", 9),
            relief="flat",
            padx=8,
            pady=2,
            cursor="hand2"
        )
        btn.pack(side=tk.RIGHT, padx=3)
        
        # Hover effect
        btn.bind("<Enter>", lambda e: btn.config(bg="#3d3d3d"))
        btn.bind("<Leave>", lambda e: btn.config(bg="#2d2d2d"))

    def _run_suggestion(self, text: str):
        """تنفيذ اقتراح"""
        self.entry.delete(0, tk.END)
        self.entry.insert(0, text)
        self.send_command(None)

    # ═══════════════════════════════════════════════════════════
    # Auto-complete
    # ═══════════════════════════════════════════════════════════

    def _on_entry_change(self, event):
        """تحديث الاقتراحات عند الكتابة"""
        # تجاهل بعض المفاتيح
        if event.keysym in ('Down', 'Up', 'Return', 'Escape'):
            return
        
        text = self.entry.get().strip()
        
        # إخفاء إذا كان النص قصيراً
        if len(text) < 2:
            self._hide_autocomplete(None)
            return
        
        # جلب الاقتراحات
        suggestions = self._get_app_suggestions(text)
        
        if suggestions:
            self._show_autocomplete(suggestions)
        else:
            self._hide_autocomplete(None)

    def _get_app_suggestions(self, text: str) -> list:
        """جلب اقتراحات التطبيقات"""
        try:
            from actions import opener
            apps = list(opener.apps_index.keys())
            
            text_lower = text.lower()
            
            # البحث في التطبيقات
            matches = []
            for app in apps:
                if text_lower in app.lower():
                    matches.append(app)
                if len(matches) >= 8:
                    break
            
            return matches
        except:
            return []

    def _show_autocomplete(self, suggestions: list):
        """عرض قائمة الاقتراحات"""
        self.autocomplete_list.delete(0, tk.END)
        
        for s in suggestions:
            self.autocomplete_list.insert(tk.END, f"  افتح {s}")
        
        if not self.autocomplete_visible:
            # وضع القائمة فوق الـ input
            self.autocomplete_list.place(
                in_=self.entry,
                x=0,
                y=-self.autocomplete_list.winfo_reqheight(),
                width=self.entry.winfo_width()
            )
            self.autocomplete_visible = True

    def _hide_autocomplete(self, event):
        """إخفاء قائمة الاقتراحات"""
        if self.autocomplete_visible:
            self.autocomplete_list.place_forget()
            self.autocomplete_visible = False

    def _focus_autocomplete(self, event):
        """التركيز على قائمة الاقتراحات"""
        if self.autocomplete_visible and self.autocomplete_list.size() > 0:
            self.autocomplete_list.focus_set()
            self.autocomplete_list.selection_set(0)

    def _select_autocomplete(self, event):
        """اختيار اقتراح"""
        selection = self.autocomplete_list.curselection()
        if selection:
            text = self.autocomplete_list.get(selection[0])
            self.entry.delete(0, tk.END)
            self.entry.insert(0, text.strip())
            self._hide_autocomplete(None)
            self.entry.focus_set()
            # إرسال الأمر مباشرة
            self.send_command(None)

    # ═══════════════════════════════════════════════════════════
    # نافذة الإعدادات
    # ═══════════════════════════════════════════════════════════

    def open_settings(self):
        """فتح نافذة الإعدادات"""
        try:
            from ui.config_window import show_config_window
            show_config_window(self.root)
        except ImportError as e:
            self.update_log(f"❌ خطأ في تحميل الإعدادات: {e}", "error")
        except Exception as e:
            self.update_log(f"❌ خطأ: {e}", "error")

    # ═══════════════════════════════════════════════════════════
    # الأوامر الصوتية
    # ═══════════════════════════════════════════════════════════

    def _setup_voice(self):
        """تهيئة نظام الصوت"""
        try:
            from core.voice import get_voice_listener
            self.voice_listener = get_voice_listener()
            
            if self.voice_listener.is_available():
                self.voice_listener.set_callbacks(
                    on_result=self._on_voice_result,
                    on_error=self._on_voice_error,
                    on_status=self._on_voice_status
                )
                self.update_log("🎤 نظام الصوت جاهز", "success")
            else:
                self.mic_btn.config(state=tk.DISABLED, bg="#555555")
                self.update_log("⚠️ نظام الصوت غير متوفر", "warning")
        except Exception as e:
            print(f"Voice setup error: {e}")
            self.voice_listener = None

    def start_voice_input(self):
        """بدء الاستماع للأمر الصوتي"""
        if not hasattr(self, 'voice_listener') or not self.voice_listener:
            self.update_log("❌ نظام الصوت غير متوفر", "error")
            return
        
        if self.voice_listener.is_listening():
            return
        
        # تغيير لون الزر للإشارة للاستماع
        self.mic_btn.config(bg=ERROR_COLOR)
        self.voice_listener.listen_arabic()

    def _on_voice_result(self, text: str):
        """استلام نتيجة الصوت"""
        self.root.after(0, lambda: self._handle_voice_result(text))

    def _handle_voice_result(self, text: str):
        """معالجة نتيجة الصوت (thread-safe)"""
        self.mic_btn.config(bg="#333333")
        self.update_log(f"🎤 أنت: {text}", "info")
        self.orchestrator.process_request(text)

    def _on_voice_error(self, error: str):
        """استلام خطأ من الصوت"""
        self.root.after(0, lambda: self._handle_voice_error(error))

    def _handle_voice_error(self, error: str):
        """معالجة خطأ الصوت (thread-safe)"""
        self.mic_btn.config(bg="#333333")
        self.update_log(error, "warning")

    def _on_voice_status(self, status: str):
        """تحديث حالة الصوت"""
        self.root.after(0, lambda: self._log_thread_safe(status, "thought"))


# ═══════════════════════════════════════════════════════════
# التشغيل
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    root = tk.Tk()
    app = JarvisApp(root)
    root.mainloop()