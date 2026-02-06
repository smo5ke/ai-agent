# actions/system_ops.py
"""
🖥️ System Operations - عمليات النظام
فتح البرامج وتنفيذ أوامر النظام
"""
import subprocess
import os
from core.base_action import BaseAction


class OpenAppAction(BaseAction):
    """فتح برنامج"""
    
    # قاموس البرامج المعروفة
    APP_ALIASES = {
        # Windows
        "notepad": "notepad.exe",
        "المفكرة": "notepad.exe",
        "paint": "mspaint.exe",
        "mspaint": "mspaint.exe",
        "الرسام": "mspaint.exe",
        "calculator": "calc.exe",
        "calc": "calc.exe",
        "الآلة الحاسبة": "calc.exe",
        "الحاسبة": "calc.exe",
        "explorer": "explorer.exe",
        "المستكشف": "explorer.exe",
        "cmd": "cmd.exe",
        "terminal": "cmd.exe",
        "powershell": "powershell.exe",
        "chrome": "chrome.exe",
        "firefox": "firefox.exe",
        "edge": "msedge.exe",
        "code": "code.exe",
        "vscode": "code.exe",
    }
    
    def __init__(self, context, app_name: str):
        super().__init__(context)
        self.app_name = app_name.lower().strip()
        self.process = None

    def execute(self):
        # البحث عن اسم البرنامج
        executable = self.APP_ALIASES.get(self.app_name, self.app_name)
        
        try:
            print(f"🖥️ Opening: {executable}")
            
            # فتح البرنامج
            if os.name == 'nt':  # Windows
                self.process = subprocess.Popen(
                    executable,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:  # Linux/Mac
                self.process = subprocess.Popen(
                    [executable],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            
            print(f"✅ Opened: {self.app_name}")
            
        except Exception as e:
            print(f"❌ Failed to open {self.app_name}: {e}")
            raise

    def rollback(self):
        # لا يمكن التراجع عن فتح برنامج
        print(f"⚠️ Cannot rollback: open_app ({self.app_name})")


# تصدير
ACTION_CLASSES = {
    "open_app": OpenAppAction
}
