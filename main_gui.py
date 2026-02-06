# main_gui.py
"""
🖥️ Jarvis AI v6.0 - Server-Client Architecture
"""
import sys
import os
import subprocess
import time
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox, QProgressDialog
from PyQt6.QtCore import QTimer

# إضافة المسار
sys.path.insert(0, str(Path(__file__).parent))

# إعدادات
MODEL_PATH = "Meta-Llama-3.1-8B-Instruct-Q6_K_L.gguf"
SERVER_SCRIPT = "brain_server.py"

def is_server_running():
    """تحقق بسيط هل السيرفر يعمل"""
    import urllib.request
    try:
        # نحاول الاتصال بالسيرفر
        # ملاحظة: السيرفر لا يدعم GET / لكن الاستجابة تعني أنه يعمل
        with urllib.request.urlopen("http://localhost:5000", timeout=1):
            return True
    except:
        return False

def start_server_process():
    """تشغيل السيرفر في الخلفية"""
    print("🚀 Auto-starting brain server...")
    if os.name == 'nt':
        # في ويندوز، نفتح نافذة جديدة ليرى المستخدم السيرفر
        subprocess.Popen(["start", "cmd", "/k", "python", SERVER_SCRIPT], shell=True)
    else:
        subprocess.Popen(["python", SERVER_SCRIPT])

def main():
    app = QApplication(sys.argv)
    
    # التحقق من وجود الموديل
    if not os.path.exists(MODEL_PATH):
        QMessageBox.critical(None, "Model Missing", f"الموديل غير موجود:\n{MODEL_PATH}")
        sys.exit(1)

    # تشغيل السيرفر تلقائياً
    start_server_process()
    
    # انتظار وهمي حتى يعمل السيرفر (يقدر المستخدم يرى النافذة السوداء)
    print("⏳ Waiting for server to initialize...")
    
    # 2. إعداد المكونات الأساسية
    from core.execution_context import ExecutionContext
    from core.orchestrator import Orchestrator
    from core.memory_manager import get_memory
    from llm.network_client import NetworkPlanner
    
    from core.system_paths import SystemPaths
    
    # 🔥 تفعيل البوصلة الذكية
    sys_paths = SystemPaths()
    root_path = sys_paths.get_root_dir()
    
    print(f"⚠️ WARNING: Agent Root is USER HOME: {root_path}")
    print(f"👉 System supports auto-translation (e.g. 'Desktop', 'Downloads')")
    
    # playground now points to User Home, not just Desktop
    context = ExecutionContext(root_path)
    memory = get_memory()
    
    # استخدام NetworkPlanner بدلاً من LLMPlanner
    planner = NetworkPlanner(port=5000)
    orchestrator = Orchestrator(context, planner=planner)
    
    from ui.main_window import MainWindow
    window = MainWindow(orchestrator)
    window.show()
    
    QMessageBox.information(
        window, 
        "Starting", 
        "تم تشغيل عمليات الذكاء في نافذة منفصلة (Brain Server).\n\n"
        "يرجى الانتظار حتى تظهر رسالة 'Brain Ready' في النافذة السوداء قبل الإرسال."
    )
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
