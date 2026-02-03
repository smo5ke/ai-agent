from .open_app import OpenAppAction
from .web import WebAction
from .watch_fs import FileSystemManager


# ننشئ نسخ (Instances) جاهزة للاستخدام
opener = OpenAppAction()
web_ops = WebAction()
fs_manager = FileSystemManager()