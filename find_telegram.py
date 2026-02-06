import subprocess

def find_telegram():
    print("🔍 Searching for Telegram via Get-AppxPackage...")
    
    cmd = ["powershell", "-NoProfile", "-Command", "Get-AppxPackage *Telegram* | Select-Object Name, PackageFamilyName, InstallLocation | Format-List"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(f"Return: {result.returncode}")
        print(f"STDOUT:\n{result.stdout}")
        print(f"STDERR:\n{result.stderr}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_telegram()
