# sandbox/python_executor.py
"""
📦 Python Executor - صندوق الرمل
تشغيل سكربتات بايثون بأمان مع timeout
"""
import subprocess
import tempfile
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class ExecutionResult:
    """نتيجة تنفيذ الكود"""
    success: bool
    stdout: str
    stderr: str
    return_code: int
    timeout: bool = False


class PythonExecutor:
    def __init__(self, timeout: int = 5, max_output: int = 10000):
        self.timeout = timeout  # ثوانٍ
        self.max_output = max_output  # حد أقصى للمخرجات
        
        # المكتبات المحظورة
        self.blocked_imports = {
            'os.system', 'subprocess', 'shutil.rmtree',
            'socket', 'requests', 'urllib'
        }

    def validate_code(self, code: str) -> tuple[bool, str]:
        """فحص الكود قبل التنفيذ"""
        
        # فحص الـ imports الخطيرة
        for blocked in self.blocked_imports:
            if blocked in code:
                return False, f"Blocked import/function: {blocked}"
        
        # فحص أوامر النظام
        dangerous = ['eval(', 'exec(', '__import__', 'open(', 'file(']
        for d in dangerous:
            if d in code and 'open(' in code:
                # نسمح بـ open للقراءة فقط
                if 'w' in code or 'a' in code:
                    return False, f"Dangerous operation: {d}"
        
        return True, "OK"

    def execute(self, code: str) -> ExecutionResult:
        """تنفيذ كود بايثون"""
        
        # 1. فحص الكود
        valid, msg = self.validate_code(code)
        if not valid:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Security Error: {msg}",
                return_code=-1
            )
        
        # 2. إنشاء ملف مؤقت
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # 3. تنفيذ الكود
            result = subprocess.run(
                ['python', temp_file],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=tempfile.gettempdir()
            )
            
            # 4. تحديد النتيجة
            stdout = result.stdout[:self.max_output]
            stderr = result.stderr[:self.max_output]
            
            return ExecutionResult(
                success=(result.returncode == 0),
                stdout=stdout,
                stderr=stderr,
                return_code=result.returncode
            )
            
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Timeout: Code execution exceeded {self.timeout} seconds",
                return_code=-1,
                timeout=True
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Execution Error: {str(e)}",
                return_code=-1
            )
        finally:
            # 5. حذف الملف المؤقت
            try:
                os.unlink(temp_file)
            except:
                pass

    def execute_simple(self, expression: str) -> str:
        """تنفيذ تعبير بسيط وإرجاع النتيجة"""
        code = f"print({expression})"
        result = self.execute(code)
        
        if result.success:
            return result.stdout.strip()
        else:
            return f"Error: {result.stderr}"


# Singleton instance
_executor: Optional[PythonExecutor] = None

def get_executor() -> PythonExecutor:
    global _executor
    if _executor is None:
        _executor = PythonExecutor()
    return _executor
