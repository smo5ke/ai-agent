# core/orchestrator.py
"""
🎼 Orchestrator v5.0 - المنسق الرئيسي
يدعم: LLM، تنفيذ، ذاكرة، أحداث، كود، GUI
"""
from typing import Optional
from dataclasses import dataclass
from core.execution_context import ExecutionContext
from core.execution_plan import ExecutionPlan, ExecutionStep
from core.execution_graph import ExecutionGraph
from core.decision_engine import validate
from core.memory_manager import get_memory
from core.event_bus import get_event_bus, Event
from guard.policy import enforce
from sandbox.python_executor import get_executor
from sandbox.python_executor import get_executor
from tools.search_tool import WebSearch
from actions.smart_browser import SmartBrowser


@dataclass
class ProcessResult:
    """نتيجة المعالجة"""
    success: bool
    message: str
    steps_count: int = 0


class Orchestrator:
    def __init__(self, context: ExecutionContext, planner=None):
        self.context = context
        self.planner = planner
        self.memory = get_memory()
        self.event_bus = get_event_bus()
        self.executor = get_executor()
        self.search_tool = WebSearch()
        self.browser = SmartBrowser()
        self._event_listening = False
        self._messages = []

    def _log(self, msg: str):
        """تسجيل رسالة"""
        self._messages.append(msg)
        print(msg)

    def _get_plan(self, text: str) -> dict:
        """جلب الخطة من الـ LLM"""
        memory_context = self.memory.get_context_for_llm(text)
        
        if self.planner:
            return self.planner.plan(text, memory_context)
        else:
            from llm.llama_runner import plan_mock
            return plan_mock(text)

    def process(self, text: str, mode: str = "user") -> ProcessResult:
        # ... (logging code omitted for brevity)
        self._messages = []
        self._log(f"📝 معالجة: {text}")

        # ... (memory and planning omitted)
        memory_context = self.memory.get_context_for_llm(text)
        try:
            raw = self._get_plan(text)
        except Exception as e:
            return ProcessResult(False, f"فشل التخطيط: {e}")

        if not raw.get("steps"):
            return ProcessResult(True, "لا يوجد إجراءات مطلوبة")

        # 3. تحويل JSON → ExecutionPlan (مع تصحيح المسارات)
        from core.system_paths import SystemPaths
        sys_paths = SystemPaths()
        
        steps = []
        special_results = []
        
        for s in raw["steps"]:
            # معالجة خاصة للأدوات
            if s["action"] in ["create_folder", "create_file", "write_text", "delete_folder", "delete_file"]:
                # تصحيح المسار (Desktop -> OneDrive/Desktop)
                raw_path = s["params"].get("name") or s["params"].get("file") or s["params"].get("path")
                if raw_path:
                    fixed_path = sys_paths.resolve_path(raw_path)
                    # تحديث الباراميترات وتوحيد المفاتيح
                    s["params"]["name"] = fixed_path  # Ensure 'name' exists for Validator/Actions
                    
                    if "file" in s["params"]: s["params"]["file"] = fixed_path
                    if "path" in s["params"]: s["params"]["path"] = fixed_path
                    
                    self._log(f"🔄 Path Resolved: {raw_path} -> {fixed_path}")

            if s["action"] == "run_python_code":
                result = self.run_python_code(s["params"]["code"])
                special_results.append(f"🐍 نتيجة Python: {result}")
                continue
            elif s["action"] == "save_memory":
                self.save_to_memory(s["params"]["fact"])
                special_results.append("💾 تم الحفظ في الذاكرة")
                continue
            elif s["action"] == "search_memory":
                results = self.search_memory(s["params"]["query"])
                special_results.append(f"🔍 نتائج البحث: {results}")
                continue
            elif s["action"] == "open_app":
                from actions.app_launcher import AppLauncher
                launcher = AppLauncher()
                app_name = s["params"].get("app") or s["params"].get("app_name") or s["params"].get("path")
                msg = launcher.open(app_name)
                special_results.append(msg)
                continue
            elif s["action"] == "search_web":
                msg = self.search_tool.search(query=s["params"]["query"])
                special_results.append(f"🌍 Search Results:\n{msg}")
                continue
            elif s["action"] == "open_url":
                url = s["params"].get("url")
                msg = self.browser.open_url(url)
                special_results.append(msg)
                continue
            elif s["action"] == "see_screen":
                from core.vision_engine import VisionEngine
                vision = VisionEngine()
                msg = vision.see_screen()
                special_results.append(f"👁️ Screen Content:\n{msg}")
                continue
            elif s["action"] == "open_program":
                from actions.app_launcher import AppLauncher
                launcher = AppLauncher()
                msg = launcher.open_program(s["params"]["name"])
                special_results.append(msg)
                continue
            
            steps.append(ExecutionStep(s["action"], s["params"]))
        
        # ... (rest of function)
        
        if not steps and special_results:
            msg = "تم تنفيذ الأوامر الخاصة:\n" + "\n".join(special_results)
            return ProcessResult(True, msg)
        
        plan = ExecutionPlan(steps)
        
        # 4. التحقق المنطقي
        try:
            validate(plan)
            self._log("✅ التحقق المنطقي نجح")
        except Exception as e:
            return ProcessResult(False, f"فشل التحقق: {e}")
        
        # 5. الفحص الأمني
        try:
            enforce(plan)
            self._log("✅ الفحص الأمني نجح")
        except Exception as e:
            return ProcessResult(False, f"فشل الأمان: {e}")
        
        # 6. التنفيذ
        graph = ExecutionGraph(plan, self.context)
        success = graph.run()
        
        # 7. تسجيل في الذاكرة
        self.memory.log_action(
            action=f"process_{mode}",
            details={"input": text[:50], "success": success}
        )
        
        # 8. حفظ الذاكرة
        self.context.save_memory()
        
        # 9. بناء الرسالة النهائية
        if success:
            msg_parts = ["✅ تم التنفيذ بنجاح!"]
            msg_parts.append(f"📁 المسار: {self.context.cwd}")
            if special_results:
                msg_parts.extend(special_results)
            message = "\n".join(msg_parts)
        else:
            message = "❌ فشل التنفيذ وتم التراجع"
        
        return ProcessResult(success, message, len(steps))

    # ===== أدوات للـ LLM =====
    
    def run_python_code(self, code: str) -> str:
        self._log("🐍 تنفيذ كود Python...")
        result = self.executor.execute(code)
        return result.stdout.strip() if result.success else f"خطأ: {result.stderr}"

    def save_to_memory(self, fact: str):
        self.memory.store(fact)
        self._log(f"💾 تم حفظ: {fact}")

    def search_memory(self, query: str) -> list[str]:
        return self.memory.retrieve(query)

    # ===== Event Loop =====
    
    def start_event_listener(self):
        if self._event_listening:
            return
        
        def on_event(event: Event):
            if self._should_respond_to_event(event):
                message = f"ملف {event.event_type}: {event.path}"
                self.process(message, mode="event")
        
        self.event_bus.set_callback(on_event)
        self.event_bus.start()
        self._event_listening = True

    def stop_event_listener(self):
        self.event_bus.stop()
        self._event_listening = False

    def _should_respond_to_event(self, event: Event) -> bool:
        ignore = ['.tmp', '.swp', '.pyc', '__pycache__', 'memory_dump.json', 'knowledge_base.json']
        return not any(p in event.path.lower() for p in ignore)


# للتوافق
def process(text: str):
    ctx = ExecutionContext(base_path=".")
    orchestrator = Orchestrator(ctx)
    return orchestrator.process(text)
