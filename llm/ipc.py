"""
🔌 LLM IPC Client
==================
واجهة للتواصل مع الـ LLM Worker Process عبر TCP Socket.
"""

import socket
from multiprocessing.connection import Client
from typing import Optional

# ═══════════════════════════════════════════════════════════
# الإعدادات (يجب أن تتطابق مع worker_process.py)
# ═══════════════════════════════════════════════════════════

ADDRESS = ('localhost', 6000)
AUTHKEY = b"jarvis"
DEFAULT_TIMEOUT = 30  # ثواني


# ═══════════════════════════════════════════════════════════
# الدوال الرئيسية
# ═══════════════════════════════════════════════════════════

def is_worker_available() -> bool:
    """فحص إذا كان الـ Worker متاح"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(ADDRESS)
        sock.close()
        return result == 0
    except:
        return False


def think(prompt: str, app_context: str = "", timeout: int = DEFAULT_TIMEOUT) -> dict:
    """
    إرسال طلب للـ LLM Worker وانتظار الرد.
    
    Args:
        prompt: النص المطلوب تحليله
        app_context: قائمة التطبيقات المتاحة
        timeout: مهلة الانتظار بالثواني
    
    Returns:
        dict: النتيجة تحتوي على:
            - success: True/False
            - response: الـ JSON المحلل (إذا نجح)
            - error: رسالة الخطأ (إذا فشل)
    """
    
    # فحص توفر الـ Worker
    if not is_worker_available():
        return {
            "success": False,
            "error": "LLM Worker غير متصل. تأكد من تشغيله: python llm/worker_process.py"
        }
    
    try:
        # إنشاء الاتصال
        conn = Client(ADDRESS, authkey=AUTHKEY)
        
        # إرسال الطلب
        request = {
            "prompt": prompt,
            "app_context": app_context
        }
        conn.send(request)
        
        # انتظار الرد مع timeout
        if conn.poll(timeout):
            result = conn.recv()
            conn.close()
            return result
        else:
            conn.close()
            return {
                "success": False,
                "error": f"انتهت المهلة ({timeout} ثانية) - الموديل بطيء جداً"
            }
            
    except ConnectionRefusedError:
        return {
            "success": False,
            "error": "لا يمكن الاتصال بـ LLM Worker. هل هو قيد التشغيل؟"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"خطأ في الاتصال: {str(e)}"
        }


# ═══════════════════════════════════════════════════════════
# اختبار سريع
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("🧪 Testing LLM IPC...")
    
    if is_worker_available():
        print("✅ Worker is available!")
        result = think("افتح كروم", "chrome, notepad, calc")
        print(f"📤 Result: {result}")
    else:
        print("❌ Worker is not available. Start it with: python llm/worker_process.py")
