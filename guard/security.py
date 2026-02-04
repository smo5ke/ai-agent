"""
🛡️ Security Hardening - تعزيز الأمان
====================================
إصلاحات أمنية للتهديدات المحددة في SECURITY.md
"""

import os
import re
from typing import Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class SecurityCheckResult:
    """نتيجة فحص أمني"""
    safe: bool
    threat_type: Optional[str] = None
    message: str = ""
    blocked_pattern: Optional[str] = None


class PathSecurityChecker:
    """
    فحص أمان المسارات.
    
    يكشف:
    - Path Traversal (../)
    - System paths
    - Wildcard patterns
    """
    
    # مسارات محظورة
    BLOCKED_PATHS = [
        r"C:\\Windows",
        r"C:\\Windows\\System32",
        r"C:\\Program Files",
        r"C:\\Program Files (x86)",
        r"C:\\ProgramData",
        r"C:\\Users\\.*\\AppData\\Local\\Microsoft",
        r"C:\\Users\\.*\\AppData\\Roaming\\Microsoft",
        r"C:\\$Recycle.Bin",
        r"C:\\System Volume Information",
    ]
    
    # أنماط Wildcard خطرة
    DANGEROUS_WILDCARDS = [
        r"\*\.\*",      # *.*
        r"\*\.exe",     # *.exe
        r"\*\.dll",     # *.dll
        r"\*\.sys",     # *.sys
        r"\*\.bat",     # *.bat
        r"\*\.cmd",     # *.cmd
        r"\*\.ps1",     # *.ps1
    ]
    
    # أنماط Path Traversal
    TRAVERSAL_PATTERNS = [
        r"\.\./",       # ../
        r"\.\.\\",      # ..\
        r"\.\./",       # ../
        r"%2e%2e",      # URL encoded ..
        r"\.\.%2f",     # ../ URL encoded
        r"\.\.%5c",     # ..\ URL encoded
    ]
    
    def check_path(self, path: str) -> SecurityCheckResult:
        """فحص مسار للتهديدات الأمنية"""
        if not path:
            return SecurityCheckResult(safe=True)
        
        # 1. تحويل لمسار مطلق
        try:
            normalized = os.path.normpath(os.path.abspath(path))
        except Exception:
            return SecurityCheckResult(
                safe=False,
                threat_type="INVALID_PATH",
                message=f"مسار غير صالح: {path}"
            )
        
        # 2. فحص Path Traversal
        traversal_check = self._check_traversal(path)
        if not traversal_check.safe:
            return traversal_check
        
        # 3. فحص المسارات المحظورة
        blocked_check = self._check_blocked_paths(normalized)
        if not blocked_check.safe:
            return blocked_check
        
        # 4. فحص Wildcards
        wildcard_check = self._check_wildcards(path)
        if not wildcard_check.safe:
            return wildcard_check
        
        return SecurityCheckResult(safe=True)
    
    def _check_traversal(self, path: str) -> SecurityCheckResult:
        """كشف Path Traversal"""
        for pattern in self.TRAVERSAL_PATTERNS:
            if re.search(pattern, path, re.IGNORECASE):
                return SecurityCheckResult(
                    safe=False,
                    threat_type="PATH_TRAVERSAL",
                    message=f"🚫 Path Traversal محظور: {path}",
                    blocked_pattern=pattern
                )
        return SecurityCheckResult(safe=True)
    
    def _check_blocked_paths(self, normalized_path: str) -> SecurityCheckResult:
        """فحص المسارات المحظورة"""
        for blocked in self.BLOCKED_PATHS:
            if re.match(blocked, normalized_path, re.IGNORECASE):
                return SecurityCheckResult(
                    safe=False,
                    threat_type="BLOCKED_PATH",
                    message=f"🚫 مسار محمي: {normalized_path}",
                    blocked_pattern=blocked
                )
        return SecurityCheckResult(safe=True)
    
    def _check_wildcards(self, path: str) -> SecurityCheckResult:
        """كشف Wildcards الخطرة"""
        for pattern in self.DANGEROUS_WILDCARDS:
            if re.search(pattern, path, re.IGNORECASE):
                return SecurityCheckResult(
                    safe=False,
                    threat_type="DANGEROUS_WILDCARD",
                    message=f"🚫 Wildcard خطر: {path}",
                    blocked_pattern=pattern
                )
        return SecurityCheckResult(safe=True)
    
    def sanitize_filename(self, filename: str) -> str:
        """تنظيف اسم الملف"""
        # إزالة الأحرف الخطرة
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\0']
        for char in dangerous_chars:
            filename = filename.replace(char, '_')
        
        # إزالة .. 
        filename = filename.replace('..', '_')
        
        # إزالة / و \
        filename = filename.replace('/', '_').replace('\\', '_')
        
        return filename.strip()


class InputSanitizer:
    """
    تنظيف المدخلات من الـ injection attacks.
    """
    
    # أنماط Prompt Injection
    INJECTION_PATTERNS = [
        r"ignore previous",
        r"forget your instructions",
        r"you are now",
        r"new instructions",
        r"system prompt",
        r"override",
        r"bypass",
        r"\[\[.*\]\]",  # [[hidden instructions]]
        r"<\|.*\|>",    # <|special tokens|>
    ]
    
    def sanitize(self, text: str) -> Tuple[str, List[str]]:
        """
        تنظيف النص وإرجاع التحذيرات.
        
        Returns:
            (cleaned_text, warnings)
        """
        warnings = []
        cleaned = text
        
        for pattern in self.INJECTION_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                warnings.append(f"⚠️ نمط مشبوه: {pattern}")
                # لا نحذف، فقط نحذر
        
        return cleaned, warnings
    
    def is_suspicious(self, text: str) -> bool:
        """هل النص مشبوه؟"""
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False


class RateLimiter:
    """
    Rate Limiting للحماية من الإساءة.
    """
    
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: List[float] = []
    
    def check(self) -> bool:
        """هل مسموح بطلب جديد؟"""
        import time
        now = time.time()
        
        # تنظيف الطلبات القديمة
        self._requests = [
            t for t in self._requests 
            if now - t < self.window_seconds
        ]
        
        if len(self._requests) >= self.max_requests:
            return False
        
        self._requests.append(now)
        return True
    
    def reset(self):
        """إعادة تعيين"""
        self._requests = []


class ExecutionTimeout:
    """
    Timeout للتنفيذ.
    """
    
    DEFAULT_TIMEOUT = 30  # ثانية
    MAX_TIMEOUT = 300     # 5 دقائق
    
    @staticmethod
    def get_timeout(intent: str) -> int:
        """الحصول على timeout حسب الـ intent"""
        timeouts = {
            "open": 10,
            "create_folder": 5,
            "create_file": 5,
            "write_file": 10,
            "delete": 5,
            "copy": 30,
            "move": 30,
            "clean": 60,
            "watch": 300,
        }
        return timeouts.get(intent, ExecutionTimeout.DEFAULT_TIMEOUT)


class AuditLogger:
    """
    سجل المراقبة الأمنية.
    """
    
    def __init__(self, log_file: str = None):
        self.log_file = log_file or "data/security_audit.log"
        self._ensure_log_dir()
    
    def _ensure_log_dir(self):
        """التأكد من وجود مجلد اللوقات"""
        log_dir = os.path.dirname(self.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
    
    def log(self, event_type: str, details: dict):
        """تسجيل حدث أمني"""
        from datetime import datetime
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            **details
        }
        
        try:
            import json
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass  # لا نفشل بسبب اللوق
    
    def log_threat(self, threat_type: str, path: str, blocked: bool):
        """تسجيل تهديد"""
        self.log("THREAT_DETECTED", {
            "threat_type": threat_type,
            "path": path,
            "blocked": blocked
        })
    
    def log_policy_decision(self, cmd_id: str, intent: str, allowed: bool, reason: str = ""):
        """تسجيل قرار سياسة"""
        self.log("POLICY_DECISION", {
            "command_id": cmd_id,
            "intent": intent,
            "allowed": allowed,
            "reason": reason
        })
    
    def log_profile_change(self, old_profile: str, new_profile: str):
        """تسجيل تغيير الوضع"""
        self.log("PROFILE_CHANGE", {
            "old_profile": old_profile,
            "new_profile": new_profile
        })


# ═══════════════════════════════════════════════════════════
# Singletons
# ═══════════════════════════════════════════════════════════

_path_checker: Optional[PathSecurityChecker] = None
_input_sanitizer: Optional[InputSanitizer] = None
_rate_limiter: Optional[RateLimiter] = None
_audit_logger: Optional[AuditLogger] = None

def get_path_checker() -> PathSecurityChecker:
    global _path_checker
    if _path_checker is None:
        _path_checker = PathSecurityChecker()
    return _path_checker

def get_input_sanitizer() -> InputSanitizer:
    global _input_sanitizer
    if _input_sanitizer is None:
        _input_sanitizer = InputSanitizer()
    return _input_sanitizer

def get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter

def get_audit_logger() -> AuditLogger:
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
