"""
⚙️ Config UI - واجهة الإعدادات
==============================
نافذة إعدادات رسومية لـ Jarvis.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional

# ألوان التصميم
BG_COLOR = "#1e1e1e"
SIDEBAR_BG = "#252526"
FG_COLOR = "#00ff41"
ACCENT_COLOR = "#00ADB5"
WARNING_COLOR = "#FFC107"
CARD_BG = "#2d2d2d"


class ConfigWindow:
    """نافذة الإعدادات"""
    
    def __init__(self, parent: Optional[tk.Tk] = None):
        self.parent = parent
        self.window: Optional[tk.Toplevel] = None
        self.config_manager = None
        self.profile_manager = None
        self._load_managers()
    
    def _load_managers(self):
        """تحميل مديري الإعدادات"""
        try:
            from core.config import get_config_manager
            self.config_manager = get_config_manager()
        except:
            pass
        
        try:
            from core.profiles import get_profile_manager
            self.profile_manager = get_profile_manager()
        except:
            pass
    
    def show(self):
        """عرض نافذة الإعدادات"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return
        
        self.window = tk.Toplevel(self.parent) if self.parent else tk.Tk()
        self.window.title("⚙️ Jarvis Settings")
        self.window.geometry("600x500")
        self.window.configure(bg=BG_COLOR)
        self.window.resizable(True, True)
        
        # إنشاء Notebook للتبويبات
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background=BG_COLOR)
        style.configure('TNotebook.Tab', background=CARD_BG, foreground=FG_COLOR, padding=[10, 5])
        style.map('TNotebook.Tab', background=[('selected', ACCENT_COLOR)])
        
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # التبويبات
        self._create_general_tab()
        self._create_profiles_tab()
        self._create_security_tab()
        self._create_about_tab()
        
        # أزرار الحفظ
        self._create_buttons()
    
    # ═══════════════════════════════════════════════════════════
    # التبويب العام
    # ═══════════════════════════════════════════════════════════
    
    def _create_general_tab(self):
        """تبويب الإعدادات العامة"""
        frame = tk.Frame(self.notebook, bg=BG_COLOR)
        self.notebook.add(frame, text="🏠 عام")
        
        # العنوان
        tk.Label(
            frame, text="⚙️ الإعدادات العامة",
            bg=BG_COLOR, fg=ACCENT_COLOR, font=("Segoe UI", 14, "bold")
        ).pack(pady=15)
        
        # === اللغة ===
        lang_frame = self._create_card(frame, "🌐 اللغة")
        self.lang_var = tk.StringVar(value="ar")
        
        ttk.Radiobutton(lang_frame, text="العربية", variable=self.lang_var, value="ar").pack(side='left', padx=10)
        ttk.Radiobutton(lang_frame, text="English", variable=self.lang_var, value="en").pack(side='left', padx=10)
        
        # === تنسيق الوقت ===
        time_frame = self._create_card(frame, "🕐 تنسيق الوقت")
        self.time_var = tk.StringVar(value="24h")
        
        ttk.Radiobutton(time_frame, text="24 ساعة", variable=self.time_var, value="24h").pack(side='left', padx=10)
        ttk.Radiobutton(time_frame, text="12 ساعة (AM/PM)", variable=self.time_var, value="12h").pack(side='left', padx=10)
        
        # === الإشعارات ===
        notif_frame = self._create_card(frame, "🔔 الإشعارات")
        self.notif_var = tk.BooleanVar(value=True)
        
        tk.Checkbutton(
            notif_frame, text="تفعيل إشعارات Windows",
            variable=self.notif_var, bg=CARD_BG, fg=FG_COLOR,
            selectcolor=BG_COLOR, activebackground=CARD_BG
        ).pack(side='left', padx=10)
        
        # === التشغيل التلقائي ===
        auto_frame = self._create_card(frame, "🚀 التشغيل")
        self.auto_start_var = tk.BooleanVar(value=False)
        
        tk.Checkbutton(
            auto_frame, text="تشغيل Jarvis عند بدء Windows",
            variable=self.auto_start_var, bg=CARD_BG, fg=FG_COLOR,
            selectcolor=BG_COLOR, activebackground=CARD_BG
        ).pack(side='left', padx=10)
    
    # ═══════════════════════════════════════════════════════════
    # تبويب الملفات الشخصية
    # ═══════════════════════════════════════════════════════════
    
    def _create_profiles_tab(self):
        """تبويب الملفات الشخصية"""
        frame = tk.Frame(self.notebook, bg=BG_COLOR)
        self.notebook.add(frame, text="👤 الأوضاع")
        
        tk.Label(
            frame, text="🎚️ أوضاع التشغيل",
            bg=BG_COLOR, fg=ACCENT_COLOR, font=("Segoe UI", 14, "bold")
        ).pack(pady=15)
        
        self.profile_var = tk.StringVar(value="safe")
        
        profiles = [
            ("🛡️ Safe Mode", "safe", "أقصى حماية - تأكيد كل العمليات"),
            ("⚡ Power Mode", "power", "سرعة مع حماية معتدلة"),
            ("🔇 Silent Mode", "silent", "تنفيذ بدون تأكيد أو إشعارات"),
        ]
        
        for title, value, desc in profiles:
            card = self._create_card(frame, title)
            
            tk.Radiobutton(
                card, text=desc,
                variable=self.profile_var, value=value,
                bg=CARD_BG, fg=FG_COLOR, selectcolor=BG_COLOR,
                activebackground=CARD_BG, font=("Segoe UI", 10)
            ).pack(side='left', padx=10)
        
        # تحميل الوضع الحالي
        if self.profile_manager:
            self.profile_var.set(self.profile_manager.current_profile)
    
    # ═══════════════════════════════════════════════════════════
    # تبويب الأمان
    # ═══════════════════════════════════════════════════════════
    
    def _create_security_tab(self):
        """تبويب إعدادات الأمان"""
        frame = tk.Frame(self.notebook, bg=BG_COLOR)
        self.notebook.add(frame, text="🔒 الأمان")
        
        tk.Label(
            frame, text="🔒 إعدادات الأمان",
            bg=BG_COLOR, fg=ACCENT_COLOR, font=("Segoe UI", 14, "bold")
        ).pack(pady=15)
        
        # === Dry-Run ===
        dry_frame = self._create_card(frame, "🧪 Dry-Run")
        self.dry_run_var = tk.BooleanVar(value=True)
        
        tk.Checkbutton(
            dry_frame, text="محاكاة العمليات الخطرة قبل التنفيذ",
            variable=self.dry_run_var, bg=CARD_BG, fg=FG_COLOR,
            selectcolor=BG_COLOR, activebackground=CARD_BG
        ).pack(side='left', padx=10)
        
        # === تأكيد الحذف ===
        delete_frame = self._create_card(frame, "🗑️ الحذف")
        self.confirm_delete_var = tk.BooleanVar(value=True)
        
        tk.Checkbutton(
            delete_frame, text="طلب تأكيد قبل حذف الملفات",
            variable=self.confirm_delete_var, bg=CARD_BG, fg=FG_COLOR,
            selectcolor=BG_COLOR, activebackground=CARD_BG
        ).pack(side='left', padx=10)
        
        # === مستوى الخطر ===
        risk_frame = self._create_card(frame, "⚠️ مستوى الخطر المسموح")
        self.risk_var = tk.StringVar(value="MEDIUM")
        
        risk_options = ["LOW", "MEDIUM", "HIGH"]
        for risk in risk_options:
            color = {"LOW": "#4CAF50", "MEDIUM": "#FFC107", "HIGH": "#FF5252"}[risk]
            tk.Radiobutton(
                risk_frame, text=risk,
                variable=self.risk_var, value=risk,
                bg=CARD_BG, fg=color, selectcolor=BG_COLOR,
                activebackground=CARD_BG
            ).pack(side='left', padx=10)
    
    # ═══════════════════════════════════════════════════════════
    # تبويب حول
    # ═══════════════════════════════════════════════════════════
    
    def _create_about_tab(self):
        """تبويب حول"""
        frame = tk.Frame(self.notebook, bg=BG_COLOR)
        self.notebook.add(frame, text="ℹ️ حول")
        
        # الشعار
        tk.Label(
            frame, text="🤖",
            bg=BG_COLOR, fg=ACCENT_COLOR, font=("Segoe UI", 48)
        ).pack(pady=20)
        
        tk.Label(
            frame, text="Jarvis AI Agent",
            bg=BG_COLOR, fg=FG_COLOR, font=("Segoe UI", 18, "bold")
        ).pack()
        
        tk.Label(
            frame, text="v2.0.0 - Enterprise Edition",
            bg=BG_COLOR, fg=ACCENT_COLOR, font=("Segoe UI", 12)
        ).pack(pady=5)
        
        tk.Label(
            frame, text="نظام ذكاء اصطناعي محلي للتحكم بـ Windows",
            bg=BG_COLOR, fg="#888", font=("Segoe UI", 10)
        ).pack(pady=10)
        
        # الإحصائيات
        stats_frame = tk.Frame(frame, bg=BG_COLOR)
        stats_frame.pack(pady=20)
        
        stats = [
            ("📁 الملفات", "40+"),
            ("🎯 Intents", "16"),
            ("📚 أمثلة", "30+"),
        ]
        
        for label, value in stats:
            tk.Label(
                stats_frame, text=f"{label}: {value}",
                bg=BG_COLOR, fg=FG_COLOR, font=("Segoe UI", 10)
            ).pack(side='left', padx=15)
    
    # ═══════════════════════════════════════════════════════════
    # مساعدات
    # ═══════════════════════════════════════════════════════════
    
    def _create_card(self, parent, title: str) -> tk.Frame:
        """إنشاء كارد"""
        container = tk.Frame(parent, bg=BG_COLOR)
        container.pack(fill='x', padx=20, pady=5)
        
        tk.Label(
            container, text=title,
            bg=BG_COLOR, fg=FG_COLOR, font=("Segoe UI", 10, "bold"),
            anchor='w'
        ).pack(fill='x')
        
        card = tk.Frame(container, bg=CARD_BG, padx=10, pady=10)
        card.pack(fill='x', pady=3)
        
        return card
    
    def _create_buttons(self):
        """أزرار الحفظ والإلغاء"""
        btn_frame = tk.Frame(self.window, bg=BG_COLOR)
        btn_frame.pack(fill='x', padx=10, pady=10)
        
        # زر الحفظ
        save_btn = tk.Button(
            btn_frame, text="💾 حفظ",
            bg=ACCENT_COLOR, fg="white",
            font=("Segoe UI", 11, "bold"),
            relief='flat', padx=20, pady=8,
            command=self._save_settings
        )
        save_btn.pack(side='right', padx=5)
        
        # زر الإلغاء
        cancel_btn = tk.Button(
            btn_frame, text="❌ إلغاء",
            bg="#555", fg="white",
            font=("Segoe UI", 11),
            relief='flat', padx=20, pady=8,
            command=self.window.destroy
        )
        cancel_btn.pack(side='right', padx=5)
        
        # زر إعادة تعيين
        reset_btn = tk.Button(
            btn_frame, text="🔄 إعادة تعيين",
            bg=WARNING_COLOR, fg="black",
            font=("Segoe UI", 11),
            relief='flat', padx=15, pady=8,
            command=self._reset_settings
        )
        reset_btn.pack(side='left', padx=5)
    
    def _save_settings(self):
        """حفظ الإعدادات"""
        try:
            # حفظ في ConfigManager
            if self.config_manager:
                self.config_manager.set("language", self.lang_var.get())
                self.config_manager.set("time_format", self.time_var.get())
                self.config_manager.set("notifications_enabled", self.notif_var.get())
                self.config_manager.set("auto_start", self.auto_start_var.get())
                self.config_manager.set("dry_run_enabled", self.dry_run_var.get())
                self.config_manager.set("confirm_delete", self.confirm_delete_var.get())
                self.config_manager.set("max_risk_level", self.risk_var.get())
                self.config_manager.save()
            
            # تغيير Profile
            if self.profile_manager:
                self.profile_manager.set_profile(self.profile_var.get())
            
            messagebox.showinfo("✅ تم", "تم حفظ الإعدادات بنجاح!")
            self.window.destroy()
            
        except Exception as e:
            messagebox.showerror("❌ خطأ", f"فشل حفظ الإعدادات: {e}")
    
    def _reset_settings(self):
        """إعادة تعيين الإعدادات"""
        if messagebox.askyesno("⚠️ تأكيد", "هل تريد إعادة تعيين كل الإعدادات؟"):
            self.lang_var.set("ar")
            self.time_var.set("24h")
            self.notif_var.set(True)
            self.auto_start_var.set(False)
            self.profile_var.set("safe")
            self.dry_run_var.set(True)
            self.confirm_delete_var.set(True)
            self.risk_var.set("MEDIUM")


# Singleton
_config_window: Optional[ConfigWindow] = None

def show_config_window(parent: Optional[tk.Tk] = None):
    """عرض نافذة الإعدادات"""
    global _config_window
    if _config_window is None:
        _config_window = ConfigWindow(parent)
    _config_window.show()
    return _config_window
