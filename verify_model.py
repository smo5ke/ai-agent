# verify_model.py
import os
import sys

MODEL_PATH = "Meta-Llama-3.1-8B-Instruct-Q6_K_L.gguf"

def test_load():
    print(f"🔍 Testing model: {MODEL_PATH}")
    
    if not os.path.exists(MODEL_PATH):
        print("❌ Model file NOT found in current directory.")
        return

    size_gb = os.path.getsize(MODEL_PATH) / (1024**3)
    print(f"📦 File size: {size_gb:.2f} GB")

    try:
        print("⏳ Importing llama_cpp...")
        from llama_cpp import Llama
        print(f"   Library version: {Llama.__module__}")
        
        print("🧠 Attempting to load model (Minimal config)...")
        llm = Llama(
            model_path=MODEL_PATH,
            n_gpu_layers=0,
            n_ctx=512,  # Very small context
            verbose=True
        )
        print("✅ SUCCESS! Model loaded correctly.")
        
        print("🗣️ Testing inference...")
        output = llm("Hello AI", max_tokens=10)
        print("✅ Inference worked:", output['choices'][0]['text'])

    except Exception as e:
        print("\n❌ LOAD FAILED!")
        print(f"Error type: {type(e).__name__}")
        print(f"Error details: {e}")
        print("\n💡 Suggestions:")
        print("1. The file might be corrupted (incomplete download).")
        print("2. Re-download the model.")
        print("3. Try 'pip install --upgrade --force-reinstall llama-cpp-python'")

if __name__ == "__main__":
    test_load()
    input("\nPress Enter to exit...")
