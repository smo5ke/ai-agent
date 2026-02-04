"""
🧪 Test Filesystem - اختبار عمليات الملفات (Sandbox)
====================================================
"""

import os
import pytest


class TestCreateOperations:
    """اختبارات الإنشاء"""
    
    def test_create_folder_in_sandbox(self, sandbox_dir):
        """إنشاء مجلد في Sandbox"""
        folder_path = os.path.join(sandbox_dir, "test_folder")
        
        os.makedirs(folder_path)
        
        assert os.path.exists(folder_path)
        assert os.path.isdir(folder_path)
    
    def test_create_file_in_sandbox(self, sandbox_dir):
        """إنشاء ملف في Sandbox"""
        file_path = os.path.join(sandbox_dir, "test.txt")
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("Hello Test")
        
        assert os.path.exists(file_path)
        assert os.path.isfile(file_path)
    
    def test_create_nested_structure(self, sandbox_dir):
        """إنشاء هيكل متداخل"""
        nested_path = os.path.join(sandbox_dir, "a", "b", "c")
        
        os.makedirs(nested_path)
        
        assert os.path.exists(nested_path)


class TestDeleteOperations:
    """اختبارات الحذف"""
    
    def test_delete_file(self, sandbox_dir):
        """حذف ملف"""
        file_path = os.path.join(sandbox_dir, "to_delete.txt")
        
        # إنشاء
        with open(file_path, "w") as f:
            f.write("delete me")
        
        assert os.path.exists(file_path)
        
        # حذف
        os.remove(file_path)
        
        assert not os.path.exists(file_path)
    
    def test_delete_folder(self, sandbox_dir):
        """حذف مجلد"""
        import shutil
        
        folder_path = os.path.join(sandbox_dir, "to_delete")
        os.makedirs(folder_path)
        
        # إنشاء ملف داخله
        with open(os.path.join(folder_path, "file.txt"), "w") as f:
            f.write("test")
        
        assert os.path.exists(folder_path)
        
        # حذف
        shutil.rmtree(folder_path)
        
        assert not os.path.exists(folder_path)


class TestRollbackOperations:
    """اختبارات Rollback في Sandbox"""
    
    def test_rollback_create_file(self, sandbox_dir, rollback_engine):
        """Rollback بعد إنشاء ملف"""
        file_path = os.path.join(sandbox_dir, "rollback_test.txt")
        cmd_id = "CMD-TEST-ROLLBACK-1"
        
        # إنشاء
        with open(file_path, "w") as f:
            f.write("test")
        
        # تسجيل للـ rollback
        rollback_engine.register(
            command_id=cmd_id,
            node_id="node-1",
            intent="create_file",
            original_path=file_path,
            rollback_type="delete"
        )
        
        assert os.path.exists(file_path)
        
        # Rollback
        result = rollback_engine.rollback(cmd_id)
        
        assert result.success == True
        assert not os.path.exists(file_path)
    
    def test_trash_system(self, sandbox_dir, rollback_engine):
        """نظام الـ Trash"""
        file_path = os.path.join(sandbox_dir, "trash_test.txt")
        cmd_id = "CMD-TEST-TRASH-1"
        
        # إنشاء ملف
        with open(file_path, "w") as f:
            f.write("trash me")
        
        # نقل للـ trash
        trash_path = rollback_engine.move_to_trash(file_path, cmd_id)
        
        assert trash_path is not None
        assert os.path.exists(trash_path)
        assert not os.path.exists(file_path)


class TestCommandRegistry:
    """اختبارات Command Registry"""
    
    def test_generate_unique_ids(self, command_registry):
        """توليد IDs فريدة"""
        id1 = command_registry.generate_id()
        id2 = command_registry.generate_id()
        id3 = command_registry.generate_id()
        
        assert id1 != id2
        assert id2 != id3
        assert id1.startswith("CMD-")
    
    def test_register_command(self, command_registry):
        """تسجيل أمر"""
        cmd_id = command_registry.register("افتح كروم", "open")
        
        record = command_registry.get(cmd_id)
        
        assert record is not None
        assert record.raw_input == "افتح كروم"
        assert record.intent == "open"
    
    def test_update_status(self, command_registry):
        """تحديث الحالة"""
        from core.command_registry import CommandStatus
        
        cmd_id = command_registry.register("test")
        command_registry.update_status(cmd_id, CommandStatus.COMPLETED)
        
        record = command_registry.get(cmd_id)
        
        assert record.status == CommandStatus.COMPLETED
