"""
🧠 Decision Engine - محرك القرار
================================
Jarvis يتخذ قرار بدل ما يسأل.

Flow:
1. أمر ناقص
2. Learning Engine يحاول إكماله
3. World Model يُكمل الباقي
4. Confidence يُحسب
5. Decision Engine يُقرر:
   - Execute (≥0.75)
   - Execute + Notify (0.5-0.75)
   - Ask User (<0.5) → Clarification ذكي
"""

from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum

from core.world_model import get_world_model, WorldModel
from core.confidence import get_confidence_calculator, ConfidenceScore, ConfidenceLevel
from core.learning_engine import get_learning_engine, LearningEngine
from core.clarification import get_clarification_generator, ClarificationGenerator
from core.schemas import Command


class DecisionAction(Enum):
    """نوع القرار"""
    EXECUTE = "execute"           # نفّذ فوراً
    EXECUTE_NOTIFY = "notify"     # نفّذ + إشعار
    ASK_USER = "ask"              # اسأل المستخدم


@dataclass
class Decision:
    """
    قرار محرك القرار.
    """
    action: DecisionAction
    command: dict                   # الأمر المُكمل
    confidence: ConfidenceScore     # نتيجة الثقة
    
    # للإشعار
    notification: str = ""
    
    # للسؤال
    question: str = ""
    missing_fields: List[str] = field(default_factory=list)
    quick_responses: List[str] = field(default_factory=list)  # 🆕
    suggestions: Dict = field(default_factory=dict)           # 🆕
    
    # معلومات إضافية
    inferred_summary: str = ""      # ملخص ما تم استنتاجه
    learned_from: str = ""          # 🆕 pattern ID إذا تعلم
    
    @property
    def should_execute(self) -> bool:
        return self.action in [DecisionAction.EXECUTE, DecisionAction.EXECUTE_NOTIFY]
    
    @property
    def should_notify(self) -> bool:
        return self.action == DecisionAction.EXECUTE_NOTIFY
    
    @property
    def should_ask(self) -> bool:
        return self.action == DecisionAction.ASK_USER


@dataclass
class ChainDecision:
    """
    قرار لسلسلة أوامر.
    
    مثال: "راقب التنزيلات وإذا تغير أنشئ مجلد"
    """
    decisions: List[Decision]
    chain_confidence: float         # ثقة السلسلة ككل
    action: DecisionAction
    
    @property
    def all_executable(self) -> bool:
        return all(d.should_execute for d in self.decisions)


# ═══════════════════════════════════════════════════════════
# 🧠 Decision Engine
# ═══════════════════════════════════════════════════════════

class DecisionEngine:
    """
    محرك القرار الذكي.
    
    يُحول Jarvis من "مساعد يسأل" إلى "روبوت يتصرف".
    
    🆕 مع Learning + Clarification.
    """
    
    def __init__(self):
        self.world_model = get_world_model()
        self.confidence_calc = get_confidence_calculator()
        self.learning = get_learning_engine()          # 🆕
        self.clarification = get_clarification_generator()  # 🆕
        self._context: Dict[str, Any] = {}
    
    # ═══════════════════════════════════════════════════════════
    # القرار الرئيسي
    # ═══════════════════════════════════════════════════════════
    
    def resolve(self, command: dict) -> Decision:
        """
        القرار على أمر واحد.
        
        🆕 مع Learning + Clarification.
        
        Args:
            command: الأمر (قد يكون ناقص)
        
        Returns:
            Decision object
        """
        intent = command.get("intent", "")
        learned_from = ""
        
        # 1. 🆕 محاولة التعلم من أنماط سابقة
        learned_command = self.learning.apply_to_command(command)
        if learned_command.get("_learning_pattern"):
            learned_from = learned_command["_learning_pattern"]
            command = learned_command
        
        # 2. إكمال الأمر بالـ World Model
        completed = self.world_model.complete_command(command)
        
        # 3. حساب الثقة
        confidence = self.confidence_calc.calculate(completed, self._context)
        
        # 4. 🆕 Boost confidence إذا تعلم
        if learned_from:
            # زيادة الثقة بـ 15%
            boosted_score = min(1.0, confidence.score + 0.15)
            confidence = ConfidenceScore(
                score=boosted_score,
                level=confidence.level if boosted_score < 0.75 else ConfidenceLevel.HIGH,
                factors=confidence.factors,
                missing=confidence.missing,
                inferred=confidence.inferred
            )
        
        # 5. تحديد القرار
        quick_responses = []
        suggestions = {}
        
        if confidence.level == ConfidenceLevel.HIGH:
            action = DecisionAction.EXECUTE
            notification = ""
            question = ""
        
        elif confidence.level == ConfidenceLevel.MEDIUM:
            action = DecisionAction.EXECUTE_NOTIFY
            notification = self._build_notification(completed, confidence)
            question = ""
        
        else:
            action = DecisionAction.ASK_USER
            notification = ""
            
            # 🆕 Clarification ذكي بدل سؤال بسيط
            clarification = self.clarification.generate(
                intent=intent,
                missing_fields=confidence.missing,
                suggestions={
                    "target": completed.get("target", ""),
                    "loc": completed.get("loc", "")
                }
            )
            
            question = clarification.question
            quick_responses = clarification.quick_responses
            suggestions = clarification.suggestions
            
            # 🆕 تسجيل للتعلم لاحقاً
            cmd_id = completed.get("_cmd_id", intent)
            self.learning.register_question(cmd_id, intent, confidence.missing)
        
        # 6. تحديث السياق
        if action != DecisionAction.ASK_USER:
            self._update_context(completed)
            
            # 🆕 تأكيد استخدام الـ pattern
            if learned_from:
                self.learning.confirm_usage(learned_from)
        
        return Decision(
            action=action,
            command=completed,
            confidence=confidence,
            notification=notification,
            question=question,
            missing_fields=confidence.missing,
            quick_responses=quick_responses,
            suggestions=suggestions,
            inferred_summary=self._build_inferred_summary(completed, confidence),
            learned_from=learned_from
        )
    
    def resolve_chain(self, commands: List[dict]) -> ChainDecision:
        """
        القرار على سلسلة أوامر.
        
        مثال: watch → on_change → create_folder
        """
        decisions = []
        total_confidence = 0.0
        
        for cmd in commands:
            decision = self.resolve(cmd)
            decisions.append(decision)
            total_confidence += decision.confidence.score
        
        # متوسط الثقة
        chain_confidence = total_confidence / len(commands) if commands else 0.0
        
        # القرار النهائي للسلسلة
        if chain_confidence >= 0.75:
            action = DecisionAction.EXECUTE
        elif chain_confidence >= 0.5:
            action = DecisionAction.EXECUTE_NOTIFY
        else:
            action = DecisionAction.ASK_USER
        
        return ChainDecision(
            decisions=decisions,
            chain_confidence=round(chain_confidence, 2),
            action=action
        )
    
    # ═══════════════════════════════════════════════════════════
    # بناء الرسائل
    # ═══════════════════════════════════════════════════════════
    
    def _build_notification(self, command: dict, confidence: ConfidenceScore) -> str:
        """بناء إشعار التنفيذ"""
        intent = command.get("intent", "")
        target = command.get("target", "")
        loc = command.get("loc", "")
        
        intent_text = {
            "create_folder": "📁 تم إنشاء مجلد",
            "create_file": "📄 تم إنشاء ملف",
            "delete": "🗑️ تم الحذف",
            "move": "📦 تم النقل",
            "copy": "📋 تم النسخ",
        }
        
        base = intent_text.get(intent, f"✅ تم {intent}")
        
        parts = [f"{base}: \"{target}\""]
        
        # إضافة الموقع إذا مُستنتج
        if command.get("_inferred_loc"):
            parts.append(f"في {loc} (افتراضي)")
        elif loc:
            parts.append(f"في {loc}")
        
        # hint للتراجع
        parts.append("\n💡 للتراجع: rollback")
        
        return " ".join(parts)
    
    def _build_question(self, command: dict, confidence: ConfidenceScore) -> str:
        """بناء سؤال للمستخدم"""
        missing = confidence.missing
        
        if "target" in missing and "location" in missing:
            return "📝 شو اسم الملف/المجلد؟ ووين؟"
        elif "target" in missing:
            return "📝 شو الاسم؟"
        elif "location" in missing:
            return "📍 وين بالضبط؟"
        else:
            return "❓ ممكن توضحلي أكتر؟"
    
    def _build_inferred_summary(self, command: dict, confidence: ConfidenceScore) -> str:
        """ملخص ما تم استنتاجه"""
        parts = []
        
        if command.get("_inferred_target"):
            parts.append(f"الاسم: {command.get('target')}")
        
        if command.get("_inferred_loc"):
            parts.append(f"الموقع: {command.get('loc')}")
        
        if parts:
            return f"🤖 Jarvis استنتج: {' | '.join(parts)}"
        return ""
    
    # ═══════════════════════════════════════════════════════════
    # السياق
    # ═══════════════════════════════════════════════════════════
    
    def _update_context(self, command: dict):
        """تحديث السياق بعد التنفيذ"""
        intent = command.get("intent")
        loc = command.get("loc")
        target = command.get("target")
        
        self._context["last_intent"] = intent
        if loc:
            self._context["last_location"] = loc
        if target:
            self._context["last_target"] = target
        
        # للـ watch
        if intent == "watch":
            self._context["watch_target"] = target or loc
    
    def set_context(self, key: str, value: Any):
        """تعيين قيمة في السياق"""
        self._context[key] = value
    
    def get_context(self) -> Dict:
        """الحصول على السياق الحالي"""
        return self._context.copy()
    
    def clear_context(self):
        """مسح السياق"""
        self._context.clear()
    
    # ═══════════════════════════════════════════════════════════
    # تنسيق للعرض
    # ═══════════════════════════════════════════════════════════
    
    def format_decision(self, decision: Decision) -> str:
        """تنسيق القرار للعرض"""
        action_emoji = {
            DecisionAction.EXECUTE: "✅",
            DecisionAction.EXECUTE_NOTIFY: "⚠️",
            DecisionAction.ASK_USER: "❓"
        }
        
        emoji = action_emoji[decision.action]
        conf = decision.confidence
        
        lines = [
            f"{emoji} Decision: {decision.action.value}",
            f"   📊 Confidence: {conf.score:.0%}",
        ]
        
        # 🆕 إظهار التعلم
        if decision.learned_from:
            lines.append(f"   📚 Learned from: {decision.learned_from}")
        
        if decision.inferred_summary:
            lines.append(f"   {decision.inferred_summary}")
        
        if decision.notification:
            lines.append(f"   📢 {decision.notification}")
        
        if decision.question:
            lines.append(f"   ❓ {decision.question}")
            if decision.quick_responses:
                lines.append(f"   💡 Quick: {', '.join(decision.quick_responses)}")
        
        return "\n".join(lines)
    
    # ═══════════════════════════════════════════════════════════
    # 🆕 Learning API
    # ═══════════════════════════════════════════════════════════
    
    def learn_from_response(self, cmd_id: str, user_response: str, 
                            original_decision: Decision = None) -> Dict:
        """
        تعلم من رد المستخدم.
        
        Args:
            cmd_id: ID الأمر
            user_response: رد المستخدم
            original_decision: القرار الأصلي
        
        Returns:
            dict مع action و updates
        """
        # تحليل الرد
        clarification_result = None
        if original_decision:
            from core.clarification import Clarification
            clarification = Clarification(
                question=original_decision.question,
                suggestions=original_decision.suggestions,
                missing_fields=original_decision.missing_fields,
                quick_responses=original_decision.quick_responses,
                confidence=original_decision.confidence.score
            )
            action, updates = self.clarification.parse_response(user_response, clarification)
        else:
            # Simple parsing
            action = "unknown"
            updates = {"raw": user_response}
        
        # التعلم
        if action in ["confirm", "update"]:
            pattern = self.learning.resolve_question(cmd_id, updates)
            return {
                "action": action,
                "updates": updates,
                "learned": pattern.pattern_id if pattern else None
            }
        
        return {
            "action": action,
            "updates": updates,
            "learned": None
        }
    
    def get_learning_stats(self) -> str:
        """إحصائيات التعلم"""
        return self.learning.format_stats()


# ═══════════════════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════════════════

_decision_engine: Optional[DecisionEngine] = None

def get_decision_engine() -> DecisionEngine:
    global _decision_engine
    if _decision_engine is None:
        _decision_engine = DecisionEngine()
    return _decision_engine
