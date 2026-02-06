# llm/llama_runner.py
"""
🧠 LLM Planner v5.1 - الدماغ الحقيقي (Safe Mode)
إعدادات آمنة جداً لتجنب Access Violation
uses Llama-3.1
"""
import json
import os
import re
from pathlib import Path
from typing import Optional


class LLMPlanner:
    """المخطط الحقيقي باستخدام LLaMA"""
    
    def __init__(self, model_path: str):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"❌ Model not found: {model_path}")
        
        print(f"🧠 Loading Real Brain: {os.path.basename(model_path)}...")
        print("⏳ Please wait... (Safe CPU Mode)")
        
        try:
            from llama_cpp import Llama
            
            # 🔥 إعدادات متطابقة مع verify_model.py الذي نجح
            self.llm = Llama(
                model_path=model_path,
                n_gpu_layers=0,      # CPU ONLY
                n_ctx=2048,          # حجم ذاكرة معقول
                n_threads=4,         # عدد أنوية آمن
                n_batch=512,         
                verbose=False,       # تقليل الضجيج
                use_mmap=True,       # تفعيل mmap (نجح في الاختبار)
                use_mlock=False
            )
            
            self.system_prompt = self._load_prompt()
            print("✅ Brain Loaded & Ready!")
            
        except Exception as e:
            print(f"❌ Llama Init Error: {e}")
            raise

    def _load_prompt(self) -> str:
        prompt_path = Path(__file__).parent / "system_prompt.txt"
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
        return "You are an AI assistant. Output JSON only."

    def plan(self, user_input: str, memory_context: str = "") -> dict:
        # بناء prompt
        full_prompt = f"""<|start_header_id|>system<|end_header_id|>

{self.system_prompt}

MEMORY CONTEXT:
{memory_context if memory_context else "No context."}

<|eot_id|><|start_header_id|>user<|end_header_id|>

{user_input}

<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""
        
        print("🤔 Thinking...")
        
        try:
            output = self.llm(
                full_prompt,
                max_tokens=1024,
                temperature=0.1,
                stop=["<|eot_id|>"]
            )
            
            raw_text = output["choices"][0]["text"].strip()
            print(f"📤 Raw output available")
            return self._extract_json(raw_text)
            
        except Exception as e:
            print(f"❌ Inference Error: {e}")
            return {"steps": []}

    def _extract_json(self, text: str) -> dict:
        text = text.strip()
        # تنظيف إضافي لوسوم Llama
        text = text.replace("<|eot_id|>", "").strip()
        
        # 1. البحث عن JSON block (قائمة أو قاموس)
        # هذا regex يبحث عن أول [ ... ] أو { ... } ويحاول التقاط المحتوى داخله
        # نستخدم [\\s\\S]*? ليكون non-greedy ويلتقط أول بلوك صحيح
        
        candidates = []
        
        # محاولة البحث عن قائمة []
        list_matches = list(re.finditer(r'\[[\s\S]*\]', text))
        if list_matches:
             # نأخذ آخر واحد غالباً لأنه قد يكون هناك أمثلة في التفكير، لكن سنحاول بذكاء
             # عادة الـ JSON النهائي يكون في آخر النص
             pass

        # البحث عن JSON كـ Code Block إذا وجد
        code_block = re.search(r'```json([\s\S]*?)```', text, re.IGNORECASE)
        if code_block:
            json_text = code_block.group(1).strip()
            try:
                data = json.loads(json_text)
                if isinstance(data, list): return {"steps": data}
                if isinstance(data, dict) and "steps" in data: return data
                if isinstance(data, dict): return {"steps": [data]} # Single action
            except:
                pass

        # البحث عن أقواس مباشرة
        # نحاول العثور على أوسع نطاق ممكن يبدأ بـ [ وينتهي بـ ]
        try:
            start_index = text.find('[')
            end_index = text.rfind(']')
            if start_index != -1 and end_index != -1 and end_index > start_index:
                json_str = text[start_index:end_index+1]
                return {"steps": json.loads(json_str)}
        except:
            pass
            
        # محاولة أخيرة مع {}
        try:
            start_index = text.find('{')
            end_index = text.rfind('}')
            if start_index != -1 and end_index != -1 and end_index > start_index:
                json_str = text[start_index:end_index+1]
                data = json.loads(json_str)
                if "steps" in data: return data
                return {"steps": [data]}
        except:
            pass

        print(f"⚠️ Could not parse JSON from: {text[:100]}...")
        return {"steps": []}
# ===== وضع الاختبار الوهمي =====

def plan_mock(text: str) -> dict:
    """نسخة وهمية - للاختبار السريع فقط"""
    return {
        "steps": [
            {"action": "create_folder", "params": {"name": "تجربة"}},
            {"action": "create_file", "params": {"name": "a.txt"}},
            {"action": "write_text", "params": {"file": "a.txt", "text": "مرحبا"}}
        ]
    }


def plan(text: str) -> dict:
    """هذه الدالة تُستخدم عندما لا يوجد planner"""
    return plan_mock(text)
