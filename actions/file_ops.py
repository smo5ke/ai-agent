# actions/file_ops.py
import os
from pathlib import Path
from core.base_action import BaseAction


class CreateFolderAction(BaseAction):
    def __init__(self, context, name):
        super().__init__(context)
        self.name = name
        self.path = Path(name) if os.path.isabs(name) else context.cwd / name
        self.created = False

    def execute(self):
        if not self.path.exists():
            self.path.mkdir(parents=True, exist_ok=True)
            self.created = True
            print(f"✅ Created Folder: {self.path}")
        else:
            print(f"ℹ️ Folder exists: {self.path}")
        
        self.context.set_cwd(self.path)

    def rollback(self):
        if self.created and self.path.exists():
            try:
                os.rmdir(self.path)
                print(f"⏪ Rollback: Deleted folder {self.path}")
            except OSError:
                print(f"⚠️ Could not rollback folder {self.path} (not empty)")


class CreateFileAction(BaseAction):
    def __init__(self, context, name):
        super().__init__(context)
        self.name = name
        self.path = Path(name) if os.path.isabs(name) else context.cwd / name
        self.existed_before = False

    def execute(self):
        if self.path.exists():
            self.existed_before = True
            with open(self.path, 'r', encoding='utf-8') as f:
                self.backup_data = f.read()
        
        self.path.touch(exist_ok=True)
        print(f"✅ Created File: {self.path}")

    def rollback(self):
        if self.existed_before and self.backup_data is not None:
            with open(self.path, 'w', encoding='utf-8') as f:
                f.write(self.backup_data)
            print(f"⏪ Rollback: Restored file {self.path}")
        elif not self.existed_before and self.path.exists():
            os.remove(self.path)
            print(f"⏪ Rollback: Deleted file {self.path}")


class WriteTextAction(BaseAction):
    def __init__(self, context, filename, text):
        super().__init__(context)
        self.filename = filename
        self.text = text
        self.path = Path(filename) if os.path.isabs(filename) else context.cwd / filename

    def execute(self):
        # حفظ المحتوى القديم
        if self.path.exists():
            with open(self.path, 'r', encoding='utf-8') as f:
                self.backup_data = f.read()
        
        with open(self.path, 'w', encoding='utf-8') as f:
            f.write(self.text)
        print(f"✅ Wrote to: {self.path}")

    def rollback(self):
        if self.backup_data is not None:
            with open(self.path, 'w', encoding='utf-8') as f:
                f.write(self.backup_data)
            print(f"⏪ Rollback: Restored content of {self.path}")
        else:
            # الملف كان فارغ
            with open(self.path, 'w', encoding='utf-8') as f:
                f.write("")
            print(f"⏪ Rollback: Cleared {self.path}")


class DeleteFolderAction(BaseAction):
    def __init__(self, context, name):
        super().__init__(context)
        self.name = name
        self.path = Path(name) if os.path.isabs(name) else context.cwd / name
        self.deleted = False

    def execute(self):
        if self.path.exists() and self.path.is_dir():
            try:
                # محاولة الحذف (يجب أن يكون فارغاً لأمان os.rmdir)
                # لو أردنا حذف شجري نحتاج shutil.rmtree لكنه خطر
                # سنستخدم rmdir للأمان حالياً
                os.rmdir(self.path)
                self.deleted = True
                print(f"✅ Deleted Folder: {self.path}")
            except OSError as e:
                print(f"❌ Failed to delete folder {self.path}: {e}")
        else:
            print(f"ℹ️ Folder not found: {self.path}")

    def rollback(self):
        if self.deleted:
            self.path.mkdir(parents=True, exist_ok=True)
            print(f"⏪ Rollback: Restored folder {self.path}")


class DeleteFileAction(BaseAction):
    def __init__(self, context, name):
        super().__init__(context)
        self.name = name
        self.path = Path(name) if os.path.isabs(name) else context.cwd / name
        self.backup_data = None
        self.deleted = False

    def execute(self):
        if self.path.exists() and self.path.is_file():
            try:
                # قراءة المحتوى للنسخ الاحتياطي
                with open(self.path, 'rb') as f:
                    self.backup_data = f.read()
                
                os.remove(self.path)
                self.deleted = True
                print(f"✅ Deleted File: {self.path}")
            except OSError as e:
                print(f"❌ Failed to delete file {self.path}: {e}")
        else:
            print(f"ℹ️ File not found: {self.path}")

    def rollback(self):
        if self.deleted and self.backup_data:
            with open(self.path, 'wb') as f:
                f.write(self.backup_data)
            print(f"⏪ Rollback: Restored file {self.path}")


ACTION_CLASSES = {
    "create_folder": CreateFolderAction,
    "create_file": CreateFileAction,
    "write_text": WriteTextAction,
    "delete_folder": DeleteFolderAction,
    "delete_file": DeleteFileAction
}
