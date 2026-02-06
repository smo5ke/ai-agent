# tools/search_tool.py
"""
🌐 Hybrid Search Tool
Uses Wikipedia for facts and Yahoo Finance for market data.
"""
try:
    import wikipedia
except ImportError:
    wikipedia = None

try:
    import yfinance as yf
except ImportError:
    yf = None

class WebSearch:
    def __init__(self):
        if not wikipedia:
            print("⚠️ Warning: wikipedia not installed. pip install wikipedia")
        if not yf:
            print("⚠️ Warning: yfinance not installed. pip install yfinance")

    def _get_financial_data(self, query: str) -> str:
        """Fetch financial data if query looks like a stock/crypto symbol."""
        if not yf:
            return ""

        query_lower = query.lower()
        symbol = None
        
        # Simple heuristic to map common names to symbols
        if "bitcoin" in query_lower or "btc" in query_lower:
            symbol = "BTC-USD"
        elif "ethereum" in query_lower or "eth" in query_lower:
            symbol = "ETH-USD"
        elif "apple" in query_lower:
            symbol = "AAPL"
        elif "google" in query_lower:
            symbol = "GOOGL"
        elif "microsoft" in query_lower:
            symbol = "MSFT"
        elif "gold" in query_lower:
            symbol = "GC=F"
        elif query.isupper() and len(query) <= 6: # Assume direct symbol if uppercase and short
            symbol = query

        if not symbol:
            return ""

        try:
            ticker = yf.Ticker(symbol)
            # Try fast_info first (faster, reliable)
            price = ticker.fast_info.last_price
            if price is None:
                # Fallback to history
                hist = ticker.history(period="1d")
                if not hist.empty:
                    price = hist['Close'].iloc[-1]
            
            if price:
                return f"💰 {symbol}: ${price:,.2f}"
        except Exception as e:
            print(f"⚠️ Yahoo Finance Error: {e}")
            
        return ""

    def _get_wiki_data(self, query: str) -> str:
        """Fetch summary from Wikipedia."""
        if not wikipedia:
            return "❌ Wikipedia module not installed."

        try:
            # Set language to english by default, or arabic if query is arabic?
            # User instructions imply general support. Let's try direct summary.
            # Detecting language is tricky without extra libs, assume English for now 
            # or let wikipedia auto-detect if possible (it defaults to 'en').
            # If the user speaks Arabic, we might want to switch language, 
            # but standard `wikipedia` lib is usually set globally.
            # Let's keep it simple as per prompt.
            
            summary = wikipedia.summary(query, sentences=3)
            return f"📚 Wikipedia: {summary}"
        except wikipedia.exceptions.DisambiguationError as e:
            return f"⚠️ Ambiguous Request. Did you mean: {', '.join(e.options[:5])}?"
        except wikipedia.exceptions.PageError:
            return "⚠️ No Wikipedia page found for this topic."
        except Exception as e:
            return f"❌ Wikipedia Error: {e}"

    def search(self, query: str, max_results: int = 3) -> str:
        """Smart hybrid search."""
        print(f"🌐 Hybrid Search: {query}...")
        
        # 1. Try Finance first
        finance_result = self._get_financial_data(query)
        if finance_result:
            return finance_result
            
        # 2. Fallback to Wikipedia
        return self._get_wiki_data(query)

# Testing
if __name__ == "__main__":
    s = WebSearch()
    print(s.search("BTC"))
    print(s.search("Python programming language"))
