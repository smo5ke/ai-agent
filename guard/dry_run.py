"""
🧪 Dry Run Engine - محرك المحاكاة
==================================
محاكاة الأوامر بدون تنفيذ فعلي.
"""

import os
from typing import Optional, Dict, List


class DryRunEngine:
    """محرك المحاكاة"""
    
    def simulate(self, command: dict) -> str:
        """
        محاكاة الأمر وإرجاع ما سيحدث.
        
        Returns:
            وصف نصي لما سيحدث
        """
        intent = command.get("intent", "unknown")
        
        # استدعاء الدالة المناسبة
        simulator = getattr(self, f"_sim_{intent}", self._sim_default)
        return simulator(command)
    
    def _sim_default(self, command: dict) -> str:
        """محاكاة افتراضية"""
        return f"سيتم تنفيذ: {command.get('intent', 'unknown')}"
    
    def _sim_open(self, command: dict) -> str:
        target = command.get("target", "?")
        return f"🚀 سيتم فتح: {target}"
    
    def _sim_clean(self, command: dict) -> str:
        """محاكاة التنظيف - الأهم"""
        loc = command.get("loc", "desktop")
        filter_key = command.get("filter_key", "*")
        dest = command.get("destination", "Cleaned")
        
        # حساب الملفات المتأثرة (محاكاة)
        affected = self._count_affected_files(loc, filter_key)
        
        return (
            f"⚠️ عملية التنظيف:\n"
            f"📁 المجلد: {loc}\n"
            f"🔍 الفلتر: {filter_key}\n"
            f"📂 الوجهة: {dest}\n"
            f"📊 الملفات المتأثرة: ~{affected} ملف\n"
            f"\n❓ هل تريد المتابعة؟"
        )
    
    def _sim_delete(self, command: dict) -> str:
        target = command.get("target", "?")
        loc = command.get("loc", "")
        
        full_path = os.path.join(loc, target) if loc else target
        
        return (
            f"⛔ عملية الحذف:\n"
            f"🗑️ سيتم حذف: {full_path}\n"
            f"\n⚠️ هذه العملية لا يمكن التراجع عنها!"
        )
    
    def _sim_move(self, command: dict) -> str:
        target = command.get("target", "?")
        dest = command.get("destination", "?")
        
        return (
            f"📦 عملية النقل:\n"
            f"📄 الملف: {target}\n"
            f"📁 إلى: {dest}"
        )
    
    def _sim_create_folder(self, command: dict) -> str:
        target = command.get("target", "?")
        loc = command.get("loc", "desktop")
        
        return f"📁 سيتم إنشاء مجلد: {target} في {loc}"
    
    def _sim_create_file(self, command: dict) -> str:
        target = command.get("target", "?")
        loc = command.get("loc", "desktop")
        
        return f"📄 سيتم إنشاء ملف: {target} في {loc}"
    
    def _sim_write_file(self, command: dict) -> str:
        target = command.get("target", "?")
        param = command.get("param", "")
        preview = param[:50] + "..." if len(param) > 50 else param
        
        return f"✏️ سيتم كتابة في {target}:\n\"{preview}\""
    
    def _count_affected_files(self, loc: str, filter_key: str) -> int:
        """حساب عدد الملفات المتأثرة (تقريبي)"""
        try:
            # تحويل الموقع
            from actions import open_app
            folder = open_app.resolve_folder(loc)
            
            if not os.path.exists(folder):
                return 0
            
            count = 0
            for f in os.listdir(folder):
                if filter_key == "*" or filter_key.lower() in f.lower():
                    count += 1
            
            return count
        except:
            return 0


def simulate_command(command: dict) -> str:
    """دالة مختصرة للمحاكاة"""
    engine = DryRunEngine()
    return engine.simulate(command)
