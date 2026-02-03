import webbrowser
import threading

# سنحتاج هذه المكتبات للأتمتة
try:
    import pyautogui
    import pyperclip
    import time
except ImportError: pass

class WebAction:
    def google_search(self, query):
        url = f"https://www.google.com/search?q={query}"
        webbrowser.open(url)
        return f"جاري البحث في جوجل عن: {query}"

    def youtube_search(self, query):
        url = f"https://www.youtube.com/results?search_query={query}"
        webbrowser.open(url)
        return f"جاري البحث في يوتيوب عن: {query}"
        
    def write_note(self, text):
        """هذه وظيفة ماكرو، نضعها هنا مؤقتاً أو في ملف macro.py"""
        def _task():
            import subprocess
            subprocess.Popen("notepad.exe")
            time.sleep(1)
            pyperclip.copy(text)
            pyautogui.hotkey('ctrl', 'v')
        
        threading.Thread(target=_task).start()
        return "جاري كتابة الملاحظة..."