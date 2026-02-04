"""
⚡ Action Executor - منفذ الأوامر
==================================
تنفيذ الأوامر بشكل منظم مع logging.
"""

import time
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ExecutionResult:
    """نتيجة التنفيذ"""
    success: bool
    message: str
    intent: str
    duration_ms: float = 0
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ExecutionLogger:
    """مسجّل التنفيذ"""
    
    def __init__(self, max_logs: int = 100):
        self._logs: list = []
        self._max_logs = max_logs
    
    def log(self, result: ExecutionResult):
        """تسجيل نتيجة تنفيذ"""
        self._logs.append({
            "timestamp": result.timestamp,
            "intent": result.intent,
            "success": result.success,
            "message": result.message,
            "duration_ms": result.duration_ms,
            "error": result.error
        })
        
        # حد أقصى للسجلات
        if len(self._logs) > self._max_logs:
            self._logs.pop(0)
    
    def get_recent(self, count: int = 10) -> list:
        """جلب آخر السجلات"""
        return self._logs[-count:]
    
    def get_by_intent(self, intent: str) -> list:
        """جلب سجلات intent معين"""
        return [l for l in self._logs if l["intent"] == intent]
    
    def get_failures(self) -> list:
        """جلب الأخطاء"""
        return [l for l in self._logs if not l["success"]]
    
    def get_stats(self) -> dict:
        """إحصائيات التنفيذ"""
        total = len(self._logs)
        if total == 0:
            return {"total": 0}
        
        successes = sum(1 for l in self._logs if l["success"])
        avg_duration = sum(l["duration_ms"] for l in self._logs) / total
        
        return {
            "total": total,
            "success_rate": successes / total * 100,
            "avg_duration_ms": avg_duration,
            "failures": total - successes
        }


class ActionExecutor:
    """منفذ الأوامر الرئيسي"""
    
    def __init__(self):
        self.logger = ExecutionLogger()
        self._executors: Dict[str, callable] = {}
    
    def register(self, intent: str, executor: callable):
        """تسجيل executor لـ intent"""
        self._executors[intent] = executor
    
    def execute(self, command: dict) -> ExecutionResult:
        """
        تنفيذ أمر مع قياس الوقت وتسجيل النتيجة.
        """
        intent = command.get("intent", "unknown")
        start_time = time.time()
        
        try:
            # البحث عن executor
            executor = self._executors.get(intent)
            
            if not executor:
                result = ExecutionResult(
                    success=False,
                    message=f"No executor for intent: {intent}",
                    intent=intent,
                    error="EXECUTOR_NOT_FOUND"
                )
            else:
                # تنفيذ
                msg = executor(command)
                result = ExecutionResult(
                    success=True,
                    message=msg or "تم التنفيذ",
                    intent=intent
                )
                
        except Exception as e:
            result = ExecutionResult(
                success=False,
                message=str(e),
                intent=intent,
                error=type(e).__name__
            )
        
        # حساب المدة
        result.duration_ms = (time.time() - start_time) * 1000
        
        # تسجيل
        self.logger.log(result)
        
        return result
    
    def get_execution_logs(self, count: int = 10) -> list:
        """جلب سجلات التنفيذ"""
        return self.logger.get_recent(count)
    
    def get_stats(self) -> dict:
        """إحصائيات التنفيذ"""
        return self.logger.get_stats()


# Singleton
_executor = None

def get_executor() -> ActionExecutor:
    global _executor
    if _executor is None:
        _executor = ActionExecutor()
    return _executor
