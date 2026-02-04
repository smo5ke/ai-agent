"""
👁️ LLM Worker Monitor
======================
مراقب صحة الـ Worker + إعادة التشغيل التلقائي.
"""

import subprocess
import sys
import os
import time
import socket

# إضافة المجلد الرئيسي للـ path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm.ipc import ADDRESS

# ═══════════════════════════════════════════════════════════
# الإعدادات
# ═══════════════════════════════════════════════════════════

WORKER_SCRIPT = os.path.join(os.path.dirname(__file__), "worker_process.py")
CHECK_INTERVAL = 5  # ثواني بين كل فحص
MAX_RESTART_ATTEMPTS = 3


# ═══════════════════════════════════════════════════════════
# دوال المراقبة
# ═══════════════════════════════════════════════════════════

def is_worker_alive() -> bool:
    """فحص إذا كان الـ Worker يعمل"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(ADDRESS)
        sock.close()
        return result == 0
    except:
        return False


def start_worker() -> subprocess.Popen:
    """تشغيل الـ Worker في process جديد"""
    print(f"🚀 Starting LLM Worker: {WORKER_SCRIPT}")
    
    # تشغيل في نافذة منفصلة على Windows
    if sys.platform == "win32":
        process = subprocess.Popen(
            [sys.executable, WORKER_SCRIPT],
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    else:
        process = subprocess.Popen(
            [sys.executable, WORKER_SCRIPT],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    
    return process


def wait_for_worker(timeout: int = 60) -> bool:
    """انتظار حتى يصبح الـ Worker جاهزاً"""
    print(f"⏳ Waiting for worker to be ready (max {timeout}s)...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_worker_alive():
            print("✅ Worker is ready!")
            return True
        time.sleep(1)
    
    print("❌ Worker failed to start in time")
    return False


def ensure_running() -> bool:
    """
    تأكد من أن الـ Worker يعمل.
    يستخدم هذا عند بدء التطبيق.
    """
    if is_worker_alive():
        print("✅ LLM Worker already running")
        return True
    
    print("⚠️ LLM Worker not running, starting...")
    process = start_worker()
    
    if wait_for_worker():
        return True
    else:
        process.terminate()
        return False


def monitor_forever():
    """
    مراقبة مستمرة + إعادة تشغيل تلقائي.
    يستخدم هذا كـ daemon منفصل.
    """
    print("=" * 50)
    print("👁️ LLM Worker Monitor Started")
    print(f"📍 Monitoring: {ADDRESS[0]}:{ADDRESS[1]}")
    print(f"⏱️ Check interval: {CHECK_INTERVAL}s")
    print("=" * 50)
    
    restart_count = 0
    worker_process = None
    
    try:
        while True:
            if not is_worker_alive():
                print(f"\n⚠️ Worker is DOWN! (Restart #{restart_count + 1})")
                
                if restart_count >= MAX_RESTART_ATTEMPTS:
                    print(f"❌ Max restart attempts ({MAX_RESTART_ATTEMPTS}) reached!")
                    print("💡 Please check logs and restart manually.")
                    time.sleep(30)  # انتظار أطول قبل المحاولة مجدداً
                    restart_count = 0
                    continue
                
                worker_process = start_worker()
                
                if wait_for_worker():
                    print("✅ Worker restarted successfully!")
                    restart_count = 0
                else:
                    restart_count += 1
                    print(f"❌ Restart failed ({restart_count}/{MAX_RESTART_ATTEMPTS})")
            else:
                # إعادة تعيين العداد عند النجاح
                if restart_count > 0:
                    restart_count = 0
            
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n🛑 Monitor shutting down...")
        if worker_process:
            worker_process.terminate()


# ═══════════════════════════════════════════════════════════
# التشغيل
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="LLM Worker Monitor")
    parser.add_argument("--daemon", action="store_true", help="Run as continuous monitor")
    parser.add_argument("--check", action="store_true", help="Just check if worker is alive")
    parser.add_argument("--start", action="store_true", help="Start worker if not running")
    
    args = parser.parse_args()
    
    if args.check:
        if is_worker_alive():
            print("✅ Worker is ALIVE")
            sys.exit(0)
        else:
            print("❌ Worker is DOWN")
            sys.exit(1)
    
    elif args.start:
        if ensure_running():
            print("✅ Worker is ready")
            sys.exit(0)
        else:
            print("❌ Failed to start worker")
            sys.exit(1)
    
    elif args.daemon:
        monitor_forever()
    
    else:
        # الوضع الافتراضي: فحص + تشغيل إذا لزم
        ensure_running()
