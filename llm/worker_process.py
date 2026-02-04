"""
🧠 LLM Worker Process
=====================
Server مستقل يشغل الـ LLM ويتواصل عبر TCP Socket.
يعمل في Process منفصل لعزل الـ crashes عن الـ UI.

التشغيل:
    python llm/worker_process.py
"""

import json
import os
import sys
from multiprocessing.connection import Listener

# إضافة المجلد الرئيسي للـ path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llama_cpp import Llama
from llm.prompts import SYSTEM_PROMPT

# ═══════════════════════════════════════════════════════════
# الإعدادات
# ═══════════════════════════════════════════════════════════

# مسار الموديل (يمكن تغييره)
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Meta-Llama-3.1-8B-Instruct-Q6_K_L.gguf")

# إعدادات الـ IPC
ADDRESS = ('localhost', 6000)
AUTHKEY = b"jarvis"

# ═══════════════════════════════════════════════════════════
# الدوال المساعدة
# ═══════════════════════════════════════════════════════════

def extract_json(text: str):
    """استخراج JSON من نص الموديل - يدعم كائن أو قائمة"""
    text = text.strip()
    
    # محاولة 1: قائمة أوامر
    try:
        start = text.find("[")
        end = text.rfind("]") + 1
        if start != -1 and end > start:
            return json.loads(text[start:end])
    except json.JSONDecodeError:
        pass
    
    # محاولة 2: كائن واحد
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(text[start:end])
    except json.JSONDecodeError:
        pass
    
    return None


def handle_request(llm: Llama, request: dict) -> dict:
    """معالجة طلب واحد"""
    try:
        prompt = request.get("prompt", "")
        app_context = request.get("app_context", "")
        
        # بناء الـ prompt الكامل
        full_prompt = SYSTEM_PROMPT.format(
            known_apps=app_context,
            user_input=prompt
        )
        
        # استدعاء الموديل
        output = llm(
            full_prompt,
            max_tokens=250,
            temperature=0.1,
            stop=["<|eot_id|>"]
        )
        
        text = output['choices'][0]['text'].strip()
        
        # استخراج JSON
        parsed = extract_json(text)
        
        if parsed:
            return {
                "success": True,
                "response": parsed,
                "raw_text": text
            }
        else:
            return {
                "success": False,
                "error": "No valid JSON in response",
                "raw_text": text
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# ═══════════════════════════════════════════════════════════
# الـ Main Server Loop
# ═══════════════════════════════════════════════════════════

def start_worker():
    """تشغيل الـ LLM Worker Server"""
    print("=" * 50)
    print("🧠 LLM Worker Starting...")
    print(f"📍 Address: {ADDRESS[0]}:{ADDRESS[1]}")
    print(f"📦 Model: {os.path.basename(MODEL_PATH)}")
    print("=" * 50)
    
    # تحميل الموديل
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Model not found: {MODEL_PATH}")
        return
    
    print("⏳ Loading model (this may take a while)...")
    llm = Llama(
        model_path=MODEL_PATH,
        n_ctx=4096,
        n_gpu_layers=0,  # CPU only للاستقرار
        verbose=False
    )
    print("✅ Model loaded successfully!")
    
    # بدء الـ Server
    print(f"\n🚀 Server listening on {ADDRESS[0]}:{ADDRESS[1]}")
    print("📡 Waiting for connections...\n")
    
    try:
        with Listener(ADDRESS, authkey=AUTHKEY) as listener:
            while True:
                try:
                    conn = listener.accept()
                    print(f"📨 Connection from: {listener.last_accepted}")
                    
                    # استقبال الطلب
                    request = conn.recv()
                    print(f"📝 Request: {request.get('prompt', '')[:50]}...")
                    
                    # معالجة الطلب
                    result = handle_request(llm, request)
                    
                    # إرسال النتيجة
                    conn.send(result)
                    
                    if result.get("success"):
                        print(f"✅ Response sent: {result.get('response', {}).get('intent', 'N/A')}")
                    else:
                        print(f"⚠️ Error: {result.get('error', 'Unknown')}")
                    
                    conn.close()
                    
                except Exception as e:
                    print(f"❌ Connection error: {e}")
                    
    except KeyboardInterrupt:
        print("\n🛑 Worker shutting down...")
    except Exception as e:
        print(f"❌ Server error: {e}")


if __name__ == "__main__":
    start_worker()
