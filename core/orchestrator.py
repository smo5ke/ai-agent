"""
🎯 Orchestrator - المنسق العام
==============================
يربط بين الواجهة والدماغ والأدوات التنفيذية.

التحديثات:
- دعم open_file لفتح الملفات
- دعم stop_watch لإيقاف المراقبة
- ربط callback تحديث قائمة المراقبة
- 🆕 Core Architecture: Command Registry + Policy Engine + Execution Graph + Rollback
"""

import threading
from core.schemas import Command
from core.permissions import check_permission, SecurityLevel
from core.memory import Memory
from llm.worker import Brain
from llm import monitor as llm_monitor
from actions.plugin_loader import PluginLoader 
from actions import opener, web_ops, fs_manager 

# 🆕 Core Architecture imports
from core.command_registry import get_command_registry, CommandStatus
from core.execution_graph import create_graph, ExecutionGraph
from guard.policy_engine import get_policy_engine
from core.rollback import get_rollback_engine
from core.execution_state import get_execution_state, ExecutionState
from core.execution_plan import get_planning_engine, PlanStatus
from core.decision_engine import get_decision_engine, DecisionAction
from ui.timeline import get_timeline_manager, TimelineStatus
from core.graph_rules import GraphRuleEngine
from core.auto_repair import AutoRepairPlanner
from core.learning_engine import get_learning_engine



class Orchestrator:
    def __init__(self, model_path):
        self.model_path = model_path
        self.brain = Brain(model_path)
        self.memory = Memory()
        self.ui_callback = None 
        self.plugin_manager = PluginLoader()
        self.plugin_manager.load_all()
        self._worker_started = False
        
        # Callback لتحديث قائمة المراقبة في UI
        self.on_watches_changed = None
        
    def start_brain(self):
        """تشغيل الـ LLM Worker + فحص الاتصال."""
        def _start():
            if not llm_monitor.is_worker_alive():
                if self.ui_callback:
                    self.ui_callback("🚀 جاري تشغيل محرك الذكاء الاصطناعي...", "thought")
                
                llm_monitor.start_worker()
                
                if llm_monitor.wait_for_worker(timeout=120):
                    self._worker_started = True
                    if self.ui_callback:
                        self.ui_callback("✅ محرك الذكاء الاصطناعي جاهز!", "success")
                else:
                    if self.ui_callback:
                        self.ui_callback("❌ فشل تشغيل محرك الذكاء الاصطناعي", "error")
                    return
            else:
                self._worker_started = True
                if self.ui_callback:
                    self.ui_callback("✅ محرك الذكاء الاصطناعي متصل", "success")
            
            self.brain.load()
        
        threading.Thread(target=_start, daemon=True).start()

    def set_watches_callback(self, callback):
        """تعيين callback لتحديث UI عند تغير المراقبة"""
        self.on_watches_changed = callback
        fs_manager.on_watches_changed = callback

    def get_active_watches(self):
        """جلب قائمة مهام المراقبة"""
        return fs_manager.get_active_watches()

    def stop_watch_by_id(self, watch_id: str) -> str:
        """إيقاف مهمة مراقبة"""
        result = fs_manager.stop_watch(watch_id)
        if self.ui_callback:
            self.ui_callback(f"🛑 {result}", "warning")
        return result

    def process_request(self, user_text):
        """معالجة طلب المستخدم"""
        if not self.brain.is_ready():
            if self.ui_callback:
                self.ui_callback("⚠️ محرك الذكاء الاصطناعي غير جاهز، جاري إعادة الاتصال...", "warning")
            if llm_monitor.ensure_running():
                pass
            else:
                if self.ui_callback:
                    self.ui_callback("❌ فشل الاتصال. شغّله يدوياً: python llm/worker_process.py", "error")
                return
        
        if self.ui_callback: 
            self.ui_callback("🤔 جاري التحليل...", "thought")

        threading.Thread(target=self._run_logic, args=(user_text,)).start()

    def _run_logic(self, user_text):
        """منطق التفكير والتنفيذ"""
        try:
            # ═══════════════════════════════════════════════════════════
            # معالجة الشروط (قبل الـ LLM)
            # ═══════════════════════════════════════════════════════════
            try:
                from core.condition_processor import get_condition_preprocessor
                preprocessor = get_condition_preprocessor()
                condition_result = preprocessor.process(user_text)
                
                if condition_result.has_condition:
                    # عرض نتيجة الفحص
                    status_msg = preprocessor.get_status_message(condition_result)
                    if self.ui_callback:
                        self.ui_callback(status_msg, "thought")
                    
                    # إذا لم يتحقق الشرط ولا يوجد else
                    if not condition_result.final_command:
                        if self.ui_callback:
                            self.ui_callback("⏭️ الشرط لم يتحقق، لا شيء للتنفيذ", "info")
                        return
                    
                    # استخدام الأمر المُعاد صياغته
                    user_text = condition_result.final_command
                    if self.ui_callback:
                        self.ui_callback(f"📝 الأمر بعد المعالجة: {user_text}", "thought")
            except ImportError:
                pass  # إذا لم يكن الـ preprocessor موجود
            
            # ═══════════════════════════════════════════════════════════
            # كشف التذكيرات يدوياً (قبل الـ LLM)
            # ═══════════════════════════════════════════════════════════
            reminder_command = self._detect_reminder(user_text)
            if reminder_command:
                self.execute(reminder_command)
                return
            
            apps_context = ", ".join(list(opener.apps_index.keys())[:100])
            result = self.brain.think(user_text, apps_context)
            
            # ═══════════════════════════════════════════════════════════
            # التعامل مع قائمة أوامر أو أمر واحد
            # ═══════════════════════════════════════════════════════════
            if isinstance(result, list):
                # قائمة أوامر متسلسلة
                if self.ui_callback:
                    self.ui_callback(f"🔗 تم استخراج {len(result)} أوامر من LLM", "info")
                
                for i, cmd in enumerate(result):
                    try:
                        command = Command(**cmd)
                        if self.ui_callback:
                            self.ui_callback(f"  {i+1}️⃣ {command.intent}: {command.target}", "thought")
                        self.execute(command)
                    except Exception as e:
                        if self.ui_callback:
                            self.ui_callback(f"  ❌ خطأ في الأمر {i+1}: {e}", "error")
                        break
                return
            
            # أمر واحد
            command = result
            self.memory.add_interaction(user_text, command.dict())

            if command.intent == "unknown":
                if self.ui_callback: 
                    self.ui_callback("⚠️ لم أفهم الأمر، حاول صياغته بشكل آخر.", "error")
                return

            security = check_permission(command.intent)
            
            # ═══════════════════════════════════════════════════════════
            # Guard Layer - فحص الأمان
            # ═══════════════════════════════════════════════════════════
            guard_result = self._check_guard(command)
            if not guard_result["allowed"]:
                if self.ui_callback:
                    self.ui_callback(f"🔒 تم رفض الأمر: {guard_result['reason']}", "error")
                return
            
            if guard_result["needs_confirm"]:
                # عرض Dry-Run وطلب تأكيد
                if self.ui_callback:
                    self.ui_callback(f"⚠️ {guard_result['dry_run_result']}", "warning")
                # TODO: انتظار تأكيد المستخدم
                # حالياً: تنفيذ مباشر (سيتم تحسينه)
            
            self.execute(command)
            
        except Exception as e:
            if self.ui_callback:
                self.ui_callback(f"❌ خطأ: {str(e)}", "error")

    def _check_guard(self, command: Command) -> dict:
        """فحص الأمان عبر Guard Layer"""
        try:
            from guard import get_guard
            guard = get_guard()
            return guard.check(command.dict())
        except Exception as e:
            # في حال فشل Guard، السماح بالتنفيذ مع تحذير
            print(f"Guard warning: {e}")
            return {"allowed": True, "needs_confirm": False, "risk_level": "UNKNOWN"}

    def execute(self, command: Command):
        """تنفيذ الأمر"""
        msg = ""
        
        # ═══════════════════════════════════════════════════════════
        # فتح التطبيقات
        # ═══════════════════════════════════════════════════════════
        if command.intent == "open":
            msg = opener.run(command.target)
        
        # ═══════════════════════════════════════════════════════════
        # فتح الملفات (جديد)
        # ═══════════════════════════════════════════════════════════
        elif command.intent == "open_file":
            msg = fs_manager.open_file(
                filename=command.target,
                folder=command.loc or "desktop"
            )
            
        # ═══════════════════════════════════════════════════════════
        # الماكرو (بحث، كتابة)
        # ═══════════════════════════════════════════════════════════
        elif command.intent == "macro":
            if command.cmd == "web_search":
                msg = web_ops.google_search(command.param)
            elif command.cmd == "youtube_search":
                msg = web_ops.youtube_search(command.param)
            elif command.cmd == "write_note":
                msg = web_ops.write_note(command.param)

        # ═══════════════════════════════════════════════════════════
        # تنظيف الملفات
        # ═══════════════════════════════════════════════════════════
        elif command.intent == "clean":
            msg = fs_manager.clean_folder(
                command.target, 
                command.filter_key, 
                command.destination or "Documents"
            )

        # ═══════════════════════════════════════════════════════════
        # المراقبة مع دعم on_change
        # ═══════════════════════════════════════════════════════════
        elif command.intent == "watch":
            # استخراج on_change action إذا موجود
            on_change_action = None
            if hasattr(command, 'on_change') and command.on_change:
                on_change_action = command.on_change
            elif hasattr(command, 'param') and command.param:
                # محاولة استخراج من param (للتراكيب المركبة)
                if isinstance(command.param, dict):
                    on_change_action = command.param
                elif isinstance(command.param, str) and ":" in command.param:
                    # تحليل format مثل "create_folder:تجربة"
                    parts = command.param.split(":")
                    if len(parts) >= 2:
                        on_change_action = {
                            "intent": parts[0],
                            "target": parts[1],
                            "loc": command.loc or "desktop"
                        }
                        
            # إنشاء callback لتنفيذ on_change
            def execute_on_change(action_dict):
                """تنفيذ الأمر عند التغيير"""
                try:
                    # إنشاء Command object وتنفيذه
                    on_change_cmd = Command(**{
                        k: v for k, v in action_dict.items() 
                        if not k.startswith("_")
                    })
                    result = self.execute(on_change_cmd)
                    if self.ui_callback:
                        self.ui_callback(f"✅ {result}", "success")
                except Exception as e:
                    if self.ui_callback:
                        self.ui_callback(f"❌ on_change error: {e}", "error")
            
            msg = fs_manager.start_watch(
                command.loc, 
                command.filter_key, 
                command.action_type, 
                self.ui_callback,
                on_change_action=on_change_action,
                on_change_callback=execute_on_change if on_change_action else None
            )

        # ═══════════════════════════════════════════════════════════
        # إيقاف المراقبة (جديد)
        # ═══════════════════════════════════════════════════════════
        elif command.intent == "stop_watch":
            if command.watch_id:
                msg = fs_manager.stop_watch(command.watch_id)
            else:
                msg = "يرجى تحديد معرف المراقبة (watch_id)"

        # ═══════════════════════════════════════════════════════════
        # جدولة المهام
        # ═══════════════════════════════════════════════════════════
        elif command.intent == "schedule":
            msg = self._handle_schedule(command)
        
        # ═══════════════════════════════════════════════════════════
        # التذكيرات
        # ═══════════════════════════════════════════════════════════
        elif command.intent == "reminder":
            msg = self._handle_reminder(command)

        # ═══════════════════════════════════════════════════════════
        # عمليات الملفات الجديدة
        # ═══════════════════════════════════════════════════════════
        elif command.intent == "create_folder":
            msg = self._handle_file_ops("create_folder", command)
        
        elif command.intent == "create_file":
            msg = self._handle_file_ops("create_file", command)
        
        elif command.intent == "write_file":
            msg = self._handle_file_ops("write_file", command)
        
        elif command.intent == "delete":
            msg = self._handle_file_ops("delete", command)
        
        elif command.intent == "rename":
            msg = self._handle_file_ops("rename", command)
        
        elif command.intent == "copy":
            msg = self._handle_file_ops("copy", command)
        
        elif command.intent == "move":
            msg = self._handle_file_ops("move", command)

        # ═══════════════════════════════════════════════════════════
        # إرسال النتيجة
        # ═══════════════════════════════════════════════════════════
        if self.ui_callback and msg:
            self.ui_callback(f"✅ {msg}", "success")
            self.memory.add_system_event(command.intent, msg)
            
        if not msg:
            msg = self.plugin_manager.run_plugin("chat", command.param or command.intent)
            
        if self.ui_callback and msg:
            self.ui_callback(f"✅ {msg}", "success")

    # ═══════════════════════════════════════════════════════════
    # معالجة الجدولة والتذكيرات
    # ═══════════════════════════════════════════════════════════
    
    def _handle_schedule(self, command: Command) -> str:
        """معالجة أمر الجدولة"""
        from core.scheduler import get_scheduler
        
        scheduler = get_scheduler()
        scheduler.set_executor(self.process_request)
        scheduler.set_ui_callback(self.ui_callback)
        
        # تحديد التأخير أو الوقت
        delay_seconds = self._parse_delay(command.delay) if command.delay else None
        
        task_id = scheduler.add_task(
            command="open" if command.target else command.cmd or "reminder",
            time_str=command.time,
            delay_seconds=delay_seconds,
            repeat=command.repeat or "once",
            command_data={"target": command.target, "param": command.param}
        )
        
        time_info = command.time or command.delay or "قريباً"
        return f"تمت جدولة '{command.target or command.param}' في {time_info} (ID: {task_id})"

    def _handle_reminder(self, command: Command) -> str:
        """معالجة أمر التذكير"""
        from core.scheduler import get_scheduler
        
        scheduler = get_scheduler()
        scheduler.set_ui_callback(self.ui_callback)
        
        # تحليل التأخير
        delay_seconds = self._parse_delay(command.delay) if command.delay else 60
        message = command.param or "تذكير!"
        
        task_id = scheduler.add_reminder(message, delay_seconds)
        
        return f"سأذكرك بـ '{message}' بعد {delay_seconds // 60} دقيقة (ID: {task_id})"

    def _parse_delay(self, delay_str: str) -> int:
        """تحويل نص التأخير إلى ثواني"""
        import re
        
        if not delay_str:
            return 60
        
        # 5m, 10s, 1h
        patterns = [
            (r'(\d+)\s*s', 1),       # ثواني
            (r'(\d+)\s*m', 60),      # دقائق
            (r'(\d+)\s*h', 3600),    # ساعات
        ]
        
        for pattern, multiplier in patterns:
            match = re.search(pattern, delay_str, re.IGNORECASE)
            if match:
                return int(match.group(1)) * multiplier
        
        # محاولة تحويل رقم مباشر (دقائق افتراضياً)
        try:
            return int(delay_str) * 60
        except:
            return 60

    def _handle_file_ops(self, operation: str, command: Command) -> str:
        """معالجة عمليات الملفات"""
        from actions.file_ops import get_file_ops
        
        file_ops = get_file_ops()
        target = command.target or ""
        loc = command.loc or "desktop"
        
        if operation == "create_folder":
            return file_ops.create_folder(target, loc)
        
        elif operation == "create_file":
            content = command.param or ""
            return file_ops.create_file(target, loc, content)
        
        elif operation == "write_file":
            content = command.param or ""
            return file_ops.write_file(target, content, loc)
        
        elif operation == "delete":
            return file_ops.delete(target, loc)
        
        elif operation == "rename":
            new_name = command.param or command.destination or ""
            return file_ops.rename(target, new_name, loc)
        
        elif operation == "copy":
            dest = command.destination or ""
            return file_ops.copy(target, dest, loc)
        
        elif operation == "move":
            dest = command.destination or ""
            return file_ops.move(target, dest, loc)
        
        return f"عملية غير معروفة: {operation}"

    # ═══════════════════════════════════════════════════════════
    # كشف الأوامر المتسلسلة
    # ═══════════════════════════════════════════════════════════
    
    def _detect_chain_command(self, text: str) -> bool:
        """
        كشف وتنفيذ الأوامر المتسلسلة (بدون LLM).
        """
        try:
            from core.chain_executor import get_chain_executor
            
            chain = get_chain_executor()
            
            # هل هذا أمر متسلسل؟
            if not chain.is_chain_command(text):
                return False
            
            if self.ui_callback:
                self.ui_callback("🔗 تم اكتشاف أوامر متسلسلة...", "thought")
            
            # تحليل الأوامر
            commands = chain.parse_chain(text)
            
            if not commands:
                return False
            
            if self.ui_callback:
                self.ui_callback(f"📋 تم استخراج {len(commands)} أوامر", "info")
            
            # تنفيذ السلسلة
            results = chain.execute_chain(commands, self._execute_chain_step)
            
            # عرض النتائج
            result_msg = chain.format_results(results)
            if self.ui_callback:
                self.ui_callback(result_msg, "success")
            
            return True
            
        except Exception as e:
            print(f"Chain error: {e}")
            return False
    
    def _execute_chain_step(self, cmd: dict) -> str:
        """تنفيذ خطوة واحدة من السلسلة"""
        from actions.file_ops import get_file_ops
        
        file_ops = get_file_ops()
        intent = cmd.get("intent")
        target = cmd.get("target", "")
        loc = cmd.get("loc", "desktop")
        param = cmd.get("param", "")
        
        if intent == "create_folder":
            return file_ops.create_folder(target, loc)
        elif intent == "create_file":
            return file_ops.create_file(target, loc, param)
        elif intent == "write_file":
            return file_ops.write_file(target, param, loc)
        elif intent == "delete":
            return file_ops.delete(target, loc)
        else:
            return f"Unknown intent: {intent}"

    # ═══════════════════════════════════════════════════════════
    # كشف التذكيرات يدوياً
    # ═══════════════════════════════════════════════════════════
    
    def _detect_reminder(self, text: str):
        """
        كشف أوامر التذكير من النص مباشرة (بدون LLM).
        يعمل لأن الـ LLM لا يفهم "ذكرني" بشكل صحيح.
        """
        import re
        
        text_lower = text.lower()
        
        # التحقق من وجود كلمات التذكير
        reminder_keywords = ['ذكرني', 'ذكّرني', 'نبهني', 'remind', 'تذكير']
        is_reminder = any(kw in text_lower for kw in reminder_keywords)
        
        if not is_reminder:
            return None
        
        # استخراج التأخير
        delay_seconds = 60  # افتراضي: دقيقة
        
        # أنماط التأخير
        patterns = [
            # بعد X دقيقة/دقائق
            (r'بعد\s*(\d+)\s*دقيق', 60),
            (r'بعد\s*(\d+)\s*دقائق', 60),
            (r'بعد\s*دقيقة', None, 60),
            (r'بعد\s*دقيقتين', None, 120),
            # بعد X ثانية/ثواني
            (r'بعد\s*(\d+)\s*ثاني', 1),
            (r'بعد\s*(\d+)\s*ثواني', 1),
            # بعد X ساعة/ساعات
            (r'بعد\s*(\d+)\s*ساع', 3600),
            (r'بعد\s*ساعة', None, 3600),
            # English patterns
            (r'in\s*(\d+)\s*min', 60),
            (r'in\s*(\d+)\s*sec', 1),
            (r'in\s*(\d+)\s*hour', 3600),
        ]
        
        for pattern_info in patterns:
            if len(pattern_info) == 2:
                pattern, multiplier = pattern_info
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    delay_seconds = int(match.group(1)) * multiplier
                    break
            elif len(pattern_info) == 3:
                pattern, _, fixed_value = pattern_info
                if re.search(pattern, text, re.IGNORECASE):
                    delay_seconds = fixed_value
                    break
        
        # استخراج رسالة التذكير
        # حذف كلمات التوقيت للحصول على الرسالة
        message = text
        remove_patterns = [
            r'ذكرني', r'ذكّرني', r'نبهني', r'remind\s*me',
            r'بعد\s*\d*\s*(دقيقة|دقائق|ثانية|ثواني|ساعة|ساعات)?',
            r'in\s*\d+\s*(minutes?|seconds?|hours?)?',
        ]
        for p in remove_patterns:
            message = re.sub(p, '', message, flags=re.IGNORECASE)
        
        # تنظيف الرسالة
        message = message.strip()
        message = re.sub(r'^[بـ\s]+', '', message)  # حذف "بـ" في البداية
        message = message.strip() or "تذكير!"
        
        # إنشاء Command
        return Command(
            intent="reminder",
            param=message,
            delay=f"{delay_seconds // 60}m" if delay_seconds >= 60 else f"{delay_seconds}s"
        )
    
    # ═══════════════════════════════════════════════════════════
    # 🆕 Core Architecture Methods
    # ═══════════════════════════════════════════════════════════
    
    def process_with_graph(self, user_text: str):
        """
        معالجة الطلب عبر Core Architecture الكامل.
        
        Flow:
        1. تسجيل الأمر → CMD-ID
        2. Policy Engine → قرار
        3. بناء Graph → Nodes
        4. تنفيذ → Rollback عند الحاجة
        """
        registry = get_command_registry()
        policy_engine = get_policy_engine()
        rollback_engine = get_rollback_engine()
        state_machine = get_execution_state()
        
        # 1. تسجيل الأمر + Init State
        cmd_id = registry.register(user_text)
        state_machine.init(cmd_id)
        
        if self.ui_callback:
            self.ui_callback(f"📝 [{cmd_id}] تم تسجيل الأمر", "thought")
        
        try:
            # 2. الحصول على الأمر من LLM
            state_machine.transition(cmd_id, ExecutionState.PARSING, "جاري التحليل بالـ LLM")
            
            apps_context = ", ".join(list(opener.apps_index.keys())[:100])
            result = self.brain.think(user_text, apps_context)
            
            if isinstance(result, list):
                commands = [Command(**cmd) for cmd in result]
            else:
                commands = [result] if result else []
            
            if not commands:
                state_machine.set_error(cmd_id, "No commands parsed")
                registry.update_status(cmd_id, CommandStatus.FAILED, error="No commands parsed")
                return
            
            # 3. فحص السياسات
            state_machine.transition(cmd_id, ExecutionState.POLICY_CHECK, "فحص السياسات")
            
            for cmd in commands:
                decision = policy_engine.evaluate(cmd.dict())
                
                if not decision.allowed:
                    state_machine.transition(cmd_id, ExecutionState.POLICY_BLOCKED, decision.reason)
                    registry.update_status(cmd_id, CommandStatus.FAILED, error=decision.reason)
                    if self.ui_callback:
                        self.ui_callback(f"🚫 [{cmd_id}] {decision.reason}", "error")
                    return
                
                if decision.warnings:
                    for w in decision.warnings:
                        if self.ui_callback:
                            self.ui_callback(w, "warning")
            
            # 4. بناء Graph
            state_machine.transition(cmd_id, ExecutionState.GRAPH_BUILT, f"تم بناء Graph: {len(commands)} nodes")
            state_machine.update_progress(cmd_id, 0, len(commands))
            
            # 5. تنفيذ Graph
            graph_result = self._execute_commands_as_graph(cmd_id, commands, rollback_engine, state_machine)
            
            # 6. تحديث الحالة النهائية
            if graph_result.success:
                state_machine.transition(cmd_id, ExecutionState.COMPLETED, "اكتمل بنجاح")
                registry.update_status(cmd_id, CommandStatus.COMPLETED)
                registry.set_rollback_available(cmd_id, True)
                if self.ui_callback:
                    self.ui_callback(f"✅ [{cmd_id}] اكتمل ({graph_result.nodes_completed} nodes)", "success")
            else:
                state_machine.set_error(cmd_id, graph_result.error or "Unknown error")
                registry.update_status(cmd_id, CommandStatus.FAILED, error=graph_result.error)
                if self.ui_callback:
                    self.ui_callback(f"❌ [{cmd_id}] فشل: {graph_result.error}", "error")
                
                # محاولة Rollback
                if rollback_engine.has_rollback(cmd_id):
                    state_machine.transition(cmd_id, ExecutionState.ROLLING_BACK, "جاري التراجع")
                    rollback_result = rollback_engine.rollback(cmd_id)
                    state_machine.mark_rolled_back(cmd_id)
                    if self.ui_callback:
                        self.ui_callback(f"↩️ Rollback: {rollback_result.rolled_back_count} عمليات", "info")
                
        except Exception as e:
            state_machine.set_error(cmd_id, str(e))
            registry.update_status(cmd_id, CommandStatus.FAILED, error=str(e))
            if self.ui_callback:
                self.ui_callback(f"❌ [{cmd_id}] خطأ: {e}", "error")
    
    def process_with_plan(self, user_text: str) -> dict:
        """
        🔒 معالجة الطلب عبر Deterministic Planning.
        
        Flow:
        1. LLM → Commands
        2. Create Plan
        3. Validate Plan
        4. Freeze Plan (Immutable)
        5. Execute
        
        Anti-Hallucination: الخطة لا تُعدل بعد التجميد.
        """
        registry = get_command_registry()
        policy_engine = get_policy_engine()
        planning_engine = get_planning_engine()
        state_machine = get_execution_state()
        rollback_engine = get_rollback_engine()
        
        # 1. تسجيل الأمر
        cmd_id = registry.register(user_text)
        state_machine.init(cmd_id)
        
        result = {
            "command_id": cmd_id,
            "plan_id": None,
            "status": "pending",
            "message": ""
        }
        
        try:
            # 2. الحصول على الأوامر من LLM
            state_machine.transition(cmd_id, ExecutionState.PARSING, "جاري التحليل بالـ LLM")
            
            apps_context = ", ".join(list(opener.apps_index.keys())[:100])
            llm_result = self.brain.think(user_text, apps_context)
            
            if isinstance(llm_result, list):
                commands = [Command(**cmd) for cmd in llm_result]
            else:
                commands = [llm_result] if llm_result else []
            
            if not commands:
                state_machine.set_error(cmd_id, "No commands parsed")
                result["status"] = "failed"
                result["message"] = "لم يتم استخراج أوامر"
                return result
            
            # 3. إنشاء الخطة
            plan = planning_engine.create_plan(cmd_id, user_text, commands)
            result["plan_id"] = plan.plan_id
            
            if self.ui_callback:
                self.ui_callback(f"📝 [{plan.plan_id}] تم إنشاء الخطة: {len(plan.steps)} خطوات", "thought")
            
            # 4. التحقق من الخطة
            validation = planning_engine.validate_plan(plan)
            
            if not validation.valid:
                state_machine.set_error(cmd_id, f"Validation failed: {validation.errors}")
                result["status"] = "validation_failed"
                result["message"] = f"فشل التحقق: {validation.errors}"
                return result
            
            if validation.warnings:
                for w in validation.warnings:
                    if self.ui_callback:
                        self.ui_callback(f"⚠️ {w}", "warning")
            
            # 5. فحص السياسات
            state_machine.transition(cmd_id, ExecutionState.POLICY_CHECK, "فحص السياسات")
            
            for cmd in commands:
                decision = policy_engine.evaluate(cmd.dict())
                if not decision.allowed:
                    state_machine.transition(cmd_id, ExecutionState.POLICY_BLOCKED, decision.reason)
                    result["status"] = "blocked"
                    result["message"] = decision.reason
                    return result
            
            # 6. تجميد الخطة 🔒
            if not planning_engine.freeze_plan(plan):
                result["status"] = "freeze_failed"
                result["message"] = "فشل تجميد الخطة"
                return result
            
            if self.ui_callback:
                self.ui_callback(f"🔒 [{plan.plan_id}] الخطة مُجمدة: {plan.frozen_hash}", "info")
            
            # 7. تحضير للتنفيذ (يتحقق من Integrity)
            frozen_commands = planning_engine.prepare_for_execution(plan)
            
            if not frozen_commands:
                result["status"] = "integrity_failed"
                result["message"] = "فشل التحقق من سلامة الخطة"
                return result
            
            # 8. تنفيذ Graph
            state_machine.transition(cmd_id, ExecutionState.GRAPH_BUILT, f"تم بناء Graph: {len(frozen_commands)} nodes")
            
            graph_result = self._execute_commands_as_graph(cmd_id, frozen_commands, rollback_engine, state_machine)
            
            # 9. تحديث الحالة
            if graph_result.success:
                state_machine.transition(cmd_id, ExecutionState.COMPLETED, "اكتمل بنجاح")
                planning_engine.mark_completed(plan, success=True)
                registry.update_status(cmd_id, CommandStatus.COMPLETED)
                registry.set_rollback_available(cmd_id, True)
                
                result["status"] = "completed"
                result["message"] = f"✅ اكتمل ({graph_result.nodes_completed} nodes)"
            else:
                planning_engine.mark_completed(plan, success=False)
                state_machine.set_error(cmd_id, graph_result.error or "Unknown error")
                
                result["status"] = "failed"
                result["message"] = graph_result.error
                
                # Rollback
                if rollback_engine.has_rollback(cmd_id):
                    state_machine.transition(cmd_id, ExecutionState.ROLLING_BACK, "جاري التراجع")
                    rollback_engine.rollback(cmd_id)
                    state_machine.mark_rolled_back(cmd_id)
            
            return result
            
        except Exception as e:
            state_machine.set_error(cmd_id, str(e))
            result["status"] = "error"
            result["message"] = str(e)
            return result
    
    def process_intelligent(self, user_text: str) -> dict:
        """
        🤖 Hybrid Intelligent Processing.
        
        Jarvis يتصرف بدل ما يسأل:
        1. LLM → Command (قد يكون ناقص)
        2. World Model يُكمل
        3. Confidence يُحسب
        4. Decision Engine يُقرر
        """
        registry = get_command_registry()
        policy_engine = get_policy_engine()
        decision_engine = get_decision_engine()
        state_machine = get_execution_state()
        rollback_engine = get_rollback_engine()
        timeline = get_timeline_manager()
        
        cmd_id = registry.register(user_text)
        state_machine.init(cmd_id)
        
        # Timeline: Start
        timeline.start_command(cmd_id, f"📝 {user_text}")
        
        result = {
            "command_id": cmd_id,
            "status": "pending",
            "decisions": [],
            "executed": False
        }
        
        try:
            # 1. Parsing
            state_machine.transition(cmd_id, ExecutionState.PARSING, "تحليل النص (LLM)")
            timeline.add_step(cmd_id, "parsing", "🧠 تحليل النص (LLM)")
            timeline.update_event("parsing", status=TimelineStatus.RUNNING)
            
            apps_context = ", ".join(list(opener.apps_index.keys())[:100])
            llm_result = self.brain.think(user_text, apps_context)
            
            if isinstance(llm_result, list):
                commands = llm_result
            else:
                commands = [llm_result] if llm_result else []
            
            if not commands:
                state_machine.set_error(cmd_id, "لم يتم التعرف على أي أمر")
                timeline.complete_step("parsing", success=False)
                timeline.complete_command(cmd_id, success=False)
                result["status"] = "failed"
                result["message"] = "لم يتم استخراج أوامر"
                return result
            
            timeline.complete_step("parsing", success=True)
            
            # 2. Decision & Execution
            step_decision = timeline.add_step(cmd_id, "decision", "⚖️ اتخاذ القرار")
            timeline.update_event("decision", status=TimelineStatus.RUNNING)
            state_machine.transition(cmd_id, ExecutionState.PLANNING, "اتخاذ القرار الذكي")
            
            all_decisions = []
            all_completed_commands = []
            
            # معالجة الأوامر (سلسلة أو مفرد)
            if len(commands) > 1:
                # سلسلة
                chain_decision = decision_engine.resolve_chain(commands)
                all_decisions = chain_decision.decisions
                
                # إضافة تفاصيل القرارات للـ Timeline
                details = []
                for d in all_decisions:
                    details.append(f"{d.action.value} ({d.confidence.score:.0%})")
                timeline.update_event("decision", details=" | ".join(details))
                
            else:
                # أمر واحد
                cmd = commands[0]
                decision = decision_engine.resolve(cmd if isinstance(cmd, dict) else cmd.dict())
                all_decisions = [decision]
                timeline.update_event("decision", details=f"{decision.action.value} ({decision.confidence.score:.0%})")
            
            timeline.complete_step("decision", success=True)
            
            # تنفيذ القرارات
            step_exec = timeline.add_step(cmd_id, "execution", "🚀 التنفيذ")
            timeline.update_event("execution", status=TimelineStatus.RUNNING)
            state_machine.transition(cmd_id, ExecutionState.EXECUTING, "بدء التنفيذ")
            
            executed_any = False
            
            for decision in all_decisions:
                result["decisions"].append({
                    "action": decision.action.value,
                    "confidence": decision.confidence.score,
                    "command": decision.command,
                    "notification": decision.notification,
                    "question": decision.question,
                    "quick_responses": decision.quick_responses, # 🆕
                    "learned_from": decision.learned_from        # 🆕
                })
                
                # إظهار التفكير
                if self.ui_callback:
                    self.ui_callback(decision_engine.format_decision(decision), "thought")
                
                # تنفيذ
                if decision.should_execute:
                    # فحص السياسات
                    cmd_obj = Command(**decision.command)
                    policy_result = policy_engine.evaluate(cmd_obj)
                    
                    if not policy_result.allowed:
                        if self.ui_callback:
                            self.ui_callback(f"⛔ تم الحظر: {policy_result.reason}", "error")
                        timeline.add_step(cmd_id, f"blocked_{id(decision)}", f"❌ محظور: {policy_result.reason}")
                        continue
                    
                    # تنفيذ فعلي
                    exec_result = self.execute(cmd_obj)
                    all_completed_commands.append(decision.command)
                    executed_any = True
                    
                    if decision.should_notify:
                        if self.ui_callback:
                            self.ui_callback(decision.notification, "info")
                
                elif decision.should_ask:
                    # إضافة حدث انتظار
                    timeline.add_step(cmd_id, "waiting", f"❓ بانتظار إجابة: {decision.question}")
                    timeline.update_event("waiting", status=TimelineStatus.PAUSED)
                    timeline.update_event(cmd_id, status=TimelineStatus.PAUSED)
                    
                    if self.ui_callback:
                        self.ui_callback(decision.question, "warning")
                    
                    result["status"] = "waiting_for_user"
                    result["question"] = decision.question
                    result["quick_responses"] = decision.quick_responses
            
            if executed_any:
                state_machine.transition(cmd_id, ExecutionState.COMPLETED, "تم التنفيذ")
                registry.update_status(cmd_id, CommandStatus.COMPLETED)
                registry.set_rollback_available(cmd_id, True)
                timeline.complete_step("execution", success=True)
                timeline.complete_command(cmd_id, success=True)
                result["status"] = "completed"
                result["executed"] = True
            elif not result.get("status") == "waiting_for_user":
                 timeline.complete_step("execution", success=True)
                 timeline.complete_command(cmd_id, success=True)
            
            return result
            
        except Exception as e:
            state_machine.set_error(cmd_id, str(e))
            timeline.update_event(cmd_id, status=TimelineStatus.FAILED, details=str(e))
            if self.ui_callback:
                self.ui_callback(f"❌ حدث خطأ: {e}", "error")
            return {"status": "error", "message": str(e)}
        

            
        except Exception as e:
            state_machine.set_error(cmd_id, str(e))
            result["status"] = "error"
            result["message"] = str(e)
            
            if self.ui_callback:
                self.ui_callback(f"❌ {e}", "error")
            
            return result
    
    def _execute_commands_as_graph(self, cmd_id: str, commands: list, rollback_engine, state_machine=None):
        """بناء وتصحيح وتنفيذ Graph من الأوامر"""
        from core.execution_graph import GraphResult
        
        # 1. بناء Graph مبدئي
        builder = create_graph(cmd_id)
        
        prev_node = None
        for i, cmd in enumerate(commands):
            # إنشاء action wrapper مع state updates
            action_func = self._create_action_func_with_state(cmd, cmd_id, i, len(commands), state_machine)
            rollback_func, rollback_data = self._create_rollback_func(cmd, rollback_engine)
            
            # إضافة للـ Graph
            node_id = builder.add_action(
                intent=cmd.intent,
                action=action_func,
                params={"command": cmd},
                depends_on=prev_node,
                rollback_action=rollback_func,
                rollback_data=rollback_data
            )
            
            prev_node = node_id
        
        # بناء الـ Graph
        graph = builder.build()
        graph.add_callback(self.ui_callback or (lambda m, l: None))
        
        # 2. Auto-Repair 🔧
        try:
            planner = AutoRepairPlanner()
            graph, fixes = planner.repair(graph)
            
            if fixes:
                msg = f"🔧 تم إصلاح الـ Graph تلقائياً: {', '.join(fixes)}"
                if self.ui_callback:
                    self.ui_callback(msg, "warning")
                
                # تعلم من الإصلاح
                learning = get_learning_engine()
                for fix in fixes:
                    learning.learn_graph_fix(
                        rule="auto_repair", 
                        trigger="graph_check", 
                        fix=fix
                    )
        except Exception as e:
            msg = f"⚠️ فشل الإصلاح التلقائي: {e}"
            if self.ui_callback:
                self.ui_callback(msg, "warning")

        # 3. Rule Validation ⚖️
        try:
            rule_engine = GraphRuleEngine()
            rule_engine.validate(graph)
        except GraphRuleError as e:
            # فشل التحقق، لن ننفذ
            msg = f"⛔ تم رفض التنفيذ لخرق القواعد: {e}"
            if self.ui_callback:
                self.ui_callback(msg, "error")
            
            # إرجاع نتيجة فشل
            return GraphResult(
                command_id=cmd_id,
                success=False,
                nodes_total=len(graph.nodes),
                nodes_completed=0,
                nodes_failed=0,
                nodes_skipped=len(graph.nodes),
                total_duration_ms=0,
                error=str(e)
            )
        
        # 4. تنفيذ
        return graph.execute()
    
    def _create_action_func_with_state(self, cmd, cmd_id, index, total, state_machine):
        """إنشاء action wrapper مع State Machine updates"""
        def action_wrapper(command):
            # إطلاق NODE_RUNNING
            if state_machine:
                state_machine.transition(
                    cmd_id,
                    ExecutionState.NODE_RUNNING,
                    f"تنفيذ: {cmd.intent}",
                    node_id=f"node-{index+1}"
                )
                state_machine.update_progress(cmd_id, index, total, f"node-{index+1}")
            
            # التنفيذ الفعلي
            result = self._execute_single_command(command)
            
            # إطلاق NODE_DONE
            if state_machine:
                state_machine.transition(
                    cmd_id,
                    ExecutionState.NODE_DONE,
                    f"اكتمل: {cmd.intent}",
                    node_id=f"node-{index+1}"
                )
                state_machine.update_progress(cmd_id, index + 1, total)
            
            return result
        return action_wrapper
    
    def _create_action_func(self, cmd: Command):
        """إنشاء دالة التنفيذ للأمر"""
        def action_wrapper(command):
            return self._execute_single_command(command)
        return action_wrapper
    
    def _execute_single_command(self, cmd: Command) -> str:
        """تنفيذ أمر واحد وإرجاع النتيجة"""
        # نفس منطق execute() لكن يُرجع string
        msg = ""
        
        if cmd.intent == "open":
            msg = opener.run(cmd.target)
        elif cmd.intent == "open_file":
            msg = fs_manager.open_file(filename=cmd.target, folder=cmd.loc or "desktop")
        elif cmd.intent == "create_folder":
            msg = fs_manager.create_folder(cmd.target, cmd.loc)
        elif cmd.intent == "create_file":
            msg = fs_manager.create_file(cmd.target, cmd.loc, cmd.param)
        elif cmd.intent == "write_file":
            msg = fs_manager.write_file(cmd.target, cmd.loc, cmd.param)
        elif cmd.intent == "delete":
            msg = fs_manager.delete_item(cmd.target, cmd.loc)
        elif cmd.intent == "rename":
            msg = fs_manager.rename_item(cmd.target, cmd.loc, cmd.param)
        elif cmd.intent == "copy":
            msg = fs_manager.copy_item(cmd.target, cmd.loc, cmd.dest)
        elif cmd.intent == "move":
            msg = fs_manager.move_item(cmd.target, cmd.loc, cmd.dest)
        else:
            msg = f"Unknown intent: {cmd.intent}"
        
        if self.ui_callback:
            self.ui_callback(f"  ✅ {msg}", "success")
        
        return msg
    
    def _create_rollback_func(self, cmd: Command, rollback_engine):
        """إنشاء دالة Rollback للأمر"""
        from actions.file_ops import resolve_path
        
        rollback_data = {}
        rollback_func = None
        
        if cmd.intent in ["create_folder", "create_file"]:
            # حذف ما تم إنشاؤه
            path = resolve_path(cmd.target, cmd.loc or "desktop")
            rollback_data = {"path": path}
            
            def delete_created(path):
                import shutil
                if os.path.exists(path):
                    if os.path.isfile(path):
                        os.remove(path)
                    else:
                        shutil.rmtree(path)
            
            rollback_func = delete_created
        
        elif cmd.intent == "delete":
            # سيتم التعامل معه في الـ action نفسه (move to trash)
            pass
        
        return rollback_func, rollback_data
    
    def get_command_history(self, count: int = 10) -> list:
        """الحصول على تاريخ الأوامر"""
        registry = get_command_registry()
        return registry.get_recent(count)
    
    def rollback_command(self, cmd_id: str) -> str:
        """تراجع عن أمر"""
        rollback_engine = get_rollback_engine()
        state_machine = get_execution_state()
        
        if not rollback_engine.has_rollback(cmd_id):
            return f"❌ لا يوجد rollback متاح لـ {cmd_id}"
        
        state_machine.request_rollback(cmd_id)
        result = rollback_engine.rollback(cmd_id)
        state_machine.mark_rolled_back(cmd_id)
        
        if result.success:
            return f"✅ تم التراجع عن {result.rolled_back_count} عمليات"
        else:
            return f"⚠️ تراجع جزئي: {result.rolled_back_count} نجح، {result.failed_count} فشل"
    
    # ═══════════════════════════════════════════════════════════
    # 🆕 State Machine API
    # ═══════════════════════════════════════════════════════════
    
    def get_execution_status(self, cmd_id: str) -> dict:
        """الحصول على حالة التنفيذ"""
        return get_execution_state().get_json(cmd_id)
    
    def get_timeline(self, cmd_id: str) -> str:
        """الحصول على Timeline"""
        return get_execution_state().format_timeline(cmd_id)
    
    def pause_execution(self, cmd_id: str) -> bool:
        """إيقاف مؤقت"""
        return get_execution_state().pause(cmd_id)
    
    def resume_execution(self, cmd_id: str) -> bool:
        """استئناف"""
        return get_execution_state().resume(cmd_id)
    
    def cancel_execution(self, cmd_id: str) -> bool:
        """إلغاء"""
        return get_execution_state().cancel(cmd_id)
    
    def get_active_executions(self) -> list:
        """الحصول على التنفيذات النشطة"""
        return [s.command_id for s in get_execution_state().get_active()]
    
    def subscribe_to_updates(self, callback):
        """الاشتراك في تحديثات التنفيذ"""
        get_execution_state().subscribe_all(callback)
    
    def get_core_status(self) -> dict:
        """حالة Core Architecture"""
        state_machine = get_execution_state()
        active = state_machine.get_active()
        
        return {
            "registry": get_command_registry().get_stats(),
            "policy_engine": f"Profile: {get_policy_engine().current_profile}",
            "rollback": get_rollback_engine().format_status(),
            "active_executions": len(active),
            "state_machine": "running" if active else "idle"
        }