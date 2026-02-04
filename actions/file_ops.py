"""
📁 File Operations - عمليات الملفات
====================================
إنشاء، حذف، نقل، نسخ، كتابة ملفات.
"""

import os
import shutil
from typing import Optional


# مسارات افتراضية
# استخدام OneDrive Desktop كمسار رئيسي
ONEDRIVE_PATH = os.path.join(os.path.expanduser("~"), "OneDrive")

PATHS = {
    # OneDrive paths (الأساسي)
    "desktop": os.path.join(ONEDRIVE_PATH, "سطح المكتب"),
    "documents": os.path.join(ONEDRIVE_PATH, "المستندات") if os.path.exists(os.path.join(ONEDRIVE_PATH, "المستندات")) else os.path.join(os.path.expanduser("~"), "Documents"),
    "downloads": os.path.join(os.path.expanduser("~"), "Downloads"),
    
    # أسماء عربية
    "سطح المكتب": os.path.join(ONEDRIVE_PATH, "سطح المكتب"),
    "المستندات": os.path.join(ONEDRIVE_PATH, "المستندات") if os.path.exists(os.path.join(ONEDRIVE_PATH, "المستندات")) else os.path.join(os.path.expanduser("~"), "Documents"),
    "التنزيلات": os.path.join(os.path.expanduser("~"), "Downloads"),
}


def resolve_path(loc: str) -> str:
    """تحويل اسم المجلد لمسار كامل"""
    if not loc:
        return PATHS["desktop"]
    
    loc_lower = loc.lower()
    
    # البحث في المسارات المعروفة
    for name, path in PATHS.items():
        if name in loc_lower:
            return path
    
    # إذا كان مسار كامل
    if os.path.isabs(loc):
        return loc
    
    # افتراضياً: سطح المكتب
    return os.path.join(PATHS["desktop"], loc)


class FileOperations:
    """عمليات الملفات"""
    
    def create_folder(self, name: str, location: str = "desktop") -> str:
        """
        إنشاء مجلد جديد.
        
        Args:
            name: اسم المجلد
            location: الموقع
            
        Returns:
            رسالة النتيجة
        """
        base = resolve_path(location)
        folder_path = os.path.join(base, name)
        
        if os.path.exists(folder_path):
            return f"⚠️ المجلد موجود مسبقاً: {name}"
        
        os.makedirs(folder_path, exist_ok=True)
        return f"📁 تم إنشاء المجلد: {name}"
    
    def create_file(self, name: str, location: str = "desktop", content: str = "") -> str:
        """
        إنشاء ملف جديد.
        
        Args:
            name: اسم الملف (مع الامتداد)
            location: الموقع
            content: المحتوى الأولي
        """
        base = resolve_path(location)
        
        # إضافة امتداد افتراضي إذا لم يكن موجوداً
        if "." not in name:
            name += ".txt"
        
        file_path = os.path.join(base, name)
        
        if os.path.exists(file_path):
            return f"⚠️ الملف موجود مسبقاً: {name}"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"📄 تم إنشاء الملف: {name}"
    
    def write_file(self, name: str, content: str, location: str = "desktop", append: bool = False) -> str:
        """
        كتابة محتوى في ملف.
        
        Args:
            name: اسم الملف
            content: المحتوى
            location: الموقع
            append: إضافة أم استبدال
        """
        base = resolve_path(location)
        file_path = os.path.join(base, name)
        
        # البحث عن الملف
        if not os.path.exists(file_path):
            # البحث بدون امتداد
            for f in os.listdir(base):
                if f.startswith(name.split('.')[0]):
                    file_path = os.path.join(base, f)
                    break
        
        mode = 'a' if append else 'w'
        with open(file_path, mode, encoding='utf-8') as f:
            f.write(content)
        
        action = "أضيف إلى" if append else "كُتب في"
        return f"✏️ تم {action}: {os.path.basename(file_path)}"
    
    def read_file(self, name: str, location: str = "desktop") -> str:
        """قراءة محتوى ملف"""
        base = resolve_path(location)
        file_path = os.path.join(base, name)
        
        if not os.path.exists(file_path):
            return f"❌ الملف غير موجود: {name}"
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return content
    
    def delete(self, name: str, location: str = "desktop") -> str:
        """حذف ملف أو مجلد"""
        base = resolve_path(location)
        path = os.path.join(base, name)
        
        if not os.path.exists(path):
            return f"❌ غير موجود: {name}"
        
        if os.path.isdir(path):
            shutil.rmtree(path)
            return f"🗑️ تم حذف المجلد: {name}"
        else:
            os.remove(path)
            return f"🗑️ تم حذف الملف: {name}"
    
    def rename(self, old_name: str, new_name: str, location: str = "desktop") -> str:
        """إعادة تسمية"""
        base = resolve_path(location)
        old_path = os.path.join(base, old_name)
        new_path = os.path.join(base, new_name)
        
        if not os.path.exists(old_path):
            return f"❌ غير موجود: {old_name}"
        
        os.rename(old_path, new_path)
        return f"✏️ تم تغيير الاسم: {old_name} → {new_name}"
    
    def copy(self, name: str, destination: str, location: str = "desktop") -> str:
        """نسخ ملف أو مجلد"""
        base = resolve_path(location)
        dest = resolve_path(destination)
        src_path = os.path.join(base, name)
        dest_path = os.path.join(dest, name)
        
        if not os.path.exists(src_path):
            return f"❌ غير موجود: {name}"
        
        if os.path.isdir(src_path):
            shutil.copytree(src_path, dest_path)
        else:
            shutil.copy2(src_path, dest_path)
        
        return f"📋 تم نسخ: {name} → {destination}"
    
    def move(self, name: str, destination: str, location: str = "desktop") -> str:
        """نقل ملف أو مجلد"""
        base = resolve_path(location)
        dest = resolve_path(destination)
        src_path = os.path.join(base, name)
        dest_path = os.path.join(dest, name)
        
        if not os.path.exists(src_path):
            return f"❌ غير موجود: {name}"
        
        shutil.move(src_path, dest_path)
        return f"📦 تم نقل: {name} → {destination}"
    
    def list_folder(self, location: str = "desktop") -> str:
        """عرض محتويات مجلد"""
        path = resolve_path(location)
        
        if not os.path.exists(path):
            return f"❌ المجلد غير موجود"
        
        items = os.listdir(path)
        folders = [f"📁 {i}" for i in items if os.path.isdir(os.path.join(path, i))]
        files = [f"📄 {i}" for i in items if os.path.isfile(os.path.join(path, i))]
        
        result = f"📂 محتويات {os.path.basename(path)}:\n"
        result += "\n".join(folders + files)
        
        return result


# Singleton
_file_ops = None

def get_file_ops() -> FileOperations:
    global _file_ops
    if _file_ops is None:
        _file_ops = FileOperations()
    return _file_ops
