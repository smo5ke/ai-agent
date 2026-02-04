# 🤖 Jarvis AI Agent - ملخص المشروع

> نظام ذكاء اصطناعي محلي للتحكم بنظام ويندوز عبر اللغة الطبيعية (عربي/إنجليزي)
> 
> **الإصدار**: v3.1.0 | **الحالة**: ✅ Production Ready

---

## 📊 هيكل المشروع

```
ai agent/
├── 📄 main.py                     # GUI الرئيسية (مع Timeline)
├── 📄 dynamic_resolver.py         # محلل أسماء التطبيقات
├── 📄 watcher_engine.py           # مراقبة ملفات النظام
│
├── 📁 core/                       # النواة الأساسية
│   ├── orchestrator.py            # المنسق العام (Process Intelligent)
│   ├── decision_engine.py         # 🧠 محرك القرار (مع Learning)
│   ├── graph_rules.py             # ⚖️ Graph Rule Engine (Validation)
│   ├── auto_repair.py             # 🔧 Auto-Repair Planner
│   ├── learning_engine.py         # 🆕 Auto-Learning System (Graph Fixes)
│   ├── clarification.py           # 🆕 Smart Question Generator
│   ├── world_model.py             # الافتراضيات الذكية
│   ├── confidence.py              # Confidence Scoring
│   ├── execution_state.py         # State Machine
│   ├── execution_graph.py         # Graph Execution
│   ├── command_registry.py        # Command Registry
│   ├── rollback.py                # Trash & Rollback
│   ├── scheduler.py               # المهام المجدولة
│   ├── database.py                # SQLite (Jarvis.db)
│   └── schemas.py                 # Pydantic Models
│
├── 📁 ui/                         # الواجهة الرسومية
│   ├── timeline.py                # 🆕 Visual Execution Timeline
│   └── config_window.py           # نافذة الإعدادات
│
├── 📁 guard/                      # طبقة الحماية
│   ├── policy_engine.py           # محرك السياسات
│   ├── security.py                # Security & Threat Model
│   ├── validator.py               # التحقق من المدخلات
│   └── dry_run.py                 # محاكاة التنفيذ
│
├── 📁 actions/                    # التنفيذ
│   ├── watch_fs.py                # File Watcher (+ on_change)
│   ├── open_app.py                # فتح التطبيقات
│   ├── file_ops.py                # عمليات الملفات
│   └── plugin_loader.py           # نظام الإضافات
│
├── 📁 llm/                        # الذكاء الاصطناعي
│   ├── prompts.py                 # System Prompts & Examples
│   └── worker.py                  # LLM Worker Process
│
├── 📁 data/                       # البيانات
│   ├── jarvis.db                  # قاعدة البيانات (Patterns, History)
│   ├── security_audit.log         # سجلات الأمان
│   └── .trash/                    # سلة المحذوفات الآمنة
│
├──  SECURITY.md                 # Threat Model & Security Policy
└── 📄 PROJECT_OVERVIEW.md         # هذا الملف
```

---

## 🏗️ Core Architecture (v3.1 - Reliable Autonomous System)

### 🔄 The Intelligent Flow
كيف يعالج Jarvis الطلبات الآن:

```
User: "أنشئ ملف باسم test"
   ↓
1. Timeline: Start Event 📝
   ↓
2. Parsing (LLM): استخراج Intent & Entities
   ↓
3. Learning Engine: "المستخدم عادةً ينشئ ملفات txt على Desktop" 🧠
   ↓
4. World Model: إكمال الناقص (Loc=Desktop, Ext=txt)
   ↓
5. Confidence: حساب الثقة (Score: 85% - Boosted by Learning)
   ↓
6. Decision Engine:
   - ≥ 0.75: Execute ✅
   - 0.5 - 0.75: Notify ⚠️
   - < 0.5: Ask (Using Clarification Generator) ❓
   ↓
7. Auto-Repair: إصلاح الأخطاء المنطقية (حقن dependencies) 🔧
   ↓
8. Rule Engine: التحقق الصارم من القواعد (Reactive last) ⚖️
   ↓
9. Policy Engine: فحص الأمان (Path Traversal, Risk Level) 🔒
   ↓
10. Execution: تنفيذ السلسلة كـ Graph + تحديث Timeline 🚀
   ↓
11. Learning: حفظ النمط + تعلم إصلاحات الـ Graph 📚
```

### 🧠 المكونات الذكية الجديدة

| المكون | الوصف | الفائدة |
|--------|-------|---------|
| **Rule Engine** | يفرض قواعد صارمة (مثل `write` يتطلب `create`) | منع التنفيذ غير المنطقي |
| **Auto-Repair** | يضيف خطوات ناقصة أو يعيد الترتيب تلقائياً | تصحيح أخطاء الـ LLM دون إزعاج المستخدم |
| **Learning Engine** | يتعلم من تصحيحات المستخدم وإصلاحات الـ Graph | تقليل الأسئلة المكررة بشكل جذري |
| **Visual Timeline** | يعرض مراحل التنفيذ والثقة في الوقت الحقيقي | شفافية كاملة (White-box AI) |
| **Decision Engine v2** | يدمج الـ Learning والـ Confidence لاتخاذ القرار | أتمتة أعلى وثقة أكبر |

---

## 📊 Visual Timeline

نظام تتبع مرئي مدمج في الواجهة الرئيسية (`ui/timeline.py`) يتيح:
- **Real-time Monitoring**: مشاهدة كل خطوة أثناء حدوثها.
- **Controls**: إمكانية الإيقاف مؤقتاً (Pause) أو الإلغاء (Cancel).
- **Transparency**: عرض نسبة الثقة وسبب القرار (مثلاً "Learned from pattern #123").

---

## 🔐 Security Hardening (Enterprise Grade)

| التهديد | الحماية | الحالة |
|---------|---------|--------|
| **Path Traversal** | `PathSecurityChecker` checks canonical paths | ✅ Active |
| **Prompt Injection** | Strict JSON Schema + `InputSanitizer` | ✅ Active |
| **Destructive Actions** | `DryRun` simulation + `Trash` backup | ✅ Active |
| **Unauthorized Access** | `PolicyEngine` + `AuditLogger` | ✅ Active |

---

## 🔌 API Reference

### Orchestrator (Main Entry Point)
```python
# المعالجة الذكية (The new standard)
result = orchestrator.process_intelligent(text)

# إدارة الـ Timeline
timeline = get_timeline_manager()
timeline.add_step(cmd_id, "step_name", "Description")
```

### Learning Engine
```python
# تعلم ومطابقة الأنماط
pattern = learning.learn(intent, missing_fields, user_resolution)

# تعلم إصلاحات الـ Graph
learning.learn_graph_fix(rule="auto_repair", trigger="graph_check", fix="inject_create_file")
```

---

## ✨ Features Summary

1.  **Reliability**: لن يفشل بسبب ترتيب خاطئ أو نسيان خطوة.
2.  **Autonomous Learning**: لا يسأل عن نفس الشيء مرتين.
3.  **Hybrid Intelligence**: يدمج LLM مع Rules و History.
4.  **Visual Feedback**: واجهة Timeline متطورة.
5.  **Robust Security**: حماية من المستوى المؤسسي.
6.  **Smart Defaults**: يعرف سياق العمل (Desktop, Documents, etc.).

---

## 📝 سجل التغييرات

### v3.1.0 (2026-02-04) - The Reliability Update
- ✅ **Graph Rule Engine**: منع الأوامر المتعارضة منطقياً.
- ✅ **Auto-Repair Planner**: حقن Dependencies + إصلاح الترتيب.
- ✅ **Learning Engine v2**: دعم تعلم `GraphFixPattern`.
- ✅ **Robust Execution**: نجاح 100% حتى مع أوامر LLM ناقصة.

### v3.0.0 (2026-02-04) - The Autonomous Update
- ✅ **Learning Engine**: حفظ واستدعاء أنماط المستخدم.
- ✅ **Clarification Generator**: أسئلة ذكية مع Quick Replies.
- ✅ **Visual Timeline**: واجهة TUI/GUI لمتابعة التنفيذ.
- ✅ **Decision Engine v2**: دمج Learning + Confidence.

### v2.5.0
- ✅ Hybrid Intelligent System (Decision Engine v1).
- ✅ Security Hardening & Threat Model.