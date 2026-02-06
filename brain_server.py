# brain_server.py
"""
🧠 Brain Server
يفصل الموديل عن الواجهة لتجنب تعارض الذاكرة
"""
import sys
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from llm.llama_runner import LLMPlanner

# إعدادات
PORT = 5000
MODEL_PATH = "Meta-Llama-3.1-8B-Instruct-Q6_K_L.gguf"

# تحميل الموديل مرة واحدة عند البدء
print(f"🧠 Server: Loading model from {MODEL_PATH}...")
try:
    planner = LLMPlanner(model_path=MODEL_PATH)
    print("✅ Server: Brain Ready!")
except Exception as e:
    print(f"❌ Server: Failed to load brain: {e}")
    planner = None

class RequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/plan':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                user_input = data.get('input', '')
                memory_context = data.get('context', '')
                
                print(f"📩 Server: Received request: {user_input[:50]}...")
                
                if planner:
                    result = planner.plan(user_input, memory_context)
                else:
                    result = {"steps": [], "error": "Model not loaded"}
                
                response = json.dumps(result).encode('utf-8')
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(response)
                
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode('utf-8'))

def run():
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, RequestHandler)
    print(f"🚀 Server: Listening on port {PORT}...")
    httpd.serve_forever()

if __name__ == '__main__':
    run()
