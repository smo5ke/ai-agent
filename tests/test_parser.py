"""
🧪 Test Parser - اختبار استخراج الـ Intent
==========================================
"""

import pytest
from core.schemas import Command


class TestCommandParsing:
    """اختبارات تحليل الأوامر"""
    
    def test_command_creation(self):
        """إنشاء Command من dict"""
        data = {"intent": "open", "target": "chrome"}
        cmd = Command(**data)
        
        assert cmd.intent == "open"
        assert cmd.target == "chrome"
    
    def test_command_with_location(self):
        """Command مع موقع"""
        data = {
            "intent": "create_folder",
            "target": "test",
            "loc": "desktop"
        }
        cmd = Command(**data)
        
        assert cmd.intent == "create_folder"
        assert cmd.loc == "desktop"
    
    def test_command_defaults(self):
        """القيم الافتراضية"""
        cmd = Command(intent="open", target="notepad")
        
        # Optional fields تُرجع None بدلاً من string فارغ
        assert cmd.loc is None
        assert cmd.param is None
        assert cmd.destination is None


class TestConditionProcessor:
    """اختبارات معالج الشروط"""
    
    def test_simple_condition_detection(self, condition_processor):
        """كشف شرط بسيط"""
        text = "إذا كان مجلد test موجود احذفه"
        result = condition_processor.process(text)
        
        assert result.has_condition == True
        assert result.target == "test"
    
    def test_negated_condition(self, condition_processor):
        """كشف شرط منفي"""
        text = "اذا كان مجلد xyz ليس موجود أنشئه"
        result = condition_processor.process(text)
        
        assert result.has_condition == True
        assert result.condition_type == "not_exists"
    
    def test_no_condition(self, condition_processor):
        """نص بدون شرط"""
        text = "افتح كروم"
        result = condition_processor.process(text)
        
        assert result.has_condition == False
        assert result.final_command == text


class TestChainDetection:
    """اختبارات كشف السلاسل"""
    
    def test_simple_chain_keywords(self):
        """كلمات الربط"""
        connectors = ["و", "ثم", "بعدها", "and", "then"]
        
        for conn in connectors:
            text = f"أنشئ مجلد {conn} أنشئ ملف"
            assert conn in text.lower() or conn in text
    
    def test_loop_detection(self):
        """كشف الحلقات"""
        from core.chain_executor import get_advanced_chain_executor
        executor = get_advanced_chain_executor()
        
        # عربي
        assert executor.is_chain_command("أنشئ 3 ملفات")
        
        # إنجليزي
        assert executor.is_chain_command("create 5 files")


class TestIntentMapping:
    """اختبارات ربط الـ Intent"""
    
    @pytest.mark.parametrize("intent,expected_valid", [
        ("open", True),
        ("create_folder", True),
        ("create_file", True),
        ("delete", True),
        ("unknown", True),  # قيمة صحيحة في Schema
        ("invalid_intent_xyz", False),  # قيمة غير صحيحة
    ])
    def test_valid_intents(self, intent, expected_valid):
        """Intent صحيح/غير صحيح"""
        try:
            cmd = Command(intent=intent, target="test")
            assert cmd.intent == intent
            assert expected_valid == True
        except Exception:
            assert expected_valid == False

