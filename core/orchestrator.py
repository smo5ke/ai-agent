import threading
from core.schemas import Command
from core.permissions import check_permission, SecurityLevel
from core.memory import Memory
from llm.worker import Brain
from actions.plugin_loader import PluginLoader 
# استيراد العضلات الجديدة
from actions import opener, web_ops, fs_manager 

class Orchestrator:
    def __init__(self, model_path):
        self.brain = Brain(model_path)
        self.memory = Memory()
        self.ui_callback = None 
        self.plugin_manager = PluginLoader()
        self.plugin_manager.load_all()
        
    def start_brain(self):
        # تشغيل الدماغ في الخلفية
        threading.Thread(target=self.brain.load, daemon=True).start()

    def process_request(self, user_text):
        # 1. إعطاء خبر للواجهة أننا نفكر
        if self.ui_callback: self.ui_callback("🤔 جاري التحليل...", "thought")

        # 2. تشغيل التفكير في خيط منفصل
        threading.Thread(target=self._run_logic, args=(user_text,)).start()

    def _run_logic(self, user_text):
        # تأكد أن هذا السطر والأسطر التالية تبدأ بمسافات فقط (Spaces)
        apps_context = ", ".join(list(opener.apps_index.keys())[:100])
        
        if self.ui_callback: 
            self.ui_callback("🤔 جاري التحليل...", "thought")
        
        # التفكير
        command = self.brain.think(user_text, apps_context)
        
        # تسجيل الحدث في الذاكرة
        self.memory.add_interaction(user_text, command.dict())

        if command.intent == "unknown":
            if self.ui_callback: 
                self.ui_callback("⚠️ لم أفهم الأمر، حاول صياغته بشكل آخر.", "error")
            return

        # فحص الأمان والتنفيذ
        security = check_permission(command.intent)
        self.execute(command)

    def execute(self, command: Command):
        msg = ""
        
        # توجيه الأوامر للملفات المتخصصة
        if command.intent == "open":
            msg = opener.run(command.target)
            
        elif command.intent == "macro":
            # الآن الحقل cmd موجود ولن يعطي خطأ
            if command.cmd == "web_search":
                msg = web_ops.google_search(command.param)
            elif command.cmd == "youtube_search":
                msg = web_ops.youtube_search(command.param)
            elif command.cmd == "write_note":
                msg = web_ops.write_note(command.param)

        elif command.intent == "clean":
            # لاحظ استخدام filter_key
            msg = fs_manager.clean_folder(command.target, command.filter_key, command.destination or "Documents")

        elif command.intent == "watch":
            # لاحظ استخدام loc و action_type
            msg = fs_manager.start_watch(command.loc, command.filter_key, command.action_type, self.ui_callback)

        # إرسال النتيجة النهائية للواجهة
        if self.ui_callback and msg:
            self.ui_callback(f"✅ {msg}", "success")
            self.memory.add_system_event(command.intent, msg)
            
        if not msg:
            # نحاول تشغيل إضافة باسم "chat" أو باسم الـ intent نفسه
            msg = self.plugin_manager.run_plugin("chat", command.param or command.intent)
            
        if self.ui_callback and msg:
            self.ui_callback(f"✅ {msg}", "success")