"""
🧠 Learning Engine - محرك التعلم
================================
Jarvis يتعلم من تصحيحاتك.

بدل يسأل نفس السؤال كل مرة:
1. يحفظ إجابتك كـ Pattern
2. يستخدمها المرة الجاية
3. يزيد الثقة مع كل تأكيد
"""

import os
import json
import sqlite3
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path


@dataclass
class LearningPattern:
    """نمط مُتعلم من تصحيح المستخدم"""
    pattern_id: str                    # UUID
    intent: str                        # create_file, watch, etc
    missing_fields: List[str]          # ["location", "name"]
    resolution: Dict[str, Any]         # {"location": "desktop"}
    confidence: float = 0.5            # 0.0 → 1.0
    usage_count: int = 0               # عدد مرات الاستخدام
    last_used: str = ""                # timestamp
    source: str = "user_confirmation"  # مصدر التعلم
    context: Dict = field(default_factory=dict)  # سياق إضافي


@dataclass 
class LearningResult:
    """نتيجة البحث في الأنماط"""
    found: bool
    pattern: Optional[LearningPattern] = None
    suggestion: Dict = field(default_factory=dict)
    confidence: float = 0.0


@dataclass
class GraphFixPattern:
    """نمط إصلاح الـ Graph"""
    fix_id: str
    rule_name: str                     # اسم القاعدة التي كُسرت
    trigger_action: str                # الفعل المسبب (write_text)
    fix_action: str                    # الفعل المصحح (inject_create_file)
    confidence_boost: float = 0.15     # زيادة الثقة عند تطبيقه
    usage_count: int = 0
    created_at: str = ""


# ═══════════════════════════════════════════════════════════
# 🗄️ Pattern Storage (SQLite)
# ═══════════════════════════════════════════════════════════

class PatternStorage:
    """تخزين الأنماط في SQLite"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            base_dir = Path(__file__).parent.parent / "data"
            base_dir.mkdir(exist_ok=True)
            db_path = str(base_dir / "learning.db")
        
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """إنشاء جدول الأنماط"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patterns (
                pattern_id TEXT PRIMARY KEY,
                intent TEXT NOT NULL,
                missing_fields TEXT,
                resolution TEXT,
                confidence REAL DEFAULT 0.5,
                usage_count INTEGER DEFAULT 0,
                last_used TEXT,
                source TEXT DEFAULT 'user_confirmation',
                context TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Index للبحث السريع
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_intent 
            ON patterns(intent)
        """)
        
        # 🆕 جدول إصلاحات الـ Graph
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS graph_fixes (
                fix_id TEXT PRIMARY KEY,
                rule_name TEXT NOT NULL,
                trigger_action TEXT NOT NULL,
                fix_action TEXT NOT NULL,
                confidence_boost REAL DEFAULT 0.15,
                usage_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save(self, pattern: LearningPattern):
        """حفظ نمط"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO patterns 
            (pattern_id, intent, missing_fields, resolution, 
             confidence, usage_count, last_used, source, context)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pattern.pattern_id,
            pattern.intent,
            json.dumps(pattern.missing_fields),
            json.dumps(pattern.resolution),
            pattern.confidence,
            pattern.usage_count,
            pattern.last_used,
            pattern.source,
            json.dumps(pattern.context)
        ))
        
        conn.commit()
        conn.close()
    
    def find(self, intent: str, missing_fields: List[str]) -> Optional[LearningPattern]:
        """البحث عن نمط مطابق"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # البحث بالـ intent والحقول الناقصة
        missing_key = json.dumps(sorted(missing_fields))
        
        cursor.execute("""
            SELECT pattern_id, intent, missing_fields, resolution,
                   confidence, usage_count, last_used, source, context
            FROM patterns
            WHERE intent = ? AND missing_fields = ?
            ORDER BY confidence DESC, usage_count DESC
            LIMIT 1
        """, (intent, missing_key))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return LearningPattern(
                pattern_id=row[0],
                intent=row[1],
                missing_fields=json.loads(row[2]),
                resolution=json.loads(row[3]),
                confidence=row[4],
                usage_count=row[5],
                last_used=row[6] or "",
                source=row[7],
                context=json.loads(row[8]) if row[8] else {}
            )
        return None
    
    def increment_usage(self, pattern_id: str, boost_confidence: float = 0.05):
        """زيادة الاستخدام والثقة"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE patterns 
            SET usage_count = usage_count + 1,
                confidence = MIN(1.0, confidence + ?),
                last_used = ?
            WHERE pattern_id = ?
        """, (boost_confidence, datetime.now().isoformat(), pattern_id))
        
        conn.commit()
        conn.close()
    
    def get_all(self, intent: str = None) -> List[LearningPattern]:
        """جلب كل الأنماط"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if intent:
            cursor.execute("""
                SELECT pattern_id, intent, missing_fields, resolution,
                       confidence, usage_count, last_used, source, context
                FROM patterns WHERE intent = ?
                ORDER BY confidence DESC
            """, (intent,))
        else:
            cursor.execute("""
                SELECT pattern_id, intent, missing_fields, resolution,
                       confidence, usage_count, last_used, source, context
                FROM patterns ORDER BY last_used DESC
            """)
        
        patterns = []
        for row in cursor.fetchall():
            patterns.append(LearningPattern(
                pattern_id=row[0],
                intent=row[1],
                missing_fields=json.loads(row[2]),
                resolution=json.loads(row[3]),
                confidence=row[4],
                usage_count=row[5],
                last_used=row[6] or "",
                source=row[7],
                context=json.loads(row[8]) if row[8] else {}
            ))
        
        conn.close()
        return patterns

    # ═══════════════════════════════════════════════════════════
    # 🔧 Graph Fix Methods
    # ═══════════════════════════════════════════════════════════

    def save_graph_fix(self, fix: GraphFixPattern):
        """حفظ إصلاح Graph"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO graph_fixes 
            (fix_id, rule_name, trigger_action, fix_action, 
             confidence_boost, usage_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            fix.fix_id,
            fix.rule_name,
            fix.trigger_action,
            fix.fix_action,
            fix.confidence_boost,
            fix.usage_count,
            fix.created_at
        ))
        
        conn.commit()
        conn.close()

    def get_graph_fixes(self, rule_name: str = None) -> List[GraphFixPattern]:
        """جلب إصلاحات الـ Graph"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if rule_name:
            cursor.execute("""
                SELECT fix_id, rule_name, trigger_action, fix_action, 
                       confidence_boost, usage_count, created_at
                FROM graph_fixes WHERE rule_name = ?
            """, (rule_name,))
        else:
            cursor.execute("""
                SELECT fix_id, rule_name, trigger_action, fix_action, 
                       confidence_boost, usage_count, created_at
                FROM graph_fixes
            """)
        
        fixes = []
        for row in cursor.fetchall():
            fixes.append(GraphFixPattern(
                fix_id=row[0],
                rule_name=row[1],
                trigger_action=row[2],
                fix_action=row[3],
                confidence_boost=row[4],
                usage_count=row[5],
                created_at=row[6]
            ))
        
        conn.close()
        return fixes


# ═══════════════════════════════════════════════════════════
# 🧠 Learning Engine
# ═══════════════════════════════════════════════════════════

class LearningEngine:
    """
    محرك التعلم - يتعلم من تصحيحات المستخدم.
    
    Flow:
    1. سؤال → إجابة المستخدم
    2. learn() → حفظ Pattern
    3. المرة الجاية → recall() → تطبيق تلقائي
    """
    
    def __init__(self, storage: PatternStorage = None):
        self.storage = storage or PatternStorage()
        self._pending_questions: Dict[str, Dict] = {}  # للأسئلة المعلقة
    
    # ═══════════════════════════════════════════════════════════
    # التعلم من إجابة المستخدم
    # ═══════════════════════════════════════════════════════════
    
    def learn(self, 
              intent: str, 
              missing_fields: List[str], 
              user_resolution: Dict[str, Any],
              context: Dict = None) -> LearningPattern:
        """
        تعلم من إجابة المستخدم.
        
        Args:
            intent: مثل "create_file"
            missing_fields: الحقول الناقصة ["location"]
            user_resolution: إجابة المستخدم {"location": "desktop"}
            context: سياق إضافي
        
        Returns:
            النمط المُتعلم
        """
        import uuid
        
        # إنشاء pattern جديد
        pattern = LearningPattern(
            pattern_id=str(uuid.uuid4())[:8],
            intent=intent,
            missing_fields=sorted(missing_fields),
            resolution=user_resolution,
            confidence=0.6,  # ثقة أولية
            usage_count=1,
            last_used=datetime.now().isoformat(),
            source="user_confirmation",
            context=context or {}
        )
        
        # حفظ
        self.storage.save(pattern)
        
        return pattern
    
    # ═══════════════════════════════════════════════════════════
    # استرجاع Pattern سابق
    # ═══════════════════════════════════════════════════════════
    
    def recall(self, intent: str, missing_fields: List[str]) -> LearningResult:
        """
        البحث عن نمط مُتعلم سابقاً.
        
        Returns:
            LearningResult مع suggestion إذا وُجد
        """
        pattern = self.storage.find(intent, missing_fields)
        
        if pattern:
            return LearningResult(
                found=True,
                pattern=pattern,
                suggestion=pattern.resolution,
                confidence=pattern.confidence
            )
        
        return LearningResult(found=False)
    
    # ═══════════════════════════════════════════════════════════
    # تأكيد الاستخدام (يزيد الثقة)
    # ═══════════════════════════════════════════════════════════
    
    def confirm_usage(self, pattern_id: str):
        """
        تأكيد أن الـ Pattern استُخدم بنجاح.
        يزيد الثقة بـ 5%.
        """
        self.storage.increment_usage(pattern_id, boost_confidence=0.05)
    
    # ═══════════════════════════════════════════════════════════
    # تكامل مع Decision Engine
    # ═══════════════════════════════════════════════════════════
    
    def apply_to_command(self, command: Dict) -> Dict:
        """
        تطبيق التعلم على أمر.
        
        يُكمل الحقول الناقصة من الأنماط المُتعلمة.
        
        Returns:
            الأمر مع الحقول المُكملة + معلومات التعلم
        """
        intent = command.get("intent", "")
        
        # جمع الحقول الناقصة
        missing = []
        for field in ["target", "loc", "destination"]:
            value = command.get(field)
            if not value or value in ["", None, "?"]:
                missing.append(field)
        
        if not missing:
            return command
        
        # البحث عن pattern
        result = self.recall(intent, missing)
        
        if result.found and result.confidence >= 0.5:
            # تطبيق الـ resolution
            enhanced = command.copy()
            for field, value in result.suggestion.items():
                if field in missing:
                    enhanced[field] = value
                    enhanced[f"_learned_{field}"] = True
            
            enhanced["_learning_pattern"] = result.pattern.pattern_id
            enhanced["_learning_confidence"] = result.confidence
            
            return enhanced
        
        return command
    
    # ═══════════════════════════════════════════════════════════
    # تسجيل سؤال معلق
    # ═══════════════════════════════════════════════════════════
    
    def register_question(self, cmd_id: str, intent: str, missing_fields: List[str]):
        """تسجيل سؤال للتعلم لاحقاً"""
        self._pending_questions[cmd_id] = {
            "intent": intent,
            "missing_fields": missing_fields,
            "asked_at": datetime.now().isoformat()
        }
    
    def resolve_question(self, cmd_id: str, user_answer: Dict) -> Optional[LearningPattern]:
        """حل السؤال والتعلم منه"""
        if cmd_id not in self._pending_questions:
            return None
        
        question = self._pending_questions.pop(cmd_id)
        
        return self.learn(
            intent=question["intent"],
            missing_fields=question["missing_fields"],
            user_resolution=user_answer
        )
    
    # ═══════════════════════════════════════════════════════════
    # إحصائيات
    # ═══════════════════════════════════════════════════════════
    
    def get_stats(self) -> Dict:
        """إحصائيات التعلم"""
        all_patterns = self.storage.get_all()
        
        return {
            "total_patterns": len(all_patterns),
            "high_confidence": len([p for p in all_patterns if p.confidence >= 0.75]),
            "total_usages": sum(p.usage_count for p in all_patterns),
            "intents": list(set(p.intent for p in all_patterns))
        }
    
    def format_stats(self) -> str:
        """تنسيق الإحصائيات للعرض"""
        stats = self.get_stats()
        return f"""📊 Learning Stats:
   📝 Patterns: {stats['total_patterns']}
   ✅ High Confidence: {stats['high_confidence']}
   🔄 Total Usages: {stats['total_usages']}
   📋 Intents: {', '.join(stats['intents']) or 'None'}"""

    # ═══════════════════════════════════════════════════════════
    # 🔧 Graph Fix Learning
    # ═══════════════════════════════════════════════════════════

    def learn_graph_fix(self, rule: str, trigger: str, fix: str):
        """تعلم إصلاح للـ Graph"""
        import uuid
        pattern = GraphFixPattern(
            fix_id=str(uuid.uuid4())[:8],
            rule_name=rule,
            trigger_action=trigger,
            fix_action=fix,
            created_at=datetime.now().isoformat()
        )
        self.storage.save_graph_fix(pattern)
        return pattern

    def get_graph_fixes(self, rule: str = None) -> List[GraphFixPattern]:
        """جلب أنماط الإصلاح"""
        return self.storage.get_graph_fixes(rule)


# ═══════════════════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════════════════

_learning_engine: Optional[LearningEngine] = None

def get_learning_engine() -> LearningEngine:
    global _learning_engine
    if _learning_engine is None:
        _learning_engine = LearningEngine()
    return _learning_engine
