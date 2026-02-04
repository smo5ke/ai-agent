"""
🧪 Test Policy Engine - اختبار محرك السياسات
============================================
"""

import pytest


class TestPolicyDecisions:
    """اختبارات قرارات السياسات"""
    
    def test_open_allowed(self, policy_engine):
        """فتح التطبيقات مسموح"""
        cmd = {"intent": "open", "target": "chrome"}
        decision = policy_engine.evaluate(cmd)
        
        assert decision.allowed == True
        assert decision.require_confirm == False
    
    def test_delete_needs_confirm(self, policy_engine):
        """الحذف يحتاج تأكيد"""
        policy_engine.set_profile("safe")
        cmd = {"intent": "delete", "target": "test.txt", "loc": "desktop"}
        decision = policy_engine.evaluate(cmd)
        
        # في Safe mode، الحذف غير مسموح
        assert decision.allowed == False or decision.require_confirm == True


class TestBlockedPaths:
    """اختبارات المسارات المحظورة"""
    
    def test_system32_blocked(self, policy_engine):
        """System32 محظور"""
        cmd = {
            "intent": "delete",
            "target": "important.dll",
            "loc": "C:\\Windows\\System32"
        }
        decision = policy_engine.evaluate(cmd)
        
        assert decision.allowed == False
        assert "محمي" in decision.reason or "blocked" in decision.reason.lower()
    
    def test_windows_folder_blocked(self, policy_engine):
        """مجلد Windows محظور"""
        cmd = {
            "intent": "create_file",
            "target": "test.txt", 
            "loc": "C:\\Windows"
        }
        decision = policy_engine.evaluate(cmd)
        
        assert decision.allowed == False
    
    def test_desktop_allowed(self, policy_engine):
        """سطح المكتب مسموح"""
        cmd = {
            "intent": "create_folder",
            "target": "test",
            "loc": "desktop"
        }
        decision = policy_engine.evaluate(cmd)
        
        assert decision.allowed == True


class TestProfiles:
    """اختبارات الأوضاع"""
    
    def test_safe_mode_strict(self, policy_engine):
        """وضع Safe صارم"""
        policy_engine.set_profile("safe")
        
        cmd = {"intent": "delete", "target": "test"}
        decision = policy_engine.evaluate(cmd)
        
        # Safe mode لا يسمح بالحذف
        assert decision.allowed == False
    
    def test_power_mode_flexible(self, policy_engine):
        """وضع Power مرن"""
        policy_engine.set_profile("power")
        
        cmd = {"intent": "create_folder", "target": "test", "loc": "desktop"}
        decision = policy_engine.evaluate(cmd)
        
        assert decision.allowed == True
        assert decision.require_confirm == False
    
    def test_silent_mode_no_confirm(self, policy_engine):
        """وضع Silent بدون تأكيد"""
        policy_engine.set_profile("silent")
        
        cmd = {"intent": "delete", "target": "test.txt", "loc": "desktop"}
        decision = policy_engine.evaluate(cmd)
        
        # Silent يسمح بكل شيء بدون تأكيد (ما عدا المسارات المحظورة)
        if decision.allowed:
            assert decision.require_confirm == False


class TestRiskLevels:
    """اختبارات مستويات الخطر"""
    
    def test_open_low_risk(self, policy_engine):
        """فتح = خطر منخفض"""
        from guard.policy_engine import RiskLevel
        
        policy = policy_engine.get_policy("open")
        assert policy.risk == RiskLevel.LOW
    
    def test_delete_high_risk(self, policy_engine):
        """حذف = خطر عالي"""
        from guard.policy_engine import RiskLevel
        
        policy = policy_engine.get_policy("delete")
        assert policy.risk == RiskLevel.HIGH
