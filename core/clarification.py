"""
💬 Clarification Generator - مولد الأسئلة الذكية
==============================================
بدل أسئلة كثيرة، سؤال واحد ذكي مع اقتراح.

مثال:
❌ قبل: "وين؟" "شو الاسم؟" "بأي صيغة؟"
✅ بعد: "بدك أنشئ ملف notes.txt على سطح المكتب؟"
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class Clarification:
    """سؤال/اقتراح للمستخدم"""
    question: str                      # السؤال أو الاقتراح
    suggestions: Dict[str, str]        # الاقتراحات
    missing_fields: List[str]          # الحقول الناقصة
    quick_responses: List[str]         # ردود سريعة
    confidence: float                  # ثقة الاقتراح
    
    @property
    def is_confirmation(self) -> bool:
        """هل هذا تأكيد (اقتراح كامل)؟"""
        return self.confidence >= 0.6
    
    @property
    def is_question(self) -> bool:
        """هل هذا سؤال (احتياج معلومات)؟"""
        return self.confidence < 0.6


# ═══════════════════════════════════════════════════════════
# 📝 Intent Templates
# ═══════════════════════════════════════════════════════════

# قوالب الأسئلة والاقتراحات لكل intent
INTENT_TEMPLATES = {
    "create_folder": {
        "confirmation": "بدك أنشئ مجلد \"{target}\" في {loc}؟",
        "question_target": "شو اسم المجلد؟",
        "question_loc": "وين بدك أنشئ المجلد؟",
        "question_both": "شو اسم المجلد ووين؟",
        "default_target": "مجلد_جديد",
        "default_loc": "سطح المكتب"
    },
    "create_file": {
        "confirmation": "بدك أنشئ ملف \"{target}\" في {loc}؟",
        "question_target": "شو اسم الملف؟",
        "question_loc": "وين بدك أنشئ الملف؟",
        "question_both": "شو اسم الملف ووين؟",
        "default_target": "ملف_جديد.txt",
        "default_loc": "سطح المكتب"
    },
    "delete": {
        "confirmation": "متأكد تحذف \"{target}\" من {loc}؟",
        "question_target": "شو بدك تحذف؟",
        "default_target": "",
        "default_loc": "سطح المكتب"
    },
    "watch": {
        "confirmation": "بدك راقب {loc}؟",
        "question_loc": "أي مجلد بدك راقب؟",
        "default_loc": "التنزيلات"
    },
    "open": {
        "confirmation": "بدي افتح {target}؟",
        "question_target": "شو بدك افتح؟",
        "default_target": ""
    }
}

# الردود السريعة
QUICK_RESPONSES = {
    "confirm": ["نفّذ", "تمام", "أي", "ماشي", "yes", "ok"],
    "cancel": ["لا", "إلغاء", "وقف", "no", "cancel"],
    "change_loc": ["غير المكان", "مكان تاني", "في التنزيلات", "في المستندات"],
    "change_name": ["غير الاسم", "اسم تاني"]
}


# ═══════════════════════════════════════════════════════════
# 💬 Clarification Generator
# ═══════════════════════════════════════════════════════════

class ClarificationGenerator:
    """
    مولد الأسئلة الذكية.
    
    بدل أسئلة متفرقة، سؤال واحد مع اقتراح.
    """
    
    def __init__(self):
        self.templates = INTENT_TEMPLATES.copy()
        self.quick_responses = QUICK_RESPONSES.copy()
    
    def generate(self, 
                 intent: str, 
                 missing_fields: List[str],
                 suggestions: Dict[str, str] = None,
                 context: Dict = None) -> Clarification:
        """
        توليد سؤال/اقتراح ذكي.
        
        Args:
            intent: نوع الأمر
            missing_fields: الحقول الناقصة
            suggestions: اقتراحات من World Model
            context: سياق إضافي
        
        Returns:
            Clarification object
        """
        suggestions = suggestions or {}
        context = context or {}
        template = self.templates.get(intent, {})
        
        # ملء الاقتراحات من الـ defaults
        filled_suggestions = self._fill_suggestions(
            intent, missing_fields, suggestions, template
        )
        
        # حساب الثقة
        confidence = self._calculate_confidence(missing_fields, filled_suggestions)
        
        # بناء السؤال
        if confidence >= 0.6:
            # اقتراح للتأكيد
            question = self._build_confirmation(intent, filled_suggestions, template)
            quick = ["نفّذ", "غير الاسم", "غير المكان", "لا"]
        else:
            # سؤال مباشر
            question = self._build_question(intent, missing_fields, template)
            quick = ["سطح المكتب", "التنزيلات", "المستندات"]
        
        return Clarification(
            question=question,
            suggestions=filled_suggestions,
            missing_fields=missing_fields,
            quick_responses=quick,
            confidence=confidence
        )
    
    def _fill_suggestions(self, 
                          intent: str, 
                          missing: List[str],
                          provided: Dict,
                          template: Dict) -> Dict:
        """ملء الاقتراحات الناقصة"""
        result = provided.copy()
        
        for field in missing:
            if field not in result:
                default_key = f"default_{field}"
                if default_key in template:
                    result[field] = template[default_key]
        
        return result
    
    def _calculate_confidence(self, missing: List[str], suggestions: Dict) -> float:
        """حساب ثقة الاقتراح"""
        if not missing:
            return 1.0
        
        filled = sum(1 for f in missing if suggestions.get(f))
        return filled / len(missing) if missing else 1.0
    
    def _build_confirmation(self, intent: str, suggestions: Dict, template: Dict) -> str:
        """بناء جملة تأكيد"""
        pattern = template.get("confirmation", "تنفيذ {intent}؟")
        
        try:
            return pattern.format(
                target=suggestions.get("target", ""),
                loc=self._humanize_loc(suggestions.get("loc", "")),
                dest=suggestions.get("destination", "")
            )
        except:
            return f"تنفيذ {intent}؟"
    
    def _build_question(self, intent: str, missing: List[str], template: Dict) -> str:
        """بناء سؤال مباشر"""
        if len(missing) >= 2 and "question_both" in template:
            return template["question_both"]
        
        if "target" in missing and "question_target" in template:
            return template["question_target"]
        
        if "loc" in missing and "question_loc" in template:
            return template["question_loc"]
        
        return "ممكن توضحلي أكتر؟"
    
    def _humanize_loc(self, loc: str) -> str:
        """تحويل location لنص مقروء"""
        mapping = {
            "desktop": "سطح المكتب",
            "downloads": "التنزيلات",
            "documents": "المستندات",
            "pictures": "الصور"
        }
        return mapping.get(loc.lower() if loc else "", loc)
    
    # ═══════════════════════════════════════════════════════════
    # تحليل رد المستخدم
    # ═══════════════════════════════════════════════════════════
    
    def parse_response(self, 
                       response: str, 
                       clarification: Clarification) -> Tuple[str, Dict]:
        """
        تحليل رد المستخدم.
        
        Returns:
            (action, updates)
            action: "confirm" | "cancel" | "update" | "unknown"
            updates: dict مع القيم الجديدة
        """
        response_lower = response.lower().strip()
        
        # تأكيد
        if response_lower in self.quick_responses["confirm"]:
            return ("confirm", clarification.suggestions)
        
        # إلغاء
        if response_lower in self.quick_responses["cancel"]:
            return ("cancel", {})
        
        # تغيير المكان
        for loc_phrase in ["في التنزيلات", "التنزيلات", "downloads"]:
            if loc_phrase in response_lower:
                return ("update", {"loc": "downloads"})
        
        for loc_phrase in ["في المستندات", "المستندات", "documents"]:
            if loc_phrase in response_lower:
                return ("update", {"loc": "documents"})
        
        for loc_phrase in ["سطح المكتب", "المكتب", "desktop"]:
            if loc_phrase in response_lower:
                return ("update", {"loc": "desktop"})
        
        # اسم محدد (إذا قصير ولا يحتوي فعل)
        if len(response.split()) <= 2 and not any(
            word in response_lower for word in ["انشئ", "احذف", "افتح", "غير"]
        ):
            if "target" in clarification.missing_fields:
                return ("update", {"target": response.strip()})
        
        return ("unknown", {"raw": response})
    
    # ═══════════════════════════════════════════════════════════
    # تنسيق للعرض
    # ═══════════════════════════════════════════════════════════
    
    def format_for_ui(self, clarification: Clarification) -> str:
        """تنسيق للعرض في UI"""
        if clarification.is_confirmation:
            return f"💡 {clarification.question}\n   [نفّذ] [غير] [لا]"
        else:
            return f"❓ {clarification.question}"


# ═══════════════════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════════════════

_clarification_generator: Optional[ClarificationGenerator] = None

def get_clarification_generator() -> ClarificationGenerator:
    global _clarification_generator
    if _clarification_generator is None:
        _clarification_generator = ClarificationGenerator()
    return _clarification_generator
