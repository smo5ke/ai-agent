# actions/smart_browser.py
"""
🚀 Smart Browser - المتصفح الذكي
Simply opens URLs provided by the intelligent agent.
"""
import webbrowser

class SmartBrowser:
    def open_url(self, url: str) -> str:
        """Opens a URL in the default browser."""
        if not url:
            return "❌ Error: Empty URL"
            
        # Validate/Fix Protocol
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
            
        try:
            webbrowser.open(url)
            return f"🚀 Opening: {url}"
        except Exception as e:
            return f"❌ Error opening browser: {e}"

if __name__ == "__main__":
    # Test
    b = SmartBrowser()
    print(b.open_url("google.com"))
