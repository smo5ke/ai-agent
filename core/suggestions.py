"""
💡 Smart Suggestions - اقتراحات ذكية
=====================================
نظام اقتراحات ذكي يعتمد على:
- الوقت الحالي (صباح، ظهر، مساء)
- سجل الاستخدام (الأكثر استخداماً)
- أنماط السلوك (ماذا يفعل المستخدم عادة في هذا الوقت)
"""

import os
from datetime import datetime
from typing import List, Dict, Optional
from core import database as db


class SmartSuggestions:
    """نظام الاقتراحات الذكية"""
    
    def __init__(self):
        # اقتراحات ثابتة حسب الوقت
        self.time_based_suggestions = {
            "morning": [  # 6:00 - 11:59
                {"text": "افتح Outlook", "icon": "📧", "reason": "تفقد الإيميل الصباحي"},
                {"text": "افتح Teams", "icon": "💼", "reason": "اجتماعات العمل"},
                {"text": "ابحث عن أخبار اليوم", "icon": "📰", "reason": "تابع الأخبار"},
            ],
            "noon": [  # 12:00 - 16:59
                {"text": "افتح يوتيوب", "icon": "🎬", "reason": "استراحة الغداء"},
                {"text": "ذكرني بعد ساعة", "icon": "⏰", "reason": "تذكير بالعودة"},
            ],
            "evening": [  # 17:00 - 21:59
                {"text": "افتح Spotify", "icon": "🎵", "reason": "وقت الاسترخاء"},
                {"text": "افتح Netflix", "icon": "🎬", "reason": "مساء الترفيه"},
                {"text": "افتح تويتر", "icon": "🐦", "reason": "تصفح السوشيال"},
            ],
            "night": [  # 22:00 - 5:59
                {"text": "ذكرني بالنوم بعد 30 دقيقة", "icon": "😴", "reason": "وقت النوم"},
                {"text": "أغلق كل البرامج", "icon": "🌙", "reason": "نهاية اليوم"},
            ]
        }
    
    def get_time_period(self) -> str:
        """تحديد فترة اليوم"""
        hour = datetime.now().hour
        
        if 6 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "noon"
        elif 17 <= hour < 22:
            return "evening"
        else:
            return "night"
    
    def get_time_suggestions(self) -> List[Dict]:
        """جلب اقتراحات حسب الوقت"""
        period = self.get_time_period()
        return self.time_based_suggestions.get(period, [])
    
    def get_frequent_apps(self, limit: int = 3) -> List[Dict]:
        """جلب التطبيقات الأكثر استخداماً"""
        try:
            stats = db.get_top_apps(limit)
            suggestions = []
            
            for app_name, count in stats:
                suggestions.append({
                    "text": f"افتح {app_name}",
                    "icon": "⭐",
                    "reason": f"استخدمته {count} مرة"
                })
            
            return suggestions
        except:
            return []
    
    def get_recent_commands(self, limit: int = 3) -> List[Dict]:
        """جلب الأوامر الأخيرة"""
        try:
            recent = db.get_recent_conversations(limit)
            suggestions = []
            
            for conv in recent:
                user_text = conv.get('user_text', '')
                if user_text and len(user_text) < 50:
                    suggestions.append({
                        "text": user_text,
                        "icon": "🕐",
                        "reason": "أمر سابق"
                    })
            
            return suggestions
        except:
            return []
    
    def get_day_based_suggestions(self) -> List[Dict]:
        """اقتراحات حسب يوم الأسبوع"""
        day = datetime.now().weekday()  # 0=Monday, 6=Sunday
        
        if day in [4, 5]:  # الجمعة والسبت (عطلة)
            return [
                {"text": "افتح Netflix", "icon": "🎬", "reason": "عطلة نهاية الأسبوع"},
                {"text": "افتح YouTube", "icon": "📺", "reason": "وقت الترفيه"},
            ]
        else:
            return [
                {"text": "افتح VS Code", "icon": "💻", "reason": "يوم عمل"},
                {"text": "افتح Slack", "icon": "💬", "reason": "تواصل الفريق"},
            ]
    
    def get_all_suggestions(self, max_total: int = 6) -> List[Dict]:
        """
        جلب كل الاقتراحات مرتبة حسب الأولوية.
        
        Returns:
            قائمة اقتراحات (max_total كحد أقصى)
        """
        all_suggestions = []
        
        # 1. اقتراحات حسب الوقت (الأهم)
        time_sugg = self.get_time_suggestions()[:2]
        all_suggestions.extend(time_sugg)
        
        # 2. التطبيقات الأكثر استخداماً
        freq_sugg = self.get_frequent_apps(2)
        all_suggestions.extend(freq_sugg)
        
        # 3. اقتراحات حسب اليوم
        day_sugg = self.get_day_based_suggestions()[:1]
        all_suggestions.extend(day_sugg)
        
        # إزالة التكرارات
        seen = set()
        unique = []
        for s in all_suggestions:
            if s["text"] not in seen:
                seen.add(s["text"])
                unique.append(s)
        
        return unique[:max_total]
    
    def get_greeting(self) -> str:
        """تحية حسب الوقت"""
        period = self.get_time_period()
        
        greetings = {
            "morning": "☀️ صباح الخير!",
            "noon": "🌤️ مرحباً!",
            "evening": "🌅 مساء الخير!",
            "night": "🌙 مساء النور!"
        }
        
        return greetings.get(period, "مرحباً!")


# Singleton
_suggestions = None

def get_suggestions() -> SmartSuggestions:
    """جلب نظام الاقتراحات"""
    global _suggestions
    if _suggestions is None:
        _suggestions = SmartSuggestions()
    return _suggestions
