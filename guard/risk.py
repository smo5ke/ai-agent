"""
🚦 Risk Analyzer - محلل المخاطر
================================
تحديد مستوى خطورة كل أمر.
"""

from enum import Enum
from typing import Dict


class RiskLevel(Enum):
    """مستويات المخاطر"""
    LOW = 1      # آمن تماماً
    MEDIUM = 2   # يحتاج انتباه
    HIGH = 3     # خطير - يحتاج تأكيد
    CRITICAL = 4 # حرج - dry-run إجباري


# خريطة المخاطر لكل intent
RISK_MAP: Dict[str, RiskLevel] = {
    # LOW - عمليات آمنة
    "open": RiskLevel.LOW,
    "open_file": RiskLevel.LOW,
    "watch": RiskLevel.LOW,
    "stop_watch": RiskLevel.LOW,
    "macro": RiskLevel.LOW,
    "reminder": RiskLevel.LOW,
    "schedule": RiskLevel.LOW,
    
    # MEDIUM - عمليات تحتاج انتباه
    "move": RiskLevel.MEDIUM,
    "copy": RiskLevel.MEDIUM,
    "rename": RiskLevel.MEDIUM,
    "create_folder": RiskLevel.MEDIUM,
    "create_file": RiskLevel.MEDIUM,
    "write_file": RiskLevel.MEDIUM,
    
    # HIGH - عمليات خطيرة
    "clean": RiskLevel.HIGH,
    "delete": RiskLevel.HIGH,
    
    # CRITICAL - عمليات حرجة
    # (مستقبلاً: system commands, registry, etc)
}

# كلمات تزيد مستوى الخطورة
DANGER_KEYWORDS = [
    "system32", "windows", "program files",
    "all", "كل", "*", 
    "format", "registry",
]

# مسارات حساسة
SENSITIVE_PATHS = [
    "C:/Windows",
    "C:/Program Files",
    "C:/Users/*/AppData",
]


class RiskAnalyzer:
    """محلل مخاطر الأوامر"""
    
    def analyze(self, command: dict) -> RiskLevel:
        """
        تحليل مستوى خطورة الأمر.
        
        Returns:
            RiskLevel
        """
        intent = command.get("intent", "unknown")
        
        # 1. مستوى أساسي من الـ intent
        base_risk = RISK_MAP.get(intent, RiskLevel.MEDIUM)
        
        # 2. فحص كلمات الخطر
        target = str(command.get("target", "")).lower()
        loc = str(command.get("loc", "")).lower()
        param = str(command.get("param", "")).lower()
        
        combined = f"{target} {loc} {param}"
        
        for keyword in DANGER_KEYWORDS:
            if keyword.lower() in combined:
                # رفع مستوى الخطورة
                if base_risk.value < RiskLevel.HIGH.value:
                    base_risk = RiskLevel.HIGH
                break
        
        # 3. فحص المسارات الحساسة
        for path in SENSITIVE_PATHS:
            if path.lower().replace("*", "") in combined:
                base_risk = RiskLevel.CRITICAL
                break
        
        return base_risk
    
    def get_risk_description(self, risk: RiskLevel) -> str:
        """وصف مستوى الخطورة"""
        descriptions = {
            RiskLevel.LOW: "✅ آمن",
            RiskLevel.MEDIUM: "⚠️ يحتاج انتباه",
            RiskLevel.HIGH: "🔴 خطير - يحتاج تأكيد",
            RiskLevel.CRITICAL: "⛔ حرج - dry-run إجباري",
        }
        return descriptions.get(risk, "❓ غير معروف")


def analyze_risk(command: dict) -> RiskLevel:
    """دالة مختصرة لتحليل المخاطر"""
    analyzer = RiskAnalyzer()
    return analyzer.analyze(command)
