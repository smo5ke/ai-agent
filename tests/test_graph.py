"""
🧪 Test Execution Graph - اختبار رسم التنفيذ
=============================================
"""

import pytest
from core.execution_graph import (
    ExecutionNode, 
    ExecutionGraph, 
    GraphBuilder,
    create_graph,
    NodeStatus
)


class TestExecutionNode:
    """اختبارات ExecutionNode"""
    
    def test_node_creation(self):
        """إنشاء Node"""
        node = ExecutionNode(
            id="node-1",
            command_id="CMD-TEST-1",
            intent="create_folder",
            action=lambda: "done"
        )
        
        assert node.id == "node-1"
        assert node.status == NodeStatus.PENDING
    
    def test_node_execution_success(self):
        """تنفيذ Node ناجح"""
        node = ExecutionNode(
            id="node-1",
            command_id="CMD-TEST-1",
            intent="test",
            action=lambda: "success"
        )
        
        result = node.execute()
        
        assert result == True
        assert node.status == NodeStatus.DONE
        assert node.result == "success"
    
    def test_node_execution_failure(self):
        """تنفيذ Node فاشل"""
        def failing_action():
            raise Exception("Test error")
        
        node = ExecutionNode(
            id="node-1",
            command_id="CMD-TEST-1",
            intent="test",
            action=failing_action
        )
        
        result = node.execute()
        
        assert result == False
        assert node.status == NodeStatus.FAILED
        assert "Test error" in node.error


class TestExecutionGraph:
    """اختبارات ExecutionGraph"""
    
    def test_graph_creation(self):
        """إنشاء Graph"""
        graph = ExecutionGraph("CMD-TEST-1")
        
        assert graph.command_id == "CMD-TEST-1"
        assert len(graph.nodes) == 0
    
    def test_add_node(self):
        """إضافة Node"""
        graph = ExecutionGraph("CMD-TEST-1")
        
        node_id = graph.add_node(
            intent="test",
            action=lambda: "done"
        )
        
        assert node_id == "node-1"
        assert len(graph.nodes) == 1
    
    def test_graph_execution_success(self):
        """تنفيذ Graph ناجح"""
        graph = ExecutionGraph("CMD-TEST-1")
        
        graph.add_node(intent="step1", action=lambda: "step1 done")
        graph.add_node(intent="step2", action=lambda: "step2 done")
        
        result = graph.execute()
        
        assert result.success == True
        assert result.nodes_completed == 2
        assert result.nodes_failed == 0
    
    def test_graph_execution_with_failure(self):
        """تنفيذ Graph مع فشل"""
        graph = ExecutionGraph("CMD-TEST-1")
        
        graph.add_node(intent="step1", action=lambda: "ok")
        graph.add_node(intent="step2", action=lambda: (_ for _ in ()).throw(Exception("fail")))
        graph.add_node(intent="step3", action=lambda: "ok")
        
        result = graph.execute()
        
        assert result.success == False
        assert result.nodes_failed == 1
        assert result.nodes_skipped >= 0


class TestDependencies:
    """اختبارات الـ Dependencies"""
    
    def test_simple_dependency(self):
        """Dependency بسيط"""
        builder = create_graph("CMD-TEST-1")
        
        node1 = builder.add_action("create_folder", lambda: "folder")
        node2 = builder.add_action("create_file", lambda: "file", depends_on=node1)
        
        graph = builder.build()
        
        assert graph.nodes["node-2"].depends_on == ["node-1"]
    
    def test_dependency_order(self):
        """ترتيب التنفيذ"""
        execution_order = []
        
        def step1():
            execution_order.append(1)
            return "step1"
        
        def step2():
            execution_order.append(2)
            return "step2"
        
        builder = create_graph("CMD-TEST-1")
        n1 = builder.add_action("s1", step1)
        n2 = builder.add_action("s2", step2, depends_on=n1)
        
        graph = builder.build()
        graph.execute()
        
        assert execution_order == [1, 2]


class TestGraphBuilder:
    """اختبارات GraphBuilder"""
    
    def test_builder_chain(self):
        """بناء سلسلة"""
        builder = create_graph("CMD-TEST-1")
        
        n1 = builder.add_action("a", lambda: "a")
        n2 = builder.add_action("b", lambda: "b", depends_on=n1)
        n3 = builder.add_action("c", lambda: "c", depends_on=n2)
        
        graph = builder.build()
        
        assert len(graph.nodes) == 3
