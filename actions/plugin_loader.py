"""
🔌 Plugin Loader - Advanced Plugin System
==========================================
نظام إضافات متطور مع دعم:
- مجلدات متعددة (داخلي + خارجي)
- واجهة موحدة للإضافات
- تفعيل/تعطيل
- إعادة تحميل
"""

import os
import sys
import importlib.util
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod


class PluginInterface(ABC):
    """واجهة موحدة للإضافات"""
    
    # معلومات الإضافة (يجب تعريفها في كل إضافة)
    NAME = "Unnamed Plugin"
    DESCRIPTION = "No description"
    VERSION = "1.0"
    COMMANDS = []  # قائمة الأوامر التي تدعمها الإضافة
    
    @abstractmethod
    def run(self, command: str, *args, **kwargs) -> Optional[str]:
        """
        تنفيذ أمر الإضافة.
        
        Args:
            command: الأمر المطلوب
            *args: معاملات إضافية
            
        Returns:
            نتيجة التنفيذ أو None
        """
        pass
    
    def on_load(self):
        """يُستدعى عند تحميل الإضافة"""
        pass
    
    def on_unload(self):
        """يُستدعى عند إلغاء تحميل الإضافة"""
        pass


class AdvancedPluginLoader:
    """محمّل إضافات متطور"""
    
    def __init__(self):
        self.plugins: Dict[str, Any] = {}
        self.plugin_info: Dict[str, dict] = {}
        self.disabled_plugins: List[str] = []
        
        # مجلدات الإضافات
        self.plugin_folders = []
        
        # المجلد الداخلي
        internal_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugins")
        if os.path.exists(internal_folder):
            self.plugin_folders.append(internal_folder)
        
        # المجلد الخارجي (Documents/JarvisPlugins)
        external_folder = os.path.join(os.path.expanduser("~"), "Documents", "JarvisPlugins")
        self.plugin_folders.append(external_folder)
        
        # إنشاء المجلد الخارجي إذا لم يكن موجوداً
        if not os.path.exists(external_folder):
            os.makedirs(external_folder)
            self._create_example_plugin(external_folder)
    
    def _create_example_plugin(self, folder: str):
        """إنشاء إضافة مثال في المجلد الخارجي"""
        example_path = os.path.join(folder, "example_plugin.py")
        example_code = '''"""
🔌 Example Plugin - إضافة مثال
================================
هذه إضافة مثال لتوضيح كيفية إنشاء إضافات جديدة.
"""

# معلومات الإضافة
NAME = "Example Plugin"
DESCRIPTION = "إضافة مثال توضيحية"
VERSION = "1.0"
COMMANDS = ["مثال", "example", "test"]


def run(command: str, *args, **kwargs):
    """
    تنفيذ أمر الإضافة.
    
    Args:
        command: الأمر المرسل
        
    Returns:
        الرد على الأمر
    """
    if command.lower() in COMMANDS:
        return "🔌 هذه إضافة مثال تعمل بنجاح!"
    return None


def on_load():
    """يُستدعى عند تحميل الإضافة"""
    print(f"✅ {NAME} loaded")
'''
        with open(example_path, 'w', encoding='utf-8') as f:
            f.write(example_code)
        print(f"📝 تم إنشاء إضافة مثال في: {example_path}")
    
    def load_all(self):
        """تحميل كل الإضافات من جميع المجلدات"""
        print("🔌 جاري تحميل الإضافات...")
        
        for folder in self.plugin_folders:
            if os.path.exists(folder):
                self._load_from_folder(folder)
        
        print(f"✅ تم تحميل {len(self.plugins)} إضافة")
    
    def _load_from_folder(self, folder: str):
        """تحميل الإضافات من مجلد معين"""
        for filename in os.listdir(folder):
            if filename.endswith(".py") and filename != "__init__.py":
                plugin_name = filename[:-3]
                
                # تجاهل الإضافات المعطلة
                if plugin_name in self.disabled_plugins:
                    print(f"⏸️ إضافة معطلة: {plugin_name}")
                    continue
                
                path = os.path.join(folder, filename)
                self._load_plugin(plugin_name, path)
    
    def _load_plugin(self, name: str, path: str) -> bool:
        """تحميل إضافة واحدة"""
        try:
            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # حفظ الإضافة
            self.plugins[name] = module
            
            # حفظ معلومات الإضافة
            self.plugin_info[name] = {
                "name": getattr(module, 'NAME', name),
                "description": getattr(module, 'DESCRIPTION', ''),
                "version": getattr(module, 'VERSION', '1.0'),
                "commands": getattr(module, 'COMMANDS', []),
                "path": path
            }
            
            # استدعاء on_load إذا كان موجوداً
            if hasattr(module, 'on_load'):
                module.on_load()
            
            print(f"✅ {self.plugin_info[name]['name']} v{self.plugin_info[name]['version']}")
            return True
            
        except Exception as e:
            print(f"❌ خطأ في تحميل {name}: {e}")
            return False
    
    def reload_plugin(self, name: str) -> bool:
        """إعادة تحميل إضافة"""
        if name not in self.plugin_info:
            return False
        
        path = self.plugin_info[name]["path"]
        
        # إلغاء التحميل أولاً
        self.unload_plugin(name)
        
        # إعادة التحميل
        return self._load_plugin(name, path)
    
    def unload_plugin(self, name: str) -> bool:
        """إلغاء تحميل إضافة"""
        if name not in self.plugins:
            return False
        
        # استدعاء on_unload إذا كان موجوداً
        if hasattr(self.plugins[name], 'on_unload'):
            self.plugins[name].on_unload()
        
        del self.plugins[name]
        del self.plugin_info[name]
        return True
    
    def disable_plugin(self, name: str):
        """تعطيل إضافة"""
        if name not in self.disabled_plugins:
            self.disabled_plugins.append(name)
            self.unload_plugin(name)
    
    def enable_plugin(self, name: str):
        """تفعيل إضافة"""
        if name in self.disabled_plugins:
            self.disabled_plugins.remove(name)
    
    def run_plugin(self, name: str, command: str, *args, **kwargs) -> Optional[str]:
        """تشغيل إضافة محددة"""
        if name in self.plugins and hasattr(self.plugins[name], 'run'):
            return self.plugins[name].run(command, *args, **kwargs)
        return None
    
    def find_plugin_for_command(self, command: str) -> Optional[str]:
        """البحث عن إضافة تدعم أمر معين"""
        command_lower = command.lower()
        
        for name, info in self.plugin_info.items():
            for cmd in info.get('commands', []):
                if cmd.lower() in command_lower or command_lower in cmd.lower():
                    return name
        return None
    
    def run_command(self, command: str, *args, **kwargs) -> Optional[str]:
        """تشغيل أمر والبحث عن الإضافة المناسبة"""
        # البحث عن إضافة تدعم الأمر
        plugin_name = self.find_plugin_for_command(command)
        if plugin_name:
            return self.run_plugin(plugin_name, command, *args, **kwargs)
        
        # محاولة تشغيل كل الإضافات
        for name in self.plugins:
            result = self.run_plugin(name, command, *args, **kwargs)
            if result:
                return result
        
        return None
    
    def get_all_plugins(self) -> List[dict]:
        """جلب قائمة كل الإضافات"""
        return list(self.plugin_info.values())
    
    def get_plugin_folders(self) -> List[str]:
        """جلب مجلدات الإضافات"""
        return self.plugin_folders


# للتوافق مع الكود القديم
class PluginLoader(AdvancedPluginLoader):
    def __init__(self, plugin_folder="plugins"):
        super().__init__()