# main.py
"""
🤖 AI Agent Clean v4.0
- Real LLM Integration (LLaMA)
- Transaction + Rollback
- Persistent Memory
- Event Bus + Reactive Loop
- Python Sandbox
"""
import os
import sys
import time
from pathlib import Path

# إعدادات
USE_REAL_LLM = False  # CLI defaults to False
USE_WATCHER = False
USE_EVENT_LOOP = False
MODEL_PATH = "Meta-Llama-3.1-8B-Instruct-Q6_K_L.gguf"


def main():
    print("=" * 60)
    print("🤖 AI Agent Clean v4.0 (CLI Mode)")
    print("=" * 60)
    
    playground = Path("./playground")
    playground.mkdir(exist_ok=True)
    
    from core.execution_context import ExecutionContext
    context = ExecutionContext(playground)
    
    from core.memory_manager import get_memory
    memory = get_memory()
    memory.set_preference("language", "arabic")
    
    # Mock LLM for CLI test
    from core.orchestrator import Orchestrator
    agent = Orchestrator(context)
    
    try:
        print("\n" + "─" * 60)
        user_input = "أنشئ مجلد تجربة وجواه ملف a.txt واكتب مرحبا"
        agent.process(user_input)
        print("\n" + "─" * 60)

    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")

if __name__ == "__main__":
    main()
