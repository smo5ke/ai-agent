from pydantic import BaseModel, Field
from typing import Optional, Literal

class Command(BaseModel):
    # تحديد النوايا المسموحة
    intent: Literal['open', 'clean', 'watch', 'macro', 'unknown']
    
    # حقول أوامر النظام
    target: Optional[str] = None
    
    # حقول المراقبة والتنظيف (لاحظ الأسماء تطابق JSON الموديل)
    loc: Optional[str] = None        # للمراقبة (Location)
    filter_key: Optional[str] = Field(None, alias="filter") # الموديل يرسل "filter" ونحن نسميه filter_key
    destination: Optional[str] = Field(None, alias="dest")  # الموديل يرسل "dest"
    action_type: Optional[str] = Field(None, alias="act")   # الموديل يرسل "act" (alert/move)
    
    # حقول الماكرو (الحقول التي كانت ناقصة وسببت الخطأ)
    cmd: Optional[str] = None       # مثل web_search
    param: Optional[str] = None     # مثل نص البحث