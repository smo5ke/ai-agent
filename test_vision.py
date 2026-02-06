import os
from core.vision_engine import VisionEngine

def test_vision():
    print("🧪 Testing Vision Engine (Ollama)...")
    vision = VisionEngine()
    
    if not vision.ready:
        print("❌ Engine not ready. Install 'ollama' package.")
        return

    print("📸 Capturing screen...")
    path = vision.capture_screen("test_vision_screen.png")
    
    if path and os.path.exists(path):
        print(f"✅ Screenshot saved: {path}")
        
        print("👁️ Analyzing image...")
        result = vision.analyze_image(path, "What is in this image? Be brief.")
        print("\n📝 Analysis Result:")
        print("-" * 40)
        print(result)
        print("-" * 40)
        
        # Cleanup
        os.remove(path)
        print("🧹 Cleanup done.")
    else:
        print("❌ Failed to capture screen.")

if __name__ == "__main__":
    test_vision()
