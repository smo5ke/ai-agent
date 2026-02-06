# core/vision_engine.py
"""
👁️ Vision Engine - عيون جارفيس (Powered by Ollama)
يستخدم نموذج llama3.2-vision لقراءة وتحليل الصور بعمق.
"""
import os
import pyautogui
from pathlib import Path

# Dependency Check
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    print("❌ Ollama library not found. Run: pip install ollama")

class VisionEngine:
    def __init__(self, model="llama3.2-vision"):
        self.model = model
        self.ready = OLLAMA_AVAILABLE

    def capture_screen(self, save_path: str = "screen_shot.png") -> str:
        """التقاط صورة للشاشة"""
        try:
            screenshot = pyautogui.screenshot()
            screenshot.save(save_path)
            return save_path
        except Exception as e:
            print(f"❌ Screenshot failed: {e}")
            return None

    def analyze_image(self, image_path: str, user_prompt: str = "Describe this image in detail") -> str:
        """تحليل الصورة باستخدام نموذج الرؤية"""
        if not self.ready:
            return "❌ Vision system is not ready (Ollama library missing)."
            
        if not os.path.exists(image_path):
            return f"❌ Image not found: {image_path}"

        try:
            print(f"👁️ Analyzing image with {self.model}...")
            response = ollama.chat(
                model=self.model,
                messages=[{
                    'role': 'user',
                    'content': user_prompt,
                    'images': [image_path]
                }]
            )
            return response['message']['content']
        except Exception as e:
            return f"❌ Vision Analysis Error: {e}\n(Make sure Ollama is running and 'llama3.2-vision' is pulled)"

    def see_screen(self) -> str:
        """الرؤية الحية: تصوير الشاشة ووصف محتوياتها"""
        path = self.capture_screen()
        if path:
            # استخدام وصف دقيق لاستخراج المعلومات
            prompt = "What do you see on this screen? If there is text, read it. If there is an error, explain it."
            description = self.analyze_image(path, prompt)
            
            # تنظيف
            try:
                os.remove(path)
            except:
                pass
                
            return description
        return "Failed to capture screen."

    # Legacy alias for backward compatibility (optional)
    def read_image(self, image_path: str) -> str:
        return self.analyze_image(image_path, "Extract all text from this image exactly as it appears.")

if __name__ == "__main__":
    vision = VisionEngine()
    if vision.ready:
        print("👁️ Vision Ready via Ollama.")
        # Test if user wants to run a quick test
        # print(vision.see_screen())
    else:
        print("❌ Vision not ready.")
