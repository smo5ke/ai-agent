# core/system_paths.py
"""
🧭 System Paths - بوصلة النظام
تحدد المسارات الحقيقية (مثل OneDrive) وتربط الأسماء العربية/الإنجليزية بالمسارات الفعلية.
"""
import os
from pathlib import Path

class SystemPaths:
    def __init__(self):
        # 1. المجلد الرئيسي للمستخدم
        self.home_dir = Path(os.path.expanduser("~"))
        
        # 2. البحث عن سطح المكتب الحقيقي (مع OneDrive)
        self.desktop_dir = self._detect_desktop()
        
        # 3. جدول التحويل الذكي (English/Arabic -> Real Absolute Path)
        self.paths_map = {
            # سطح المكتب (يعتمد على الكشف الذكي)
            "desktop": self.desktop_dir,
            "سطح المكتب": self.desktop_dir,
            
            # التنزيلات
            "downloads": self.home_dir / "Downloads",
            "download": self.home_dir / "Downloads",
            "التنزيلات": self.home_dir / "Downloads",
            "تنزيلات": self.home_dir / "Downloads",
            
            # المستندات
            "documents": self.home_dir / "Documents",
            "document": self.home_dir / "Documents",
            "المستندات": self.home_dir / "Documents",
            "مستندات": self.home_dir / "Documents",
            
            # الصور
            "pictures": self.home_dir / "Pictures",
            "الصور": self.home_dir / "Pictures",
            "صور": self.home_dir / "Pictures",
            
            # الفيديو
            "videos": self.home_dir / "Videos",
            "الفيديو": self.home_dir / "Videos",
            "فيديو": self.home_dir / "Videos",
            
            # الموسيقى
            "music": self.home_dir / "Music",
            "الموسيقى": self.home_dir / "Music"
        }

        print(f"🧭 Home: {self.home_dir}")
        print(f"🧭 Desktop: {self.desktop_dir}")

    def _detect_desktop(self) -> Path:
        """اكتشاف مسار سطح المكتب مع دعم OneDrive"""
        
        # محاولة 1: عبر متغيرات البيئة (OneDrive)
        onedrive_path = os.environ.get("OneDrive") or os.environ.get("OneDriveConsumer")
        
        if onedrive_path:
            onedrive_desktop = Path(onedrive_path) / "Desktop"
            if onedrive_desktop.exists():
                return onedrive_desktop
            
            arabic_desktop = Path(onedrive_path) / "سطح المكتب"
            if arabic_desktop.exists():
                return arabic_desktop

        # محاولة 2: المسار القياسي
        standard_desktop = self.home_dir / "Desktop"
        if standard_desktop.exists():
            return standard_desktop
            
        # محاولة 3: المسار العربي القياسي
        arabic_standard = self.home_dir / "سطح المكتب"
        if arabic_standard.exists():
            return arabic_standard
            
        # fallback
        return standard_desktop

    def get_root_dir(self) -> Path:
        return self.home_dir

    def resolve_path(self, user_path: str) -> str:
        """
        تحويل المسار بذكاء.
        Example: "التنزيلات/ملف.txt" -> "C:/Users/.../Downloads/ملف.txt"
        """
        path_obj = Path(user_path)
        parts = path_obj.parts
        
        if not parts:
            return str(self.home_dir / user_path)
            
        first_part = parts[0].lower() # توحيد حالة الأحرف للمقارنة
        
        # هل الجزء الأول موجود في الخريطة؟
        if first_part in self.paths_map:
            real_base = self.paths_map[first_part]
            
            if len(parts) > 1:
                # دمج المسار الحقيقي مع الباقي
                full_path = real_base / Path(*parts[1:])
            else:
                full_path = real_base
                
            return str(full_path)
            
        # إذا لم يكن في الخريطة، نعامله كمسار نسبي للمجلد الرئيسي
        # إلا إذا كان مساراً مطلقاً أصلاً
        if os.path.isabs(user_path):
            return user_path
            
        return str(self.home_dir / user_path)
