# test_search_tool.py
from tools.search_tool import WebSearch

def test():
    print("🧪 Testing Web Search...")
    searcher = WebSearch()
    
    queries = ["Bitcoin price today", "بطيخ"]
    
    for q in queries:
        print(f"\n🔎 Searching for: {q}")
        result = searcher.search(q)
        print("📝 Result:")
        print(result)
        print("-" * 40)

if __name__ == "__main__":
    test()
