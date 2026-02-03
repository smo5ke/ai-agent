import json
from llama_cpp import Llama
from core.schemas import Command
from llm.prompts import SYSTEM_PROMPT # استيراد البرومبت من الملف الخارجي

class Brain:
    def __init__(self, model_path):
        self.model_path = model_path
        self.llm = None
    
    def load(self):
        print(f"🧠 Loading Model from: {self.model_path}...")
        try:
            # n_ctx=4096 ليعطيه ذاكرة جيدة للمحادثة
            self.llm = Llama(model_path=self.model_path, n_ctx=4096, verbose=False, n_gpu_layers=0)
            return True
        except Exception as e:
            print(f"❌ Brain Load Error: {e}")
            return False

    def think(self, user_input, app_context) -> Command:
        if not self.llm:
            return Command(intent="unknown")

        # دمج سياق التطبيقات مع البرومبت الأساسي
        full_prompt = SYSTEM_PROMPT.format(known_apps=app_context, user_input=user_input)

        try:
            output = self.llm(full_prompt, max_tokens=250, temperature=0.1, stop=["<|eot_id|>"])
            text = output['choices'][0]['text'].strip()
            
            # استخراج JSON
            if "{" in text:
                json_str = text[text.find('{'):text.rfind('}')+1]
                data = json.loads(json_str)
                # التحقق والتنظيف عبر Pydantic
                return Command(**data)
            else:
                return Command(intent="unknown")
            
        except Exception as e:
            print(f"⚠️ Thinking Error: {e}")
            return Command(intent="unknown")