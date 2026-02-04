"""
🔧 Auto-Repair Planner - مصلح الـ Graph
=======================================
يقوم بإصلاح الـ Graph تلقائياً قبل التنفيذ.

Capabilities:
1. Reorder Nodes: نقل أوامر المراقبة للنهاية.
2. Inject Nodes: إضافة أوامر مفقودة (create_folder, create_file).
3. Path Normalization: توحيد المسارات.
"""

from typing import List, Dict, Optional, Tuple
from core.execution_graph import ExecutionGraph, ExecutionNode, create_graph
from core.graph_rules import NodeType, GraphRuleEngine, GraphRuleError

class AutoRepairPlanner:
    """مخطط الإصلاح التلقائي"""
    
    def __init__(self):
        self.rule_engine = GraphRuleEngine()
    
    def repair(self, graph: ExecutionGraph) -> Tuple[ExecutionGraph, List[str]]:
        """
        إصلاح الـ Graph.
        
        Returns:
            (New Graph, List of fixes applied)
        """
        fixes = []
        
        # 1. إصلاح ترتيب Reactive Actions
        if self._needs_reorder_reactive(graph):
            graph = self._fix_reorder_reactive(graph)
            fixes.append("reorder_reactive_to_end")
        
        # 2. حقن create_folder المفقود
        if self._needs_folder_injection(graph):
            graph = self._fix_inject_folder(graph)
            fixes.append("inject_create_folder")
            
        # 3. حقن create_file المفقود قبل الكتابة
        if self._needs_file_injection(graph):
            graph = self._fix_inject_file(graph)
            fixes.append("inject_create_file")
            
        return graph, fixes
        
    # ═══════════════════════════════════════════════════════════
    # Checkers & Fixers
    # ═══════════════════════════════════════════════════════════
    
    def _needs_reorder_reactive(self, graph: ExecutionGraph) -> bool:
        """هل نحتاج إعادة ترتيب المراقبة؟"""
        try:
            self.rule_engine._rule_reactive_must_be_last(graph, list(graph.nodes.values()))
            return False
        except GraphRuleError:
            return True
            
    def _fix_reorder_reactive(self, graph: ExecutionGraph) -> ExecutionGraph:
        """نقل المراقبة للنهاية"""
        # هذا يتطلب إعادة بناء الـ dependencies
        # للتبسيط، سنجعل كل الـ reactive nodes تعتمد على آخر imperative node
        
        nodes = list(graph.nodes.values())
        imperative_nodes = [n for n in nodes if self.rule_engine._get_node_type(n.intent) == NodeType.IMPERATIVE]
        reactive_nodes = [n for n in nodes if self.rule_engine._get_node_type(n.intent) == NodeType.REACTIVE]
        
        if not imperative_nodes or not reactive_nodes:
            return graph
            
        # العثور على آخر node تنفيذي
        # (في الواقع، يجب أن تعتمد المراقبة على *نجاح* العملية التي نراقبها)
        # سنجعلها تعتمد على *كل* الـ imperative nodes لضمان أنها الأخيرة
        
        for r_node in reactive_nodes:
            # مسح الاعتمادات القديمة التي قد تسبب دورات
            r_node.depends_on = []
            
            # الاعتماد على كل الـ imperative nodes
            for i_node in imperative_nodes:
                if i_node.id not in r_node.depends_on:
                    r_node.depends_on.append(i_node.id)
                    
        return graph

    def _needs_file_injection(self, graph: ExecutionGraph) -> bool:
        """هل نحتاج حقن create_file؟"""
        # إذا كان هناك write بدون create
        nodes = list(graph.nodes.values())
        write_intents = ["write_text", "append_text"]
        create_intents = ["create_file", "touch"]
        
        for node in nodes:
            if node.intent in write_intents:
                # تحقق مبسط: هل يوجد أي create للملف المستهدف؟
                target = self._get_target_path(node)
                if not target: continue
                
                has_create = False
                for other in nodes:
                    if other.intent in create_intents:
                        other_target = self._get_target_path(other)
                        if other_target and other_target == target:
                            has_create = True
                            break
                
                if not has_create:
                    return True
        return False

    def _fix_inject_file(self, graph: ExecutionGraph) -> ExecutionGraph:
        """حقن create_file قبل الكتابة"""
        # ملاحظة: تعديل graph مباشر صعب، سنستخدم GraphBuilder جديد أو نعدل الحالي بحذر
        # هنا سنعدل الحالي
        
        nodes = list(graph.nodes.values())
        write_intents = ["write_text", "append_text"]
        new_nodes = []
        
        from actions.file_ops import get_file_ops # نحتاج الدالة
        
        for node in nodes:
            if node.intent in write_intents:
                target = self._get_target_path(node)
                if not target: continue
                
                # هل يوجد create؟
                if self._has_create_for(nodes, target):
                    continue
                
                # إنشاء node جديد
                import os
                
                # استخراج الاسم والموقع
                if os.path.isabs(target):
                    name = os.path.basename(target)
                    location = os.path.dirname(target)
                else:
                    name = target
                    location = "desktop"
                
                create_id = graph.add_node(
                    intent="create_file",
                    action=get_file_ops().create_file,
                    params={"name": name, "location": location},
                    depends_on=node.depends_on # يرث الاعتمادات
                )
                
                # تعديل الـ write ليعتمد على الـ create الجديد
                node.depends_on = [create_id]
                
        return graph

    def _needs_folder_injection(self, graph: ExecutionGraph) -> bool:
        # TODO Implementation
        return False
        
    def _fix_inject_folder(self, graph: ExecutionGraph) -> ExecutionGraph:
        # TODO Implementation
        return graph

    # Helper
    def _get_target_path(self, node: ExecutionNode) -> Optional[str]:
        p = node.params
        return p.get("target") or p.get("path") or (p.get("command", {}).get("target"))

    def _has_create_for(self, nodes: List[ExecutionNode], target: str) -> bool:
        create_intents = ["create_file", "touch"]
        for n in nodes:
            if n.intent in create_intents:
                t = self._get_target_path(n)
                if t and t == target:
                    return True
        return False
