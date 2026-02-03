class BaseAction:
    """
    هذا هو الكلاس الأساسي لكل الأدوات.
    """
    def run(self, *args, **kwargs):
        raise NotImplementedError("يجب على كل أداة تنفيذ دالة run الخاصة بها!")