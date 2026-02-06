# ui/worker.py
"""
🔧 Agent Worker - خيط العمل في الخلفية
يربط الـ GUI بالـ Orchestrator
"""
from PyQt6.QtCore import QThread, pyqtSignal
from typing import Optional


class AgentWorker(QThread):
    """Worker thread للتواصل مع الـ Orchestrator"""
    
    # Signals
    new_message = pyqtSignal(str, str)      # (text, sender: "user"/"ai")
    status_update = pyqtSignal(str)          # status message
    finished_processing = pyqtSignal(bool)   # success/failure
    
    def __init__(self, orchestrator):
        super().__init__()
        self.orchestrator = orchestrator
        self.user_input: Optional[str] = None
        self._running = True

    def process(self, text: str):
        """تعيين النص للمعالجة وبدء الخيط"""
        self.user_input = text
        if not self.isRunning():
            self.start()

    def run(self):
        """الحلقة الرئيسية"""
        if not self.user_input:
            return
        
        try:
            self.status_update.emit("🤔 جاري التفكير...")
            
            # معالجة الطلب
            result = self.orchestrator.process(self.user_input)
            
            # إرسال النتيجة
            if result.success:
                self.new_message.emit(result.message, "ai")
                self.status_update.emit("✅ تم")
            else:
                self.new_message.emit(f"❌ {result.message}", "ai")
                self.status_update.emit("❌ فشل")
            
            self.finished_processing.emit(result.success)
            
        except Exception as e:
            self.new_message.emit(f"⚠️ خطأ: {str(e)}", "ai")
            self.status_update.emit("⚠️ خطأ")
            self.finished_processing.emit(False)

    def stop(self):
        """إيقاف الـ Worker"""
        self._running = False
        self.quit()
        self.wait()
