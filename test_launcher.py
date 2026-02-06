from actions.app_launcher import AppLauncher
import json

def test_launcher():
    launcher = AppLauncher()
    
    print(f"📊 Total Apps Indexed: {len(launcher.apps_index)}")
    
    queries = ["Telegram", "Telegram Desktop", "3d max", "Word", "Chrome"]
    
    print("\n🔍 Testing Queries:")
    for q in queries:
        result = launcher.find_closest_app(q)
        print(f"   '{q}' -> {result}")

    # Check if Telegram is actually in the keys
    print("\n🧐 Searching for 'telegram' in index keys:")
    params = [k for k in launcher.apps_index.keys() if "telegram" in k]
    print(f"   Found matches: {params}")

if __name__ == "__main__":
    test_launcher()
