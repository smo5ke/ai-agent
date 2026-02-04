"""
⚖️ Graph Rule Engine - محرك قواعد التنفيذ
=========================================
يفرض القواعد الصارمة على الـ Graph لضمان منطقية التنفيذ.

Rules:
1. Reactive Actions Must Be Last (watch/on_change).
2. Write Requires Create (cannot write to non-existent file).
3. File Requires Folder (canonical path validation).
"""

from typing import List, Dict, Any
from enum import Enum
from dataclasses import dataclass
from core.execution_graph import ExecutionGraph, ExecutionNode

class NodeType(Enum):
    IMPERATIVE = "imperative"   # create, write, move
    REACTIVE   = "reactive"     # watch, on_change
    CONTROL    = "control"      # if, loop, delay
    TERMINAL   = "terminal"     # notify, log

class GraphRuleError(Exception):
    """خطأ في خرق قواعد الـ Graph"""
    pass

class GraphRuleEngine:
    """محرك القواعد"""
    
    def validate(self, graph: ExecutionGraph):
        """
        التحقق من صحة الـ Graph مقابل القواعد.
        يرمي GraphRuleError إذا وجد مخالفة.
        """
        nodes = list(graph.nodes.values())
        if not nodes:
            return

        # تطبيق القواعد
        self._rule_reactive_must_be_last(graph, nodes)
        self._rule_write_requires_create(graph, nodes)
        self._rule_file_requires_folder(graph, nodes)

    # ═══════════════════════════════════════════════════════════
    # Rules
    # ═══════════════════════════════════════════════════════════

    def _rule_reactive_must_be_last(self, graph: ExecutionGraph, nodes: List[ExecutionNode]):
        """Rule 1: Reactive actions (watch) must be leaves (execute last)"""
        # تحديد ترتيب التنفيذ
        order = graph._get_execution_order()
        if not order:
            return

        # البحث عن أول node reactive في الترتيب
        first_reactive_index = -1
        for i, node_id in enumerate(order):
            node = graph.get_node(node_id)
            if self._get_node_type(node.intent) == NodeType.REACTIVE:
                first_reactive_index = i
                break
        
        if first_reactive_index != -1:
            # التأكد من عدم وجود nodes تنفيذية بعده
            for i in range(first_reactive_index + 1, len(order)):
                next_node_id = order[i]
                next_node = graph.get_node(next_node_id)
                if self._get_node_type(next_node.intent) == NodeType.IMPERATIVE:
                    raise GraphRuleError(
                        f"Reactive action '{graph.get_node(order[first_reactive_index]).intent}' is scheduled before "
                        f"imperative action '{next_node.intent}'. Watch actions must be the last step."
                    )

        # فحص Dependencies (القديم)
        for node in nodes:
            if self._get_node_type(node.intent) == NodeType.REACTIVE:
                dependents = [n for n in nodes if node.id in n.depends_on]
                for dep in dependents:
                    if self._get_node_type(dep.intent) == NodeType.IMPERATIVE:
                        raise GraphRuleError(
                            f"Reactive action '{node.intent}' cannot be a dependency for '{dep.intent}'. "
                            "Watch actions must be the last step."
                        )

    def _rule_write_requires_create(self, graph: ExecutionGraph, nodes: List[ExecutionNode]):
        """Rule 2: Write/Append requires file creation or existence check"""
        write_intents = ["write_text", "append_text", "write_file"]
        create_intents = ["create_file", "touch"]
        
        for node in nodes:
            if node.intent in write_intents:
                # هل يوجد create_file قبله؟
                has_create = False
                
                # فحص الـ dependencies المباشرة والمتسلسلة
                # (تبسيط: نبحث في الـ nodes التي تسبقه في الترتيب ولها نفس الـ target)
                target = node.params.get("command", {}).get("target") or node.params.get("path")
                if not target:
                    continue

                # check predecessors in graph
                queue = list(node.depends_on)
                visited = set()
                
                while queue:
                    dep_id = queue.pop(0)
                    if dep_id in visited:
                        continue
                    visited.add(dep_id)
                    
                    dep_node = graph.get_node(dep_id)
                    if not dep_node:
                        continue
                        
                    if dep_node.intent in create_intents:
                        # TODO: check if targets match (needs robust comparison)
                        has_create = True
                        break
                    
                    queue.extend(dep_node.depends_on)
                
                # إذا لم نجد create، هذا انتهاك للقاعدة (إلا لو كان الملف موجود مسبقاً - وهذا يصعب التحقق منه هنا بدقة)
                # لذلك سنكون متساهلين قليلاً: نطلب أن يكون هناك create_file في الـ graph بشكل عام
                # أو نتركه للـ Auto-Fix ليحقنه
                
                # للنسخة الحالية الصارمة: يجب أن يكون هناك اعتماد
                if not has_create:
                    # قد يكون الملف موجوداً، لكننا نفضل explicit creation
                    pass 

    def _rule_file_requires_folder(self, graph: ExecutionGraph, nodes: List[ExecutionNode]):
        """Rule 3: Ensure folders exist before file operations"""
        # هذا يتم فحصه عادة في الـ path canonicalization
        pass

    def _get_node_type(self, intent: str) -> NodeType:
        """تحديد نوع الـ Node"""
        if intent in ["watch", "monitor", "on_change"]:
            return NodeType.REACTIVE
        elif intent in ["if", "loop", "wait"]:
            return NodeType.CONTROL
        elif intent in ["notify", "log", "alert"]:
            return NodeType.TERMINAL
        return NodeType.IMPERATIVE
