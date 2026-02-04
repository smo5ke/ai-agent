"""
📊 Execution Graph - رسم التنفيذ
================================
تحويل الأوامر إلى Graph قابل للتتبع والتنفيذ.

Flow:
Command → Graph → Nodes → Execute → Rollback (عند الحاجة)
"""

import threading
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import traceback


class NodeStatus(Enum):
    """حالة الـ Node"""
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ExecutionNode:
    """
    عقدة في Graph التنفيذ.
    
    كل عقدة تمثل عملية واحدة قابلة للتنفيذ والتراجع.
    """
    id: str                              # node-1, node-2
    command_id: str                      # CMD-20260204-8F3A
    intent: str                          # create_file, delete, etc
    action: Callable                     # الدالة المنفذة
    params: Dict = field(default_factory=dict)
    
    # الحالة
    status: NodeStatus = NodeStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    
    # التوقيت
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: int = 0
    
    # Rollback
    rollback_action: Optional[Callable] = None
    rollback_data: Dict = field(default_factory=dict)
    
    # Dependencies
    depends_on: List[str] = field(default_factory=list)
    
    def execute(self) -> bool:
        """تنفيذ الـ Node"""
        self.status = NodeStatus.RUNNING
        self.started_at = datetime.now()
        
        try:
            self.result = self.action(**self.params)
            self.status = NodeStatus.DONE
            return True
            
        except Exception as e:
            self.error = str(e)
            self.status = NodeStatus.FAILED
            return False
            
        finally:
            self.completed_at = datetime.now()
            if self.started_at:
                self.duration_ms = int(
                    (self.completed_at - self.started_at).total_seconds() * 1000
                )
    
    def rollback(self) -> bool:
        """تراجع عن التنفيذ"""
        if not self.rollback_action:
            return False
        
        try:
            self.rollback_action(**self.rollback_data)
            return True
        except Exception as e:
            print(f"Rollback failed for {self.id}: {e}")
            return False
    
    def can_execute(self, completed_nodes: set) -> bool:
        """هل يمكن التنفيذ؟ (كل الـ dependencies مكتملة)"""
        return all(dep in completed_nodes for dep in self.depends_on)
    
    def to_dict(self) -> Dict:
        """تحويل لـ dict"""
        return {
            "id": self.id,
            "intent": self.intent,
            "status": self.status.value,
            "result": str(self.result) if self.result else None,
            "error": self.error,
            "duration_ms": self.duration_ms
        }


@dataclass
class GraphResult:
    """نتيجة تنفيذ Graph"""
    command_id: str
    success: bool
    nodes_total: int
    nodes_completed: int
    nodes_failed: int
    nodes_skipped: int
    total_duration_ms: int
    failed_node: Optional[str] = None
    error: Optional[str] = None


class ExecutionGraph:
    """
    رسم التنفيذ.
    
    يدير مجموعة من ExecutionNodes ويحترم الـ dependencies.
    """
    
    def __init__(self, command_id: str):
        self.command_id = command_id
        self.nodes: Dict[str, ExecutionNode] = {}
        self.context: Dict[str, Any] = {}  # shared memory
        self._node_counter = 0
        self._lock = threading.Lock()
        self._callbacks: List[Callable] = []
    
    # ═══════════════════════════════════════════════════════════
    # إضافة Nodes
    # ═══════════════════════════════════════════════════════════
    
    def add_node(
        self,
        intent: str,
        action: Callable,
        params: Dict = None,
        depends_on: List[str] = None,
        rollback_action: Callable = None,
        rollback_data: Dict = None
    ) -> str:
        """إضافة node جديد"""
        with self._lock:
            self._node_counter += 1
            node_id = f"node-{self._node_counter}"
            
            node = ExecutionNode(
                id=node_id,
                command_id=self.command_id,
                intent=intent,
                action=action,
                params=params or {},
                depends_on=depends_on or [],
                rollback_action=rollback_action,
                rollback_data=rollback_data or {}
            )
            
            self.nodes[node_id] = node
            return node_id
    
    def add_callback(self, callback: Callable):
        """إضافة callback للإشعارات"""
        self._callbacks.append(callback)
    
    def _notify(self, message: str, level: str = "info"):
        """إرسال إشعار"""
        for callback in self._callbacks:
            try:
                callback(message, level)
            except:
                pass
    
    # ═══════════════════════════════════════════════════════════
    # التنفيذ
    # ═══════════════════════════════════════════════════════════
    
    def execute(self, stop_on_failure: bool = True) -> GraphResult:
        """تنفيذ كل الـ nodes بترتيب الـ dependencies"""
        start_time = datetime.now()
        completed_nodes: set = set()
        failed_node: Optional[str] = None
        error_msg: Optional[str] = None
        
        # ترتيب التنفيذ (topological sort بسيط)
        execution_order = self._get_execution_order()
        
        self._notify(f"📊 بدء تنفيذ Graph ({len(execution_order)} nodes)", "thought")
        
        for node_id in execution_order:
            node = self.nodes[node_id]
            
            # تخطي إذا فشل node سابق
            if stop_on_failure and failed_node:
                node.status = NodeStatus.SKIPPED
                continue
            
            # فحص dependencies
            if not node.can_execute(completed_nodes):
                node.status = NodeStatus.SKIPPED
                continue
            
            # تنفيذ
            self._notify(f"⚙️ [{node_id}] {node.intent}", "thought")
            
            success = node.execute()
            
            if success:
                completed_nodes.add(node_id)
                # تحديث السياق
                self.context[node_id] = node.result
            else:
                failed_node = node_id
                error_msg = node.error
                self._notify(f"❌ [{node_id}] {node.error}", "error")
                
                if stop_on_failure:
                    # Skip remaining nodes
                    for remaining_id in execution_order[execution_order.index(node_id)+1:]:
                        self.nodes[remaining_id].status = NodeStatus.SKIPPED
        
        # حساب الإحصائيات
        total_duration = int((datetime.now() - start_time).total_seconds() * 1000)
        
        nodes_completed = sum(1 for n in self.nodes.values() if n.status == NodeStatus.DONE)
        nodes_failed = sum(1 for n in self.nodes.values() if n.status == NodeStatus.FAILED)
        nodes_skipped = sum(1 for n in self.nodes.values() if n.status == NodeStatus.SKIPPED)
        
        result = GraphResult(
            command_id=self.command_id,
            success=failed_node is None,
            nodes_total=len(self.nodes),
            nodes_completed=nodes_completed,
            nodes_failed=nodes_failed,
            nodes_skipped=nodes_skipped,
            total_duration_ms=total_duration,
            failed_node=failed_node,
            error=error_msg
        )
        
        status = "✅" if result.success else "❌"
        self._notify(f"{status} Graph completed: {nodes_completed}/{len(self.nodes)}", "info")
        
        return result
    
    def _get_execution_order(self) -> List[str]:
        """ترتيب التنفيذ (topological sort)"""
        # بسيط: nodes بدون dependencies أولاً
        order = []
        added = set()
        
        while len(order) < len(self.nodes):
            for node_id, node in self.nodes.items():
                if node_id in added:
                    continue
                
                # كل الـ dependencies مضافة؟
                if all(dep in added for dep in node.depends_on):
                    order.append(node_id)
                    added.add(node_id)
        
        return order
    
    # ═══════════════════════════════════════════════════════════
    # Rollback
    # ═══════════════════════════════════════════════════════════
    
    def rollback(self) -> int:
        """
        تراجع عن كل الـ nodes المكتملة (بترتيب عكسي).
        
        Returns:
            عدد الـ nodes التي تم التراجع عنها
        """
        rolled_back = 0
        
        # ترتيب عكسي
        completed_nodes = [
            n for n in self.nodes.values() 
            if n.status == NodeStatus.DONE
        ]
        completed_nodes.sort(
            key=lambda x: x.completed_at or datetime.min, 
            reverse=True
        )
        
        for node in completed_nodes:
            if node.rollback():
                rolled_back += 1
                self._notify(f"↩️ Rolled back: {node.id}", "info")
        
        return rolled_back
    
    # ═══════════════════════════════════════════════════════════
    # استعلام
    # ═══════════════════════════════════════════════════════════
    
    def get_status(self) -> Dict:
        """حالة Graph"""
        return {
            "command_id": self.command_id,
            "nodes": {nid: n.to_dict() for nid, n in self.nodes.items()},
            "context": {k: str(v) for k, v in self.context.items()}
        }
    
    def get_node(self, node_id: str) -> Optional[ExecutionNode]:
        """الحصول على node"""
        return self.nodes.get(node_id)
    
    def format_status(self) -> str:
        """تنسيق الحالة للعرض"""
        lines = [f"📊 Graph [{self.command_id}]"]
        
        status_icons = {
            NodeStatus.PENDING: "⏳",
            NodeStatus.RUNNING: "⚙️",
            NodeStatus.DONE: "✅",
            NodeStatus.FAILED: "❌",
            NodeStatus.SKIPPED: "⏭️"
        }
        
        for node_id, node in self.nodes.items():
            icon = status_icons.get(node.status, "❓")
            deps = f" (→ {', '.join(node.depends_on)})" if node.depends_on else ""
            lines.append(f"  {icon} {node_id}: {node.intent}{deps}")
        
        return "\n".join(lines)


class GraphBuilder:
    """
    بناء Graph من الأوامر.
    
    يحول Commands إلى ExecutionGraph.
    """
    
    def __init__(self, command_id: str):
        self.graph = ExecutionGraph(command_id)
    
    def add_action(
        self,
        intent: str,
        action: Callable,
        params: Dict = None,
        depends_on: str = None,
        rollback_action: Callable = None,
        rollback_data: Dict = None
    ) -> str:
        """إضافة action"""
        deps = [depends_on] if depends_on else []
        return self.graph.add_node(
            intent=intent,
            action=action,
            params=params,
            depends_on=deps,
            rollback_action=rollback_action,
            rollback_data=rollback_data
        )
    
    def add_condition(
        self,
        check_func: Callable,
        then_action: Callable,
        else_action: Callable = None,
        params: Dict = None
    ) -> str:
        """إضافة condition node"""
        def condition_wrapper(**kwargs):
            if check_func(**kwargs):
                return then_action(**kwargs)
            elif else_action:
                return else_action(**kwargs)
            return None
        
        return self.graph.add_node(
            intent="condition",
            action=condition_wrapper,
            params=params or {}
        )
    
    def build(self) -> ExecutionGraph:
        """الحصول على Graph النهائي"""
        return self.graph


# ═══════════════════════════════════════════════════════════
# Helper
# ═══════════════════════════════════════════════════════════

def create_graph(command_id: str) -> GraphBuilder:
    """إنشاء GraphBuilder جديد"""
    return GraphBuilder(command_id)
