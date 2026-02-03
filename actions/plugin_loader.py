import os
import importlib.util

class PluginLoader:
    def __init__(self, plugin_folder="plugins"):
        self.plugin_folder = plugin_folder
        self.plugins = {}

    def load_all(self):
        """تحميل كل الملفات الموجودة في مجلد plugins"""
        if not os.path.exists(self.plugin_folder):
            os.makedirs(self.plugin_folder)
            return

        print("🔌 جاري فحص وتحميل الإضافات...")
        for filename in os.listdir(self.plugin_folder):
            if filename.endswith(".py") and filename != "__init__.py":
                plugin_name = filename[:-3]
                path = os.path.join(self.plugin_folder, filename)
                
                # تحميل الوحدة ديناميكياً
                spec = importlib.util.spec_from_file_location(plugin_name, path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # تسجيل الإضافة
                self.plugins[plugin_name] = module
                print(f"✅ إضافة مفعلة: {plugin_name}")

    def run_plugin(self, name, *args):
        """تشغيل إضافة محددة"""
        if name in self.plugins and hasattr(self.plugins[name], 'run'):
            return self.plugins[name].run(*args)
        return None