# test_hybrid_search.py
from tools.search_tool import WebSearch
import time

def test():
    print("🧪 Testing Hybrid Search (Wikipedia + Yahoo Finance)...")
    searcher = WebSearch()
    
    queries = [
        "Bitcoin",         # Should trigger Crypto check
        "AAPL",            # Stock symbol
        "Python (programming language)", # Wikipedia
        "Albert Einstein"  # Wikipedia
    ]
    
    for q in queries:
        print(f"\n🔎 Searching for: {q}")
        try:
            result = searcher.search(q)
            print("📝 Result:")
            print(result)
        except Exception as e:
            print(f"❌ Error: {e}")
        print("-" * 40)
        time.sleep(1)

if __name__ == "__main__":
    test()
