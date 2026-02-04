"""
🎤 Voice - الأوامر الصوتية
===========================
نظام التعرف على الصوت وتحويله لنص.
"""

import threading
from typing import Callable, Optional

# محاولة استيراد المكتبات
try:
    import speech_recognition as sr
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False
    print("⚠️ SpeechRecognition not installed. Run: pip install SpeechRecognition pyaudio")


class VoiceListener:
    """مستمع الأوامر الصوتية"""
    
    def __init__(self):
        self._listening = False
        self._recognizer = None
        self._microphone = None
        self._on_result = None
        self._on_error = None
        self._on_status = None
        
        if SPEECH_AVAILABLE:
            self._recognizer = sr.Recognizer()
            # ضبط حساسية الميكروفون
            self._recognizer.energy_threshold = 300
            self._recognizer.dynamic_energy_threshold = True
            self._recognizer.pause_threshold = 0.8
    
    def is_available(self) -> bool:
        """فحص توفر نظام الصوت"""
        return SPEECH_AVAILABLE
    
    def set_callbacks(
        self, 
        on_result: Callable[[str], None],
        on_error: Callable[[str], None] = None,
        on_status: Callable[[str], None] = None
    ):
        """تعيين callbacks للنتائج والأخطاء"""
        self._on_result = on_result
        self._on_error = on_error
        self._on_status = on_status
    
    def listen_once(self, language: str = "ar-SA"):
        """
        استمع مرة واحدة وحوّل الصوت لنص.
        
        Args:
            language: اللغة (ar-SA للعربية، en-US للإنجليزية)
        """
        if not SPEECH_AVAILABLE:
            if self._on_error:
                self._on_error("❌ مكتبة الصوت غير متوفرة")
            return
        
        def _listen():
            try:
                if self._on_status:
                    self._on_status("🎤 جاري الاستماع...")
                
                self._listening = True
                
                with sr.Microphone() as source:
                    # تعديل للضوضاء المحيطة
                    self._recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    
                    # الاستماع
                    audio = self._recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
                if self._on_status:
                    self._on_status("🔄 جاري تحليل الصوت...")
                
                # تحويل لنص باستخدام Google
                text = self._recognizer.recognize_google(audio, language=language)
                
                if self._on_result:
                    self._on_result(text)
                    
            except sr.WaitTimeoutError:
                if self._on_error:
                    self._on_error("⏱️ انتهت المهلة - لم أسمع شيئاً")
            except sr.UnknownValueError:
                if self._on_error:
                    self._on_error("❓ لم أفهم ما قلته")
            except sr.RequestError as e:
                if self._on_error:
                    self._on_error(f"❌ خطأ في الاتصال: {e}")
            except Exception as e:
                if self._on_error:
                    self._on_error(f"❌ خطأ: {e}")
            finally:
                self._listening = False
                if self._on_status:
                    self._on_status("🎤 جاهز")
        
        # تشغيل في thread منفصل
        threading.Thread(target=_listen, daemon=True).start()
    
    def listen_arabic(self):
        """استمع بالعربية"""
        self.listen_once("ar-SA")
    
    def listen_english(self):
        """استمع بالإنجليزية"""
        self.listen_once("en-US")
    
    def is_listening(self) -> bool:
        """هل يستمع حالياً؟"""
        return self._listening
    
    def stop(self):
        """إيقاف الاستماع"""
        self._listening = False


# Singleton
_listener = None

def get_voice_listener() -> VoiceListener:
    """جلب مستمع الصوت"""
    global _listener
    if _listener is None:
        _listener = VoiceListener()
    return _listener
