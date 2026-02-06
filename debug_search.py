from duckduckgo_search import DDGS
import json

try:
    from googlesearch import search
    print("🚀 محاولة البحث (الوضع البسيط)...")
    
    query = "Bitcoin price USD today"
    
    # ألغينا advanced=True لأنه يسبب المشكلة
    # هذا سيرجع روابط فقط، لكنه أضمن
    results = search(query, num_results=5, advanced=False)
    
    found = False
    for i, link in enumerate(results, 1):
        print(f"🔗 نتيجة {i}: {link}")
        found = True
        
    if not found:
        print("❌ البحث عاد فارغاً أيضاً! قد يكون الـ IP محظوراً مؤقتاً.")
    else:
        print("\n✅ البحث يعمل بنجاح!")

except Exception as e:
    print(f"❌ خطأ: {e}")