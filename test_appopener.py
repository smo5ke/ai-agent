from AppOpener import open as app_opener

def test():
    print("🧪 Testing AppOpener...")
    try:
        # Just print keys or something harmless? 
        # AppOpener doesn't have a 'list' function easily accessible without input usually?
        # Let's just try to open 'calculator' which is safe.
        # But we don't want to spam user screens.
        # Let's just import it.
        print("✅ AppOpener imported successfully.")
    except Exception as e:
        print(f"❌ Failed to import AppOpener: {e}")

if __name__ == "__main__":
    test()
