# core/execution_graph.py
"""
⚡ Execution Graph - منفذ الخطوات
يدعم file_ops و system_ops مع Rollback
"""
from actions.file_ops import ACTION_CLASSES as FILE_ACTIONS
from actions.system_ops import ACTION_CLASSES as SYSTEM_ACTIONS


# دمج كل الـ Actions
ALL_ACTIONS = {**FILE_ACTIONS, **SYSTEM_ACTIONS}


class ExecutionGraph:
    def __init__(self, plan, ctx):
        self.plan = plan
        self.ctx = ctx
        self.history = []

    def run(self):
        print("🚀 Starting Execution...")
        
        try:
            for step in self.plan.steps:
                action = self._create_action(step)
                action.execute()
                self.history.append(action)
                self.ctx.log_event(f"Executed: {step.action}")

            print("✅ All steps completed successfully.")
            return True

        except Exception as e:
            print(f"❌ Error occurred: {e}")
            print("🔄 Initiating Rollback...")
            self.rollback_all()
            return False

    def _create_action(self, step):
        """Factory: يحول الخطوة إلى كلاس مناسب"""
        
        action_class = ALL_ACTIONS.get(step.action)
        if not action_class:
            raise ValueError(f"Unknown action: {step.action}")
        
        # تحويل الـ params حسب نوع الـ action
        if step.action == "create_folder":
            return action_class(self.ctx, step.params["name"])
        elif step.action == "create_file":
            return action_class(self.ctx, step.params["name"])
        elif step.action == "write_text":
            return action_class(self.ctx, step.params["file"], step.params["text"])
        elif step.action == "open_app":
            return action_class(self.ctx, step.params.get("app", step.params.get("app_name", "")))
        
        raise ValueError(f"No handler for action: {step.action}")

    def rollback_all(self):
        """التراجع عن كل العمليات بالترتيب العكسي"""
        print(f"⏪ Rolling back {len(self.history)} operations...")
        
        for action in reversed(self.history):
            try:
                action.rollback()
            except Exception as e:
                print(f"⚠️ Rollback failed for {action}: {e}")
        
        self.history.clear()
        print("🔄 Rollback complete.")
