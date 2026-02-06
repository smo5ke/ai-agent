# guard/policy.py

FORBIDDEN = ["..", "/", "\\"]

ALLOWED_ACTIONS = {
    "create_folder",
    "create_file",
    "write_text",
    "run_python_code",
    "save_memory",
    "search_memory",
    "open_app"
}


def enforce(plan):
    """يفحص الخطة لمنع أي تصرف خطير"""
    
    for step in plan.steps:
        # فحص الـ action
        if step.action not in ALLOWED_ACTIONS:
            raise Exception(f"Action not allowed: {step.action}")
        
    return True
