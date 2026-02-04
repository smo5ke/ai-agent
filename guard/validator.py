"""
✅ Schema Validator - التحقق من صحة الأوامر
============================================
"""

from typing import Tuple, Optional
from pydantic import ValidationError


# الـ Intents المسموحة
VALID_INTENTS = [
    "open", "open_file", "clean", "watch", "stop_watch",
    "macro", "schedule", "reminder", "unknown",
    # جديد
    "create_folder", "create_file", "write_file", "delete", "rename", "copy", "move"
]

# الحقول المطلوبة لكل intent
REQUIRED_FIELDS = {
    "open": ["target"],
    "open_file": ["target"],
    "watch": ["loc"],
    "clean": ["loc"],
    "macro": ["cmd"],
    "schedule": ["target", "time"],
    "reminder": ["param"],
    "create_folder": ["target"],
    "create_file": ["target"],
    "write_file": ["target", "param"],
    "delete": ["target"],
}


class SchemaValidator:
    """مدقق Schema للأوامر"""
    
    def validate(self, command: dict) -> Tuple[bool, Optional[str]]:
        """
        التحقق من صحة الأمر.
        
        Returns:
            (is_valid, error_message)
        """
        # 1. التحقق من وجود intent
        intent = command.get("intent")
        if not intent:
            return False, "Missing 'intent' field"
        
        # 2. التحقق من أن الـ intent صالح
        if intent not in VALID_INTENTS:
            return False, f"Invalid intent: {intent}"
        
        # 3. التحقق من الحقول المطلوبة
        required = REQUIRED_FIELDS.get(intent, [])
        for field in required:
            if not command.get(field):
                return False, f"Missing required field: {field}"
        
        # 4. التحقق من أنواع البيانات
        if command.get("target") and not isinstance(command["target"], str):
            return False, "Field 'target' must be string"
        
        if command.get("loc") and not isinstance(command["loc"], str):
            return False, "Field 'loc' must be string"
        
        return True, None


def validate_command(command: dict) -> Tuple[bool, Optional[str]]:
    """دالة مختصرة للتحقق"""
    validator = SchemaValidator()
    return validator.validate(command)
