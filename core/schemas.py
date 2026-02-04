from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any

class Command(BaseModel):
    # تحديد النوايا المسموحة
    intent: Literal[
        'open', 'open_file', 'clean', 'watch', 'stop_watch', 
        'macro', 'schedule', 'reminder', 'unknown',
        # عمليات الملفات الجديدة
        'create_folder', 'create_file', 'write_file', 
        'delete', 'rename', 'copy', 'move'
    ]
    
    # حقول أوامر النظام
    target: Optional[str] = None
    
    # حقول المراقبة والتنظيف
    loc: Optional[str] = None
    filter_key: Optional[str] = Field(None, alias="filter")
    destination: Optional[str] = Field(None, alias="dest")
    action_type: Optional[str] = Field(None, alias="act")
    
    # حقول الماكرو
    cmd: Optional[str] = None
    param: Optional[str] = None
    
    # حقل إيقاف المراقبة
    watch_id: Optional[str] = None
    
    # حقول الجدولة
    time: Optional[str] = None      # وقت التنفيذ HH:MM
    delay: Optional[str] = None     # تأخير مثل 5m, 10s
    repeat: Optional[str] = None    # once, daily, hourly
    
    # 🆕 الأمر المركب (on_change)
    on_change: Optional[Dict[str, Any]] = None  # {"intent": "create_folder", "target": "تجربة"}