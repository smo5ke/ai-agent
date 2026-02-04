import unittest
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.execution_graph import create_graph
from core.auto_repair import AutoRepairPlanner
from core.graph_rules import GraphRuleEngine, GraphRuleError

class TestAutoRepair(unittest.TestCase):
    
    def test_reorder_reactive(self):
        """Test moving watch command to the end"""
        builder = create_graph("test-1")
        
        # Add nodes in wrong order: watch -> create -> write
        builder.add_action("watch", lambda: None, params={"path": "."})
        create_id = builder.add_action("create_file", lambda: None, params={"path": "a.txt"})
        builder.add_action("write_text", lambda: None, params={"path": "a.txt"}, depends_on=create_id)
        
        graph = builder.build()
        
        # Repair
        planner = AutoRepairPlanner()
        new_graph, fixes = planner.repair(graph)
        
        print(f"Fixes: {fixes}")
        self.assertIn("reorder_reactive_to_end", fixes)
        
        # Validate Rule
        rule_engine = GraphRuleEngine()
        try:
            rule_engine.validate(new_graph)
            print("✅ Graph is valid after repair")
        except GraphRuleError as e:
            self.fail(f"Graph still invalid: {e}")

    def test_inject_create_file(self):
        """Test injecting missing create_file"""
        builder = create_graph("test-2")
        
        # Write without create
        builder.add_action("write_text", lambda: None, params={"path": "missing.txt"})
        
        graph = builder.build()
        
        planner = AutoRepairPlanner()
        new_graph, fixes = planner.repair(graph)
        
        print(f"Fixes: {fixes}")
        self.assertIn("inject_create_file", fixes)
        
        # Check if create_file node exists
        nodes = list(new_graph.nodes.values())
        create_nodes = [n for n in nodes if n.intent == "create_file"]
        self.assertEqual(len(create_nodes), 1)
        self.assertEqual(create_nodes[0].params["name"], "missing.txt")

if __name__ == '__main__':
    unittest.main()
