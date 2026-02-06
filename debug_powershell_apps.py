import subprocess
import json

def test_powershell():
    print("🔍 Testing PowerShell Get-StartApps...")
    
    cmd = ["powershell", "-NoProfile", "-Command", "Get-StartApps | ConvertTo-Json"]
    
    try:
        # Run without creating a hidden window first to see if that matters, 
        # but capture output.
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print(f"Return Code: {result.returncode}")
        
        if result.stderr:
            print(f"❌ STDERR:\n{result.stderr}")
            
        if result.stdout:
            print(f"✅ STDOUT (First 500 chars):\n{result.stdout[:500]}")
            try:
                data = json.loads(result.stdout)
                print(f"✅ Parsed JSON. Found {len(data)} apps.")
                
                # Search for Telegram
                telegram = [app for app in data if "telegram" in app.get("Name", "").lower()]
                if telegram:
                    print(f"🎉 Make sure to see this: Found Telegram: {telegram}")
                else:
                    print("⚠️ Telegram not found in PowerShell output.")
            except Exception as e:
                print(f"❌ JSON Parse Error: {e}")
        else:
            print("⚠️ STDOUT is empty.")
            
    except Exception as e:
        print(f"❌ Execution Error: {e}")

if __name__ == "__main__":
    test_powershell()
