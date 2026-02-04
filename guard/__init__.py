"""
🔒 Guard Layer - طبقة الأمان
============================
الحماية والتحقق قبل تنفيذ أي أمر.
"""

from .validator import SchemaValidator, validate_command
from .risk import RiskAnalyzer, RiskLevel, analyze_risk
from .dry_run import DryRunEngine, simulate_command
from .confirm import ConfirmationManager, needs_confirmation


class GuardLayer:
    """طبقة الأمان الرئيسية"""
    
    def __init__(self):
        self.validator = SchemaValidator()
        self.risk_analyzer = RiskAnalyzer()
        self.dry_run = DryRunEngine()
        self.confirmation = ConfirmationManager()
    
    def check(self, command: dict) -> dict:
        """
        فحص أمر قبل التنفيذ.
        
        Returns:
            {
                "allowed": bool,
                "risk_level": str,
                "needs_confirm": bool,
                "dry_run_result": str,
                "reason": str
            }
        """
        result = {
            "allowed": True,
            "risk_level": "LOW",
            "needs_confirm": False,
            "dry_run_result": None,
            "reason": ""
        }
        
        # 1. التحقق من Schema
        is_valid, error = self.validator.validate(command)
        if not is_valid:
            result["allowed"] = False
            result["reason"] = f"Schema Error: {error}"
            return result
        
        # 2. تحليل المخاطر
        risk = self.risk_analyzer.analyze(command)
        result["risk_level"] = risk.name
        
        # 3. هل يحتاج تأكيد؟
        if risk.value >= RiskLevel.HIGH.value:
            result["needs_confirm"] = True
            result["dry_run_result"] = self.dry_run.simulate(command)
        
        return result


# Singleton
_guard = None

def get_guard() -> GuardLayer:
    global _guard
    if _guard is None:
        _guard = GuardLayer()
    return _guard
