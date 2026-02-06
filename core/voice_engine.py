# core/voice_engine.py
"""
🗣️ Voice Engine - فم جارفيس
يستخدم edge-tts لتوليد صوت طبيعي (عربي/إنجليزي)
"""
import os
import asyncio
import pygame
import threading
from langdetect import detect
import edge_tts
import speech_recognition as sr

class VoiceEngine:
    def __init__(self):
        # إعدادات الأصوات
        self.VOICE_AR = "ar-EG-ShakirNeural"  # صوت عربي طبيعي
        self.VOICE_EN = "en-US-ChristopherNeural"  # صوت إنجليزي
        self.output_file = "speech.mp3"
        
        # تهيئة pygame للصوت
        pygame.mixer.init()
        self.is_speaking = False
        
        # تهيئة التعرف على الصوت
        self.recognizer = sr.Recognizer()
        # تحسين الحساسية
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True

    def listen(self) -> str:
        """الاستماع للميكروفون وتحويل الصوت لنص"""
        try:
            with sr.Microphone() as source:
                print("🎤 Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                print("👂 Listening...")
                # timeout: كم ينتظر قبل أن يبدأ الكلام (reduced to 2s)
                # phrase_time_limit: أقصى مدة للجملة (reduced to 5s)
                audio = self.recognizer.listen(source, timeout=2, phrase_time_limit=5)
                
                print("⏳ Recognizing...")
                # المحاولة بالعربية أولاً
                try:
                    text = self.recognizer.recognize_google(audio, language="ar-SA")
                    return text
                except sr.UnknownValueError:
                    # إذا فشل، نجرب الإنجليزية
                    try:
                        text = self.recognizer.recognize_google(audio, language="en-US")
                        return text
                    except sr.UnknownValueError:
                        return ""
                except sr.RequestError as e:
                    print(f"❌ Connection Error: {e}")
                    return ""
                    
        except Exception as e:
            print(f"❌ Microphone Error: {e}")
            return ""

    def _detect_language(self, text: str) -> str:
        """كتشاف لغة النص"""
        try:
            # طريقة بسيطة: إذا كان يحتوي على حروف عربية فهو عربي
            if any("\u0600" <= char <= "\u06FF" for char in text):
                return "ar"
            return "en"
        except:
            return "en"

    def speak(self, text: str):
        """دالة التحدث الرئيسية (Non-blocking)"""
        # تشغيل في Thread منفصل لعدم تجميد الواجهة
        threading.Thread(target=self._speak_sync, args=(text,), daemon=True).start()

    def _speak_sync(self, text: str):
        """التنفيذ الفعلي (متزامن داخل الـ Thread)"""
        if not text or len(text.strip()) == 0:
            return

        # 1. تحديد الصوت المناسب
        lang = self._detect_language(text)
        voice = self.VOICE_AR if lang == "ar" else self.VOICE_EN
        
        # 2. توليد الصوت (Async Wrapper)
        try:
            asyncio.run(self._generate_audio(text, voice))
            
            # 3. تشغيل الصوت
            self._play_audio()
        except Exception as e:
            print(f"❌ Voice Error: {e}")

    async def _generate_audio(self, text: str, voice: str):
        """توليد ملف الصوت باستخدام edge-tts"""
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(self.output_file)

    def _play_audio(self):
        """تشغيل الملف الناتج"""
        try:
            # التأكد من عدم تشغيل صوت سابق
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
                
            pygame.mixer.music.load(self.output_file)
            pygame.mixer.music.play()
            
            self.is_speaking = True
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            self.is_speaking = False
            
            # تحرير الملف (اختياري، لكن pygame يبقيه مفتوحاً أحياناً)
            pygame.mixer.music.unload()
        except Exception as e:
            print(f"❌ Playback Error: {e}")

# تجربة عند التشغيل المباشر
if __name__ == "__main__":
    engine = VoiceEngine()
    print("🔊 Testing English...")
    engine._speak_sync("Hello, I am Jarvis.")
    
    print("🔊 Testing Arabic...")
    engine._speak_sync("مرحباً، أنا جارفيس. كيف حالك اليوم؟")
