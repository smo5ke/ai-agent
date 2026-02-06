# core/execution_plan.py
class ExecutionStep:
    def __init__(self, action, params):
        self.action = action
        self.params = params


class ExecutionPlan:
    def __init__(self, steps):
        self.steps = steps
