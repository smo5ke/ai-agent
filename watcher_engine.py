import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- 1. المعالج الذكي (الفلتر) ---
class SystemHandler(FileSystemEventHandler):
    def on_created(self, event):
        path = event.src_path
        filename = os.path.basename(path)
        
        # تجاهل الملفات المؤقتة
        if filename.startswith(".") or filename.startswith("~$") or filename.lower().endswith(('.tmp', '.log', '.dat', '.ini')):
            return

        # تحديد نوع المنطقة (برامج ولا شخصي؟)
        is_program = "Program Files" in path or "AppData" in path
        
        if is_program:
             self.handle_installation(event)
        else:
             self.handle_user_files(event)

    def handle_installation(self, event):
        if event.is_directory:
            parent = os.path.dirname(event.src_path)
            if parent.endswith("Program Files") or parent.endswith("Program Files (x86)"):
                print(f"\n🎉 [تثبيت جديد] برنامج: {os.path.basename(event.src_path)}")
                print(f"   📂 المسار: {event.src_path}")
        elif event.src_path.lower().endswith(".exe"):
            print(f"\n⚙️ [ملف تنفيذي] نزل ملف exe: {os.path.basename(event.src_path)}")

    def handle_user_files(self, event):
        what = "مجلد" if event.is_directory else "ملف"
        folder_name = os.path.basename(os.path.dirname(event.src_path))
        print(f"\n👀 [شخصي - {folder_name}] تم إنشاء {what}: {os.path.basename(event.src_path)}")
        print(f"   📍 المسار: {event.src_path}")

# --- 2. إعداد الأخطبوط (البحث عن كل المسارات) ---
def find_all_targets():
    user_home = os.path.expanduser("~")
    targets = []

    # أ) البحث الديناميكي عن OneDrive (مهما كان اسمه)
    # بنعمل مسح لمجلد المستخدم، أي مجلد فيه كلمة OneDrive بناخذه
    try:
        for item in os.listdir(user_home):
            full_path = os.path.join(user_home, item)
            if os.path.isdir(full_path) and "onedrive" in item.lower():
                targets.append(full_path)
                # كمان بنضيف سطح المكتب اللي جوا الون درايف بشكل صريح للتأكيد
                desktop_in_od = os.path.join(full_path, "Desktop")
                if os.path.exists(desktop_in_od): targets.append(desktop_in_od)
                
                desktop_in_od_ar = os.path.join(full_path, "سطح المكتب")
                if os.path.exists(desktop_in_od_ar): targets.append(desktop_in_od_ar)
    except: pass

    # ب) المسارات الأساسية (محلية)
    basic_paths = [
        os.path.join(user_home, "Desktop"),
        os.path.join(user_home, "سطح المكتب"), # للعربي
        os.path.join(user_home, "Downloads"),
        os.path.join(user_home, "Documents"),
        os.path.join(user_home, "Pictures")
    ]
    targets.extend(basic_paths)

    # ج) مسارات النظام (البرامج)
    sys_paths = [
        r"C:\Program Files",
        r"C:\Program Files (x86)",
        os.path.join(user_home, "AppData", "Local", "Programs")
    ]
    targets.extend(sys_paths)

    # تنظيف القائمة (حذف المكرر والمسارات غير الموجودة)
    final_targets = []
    seen = set()
    for t in targets:
        if os.path.exists(t) and t not in seen:
            final_targets.append(t)
            seen.add(t)
            
    return final_targets

def start_system_watch():
    observer = Observer()
    handler = SystemHandler()

    all_targets = find_all_targets()
    
    print("🛡️ جاري نشر العيون (بما في ذلك كل مجلدات OneDrive)...")
    
    for folder in all_targets:
        try:
            # recursive=True تعني: راقب المجلد وكل اللي جواته
            observer.schedule(handler, folder, recursive=True)
            
            if "OneDrive" in folder:
                print(f"   ☁️ تم تأمين OneDrive: {folder}")
            elif "Program" in folder:
                print(f"   💻 تم تأمين البرامج: {folder}")
            else:
                print(f"   👤 تم تأمين ملفات: {folder}")
                
        except Exception as e:
            print(f"   ⚠️ تجاوز {folder}: {e}")

    observer.start()
    print("\n🚀 النظام يعمل! (يراقب كل شيء حرفياً).")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        observer.join()

if __name__ == "__main__":
    start_system_watch()