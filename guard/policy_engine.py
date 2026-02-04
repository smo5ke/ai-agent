"""
🛡️ Policy Engine - محرك السياسات
=================================
تحكم مركزي بالصلاحيات والأمان.

Flow:
Command → Policy Engine → Decision → Execute/Block
"""

import os
import re
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

# 🆕 Security Hardening
from guard.security import get_path_checker, get_audit_logger


class RiskLevel(Enum):
    """مستوى الخطر"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    
    def __lt__(self, other):
        order = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        return order.index(self) < order.index(other)
    
    def __le__(self, other):
        return self == other or self < other


@dataclass
class Policy:
    """سياسة واحدة"""
    intent: str                                    # delete, create_file, etc
    risk: RiskLevel = RiskLevel.LOW
    requires_confirmation: bool = False
    allowed_profiles: List[str] = field(default_factory=lambda: ["safe", "power", "silent"])
    dry_run_allowed: bool = True
    blocked_paths: List[str] = field(default_factory=list)
    allowed_paths: List[str] = field(default_factory=list)
    max_items: int = -1                            # -1 = unlimited


@dataclass
class Decision:
    """قرار السياسة"""
    allowed: bool
    reason: str = ""
    require_confirm: bool = False
    force_dry_run: bool = False
    risk_level: RiskLevel = RiskLevel.LOW
    warnings: List[str] = field(default_factory=list)


class PolicyEngine:
    """
    محرك السياسات المركزي.
    
    يُقيّم كل أمر ويُقرر إذا كان مسموحاً أم لا.
    """
    
    # المسارات المحظورة دائماً
    ALWAYS_BLOCKED_PATHS = [
        r".*[\\/]Windows[\\/].*",
        r".*[\\/]System32[\\/].*",
        r".*[\\/]Program Files[\\/].*",
        r".*[\\/]Program Files \(x86\)[\\/].*",
        r"C:[\\/]$",
        r".*[\\/]\.git[\\/].*",
        r".*[\\/]node_modules[\\/].*",
    ]
    
    def __init__(self):
        self.policies: Dict[str, Policy] = {}
        self.current_profile = "power"
        self._load_default_policies()
    
    # ═══════════════════════════════════════════════════════════
    # تحميل السياسات الافتراضية
    # ═══════════════════════════════════════════════════════════
    
    def _load_default_policies(self):
        """تحميل السياسات الافتراضية"""
        
        # فتح التطبيقات - آمن
        self.policies["open"] = Policy(
            intent="open",
            risk=RiskLevel.LOW,
            requires_confirmation=False
        )
        
        # فتح الملفات - آمن
        self.policies["open_file"] = Policy(
            intent="open_file",
            risk=RiskLevel.LOW,
            requires_confirmation=False
        )
        
        # إنشاء مجلد - منخفض
        self.policies["create_folder"] = Policy(
            intent="create_folder",
            risk=RiskLevel.LOW,
            requires_confirmation=False
        )
        
        # إنشاء ملف - منخفض
        self.policies["create_file"] = Policy(
            intent="create_file",
            risk=RiskLevel.LOW,
            requires_confirmation=False
        )
        
        # الكتابة في ملف - متوسط
        self.policies["write_file"] = Policy(
            intent="write_file",
            risk=RiskLevel.MEDIUM,
            requires_confirmation=False
        )
        
        # الحذف - عالي
        self.policies["delete"] = Policy(
            intent="delete",
            risk=RiskLevel.HIGH,
            requires_confirmation=True,
            allowed_profiles=["power", "silent"]
        )
        
        # إعادة التسمية - متوسط
        self.policies["rename"] = Policy(
            intent="rename",
            risk=RiskLevel.MEDIUM,
            requires_confirmation=False
        )
        
        # النقل - متوسط
        self.policies["move"] = Policy(
            intent="move",
            risk=RiskLevel.MEDIUM,
            requires_confirmation=False
        )
        
        # النسخ - منخفض
        self.policies["copy"] = Policy(
            intent="copy",
            risk=RiskLevel.LOW,
            requires_confirmation=False
        )
        
        # Macro - منخفض
        self.policies["macro"] = Policy(
            intent="macro",
            risk=RiskLevel.LOW,
            requires_confirmation=False
        )
        
        # المراقبة - منخفض
        self.policies["watch"] = Policy(
            intent="watch",
            risk=RiskLevel.LOW,
            requires_confirmation=False
        )
        
        # الجدولة - متوسط
        self.policies["schedule"] = Policy(
            intent="schedule",
            risk=RiskLevel.MEDIUM,
            requires_confirmation=False
        )
        
        # التذكير - منخفض
        self.policies["reminder"] = Policy(
            intent="reminder",
            risk=RiskLevel.LOW,
            requires_confirmation=False
        )
    
    # ═══════════════════════════════════════════════════════════
    # التقييم
    # ═══════════════════════════════════════════════════════════
    
    def evaluate(self, command: dict, profile: str = None) -> Decision:
        """
        تقييم أمر وإرجاع القرار.
        
        Args:
            command: الأمر (dict with intent, target, loc, etc)
            profile: الـ profile الحالي (safe, power, silent)
        
        Returns:
            Decision object
        """
        profile = profile or self.current_profile
        intent = command.get("intent", "")
        target = command.get("target", "")
        loc = command.get("loc", "")
        
        # الحصول على السياسة
        policy = self.policies.get(intent)
        
        if not policy:
            # intent غير معروف - نسمح بحذر
            return Decision(
                allowed=True,
                reason="Unknown intent, proceeding with caution",
                risk_level=RiskLevel.MEDIUM,
                warnings=["Intent not in policy database"]
            )
        
        warnings = []
        
        # ═══════════════════════════════════════════════════════════
        # فحص المسار
        # ═══════════════════════════════════════════════════════════
        
        # بناء المسار الكامل للفحص
        full_path = self._resolve_path(target, loc)
        
        # 🆕 فحص أمني شامل (Path Traversal + Wildcards)
        path_checker = get_path_checker()
        security_result = path_checker.check_path(full_path)
        
        if not security_result.safe:
            # تسجيل التهديد
            audit_logger = get_audit_logger()
            audit_logger.log_threat(security_result.threat_type, full_path, True)
            
            return Decision(
                allowed=False,
                reason=security_result.message,
                risk_level=RiskLevel.CRITICAL
            )
        
        # فحص المسارات المحظورة دائماً
        if self._is_blocked_path(full_path):
            return Decision(
                allowed=False,
                reason=f"🚫 مسار محمي: {full_path}",
                risk_level=RiskLevel.CRITICAL
            )
        
        # فحص المسارات المحظورة في السياسة
        for blocked in policy.blocked_paths:
            if re.match(blocked, full_path, re.IGNORECASE):
                return Decision(
                    allowed=False,
                    reason=f"Path blocked by policy: {blocked}",
                    risk_level=RiskLevel.HIGH
                )
        
        # ═══════════════════════════════════════════════════════════
        # فحص الـ Profile
        # ═══════════════════════════════════════════════════════════
        
        if profile not in policy.allowed_profiles:
            return Decision(
                allowed=False,
                reason=f"🔒 غير مسموح في وضع {profile}",
                risk_level=policy.risk
            )
        
        # ═══════════════════════════════════════════════════════════
        # تحديد إذا يحتاج تأكيد
        # ═══════════════════════════════════════════════════════════
        
        require_confirm = policy.requires_confirmation
        force_dry_run = False
        
        # Safe mode يفرض تأكيد على كل شيء
        if profile == "safe":
            require_confirm = True
            if policy.risk >= RiskLevel.MEDIUM:
                force_dry_run = True
        
        # Silent mode لا يحتاج تأكيد
        if profile == "silent":
            require_confirm = False
        
        # تحذيرات إضافية
        if policy.risk >= RiskLevel.HIGH:
            warnings.append(f"⚠️ عملية عالية الخطورة: {intent}")
        
        return Decision(
            allowed=True,
            reason="✅ مسموح",
            require_confirm=require_confirm,
            force_dry_run=force_dry_run,
            risk_level=policy.risk,
            warnings=warnings
        )
    
    def _is_blocked_path(self, path: str) -> bool:
        """فحص إذا كان المسار محظور"""
        for pattern in self.ALWAYS_BLOCKED_PATHS:
            if re.match(pattern, path, re.IGNORECASE):
                return True
        return False
    
    def _resolve_path(self, target: str, loc: str) -> str:
        """تحويل الهدف والموقع لمسار"""
        if not target:
            return ""
        
        # إذا كان مسار كامل
        if os.path.isabs(target):
            return target
        
        # المواقع المعروفة
        locations = {
            "desktop": os.path.expanduser("~/Desktop"),
            "downloads": os.path.expanduser("~/Downloads"),
            "documents": os.path.expanduser("~/Documents"),
        }
        
        base = locations.get(loc, loc)
        
        # OneDrive
        onedrive_desktop = os.path.expanduser("~/OneDrive/سطح المكتب")
        if loc == "desktop" and os.path.exists(onedrive_desktop):
            base = onedrive_desktop
        
        return os.path.join(base, target) if base else target
    
    # ═══════════════════════════════════════════════════════════
    # إدارة السياسات
    # ═══════════════════════════════════════════════════════════
    
    def set_profile(self, profile: str):
        """تغيير الـ profile"""
        if profile in ["safe", "power", "silent"]:
            self.current_profile = profile
    
    def add_policy(self, policy: Policy):
        """إضافة سياسة جديدة"""
        self.policies[policy.intent] = policy
    
    def get_policy(self, intent: str) -> Optional[Policy]:
        """الحصول على سياسة"""
        return self.policies.get(intent)
    
    def get_all_policies(self) -> Dict[str, Policy]:
        """الحصول على كل السياسات"""
        return self.policies.copy()
    
    # ═══════════════════════════════════════════════════════════
    # تنسيق للعرض
    # ═══════════════════════════════════════════════════════════
    
    def format_decision(self, decision: Decision) -> str:
        """تنسيق القرار للعرض"""
        if decision.allowed:
            status = "✅ مسموح"
        else:
            status = "❌ محظور"
        
        lines = [f"{status}: {decision.reason}"]
        
        if decision.require_confirm:
            lines.append("⚠️ يتطلب تأكيد المستخدم")
        
        if decision.force_dry_run:
            lines.append("🔍 سيتم محاكاة التنفيذ أولاً")
        
        for warning in decision.warnings:
            lines.append(warning)
        
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════════════════

_policy_engine: Optional[PolicyEngine] = None

def get_policy_engine() -> PolicyEngine:
    global _policy_engine
    if _policy_engine is None:
        _policy_engine = PolicyEngine()
    return _policy_engine
