"""
↩️ Rollback Engine - محرك التراجع
==================================
Smart Undo لاسترجاع الحالة بعد الفشل.

Features:
- Trash System لحفظ المحذوفات
- Rollback Actions لكل عملية
- استرجاع حسب Command ID
"""

import os
import shutil
import json
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field


@dataclass
class RollbackRecord:
    """سجل Rollback واحد"""
    command_id: str
    node_id: str
    intent: str
    original_path: str
    backup_path: Optional[str] = None
    rollback_type: str = ""  # delete, restore, move_back, rename_back
    metadata: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    executed: bool = False


@dataclass
class RollbackResult:
    """نتيجة Rollback"""
    command_id: str
    success: bool
    rolled_back_count: int
    failed_count: int
    errors: List[str] = field(default_factory=list)


class RollbackEngine:
    """
    محرك التراجع.
    
    يحفظ نسخ احتياطية ويسترجعها عند الحاجة.
    """
    
    def __init__(self, data_dir: str = None):
        # مجلد البيانات
        if data_dir is None:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base, "data")
        
        self.data_dir = data_dir
        self.trash_dir = os.path.join(data_dir, ".trash")
        self.backup_dir = os.path.join(data_dir, ".backup")
        self.registry_file = os.path.join(data_dir, ".rollback_registry.json")
        
        # إنشاء المجلدات
        os.makedirs(self.trash_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # سجل الـ Rollback
        self._records: Dict[str, List[RollbackRecord]] = {}
        self._load_registry()
    
    # ═══════════════════════════════════════════════════════════
    # حفظ واسترجاع السجل
    # ═══════════════════════════════════════════════════════════
    
    def _load_registry(self):
        """تحميل السجل من الملف"""
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for cmd_id, records in data.items():
                        self._records[cmd_id] = [
                            RollbackRecord(**r) for r in records
                        ]
            except:
                pass
    
    def _save_registry(self):
        """حفظ السجل للملف"""
        data = {}
        for cmd_id, records in self._records.items():
            data[cmd_id] = [
                {
                    "command_id": r.command_id,
                    "node_id": r.node_id,
                    "intent": r.intent,
                    "original_path": r.original_path,
                    "backup_path": r.backup_path,
                    "rollback_type": r.rollback_type,
                    "metadata": r.metadata,
                    "created_at": r.created_at.isoformat(),
                    "executed": r.executed
                }
                for r in records
            ]
        
        try:
            with open(self.registry_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    # ═══════════════════════════════════════════════════════════
    # تسجيل Rollback
    # ═══════════════════════════════════════════════════════════
    
    def register(
        self,
        command_id: str,
        node_id: str,
        intent: str,
        original_path: str,
        backup_path: str = None,
        rollback_type: str = "",
        metadata: Dict = None
    ) -> RollbackRecord:
        """تسجيل عملية قابلة للتراجع"""
        record = RollbackRecord(
            command_id=command_id,
            node_id=node_id,
            intent=intent,
            original_path=original_path,
            backup_path=backup_path,
            rollback_type=rollback_type or self._get_rollback_type(intent),
            metadata=metadata or {}
        )
        
        if command_id not in self._records:
            self._records[command_id] = []
        
        self._records[command_id].append(record)
        self._save_registry()
        
        return record
    
    def _get_rollback_type(self, intent: str) -> str:
        """تحديد نوع الـ Rollback"""
        mapping = {
            "create_file": "delete",
            "create_folder": "delete",
            "delete": "restore",
            "move": "move_back",
            "rename": "rename_back",
            "copy": "delete",
            "write_file": "restore_backup"
        }
        return mapping.get(intent, "unknown")
    
    # ═══════════════════════════════════════════════════════════
    # Trash System
    # ═══════════════════════════════════════════════════════════
    
    def move_to_trash(self, path: str, command_id: str) -> Optional[str]:
        """
        نقل ملف/مجلد للـ Trash.
        
        Returns:
            المسار في الـ Trash أو None عند الفشل
        """
        if not os.path.exists(path):
            return None
        
        # إنشاء مجلد خاص بالـ Command
        cmd_trash = os.path.join(self.trash_dir, command_id)
        os.makedirs(cmd_trash, exist_ok=True)
        
        # اسم الملف مع timestamp
        basename = os.path.basename(path)
        timestamp = datetime.now().strftime("%H%M%S")
        trash_name = f"{timestamp}_{basename}"
        trash_path = os.path.join(cmd_trash, trash_name)
        
        try:
            shutil.move(path, trash_path)
            return trash_path
        except Exception as e:
            print(f"Failed to move to trash: {e}")
            return None
    
    def restore_from_trash(self, command_id: str, original_name: str) -> bool:
        """
        استرجاع ملف من الـ Trash.
        
        Args:
            command_id: معرف الأمر
            original_name: اسم الملف الأصلي
        
        Returns:
            نجاح الاسترجاع
        """
        cmd_trash = os.path.join(self.trash_dir, command_id)
        
        if not os.path.exists(cmd_trash):
            return False
        
        # البحث عن الملف
        for filename in os.listdir(cmd_trash):
            if filename.endswith(f"_{original_name}") or filename == original_name:
                trash_path = os.path.join(cmd_trash, filename)
                
                # استرجاع للمسار الأصلي
                records = self._records.get(command_id, [])
                for record in records:
                    if original_name in record.original_path:
                        try:
                            shutil.move(trash_path, record.original_path)
                            return True
                        except:
                            pass
        
        return False
    
    # ═══════════════════════════════════════════════════════════
    # Backup System
    # ═══════════════════════════════════════════════════════════
    
    def create_backup(self, path: str, command_id: str) -> Optional[str]:
        """
        إنشاء نسخة احتياطية قبل التعديل.
        
        Returns:
            مسار النسخة الاحتياطية
        """
        if not os.path.exists(path):
            return None
        
        cmd_backup = os.path.join(self.backup_dir, command_id)
        os.makedirs(cmd_backup, exist_ok=True)
        
        basename = os.path.basename(path)
        backup_path = os.path.join(cmd_backup, basename)
        
        try:
            if os.path.isfile(path):
                shutil.copy2(path, backup_path)
            else:
                shutil.copytree(path, backup_path)
            return backup_path
        except Exception as e:
            print(f"Failed to create backup: {e}")
            return None
    
    def restore_backup(self, backup_path: str, original_path: str) -> bool:
        """استرجاع من النسخة الاحتياطية"""
        if not os.path.exists(backup_path):
            return False
        
        try:
            if os.path.exists(original_path):
                if os.path.isfile(original_path):
                    os.remove(original_path)
                else:
                    shutil.rmtree(original_path)
            
            if os.path.isfile(backup_path):
                shutil.copy2(backup_path, original_path)
            else:
                shutil.copytree(backup_path, original_path)
            
            return True
        except:
            return False
    
    # ═══════════════════════════════════════════════════════════
    # Rollback
    # ═══════════════════════════════════════════════════════════
    
    def rollback(self, command_id: str) -> RollbackResult:
        """
        تراجع عن كل عمليات أمر معين.
        
        يتم التراجع بترتيب عكسي.
        """
        records = self._records.get(command_id, [])
        
        if not records:
            return RollbackResult(
                command_id=command_id,
                success=False,
                rolled_back_count=0,
                failed_count=0,
                errors=["No rollback records found"]
            )
        
        rolled_back = 0
        failed = 0
        errors = []
        
        # ترتيب عكسي
        for record in reversed(records):
            if record.executed:
                continue
            
            success = self._execute_rollback(record)
            
            if success:
                record.executed = True
                rolled_back += 1
            else:
                failed += 1
                errors.append(f"Failed to rollback {record.node_id}: {record.intent}")
        
        self._save_registry()
        
        return RollbackResult(
            command_id=command_id,
            success=failed == 0,
            rolled_back_count=rolled_back,
            failed_count=failed,
            errors=errors
        )
    
    def _execute_rollback(self, record: RollbackRecord) -> bool:
        """تنفيذ Rollback واحد"""
        rollback_type = record.rollback_type
        
        try:
            if rollback_type == "delete":
                # حذف ما تم إنشاؤه
                if os.path.exists(record.original_path):
                    if os.path.isfile(record.original_path):
                        os.remove(record.original_path)
                    else:
                        shutil.rmtree(record.original_path)
                return True
            
            elif rollback_type == "restore":
                # استرجاع من الـ Trash
                if record.backup_path and os.path.exists(record.backup_path):
                    shutil.move(record.backup_path, record.original_path)
                    return True
                return False
            
            elif rollback_type == "move_back":
                # إرجاع الملف لمكانه الأصلي
                dest = record.metadata.get("destination")
                if dest and os.path.exists(dest):
                    shutil.move(dest, record.original_path)
                    return True
                return False
            
            elif rollback_type == "rename_back":
                # إعادة التسمية الأصلية
                new_name = record.metadata.get("new_name")
                new_path = os.path.join(
                    os.path.dirname(record.original_path),
                    new_name
                )
                if os.path.exists(new_path):
                    os.rename(new_path, record.original_path)
                    return True
                return False
            
            elif rollback_type == "restore_backup":
                # استرجاع من النسخة الاحتياطية
                if record.backup_path:
                    return self.restore_backup(
                        record.backup_path,
                        record.original_path
                    )
                return False
            
            return False
            
        except Exception as e:
            print(f"Rollback error: {e}")
            return False
    
    # ═══════════════════════════════════════════════════════════
    # استعلام
    # ═══════════════════════════════════════════════════════════
    
    def get_records(self, command_id: str) -> List[RollbackRecord]:
        """الحصول على سجلات أمر"""
        return self._records.get(command_id, [])
    
    def has_rollback(self, command_id: str) -> bool:
        """هل يوجد Rollback متاح؟"""
        records = self._records.get(command_id, [])
        return any(not r.executed for r in records)
    
    def get_trash_size(self) -> int:
        """حجم الـ Trash بالبايت"""
        total = 0
        for root, dirs, files in os.walk(self.trash_dir):
            for f in files:
                total += os.path.getsize(os.path.join(root, f))
        return total
    
    def clear_trash(self, older_than_days: int = 7) -> int:
        """
        تنظيف الـ Trash.
        
        Args:
            older_than_days: حذف الملفات الأقدم من X أيام
        
        Returns:
            عدد الملفات المحذوفة
        """
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(days=older_than_days)
        deleted = 0
        
        for cmd_folder in os.listdir(self.trash_dir):
            cmd_path = os.path.join(self.trash_dir, cmd_folder)
            
            if not os.path.isdir(cmd_path):
                continue
            
            # فحص تاريخ المجلد
            mtime = datetime.fromtimestamp(os.path.getmtime(cmd_path))
            
            if mtime < cutoff:
                try:
                    shutil.rmtree(cmd_path)
                    deleted += 1
                except:
                    pass
        
        return deleted
    
    def format_status(self) -> str:
        """تنسيق الحالة للعرض"""
        total_records = sum(len(r) for r in self._records.values())
        pending = sum(
            1 for records in self._records.values()
            for r in records if not r.executed
        )
        
        trash_size = self.get_trash_size()
        trash_mb = trash_size / (1024 * 1024)
        
        return (
            f"↩️ Rollback Engine\n"
            f"  📝 سجلات: {total_records}\n"
            f"  ⏳ قابلة للتراجع: {pending}\n"
            f"  🗑️ Trash: {trash_mb:.2f} MB"
        )


# ═══════════════════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════════════════

_rollback_engine: Optional[RollbackEngine] = None

def get_rollback_engine() -> RollbackEngine:
    global _rollback_engine
    if _rollback_engine is None:
        _rollback_engine = RollbackEngine()
    return _rollback_engine
