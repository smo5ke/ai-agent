# llm/network_client.py
"""
📡 Network Client
عميل يتصل بالسيرفر بدلاً من تحميل الموديل مباشرة
"""
import json
import urllib.request
import urllib.error

class NetworkPlanner:
    def __init__(self, port=5000):
        self.url = f"http://localhost:{port}/plan"
        print(f"📡 NetworkPlanner: Connected to brain on port {port}")

    def plan(self, user_input: str, memory_context: str = "") -> dict:
        """إرسال طلب للسيرفر"""
        data = {
            "input": user_input,
            "context": memory_context
        }
        
        req = urllib.request.Request(
            self.url,
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result
        except urllib.error.URLError:
            print("⚠️ NetworkPlanner: Connection refused. Is server running?")
            return {"steps": [], "error": "Connection refused"}
        except Exception as e:
            print(f"⚠️ NetworkPlanner Error: {e}")
            return {"steps": []}
