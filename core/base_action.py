# core/base_action.py
from abc import ABC, abstractmethod

class BaseAction(ABC):
    def __init__(self, context):
        self.context = context
        self.backup_data = None  # لحفظ الحالة قبل التغيير

    @abstractmethod
    def execute(self):
        pass

    @abstractmethod
    def rollback(self):
        pass
