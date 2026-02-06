# ui/main_window.py
"""
🖥️ Main Window - واجهة المحادثة
تصميم يشبه ChatGPT مع PyQt6
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLineEdit, QPushButton,
    QStatusBar, QLabel, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from ui.worker import AgentWorker


class ChatMessage(QFrame):
    """رسالة في المحادثة"""
    def __init__(self, text: str, sender: str, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        
        # النص
        label = QLabel(text)
        label.setWordWrap(True)
        label.setFont(QFont("Segoe UI", 11))
        
        # التنسيق حسب المرسل
        if sender == "user":
            self.setStyleSheet("""
                ChatMessage {
                    background-color: #0084ff;
                    border-radius: 15px;
                    margin-left: 50px;
                }
            """)
            label.setStyleSheet("color: white;")
        else:
            self.setStyleSheet("""
                ChatMessage {
                    background-color: #e4e6eb;
                    border-radius: 15px;
                    margin-right: 50px;
                }
            """)
            label.setStyleSheet("color: #050505;")
        
        layout.addWidget(label)


class MainWindow(QMainWindow):
    """النافذة الرئيسية"""
    
    def __init__(self, orchestrator):
        super().__init__()
        self.orchestrator = orchestrator
        self.worker = None
        
        # 🎙️ Voice Setup
        from core.voice_engine import VoiceEngine
        # 🎙️ Voice Setup
        from core.voice_engine import VoiceEngine
        self.voice = VoiceEngine()
        self.voice_enabled = False  # Default OFF as requested
        self.is_listening = False
        
        self.setup_ui()
        self.setup_worker()
        
    def setup_ui(self):
        """إعداد الواجهة"""
        self.setWindowTitle("🤖 Jarvis AI v9.0 (Voice Enabled)")
        self.setMinimumSize(800, 600)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a2e;
            }
            QListWidget {
                background-color: #16213e;
                border: none;
                border-radius: 10px;
                padding: 10px;
            }
            QLineEdit {
                background-color: #0f3460;
                border: 2px solid #e94560;
                border-radius: 20px;
                padding: 12px 20px;
                color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #00d9ff;
            }
            QPushButton {
                background-color: #e94560;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 12px 25px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff6b6b;
            }
            QPushButton:disabled {
                background-color: #444;
            }
            QStatusBar {
                background-color: #0f3460;
                color: #00d9ff;
            }
        """)
        
        # Central Widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        header = QLabel("🤖 Jarvis AI Assistant")
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.setStyleSheet("color: #00d9ff; margin-bottom: 10px;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Chat List
        self.chat_list = QListWidget()
        self.chat_list.setSpacing(8)
        self.chat_list.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        layout.addWidget(self.chat_list, 1)
        
        # Input Area (Lines 136-153)
        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("اكتب أمرك هنا... (مثال: أنشئ مجلد test)")
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field, 1)
        
        # 🔇 Speaker Toggle (NEW)
        self.speaker_btn = QPushButton("🔇") # Default Muted
        self.speaker_btn.setFixedWidth(40)
        self.speaker_btn.clicked.connect(self.toggle_voice)
        self.speaker_btn.setToolTip("تشغيل/إيقاف الصوت التلقائي")
        input_layout.addWidget(self.speaker_btn)

        # 🎤 Mic Button
        self.mic_btn = QPushButton("🎤")
        self.mic_btn.setFixedWidth(50)
        self.mic_btn.clicked.connect(self.toggle_listening) # Changed to toggle
        input_layout.addWidget(self.mic_btn)

        self.send_btn = QPushButton("إرسال ➤")
        self.send_btn.clicked.connect(self.send_message)
        self.send_btn.setFixedWidth(100)
        input_layout.addWidget(self.send_btn)
        
        layout.addLayout(input_layout)
        
        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("👋 مرحباً! اكتب أمرك وسأنفذه لك.")
        
        # رسالة ترحيب
        msg_welcome = "مرحباً! أنا Jarvis، مساعدك الذكي. 🤖\nيمكنني إنشاء الملفات والمجلدات وتنفيذ أكواد Python."
        self.add_message(msg_welcome, "ai")
        # Speak welcome message only if enabled (default OFF)
        if self.voice_enabled:
            self.voice.speak(msg_welcome)

    def setup_worker(self):
        """إعداد خيط العمل"""
        self.worker = AgentWorker(self.orchestrator)
        self.worker.new_message.connect(self.on_ai_message)
        self.worker.status_update.connect(self.on_status_update)
        self.worker.finished_processing.connect(self.on_processing_done)

    def send_message(self):
        """إرسال رسالة"""
        text = self.input_field.text().strip()
        if not text:
            return
        
        # عرض رسالة المستخدم
        self.add_message(text, "user")
        self.input_field.clear()
        
        # تعطيل الإدخال
        self.input_field.setEnabled(False)
        self.send_btn.setEnabled(False)
        
        # إرسال للـ Worker
        self.worker.user_input = text
        self.worker.start()

    def toggle_voice(self):
        """تفعيل/تعطيل الصوت التلقائي"""
        self.voice_enabled = not self.voice_enabled
        if self.voice_enabled:
            self.speaker_btn.setText("🔈")
            self.status_bar.showMessage("🔊 الصوت مفعل")
        else:
            self.speaker_btn.setText("🔇")
            self.status_bar.showMessage("🔇 الصوت معطل")

    def toggle_listening(self):
        """بدء أو إيقاف الاستماع"""
        if self.is_listening:
            # User wants to stop/cancel
            self.is_listening = False # Flag indicates 'stop requested'
            self.status_bar.showMessage("🛑 Stopping listener...")
            self.mic_btn.setText("🎤")
            # We cannot easily kill the thread, but we will ignore its result
            # and re-enable UI immediately.
            self.input_field.setEnabled(True)
            self.input_field.setFocus()
        else:
            # Start listening
            self.is_listening = True
            self.mic_btn.setText("🛑") # Change icon to Stop
            self.status_bar.showMessage("🎤 Listening... تكلم الآن")
            self.input_field.setEnabled(False)
            
            import threading
            threading.Thread(target=self._listen_thread, daemon=True).start()

    def _listen_thread(self):
        """خيط الاستماع"""
        # إذا قمنا بالإلغاء فوراً، لا داعي للاستماع
        if not self.is_listening: return

        text = self.voice.listen() # This blocks for 2-7 seconds
        
        # إذا قام المستخدم بالإلغاء أثناء الانتظار، نتجاهل النتيجة
        if not self.is_listening:
            return

        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, lambda: self._on_listen_finished(text))

    def _on_listen_finished(self, text):
        """بعد انتهاء الاستماع"""
        self.is_listening = False
        self.mic_btn.setText("🎤")
        self.input_field.setEnabled(True)
        self.input_field.setFocus()
        
        if text:
            self.input_field.setText(text)
            self.status_bar.showMessage("✅ تم التعرف على الصوت")
        else:
            self.status_bar.showMessage("❌ لم يتم التعرف على الصوت")

    def add_message(self, text: str, sender: str):
        """إضافة رسالة للمحادثة"""
        item = QListWidgetItem()
        widget = ChatMessage(text, sender)
        
        item.setSizeHint(widget.sizeHint())
        
        self.chat_list.addItem(item)
        self.chat_list.setItemWidget(item, widget)
        self.chat_list.scrollToBottom()

    def on_ai_message(self, text: str, sender: str):
        """استقبال رسالة من الـ AI"""
        self.add_message(text, sender)
        # 🗣️ Speak the response
        if sender == "ai" or sender == "assistant":
             if self.voice_enabled:
                 self.voice.speak(text)

    def on_status_update(self, status: str):
        """تحديث الحالة"""
        self.status_bar.showMessage(status)

    def on_processing_done(self, success: bool):
        """انتهاء المعالجة"""
        self.input_field.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.input_field.setFocus()

    def closeEvent(self, event):
        """إغلاق النافذة"""
        if self.worker:
            self.worker.stop()
        event.accept()
