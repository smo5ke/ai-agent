"""
🔒 Execution Plan - خطة التنفيذ المُجمدة
=======================================
Plan → Validate → Freeze → Execute

Anti-Hallucination: منع الـ LLM من تغيير الخطة بعد الموافقة.
"""

import hashlib
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from pydantic import ValidationError

from core.schemas import Command


class PlanStatus(Enum):
    """حالة الخطة"""
    DRAFT = "draft"          # مسودة قابلة للتعديل
    VALIDATED = "validated"  # تم التحقق
    FROZEN = "frozen"        # مُجمدة لا تُعدل
    EXECUTING = "executing"  # قيد التنفيذ
    COMPLETED = "completed"  # اكتملت
    FAILED = "failed"        # فشلت
    CANCELLED = "cancelled"  # ملغاة


@dataclass
class PlanStep:
    """خطوة واحدة في الخطة"""
    index: int
    intent: str
    target: str
    location: str = ""
    params: Dict = field(default_factory=dict)
    validated: bool = False
    validation_errors: List[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    """نتيجة التحقق"""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class ExecutionPlan:
    """
    خطة التنفيذ المُجمدة.
    
    بعد الـ Freeze، الخطة لا تُعدل أبداً.
    أي تغيير = خطة جديدة.
    """
    plan_id: str
    command_id: str
    raw_input: str
    steps: List[PlanStep] = field(default_factory=list)
    status: PlanStatus = PlanStatus.DRAFT
    
    # التحقق
    validation_result: Optional[ValidationResult] = None
    
    # التجميد
    frozen_at: Optional[datetime] = None
    frozen_hash: Optional[str] = None
    
    # Audit
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "llm"
    
    def add_step(self, intent: str, target: str, location: str = "", params: Dict = None) -> PlanStep:
        """إضافة خطوة (فقط في DRAFT)"""
        if self.status != PlanStatus.DRAFT:
            raise ValueError(f"Cannot modify plan in {self.status.value} status")
        
        step = PlanStep(
            index=len(self.steps),
            intent=intent,
            target=target,
            location=location,
            params=params or {}
        )
        self.steps.append(step)
        return step
    
    def compute_hash(self) -> str:
        """حساب hash للخطة"""
        data = {
            "plan_id": self.plan_id,
            "command_id": self.command_id,
            "steps": [
                {
                    "intent": s.intent,
                    "target": s.target,
                    "location": s.location,
                    "params": s.params
                }
                for s in self.steps
            ]
        }
        json_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(json_str.encode()).hexdigest()[:16]
    
    def verify_integrity(self) -> bool:
        """التحقق من عدم التلاعب"""
        if not self.frozen_hash:
            return False
        return self.compute_hash() == self.frozen_hash
    
    def to_commands(self) -> List[Command]:
        """تحويل الخطة لأوامر"""
        commands = []
        for step in self.steps:
            cmd = Command(
                intent=step.intent,
                target=step.target,
                loc=step.location,
                **step.params
            )
            commands.append(cmd)
        return commands
    
    def to_dict(self) -> Dict:
        """تحويل لـ dict"""
        return {
            "plan_id": self.plan_id,
            "command_id": self.command_id,
            "status": self.status.value,
            "steps_count": len(self.steps),
            "steps": [
                {
                    "index": s.index,
                    "intent": s.intent,
                    "target": s.target,
                    "location": s.location
                }
                for s in self.steps
            ],
            "frozen_hash": self.frozen_hash,
            "created_at": self.created_at.isoformat()
        }


class PlanValidator:
    """
    مُحقق الخطة.
    
    يتحقق من:
    - صحة الـ Schema
    - صحة الـ Intent
    - صحة المسارات
    """
    
    # الـ intents المسموحة
    VALID_INTENTS = {
        'open', 'open_file', 'clean', 'watch', 'stop_watch',
        'macro', 'schedule', 'reminder', 'unknown',
        'create_folder', 'create_file', 'write_file',
        'delete', 'rename', 'copy', 'move'
    }
    
    # الـ intents التي تحتاج target
    REQUIRES_TARGET = {
        'open', 'open_file', 'create_folder', 'create_file',
        'write_file', 'delete', 'rename', 'copy', 'move', 'watch'
    }
    
    def validate(self, plan: ExecutionPlan) -> ValidationResult:
        """التحقق من الخطة"""
        errors = []
        warnings = []
        
        if not plan.steps:
            errors.append("الخطة فارغة - لا توجد خطوات")
            return ValidationResult(valid=False, errors=errors)
        
        for step in plan.steps:
            step_errors = self._validate_step(step)
            
            if step_errors:
                step.validated = False
                step.validation_errors = step_errors
                errors.extend([f"Step {step.index}: {e}" for e in step_errors])
            else:
                step.validated = True
        
        # تحذيرات
        if len(plan.steps) > 10:
            warnings.append(f"خطة طويلة ({len(plan.steps)} خطوات) - قد تستغرق وقتاً")
        
        result = ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
        
        plan.validation_result = result
        
        if result.valid:
            plan.status = PlanStatus.VALIDATED
        
        return result
    
    def _validate_step(self, step: PlanStep) -> List[str]:
        """التحقق من خطوة واحدة"""
        errors = []
        
        # 1. التحقق من الـ intent
        if step.intent not in self.VALID_INTENTS:
            errors.append(f"Intent غير معروف: {step.intent}")
        
        # 2. التحقق من الـ target
        if step.intent in self.REQUIRES_TARGET and not step.target:
            errors.append(f"Intent '{step.intent}' يحتاج target")
        
        # 3. التحقق من المسار (للـ delete)
        if step.intent == "delete":
            if step.target and any(
                blocked in step.target.lower() 
                for blocked in ["system32", "windows", "program files"]
            ):
                errors.append(f"مسار محظور: {step.target}")
        
        return errors


class PlanFreezer:
    """
    مُجمد الخطة.
    
    بعد التجميد، الخطة Immutable.
    """
    
    def freeze(self, plan: ExecutionPlan) -> bool:
        """تجميد الخطة"""
        if plan.status != PlanStatus.VALIDATED:
            return False
        
        plan.frozen_at = datetime.now()
        plan.frozen_hash = plan.compute_hash()
        plan.status = PlanStatus.FROZEN
        
        return True
    
    def is_frozen(self, plan: ExecutionPlan) -> bool:
        """هل الخطة مُجمدة؟"""
        return plan.status == PlanStatus.FROZEN
    
    def is_tampered(self, plan: ExecutionPlan) -> bool:
        """هل تم التلاعب بالخطة؟"""
        if not plan.frozen_hash:
            return False
        return plan.compute_hash() != plan.frozen_hash


class PlanBuilder:
    """
    بناء الخطة من output الـ LLM.
    """
    
    def __init__(self, command_id: str, raw_input: str):
        self.command_id = command_id
        self.raw_input = raw_input
        self.plan_id = f"PLAN-{command_id.replace('CMD-', '')}"
        self.plan = ExecutionPlan(
            plan_id=self.plan_id,
            command_id=command_id,
            raw_input=raw_input
        )
    
    def add_step(self, intent: str, target: str = "", 
                 location: str = "", **params) -> "PlanBuilder":
        """إضافة خطوة"""
        self.plan.add_step(intent, target, location, params)
        return self
    
    def from_commands(self, commands: List[Command]) -> "PlanBuilder":
        """بناء من أوامر"""
        for cmd in commands:
            self.plan.add_step(
                intent=cmd.intent,
                target=cmd.target or "",
                location=cmd.loc or "",
                params={
                    "param": cmd.param,
                    "dest": cmd.destination,
                    "filter": cmd.filter_key
                }
            )
        return self
    
    def build(self) -> ExecutionPlan:
        """الحصول على الخطة"""
        return self.plan


class PlanningEngine:
    """
    محرك التخطيط الكامل.
    
    Flow: Create → Validate → Freeze → Execute
    """
    
    def __init__(self):
        self.validator = PlanValidator()
        self.freezer = PlanFreezer()
        self._plans: Dict[str, ExecutionPlan] = {}
    
    def create_plan(self, command_id: str, raw_input: str, 
                    commands: List[Command]) -> ExecutionPlan:
        """إنشاء خطة من الأوامر"""
        builder = PlanBuilder(command_id, raw_input)
        builder.from_commands(commands)
        plan = builder.build()
        
        self._plans[plan.plan_id] = plan
        return plan
    
    def validate_plan(self, plan: ExecutionPlan) -> ValidationResult:
        """التحقق من الخطة"""
        return self.validator.validate(plan)
    
    def freeze_plan(self, plan: ExecutionPlan) -> bool:
        """تجميد الخطة"""
        return self.freezer.freeze(plan)
    
    def get_plan(self, plan_id: str) -> Optional[ExecutionPlan]:
        """الحصول على خطة"""
        return self._plans.get(plan_id)
    
    def prepare_for_execution(self, plan: ExecutionPlan) -> Optional[List[Command]]:
        """
        تحضير الخطة للتنفيذ.
        
        يتحقق من:
        1. الخطة مُجمدة
        2. لم يتم التلاعب بها
        
        Returns:
            List[Command] إذا نجح، None إذا فشل
        """
        if not self.freezer.is_frozen(plan):
            return None
        
        if self.freezer.is_tampered(plan):
            return None
        
        plan.status = PlanStatus.EXECUTING
        return plan.to_commands()
    
    def mark_completed(self, plan: ExecutionPlan, success: bool = True):
        """تحديث حالة الخطة بعد التنفيذ"""
        plan.status = PlanStatus.COMPLETED if success else PlanStatus.FAILED
    
    def format_plan(self, plan: ExecutionPlan) -> str:
        """تنسيق الخطة للعرض"""
        status_icons = {
            PlanStatus.DRAFT: "📝",
            PlanStatus.VALIDATED: "✅",
            PlanStatus.FROZEN: "🔒",
            PlanStatus.EXECUTING: "⚙️",
            PlanStatus.COMPLETED: "✅",
            PlanStatus.FAILED: "❌",
            PlanStatus.CANCELLED: "🚫"
        }
        
        icon = status_icons.get(plan.status, "❓")
        lines = [
            f"{icon} Plan [{plan.plan_id}] - {plan.status.value.upper()}",
            f"   📝 Input: {plan.raw_input[:50]}...",
            f"   📊 Steps: {len(plan.steps)}",
        ]
        
        if plan.frozen_hash:
            lines.append(f"   🔒 Hash: {plan.frozen_hash}")
        
        for step in plan.steps:
            check = "✓" if step.validated else "✗"
            lines.append(f"   [{check}] {step.index+1}. {step.intent}: {step.target}")
        
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════════════════

_planning_engine: Optional[PlanningEngine] = None

def get_planning_engine() -> PlanningEngine:
    global _planning_engine
    if _planning_engine is None:
        _planning_engine = PlanningEngine()
    return _planning_engine
