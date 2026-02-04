"""
🎯 Confidence Score - نظام حساب الثقة
=====================================
Jarvis يحسب مستوى ثقته بالقرار.

Confidence ≥ 0.75 → نفّذ
Confidence 0.5-0.75 → نفّذ + إشعار
Confidence < 0.5 → اسأل
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class ConfidenceLevel(Enum):
    """مستوى الثقة"""
    HIGH = "high"          # ≥ 0.75 - نفّذ فوراً
    MEDIUM = "medium"      # 0.5-0.75 - نفّذ + إشعار
    LOW = "low"            # < 0.5 - اسأل


@dataclass
class ConfidenceScore:
    """نتيجة حساب الثقة"""
    score: float                    # 0.0 → 1.0
    level: ConfidenceLevel
    factors: Dict[str, float] = field(default_factory=dict)
    missing: List[str] = field(default_factory=list)
    inferred: Dict[str, str] = field(default_factory=dict)
    
    @property
    def should_execute(self) -> bool:
        """هل ننفذ؟"""
        return self.score >= 0.5
    
    @property
    def should_notify(self) -> bool:
        """هل نُشعر المستخدم؟"""
        return 0.5 <= self.score < 0.75
    
    @property
    def should_ask(self) -> bool:
        """هل نسأل المستخدم؟"""
        return self.score < 0.5


# ═══════════════════════════════════════════════════════════
# 📊 Confidence Factors
# ═══════════════════════════════════════════════════════════

# أوزان عوامل الثقة
CONFIDENCE_WEIGHTS = {
    # المعلومات المتوفرة
    "intent_explicit": 0.20,      # الـ intent واضح
    "target_explicit": 0.20,      # الـ target محدد
    "location_explicit": 0.15,    # الـ location محدد
    
    # الذكاء
    "has_default": 0.15,          # يوجد افتراضي
    "context_available": 0.10,    # سياق من العملية السابقة
    "pattern_match": 0.10,        # نمط معروف
    
    # الأمان
    "rollback_available": 0.10,   # قابل للتراجع
}


# الـ intents القابلة للتراجع (أكثر ثقة)
ROLLBACK_SAFE_INTENTS = {
    "create_folder",
    "create_file",
    "write_file",
    "copy",
    "move",
    "rename",
}


# ═══════════════════════════════════════════════════════════
# 🧮 Confidence Calculator
# ═══════════════════════════════════════════════════════════

class ConfidenceCalculator:
    """
    حاسبة الثقة.
    
    تحسب مستوى ثقة Jarvis بأن القرار صحيح.
    """
    
    def __init__(self):
        self.weights = CONFIDENCE_WEIGHTS.copy()
        self.rollback_safe = ROLLBACK_SAFE_INTENTS.copy()
    
    def calculate(self, command: dict, context: dict = None) -> ConfidenceScore:
        """
        حساب Confidence Score.
        
        Args:
            command: الأمر (مع الحقول المُكملة)
            context: السياق (آخر عملية، الذاكرة، الخ)
        
        Returns:
            ConfidenceScore
        """
        context = context or {}
        factors = {}
        missing = []
        inferred = {}
        
        intent = command.get("intent", "")
        target = command.get("target")
        loc = command.get("loc")
        
        # ═══════════════════════════════════════════════════════════
        # 1. Intent واضح؟
        # ═══════════════════════════════════════════════════════════
        if intent and intent != "unknown":
            factors["intent_explicit"] = self.weights["intent_explicit"]
        else:
            missing.append("intent")
        
        # ═══════════════════════════════════════════════════════════
        # 2. Target محدد أو مُستنتج؟
        # ═══════════════════════════════════════════════════════════
        if target and target not in ["", None, "?"]:
            if command.get("_inferred_target"):
                # مُستنتج - نصف الوزن
                factors["target_explicit"] = self.weights["target_explicit"] * 0.5
                inferred["target"] = target
            else:
                factors["target_explicit"] = self.weights["target_explicit"]
        else:
            missing.append("target")
        
        # ═══════════════════════════════════════════════════════════
        # 3. Location محدد أو مُستنتج؟
        # ═══════════════════════════════════════════════════════════
        if loc and loc not in ["", None, "?"]:
            if command.get("_inferred_loc"):
                # مُستنتج - نصف الوزن
                factors["location_explicit"] = self.weights["location_explicit"] * 0.5
                inferred["loc"] = loc
            else:
                factors["location_explicit"] = self.weights["location_explicit"]
        else:
            missing.append("location")
        
        # ═══════════════════════════════════════════════════════════
        # 4. يوجد افتراضي؟
        # ═══════════════════════════════════════════════════════════
        if command.get("_inferred_loc") or command.get("_inferred_target"):
            factors["has_default"] = self.weights["has_default"]
        
        # ═══════════════════════════════════════════════════════════
        # 5. سياق متوفر؟
        # ═══════════════════════════════════════════════════════════
        if context.get("last_intent") or context.get("last_location"):
            factors["context_available"] = self.weights["context_available"]
        
        # ═══════════════════════════════════════════════════════════
        # 6. نمط معروف؟
        # ═══════════════════════════════════════════════════════════
        # مثال: watch → create_folder هو نمط شائع
        if self._is_known_pattern(intent, context):
            factors["pattern_match"] = self.weights["pattern_match"]
        
        # ═══════════════════════════════════════════════════════════
        # 7. قابل للتراجع؟
        # ═══════════════════════════════════════════════════════════
        if intent in self.rollback_safe:
            factors["rollback_available"] = self.weights["rollback_available"]
        
        # ═══════════════════════════════════════════════════════════
        # حساب المجموع
        # ═══════════════════════════════════════════════════════════
        score = sum(factors.values())
        score = min(1.0, max(0.0, score))  # Clamp to 0-1
        
        # تحديد المستوى
        if score >= 0.75:
            level = ConfidenceLevel.HIGH
        elif score >= 0.5:
            level = ConfidenceLevel.MEDIUM
        else:
            level = ConfidenceLevel.LOW
        
        return ConfidenceScore(
            score=round(score, 2),
            level=level,
            factors=factors,
            missing=missing,
            inferred=inferred
        )
    
    def _is_known_pattern(self, intent: str, context: dict) -> bool:
        """هل هذا نمط معروف؟"""
        last_intent = context.get("last_intent")
        
        known_patterns = [
            ("watch", "create_folder"),
            ("watch", "create_file"),
            ("open", "write_file"),
            ("create_folder", "create_file"),
        ]
        
        return (last_intent, intent) in known_patterns
    
    def format_score(self, conf: ConfidenceScore) -> str:
        """تنسيق النتيجة للعرض"""
        emoji = {
            ConfidenceLevel.HIGH: "✅",
            ConfidenceLevel.MEDIUM: "⚠️",
            ConfidenceLevel.LOW: "❓"
        }
        
        lines = [
            f"{emoji[conf.level]} Confidence: {conf.score:.0%} ({conf.level.value})"
        ]
        
        if conf.inferred:
            for key, value in conf.inferred.items():
                lines.append(f"   📍 {key}: {value} (مُستنتج)")
        
        if conf.missing:
            lines.append(f"   ❓ ناقص: {', '.join(conf.missing)}")
        
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════════════════

_confidence_calculator: Optional[ConfidenceCalculator] = None

def get_confidence_calculator() -> ConfidenceCalculator:
    global _confidence_calculator
    if _confidence_calculator is None:
        _confidence_calculator = ConfidenceCalculator()
    return _confidence_calculator
