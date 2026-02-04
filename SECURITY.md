# 🛡️ Jarvis Security Threat Model

> تحليل أمني شامل للنظام - Attack Surface Map + Mitigations
> 
> **Status**: ✅ Security Hardening Implemented
> 
> **New File**: `guard/security.py`
> - PathSecurityChecker (Traversal + Wildcards)
> - InputSanitizer (Prompt Injection)
> - RateLimiter
> - AuditLogger

---

## 📊 Attack Surface Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      USER INPUT                                   │
│  ┌──────────────────┐     ┌──────────────────┐                  │
│  │  Text Commands   │     │  Voice Commands  │                  │
│  └────────┬─────────┘     └────────┬─────────┘                  │
│           │                         │                            │
│           └──────────┬──────────────┘                            │
│                      ▼                                           │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    🧠 LLM LAYER                              │ │
│  │  • Prompt Injection      • JSON Tampering                   │ │
│  │  • Partial Hallucination • Hidden Commands                  │ │
│  └────────────────────────────┬────────────────────────────────┘ │
│                               ▼                                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              🔒 PLANNING & VALIDATION                        │ │
│  │  • Schema Bypass         • Freeze Tampering                 │ │
│  │  • Intent Spoofing                                          │ │
│  └────────────────────────────┬────────────────────────────────┘ │
│                               ▼                                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │               🛡️ POLICY ENGINE                               │ │
│  │  • Policy Bypass         • Profile Switch Attack            │ │
│  │  • Path Traversal                                           │ │
│  └────────────────────────────┬────────────────────────────────┘ │
│                               ▼                                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              ⚙️ EXECUTION LAYER                              │ │
│  │  • Race Conditions       • TOCTOU Bugs                      │ │
│  │  • Infinite Loops        • Resource Exhaustion              │ │
│  └────────────────────────────┬────────────────────────────────┘ │
│                               ▼                                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │               ↩️ ROLLBACK ENGINE                             │ │
│  │  • Rollback Abuse        • Trash Overflow                   │ │
│  │  • Restore Tampering                                        │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧠 1. LLM Layer Threats

| Threat | Severity | Description | Mitigation | Status |
|--------|----------|-------------|------------|--------|
| **Prompt Injection** | 🔴 HIGH | المستخدم يحقن تعليمات تغير سلوك الـ LLM | Schema validation + Freeze Plan | ✅ |
| **JSON Tampering** | 🔴 HIGH | الـ LLM يضيف أوامر مخفية | Plan Validator + Whitelist Intents | ✅ |
| **Partial Hallucination** | 🟠 MEDIUM | الـ LLM يخترع targets غير موجودة | Path validation before execution | ⚠️ |
| **Intent Spoofing** | 🟠 MEDIUM | الـ LLM يُرجع intent مموه | Literal Intent validation | ✅ |
| **Hidden Commands** | 🔴 HIGH | أوامر مخفية في chain | Plan Review + Step-by-step display | ✅ |

### الحماية المُنفذة:
```python
# 1. Schema Validation with Pydantic Literal
intent: Literal['open', 'delete', 'create_folder', ...]  # ✅

# 2. Plan Freezing (Immutable)
plan.frozen_hash = sha256(plan_json)  # ✅

# 3. Integrity Check
if plan.compute_hash() != plan.frozen_hash:
    raise TamperedPlanError  # ✅
```

### مطلوب:
- [ ] إضافة path existence validation قبل التنفيذ
- [ ] Rate limiting على الـ LLM calls

---

## ⚙️ 2. Execution Layer Threats

| Threat | Severity | Description | Mitigation | Status |
|--------|----------|-------------|------------|--------|
| **Race Condition** | 🟠 MEDIUM | تنفيذ متزامن يفسد الملفات | Single-threaded execution | ✅ |
| **TOCTOU Bug** | 🔴 HIGH | الملف يتغير بين Check و Execution | Atomic operations + Lock | ⚠️ |
| **Infinite Loop** | 🔴 HIGH | chain بدون نهاية | `MAX_CHAIN_ITERATIONS = 50` | ✅ |
| **Resource Exhaustion** | 🟠 MEDIUM | إنشاء آلاف الملفات | Chain limit + Warning | ✅ |
| **Node Failure Cascade** | 🟠 MEDIUM | فشل node يفسد النظام | Rollback on failure | ✅ |

### الحماية المُنفذة:
```python
# 1. Chain Limit
MAX_CHAIN_ITERATIONS = 50  # ✅

# 2. Execution State Tracking
state_machine.transition(cmd_id, ExecutionState.NODE_RUNNING)  # ✅

# 3. Auto Rollback
if not graph_result.success:
    rollback_engine.rollback(cmd_id)  # ✅
```

### مطلوب:
- [ ] File locking mechanism
- [ ] Timeout per node execution

---

## 🛡️ 3. Policy Engine Threats

| Threat | Severity | Description | Mitigation | Status |
|--------|----------|-------------|------------|--------|
| **Policy Bypass** | 🔴 CRITICAL | تجاوز فحص الحماية | Centralized evaluation | ✅ |
| **Profile Switch Attack** | 🟠 MEDIUM | التبديل لـ silent mode | Profile change logging | ⚠️ |
| **Path Traversal** | 🔴 HIGH | `../../../Windows/System32` | Absolute path normalization | ⚠️ |
| **Wildcard Abuse** | 🟠 MEDIUM | `delete *.*` | Wildcard pattern block | ⚠️ |

### الحماية المُنفذة:
```python
# 1. Blocked Paths
BLOCKED_PATHS = [
    "C:\\Windows",
    "C:\\Windows\\System32",
    "C:\\Program Files",
    ...
]  # ✅

# 2. Central Policy Evaluation
decision = policy_engine.evaluate(command)
if not decision.allowed:
    return BLOCKED  # ✅
```

### مطلوب:
- [ ] Path traversal detection (`..` sequences)
- [ ] Wildcard pattern detection
- [ ] Profile change audit log

---

## 🧩 4. IPC (Inter-Process Communication) Threats

| Threat | Severity | Description | Mitigation | Status |
|--------|----------|-------------|------------|--------|
| **LLM Process Crash** | 🟠 MEDIUM | الـ worker يموت | Crash Recovery + Retry | ✅ |
| **Fake Response Injection** | 🔴 HIGH | رد مزور من process | Process signature validation | ❌ |
| **Message Queue Overflow** | 🟡 LOW | رسائل كثيرة تفيض | Queue size limit | ⚠️ |
| **Timeout Bypass** | 🟠 MEDIUM | العملية لا تنتهي | Timeout enforcement | ⚠️ |

### الحماية المُنفذة:
```python
# 1. Crash Recovery
crash_recovery.register(process)
crash_recovery.auto_restart()  # ✅

# 2. Process Monitoring
llm_monitor.check_health()  # ✅
```

### مطلوب:
- [ ] Response signature/checksum
- [ ] Strict timeout enforcement
- [ ] Queue size limits

---

## ↩️ 5. Rollback Engine Threats

| Threat | Severity | Description | Mitigation | Status |
|--------|----------|-------------|------------|--------|
| **Rollback Abuse** | 🟠 MEDIUM | Rollback متكرر يفسد الحالة | Rollback count limit | ⚠️ |
| **Trash Overflow** | 🟡 LOW | سلة المحذوفات تمتلئ | Auto-cleanup policy | ⚠️ |
| **Restore Tampering** | 🔴 HIGH | استعادة ملف معدّل | Restore integrity check | ⚠️ |
| **Partial Rollback** | 🟠 MEDIUM | فشل بعد rollback جزئي | Transaction-like behavior | ⚠️ |

### الحماية المُنفذة:
```python
# 1. Trash System
rollback_engine.move_to_trash(file_path, cmd_id)  # ✅

# 2. Rollback Registry
rollback_engine.register(cmd_id, node_id, intent)  # ✅
```

### مطلوب:
- [ ] Trash auto-cleanup (7 days)
- [ ] Restore file checksum
- [ ] Transaction wrapper

---

## 📋 Threat Summary Matrix

| Category | Total | Critical | High | Medium | Low | Mitigated |
|----------|-------|----------|------|--------|-----|-----------|
| LLM | 5 | 0 | 3 | 2 | 0 | 4/5 |
| Execution | 5 | 0 | 2 | 3 | 0 | 4/5 |
| Policy | 4 | 1 | 2 | 1 | 0 | 2/4 |
| IPC | 4 | 0 | 1 | 2 | 1 | 2/4 |
| Rollback | 4 | 0 | 1 | 2 | 1 | 2/4 |
| **Total** | **22** | **1** | **9** | **10** | **2** | **14/22** |

---

## 🚀 Priority Fixes Required

### 🔴 Critical (Must Fix)
1. **Path Traversal Detection** - منع `../` sequences
2. **Wildcard Pattern Block** - منع `*.*` patterns

### 🟠 High Priority
3. **File Locking** - قفل الملفات أثناء التنفيذ
4. **Node Timeout** - timeout لكل node
5. **Profile Change Audit** - تسجيل تغيير الأوضاع

### 🟡 Medium Priority
6. **Trash Auto-Cleanup** - تنظيف تلقائي
7. **Queue Size Limits** - حد لرسائل IPC
8. **Restore Checksum** - التحقق عند الاستعادة

---

## ✅ Security Checklist

- [x] Schema validation (Pydantic)
- [x] Plan freezing (SHA256)
- [x] Integrity verification
- [x] Blocked paths list
- [x] Rollback mechanism
- [x] Crash recovery
- [x] State machine tracking
- [ ] Path traversal detection
- [ ] Wildcard blocking
- [ ] File locking
- [ ] Timeout enforcement
- [ ] Audit logging

---

## 🔒 Recommended Security Mode

للـ production، يُنصح بـ:

```python
# config.py
SECURITY_MODE = "paranoid"

# في هذا الوضع:
# - كل أمر يحتاج تأكيد
# - لا يُسمح بـ delete أبداً
# - Dry-run إجباري
# - Full audit log
```

---

> **Last Updated**: 2026-02-04
> **Review Status**: Initial Assessment
> **Next Review**: After implementing priority fixes
