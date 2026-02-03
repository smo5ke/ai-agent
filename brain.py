import os
import json
import webbrowser
import subprocess
import shutil
import time
import threading
from llama_cpp import Llama

# --- 1. الموديل ---
MODEL_PATH = "qwen2.5-7b-instruct-q3_k_m.gguf"
if not os.path.exists(MODEL_PATH): exit()
llm = Llama(model_path=MODEL_PATH, n_ctx=8192, n_gpu_layers=-1, verbose=False)

# --- 2. إعدادات النظام ---
APPS_MAP = {}
FOLDERS_MAP = {}
SEARCH_PATHS = []

def get_system_context():
    # (نفس كود جلب التطبيقات والمجلدات السابق)
    global APPS_MAP, FOLDERS_MAP, SEARCH_PATHS
    user_home = os.path.expanduser("~")
    SEARCH_PATHS = [
        os.path.join(user_home, "Desktop"),
        os.path.join(user_home, "OneDrive", "Desktop"),
        os.path.join(user_home, "Documents")
    ]
    # (تخيل باقي كود الفهرسة هنا اختصاراً)

get_system_context()

# --- 3. المراقب المرن (The Flexible Watcher) ---
WATCH_CONFIG = {
    "active": False,
    "folder_path": "",
    "interval": 60, # الافتراضي دقيقة
    "action_type": "move_to_d" # الافتراضي
}

def background_watcher():
    print("👀 نظام المراقبة في وضع الاستعداد...")
    while True:
        if WATCH_CONFIG["active"]:
            folder = WATCH_CONFIG["folder_path"]
            interval = WATCH_CONFIG["interval"]
            
            if os.path.exists(folder):
                files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
                
                if files:
                    print(f"\n⚡ [تنبيه] تم رصد {len(files)} ملفات في {folder}")
                    # هنا ننفذ الأكشن (نقل تلقائي لمجلد باسم التاريخ مثلاً)
                    dest_base = "D:\\Auto_Sorted"
                    os.makedirs(dest_base, exist_ok=True)
                    
                    for f in files:
                        try:
                            src = os.path.join(folder, f)
                            dst = os.path.join(dest_base, f)
                            shutil.move(src, dst)
                            print(f"✅ تم أرشفة: {f}")
                        except: pass
            
            # ننتظر الفترة التي حددها المستخدم بالضبط
            time.sleep(interval)
        else:
            # إذا المراقبة مطفية، بنشيك كل ثانية بس عشان ما نعلق
            time.sleep(1)

# تشغيل الخيط
t = threading.Thread(target=background_watcher, daemon=True)
t.start()

# --- 4. الدماغ (منطق الكلمات المفتاحية) ---
def think(prompt):
    # فحص يدوي سريع للكلمة المفتاحية (أسرع وأدق من الموديل)
    if prompt.strip().startswith("انتهت المراقبة") or prompt == "وقف":
        return json.dumps({"action": "stop_monitoring"})
        
    if prompt.strip().startswith("مراقبة"):
        # هنا بنخلي الموديل يستخرج التفاصيل بس (المجلد + الوقت)
        system_prompt = f"""
        User wants to START MONITORING. Extract:
        1. 'folder': The folder name.
        2. 'minutes': The time interval in minutes (default to 15 if not said).
        
        User said: "{prompt}"
        Output JSON: {{"action": "start_monitoring", "folder": "name", "minutes": 10}}
        """
        output = llm(f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n", max_tokens=100, stop=["<|im_end|>"])
        return output['choices'][0]['text'].strip()

    # إذا مو مراقبة، كمل شغلك العادي
    system_prompt = """
    You are an OS Agent.
    TOOLS:
    1. {{"action": "open_app", "target": "name"}}
    2. {{"action": "manage_file", "operation": "move", "file_name": "name", "destination": "dest"}}
    """
    output = llm(f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n", max_tokens=200, stop=["<|im_end|>"])
    return output['choices'][0]['text'].strip()

# --- 5. التنفيذ ---
def execute(response_json):
    try:
        clean = response_json[response_json.find('{'):response_json.rfind('}')+1].replace('\\', '/')
        data = json.loads(clean)
        action = data.get("action")

        # --- أوامر المراقبة ---
        if action == "stop_monitoring":
            WATCH_CONFIG["active"] = False
            print("🛑 تم إيقاف المراقبة بناءً على طلبك.")

        elif action == "start_monitoring":
            folder_name = data.get("folder")
            minutes = data.get("minutes", 15) # الافتراضي 15 لو ما حدد
            
            # محاولة إيجاد المسار الكامل للمجلد
            full_path = folder_name
            if ":" not in folder_name:
                full_path = os.path.join(SEARCH_PATHS[0], folder_name) # نفترض سطح المكتب
            
            WATCH_CONFIG["folder_path"] = full_path
            WATCH_CONFIG["interval"] = int(minutes) * 60 # تحويل لثواني
            WATCH_CONFIG["active"] = True
            
            print(f"👀 بدأت المراقبة على: {full_path}")
            print(f"⏱️ دورة الفحص: كل {minutes} دقيقة.")

        # --- باقي الأوامر (تطبيقات وملفات) ---
        elif action == "open_app":
            # (نفس كود فتح التطبيقات)
            pass 
            
    except Exception as e:
        print(f"Error: {e}")

# --- التشغيل ---
print("🕵️ الإيجنت جاهز. جرب: 'مراقبة مجلد X كل 5 دقائق'")
while True:
    q = input("\n🎤 آمرني: ")
    if q == "exit": break
    execute(think(q))