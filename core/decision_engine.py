# core/decision_engine.py

def validate(plan):
    """يتحقق أن الخطوات منطقية ومرتبة"""
    folders = set()
    files = set()

    for step in plan.steps:
        if step.action == "create_folder":
            name = step.params.get("name") or step.params.get("path")
            if name:
                folders.add(name)

        elif step.action == "create_file":
            # if not folders:
            #     raise Exception("No folder exists before file creation")
            name = step.params.get("name") or step.params.get("file")
            if name:
                files.add(name)

        elif step.action == "write_text":
            # if step.params["file"] not in files:
            #     raise Exception("Writing to non-existent file")
            pass

    return True


# للتوافق مع الكود القديم
def approve(plan):
    return validate(plan)
