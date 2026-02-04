"""
🧪 Test Configuration - إعدادات pytest
======================================
Fixtures مشتركة لكل الاختبارات.
"""

import os
import sys
import shutil
import tempfile
import pytest

# إضافة المشروع للـ path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


# ═══════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════

@pytest.fixture
def sandbox_dir():
    """
    مجلد Sandbox مؤقت للاختبارات.
    
    يُحذف تلقائياً بعد انتهاء الاختبار.
    """
    temp_dir = tempfile.mkdtemp(prefix="jarvis_test_")
    yield temp_dir
    # تنظيف
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def sample_commands():
    """أوامر نموذجية للاختبار"""
    return [
        {"intent": "open", "target": "chrome"},
        {"intent": "create_folder", "target": "test_folder", "loc": "desktop"},
        {"intent": "create_file", "target": "test.txt", "loc": "desktop"},
        {"intent": "delete", "target": "test.txt", "loc": "desktop"},
    ]


@pytest.fixture
def mock_ui_callback():
    """Callback وهمي لتسجيل الرسائل"""
    messages = []
    
    def callback(msg, level="info"):
        messages.append({"msg": msg, "level": level})
    
    callback.messages = messages
    return callback


@pytest.fixture
def command_registry():
    """Command Registry جديد للاختبار"""
    from core.command_registry import CommandRegistry
    return CommandRegistry()


@pytest.fixture
def policy_engine():
    """Policy Engine جديد للاختبار"""
    from guard.policy_engine import PolicyEngine
    return PolicyEngine()


@pytest.fixture
def rollback_engine(sandbox_dir):
    """Rollback Engine يستخدم الـ sandbox"""
    from core.rollback import RollbackEngine
    return RollbackEngine(data_dir=sandbox_dir)


@pytest.fixture  
def condition_processor():
    """Condition Processor للاختبار"""
    from core.condition_processor import ConditionPreprocessor
    return ConditionPreprocessor()
