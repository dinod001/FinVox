import os
import sys
import json

# Ensure project root and src are in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from src.agents.tools.market_tools import get_market_data

def test_market_tool():
    print("="*60)
    print("Integration Test: Market Data Tool (yfinance)")
    print("="*60)
    
    # ---------------------------------------------------------
    # Test 1: Single Ticker
    # ---------------------------------------------------------
    print("\n[Test 1] Fetching data for a SINGLE ticker (USD/LKR)...")
    single_ticker = ["LKR=X"]
    
    # Note: Since it's a LangChain @tool, we call the underlying python function via .invoke() or directly.
    # In Langchain v0.1+, tools are callable directly or via invoke.
    try:
        single_result = get_market_data.invoke({"ticker_symbols": single_ticker})
        print("✅ Result:")
        print(json.dumps(single_result, indent=2))
    except Exception as e:
        print(f"❌ Failed: {e}")

    # ---------------------------------------------------------
    # Test 2: Multiple Tickers
    # ---------------------------------------------------------
    print("\n[Test 2] Fetching data for MULTIPLE tickers (Apple, S&P 500, Gold)...")
    multiple_tickers = ["AAPL", "^GSPC", "GC=F"]
    
    try:
        multi_result = get_market_data.invoke({"ticker_symbols": multiple_tickers})
        print("✅ Result:")
        print(json.dumps(multi_result, indent=2))
    except Exception as e:
        print(f"❌ Failed: {e}")

    # ---------------------------------------------------------
    # Test 3: SME Specific Forex & Gold
    # ---------------------------------------------------------
    print("\n[Test 3] Fetching SME Specific Data (Euro, GBP, Gold)...")
    sme_tickers = ["EURLKR=X", "GBPLKR=X", "GC=F"]
    
    try:
        sme_result = get_market_data.invoke({"ticker_symbols": sme_tickers})
        print("✅ Result:")
        print(json.dumps(sme_result, indent=2))
    except Exception as e:
        print(f"❌ Failed: {e}")

    # ---------------------------------------------------------
    # Test 4: Investment Advisor Tool (Tavily)
    # ---------------------------------------------------------
    print("\n[Test 4] Fetching Investment Data via Tavily (Sri Lanka Treasury Bills 2026)...")
    from src.agents.tools.investment_tools import search_investment_opportunities
    
    try:
        investment_result = search_investment_opportunities.invoke({"query": "Sri Lanka Treasury Bill Rates 2026"})
        print("✅ Result:")
        print(json.dumps(investment_result, indent=2))
    except Exception as e:
        print(f"❌ Failed: {e}")

    print("\n" + "="*60)
    print("Test Completed!")
    print("="*60)

if __name__ == "__main__":
    test_market_tool()
