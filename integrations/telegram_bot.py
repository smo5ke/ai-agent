"""
🤖 Telegram Bot - التحكم عن بعد
================================
التحكم بـ Jarvis عبر Telegram.
"""

import asyncio
import threading
from typing import Optional, Callable

# محاولة استيراد المكتبة
try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("⚠️ python-telegram-bot not installed. Run: pip install python-telegram-bot")


class TelegramBot:
    """بوت Telegram للتحكم عن بعد"""
    
    def __init__(self, token: str, allowed_users: list = None):
        """
        تهيئة البوت.
        
        Args:
            token: توكن البوت من @BotFather
            allowed_users: قائمة user_ids المسموح لهم (للأمان)
        """
        self.token = token
        self.allowed_users = allowed_users or []
        self._app = None
        self._running = False
        self._thread = None
        self._orchestrator = None
        self._on_message = None
        
    def set_orchestrator(self, orchestrator):
        """ربط الـ Orchestrator"""
        self._orchestrator = orchestrator
    
    def set_message_callback(self, callback: Callable[[str, str], None]):
        """callback عند إرسال رسالة للبوت"""
        self._on_message = callback
    
    def _is_authorized(self, user_id: int) -> bool:
        """فحص صلاحية المستخدم"""
        if not self.allowed_users:
            return True  # السماح للجميع إذا لم تُحدد قائمة
        return user_id in self.allowed_users
    
    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /start"""
        user = update.effective_user
        
        if not self._is_authorized(user.id):
            await update.message.reply_text("⛔ غير مصرح لك باستخدام هذا البوت.")
            return
        
        await update.message.reply_text(
            f"🤖 مرحباً {user.first_name}!\n\n"
            f"أنا Jarvis - مساعدك الذكي.\n\n"
            f"📋 الأوامر المتاحة:\n"
            f"/status - حالة النظام\n"
            f"/tasks - المهام المجدولة\n"
            f"/watches - مهام المراقبة\n\n"
            f"أو أرسل أي أمر مباشرة:\n"
            f"• افتح كروم\n"
            f"• ذكرني بعد 5 دقائق\n"
            f"• ابحث عن بايثون"
        )
    
    async def _status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /status"""
        if not self._is_authorized(update.effective_user.id):
            return
        
        status_text = (
            "🖥️ **حالة النظام**\n\n"
            f"✅ Jarvis: يعمل\n"
            f"🤖 Telegram Bot: متصل\n"
        )
        
        # إضافة معلومات المهام
        try:
            from core.scheduler import get_scheduler
            scheduler = get_scheduler()
            tasks = scheduler.get_tasks_for_ui()
            status_text += f"⏰ المهام المجدولة: {len(tasks)}\n"
        except:
            pass
        
        # إضافة معلومات المراقبة
        try:
            from actions import fs_manager
            watches = fs_manager.get_active_watches()
            status_text += f"👁️ مهام المراقبة: {len(watches)}\n"
        except:
            pass
        
        await update.message.reply_text(status_text, parse_mode='Markdown')
    
    async def _tasks_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /tasks"""
        if not self._is_authorized(update.effective_user.id):
            return
        
        try:
            from core.scheduler import get_scheduler
            scheduler = get_scheduler()
            tasks = scheduler.get_tasks_for_ui()
            
            if not tasks:
                await update.message.reply_text("📋 لا توجد مهام مجدولة.")
                return
            
            text = "⏰ **المهام المجدولة:**\n\n"
            for t in tasks:
                text += f"• {t.get('command', '?')} - {t.get('remaining', '?')}\n"
            
            await update.message.reply_text(text, parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ: {e}")
    
    async def _watches_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /watches"""
        if not self._is_authorized(update.effective_user.id):
            return
        
        try:
            from actions import fs_manager
            watches = fs_manager.get_active_watches()
            
            if not watches:
                await update.message.reply_text("👁️ لا توجد مهام مراقبة نشطة.")
                return
            
            text = "👁️ **مهام المراقبة:**\n\n"
            for w in watches:
                text += f"• {w.get('folder', '?')}\n"
            
            await update.message.reply_text(text, parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ: {e}")
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة الرسائل النصية"""
        if not self._is_authorized(update.effective_user.id):
            return
        
        user_text = update.message.text
        
        # إرسال للـ Orchestrator
        if self._orchestrator:
            try:
                # تنفيذ الأمر
                await update.message.reply_text(f"🔄 جاري تنفيذ: {user_text}")
                
                # تنفيذ في thread منفصل
                result = await asyncio.get_event_loop().run_in_executor(
                    None, 
                    lambda: self._execute_command(user_text)
                )
                
                await update.message.reply_text(f"✅ {result or 'تم التنفيذ'}")
            except Exception as e:
                await update.message.reply_text(f"❌ خطأ: {e}")
        else:
            await update.message.reply_text("⚠️ النظام غير جاهز بعد.")
    
    def _execute_command(self, text: str) -> str:
        """تنفيذ أمر عبر الـ Orchestrator"""
        if not self._orchestrator:
            return "غير متصل بالنظام"
        
        # تنفيذ الأمر
        self._orchestrator.process_request(text)
        return "تم إرسال الأمر"
    
    async def send_message(self, chat_id: int, text: str):
        """إرسال رسالة لمستخدم معين"""
        if self._app:
            await self._app.bot.send_message(chat_id=chat_id, text=text)
    
    def start(self):
        """بدء البوت"""
        if not TELEGRAM_AVAILABLE:
            print("❌ Telegram not available")
            return
        
        if not self.token:
            print("❌ No Telegram token provided")
            return
        
        def run_bot():
            asyncio.run(self._run())
        
        self._thread = threading.Thread(target=run_bot, daemon=True)
        self._thread.start()
        self._running = True
        print("🤖 Telegram Bot started")
    
    async def _run(self):
        """تشغيل البوت"""
        self._app = Application.builder().token(self.token).build()
        
        # إضافة الأوامر
        self._app.add_handler(CommandHandler("start", self._start_command))
        self._app.add_handler(CommandHandler("status", self._status_command))
        self._app.add_handler(CommandHandler("tasks", self._tasks_command))
        self._app.add_handler(CommandHandler("watches", self._watches_command))
        self._app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
        
        # بدء البوت
        await self._app.initialize()
        await self._app.start()
        await self._app.updater.start_polling()
        
        # البقاء يعمل
        while self._running:
            await asyncio.sleep(1)
    
    def stop(self):
        """إيقاف البوت"""
        self._running = False


# Singleton
_bot = None

def get_telegram_bot(token: str = None) -> TelegramBot:
    """جلب البوت"""
    global _bot
    if _bot is None and token:
        _bot = TelegramBot(token)
    return _bot


def init_telegram(token: str, orchestrator=None, allowed_users: list = None):
    """تهيئة وتشغيل البوت"""
    global _bot
    _bot = TelegramBot(token, allowed_users)
    if orchestrator:
        _bot.set_orchestrator(orchestrator)
    _bot.start()
    return _bot
