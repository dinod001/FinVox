import yfinance as yf
from typing import Dict, Any, List
from datetime import datetime, timezone
from src.infrastructure.log import log

class MarketTool:
    """
    Encapsulates market data fetching.
    While it doesn't currently require heavy dependencies like a DB engine,
    making it a class fits the dependency injection pattern of the rest of the application.
    """

    def fetch_data(self, ticker_symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Fetch real-time market data (price, currency rates, stocks) for multiple ticker symbols at once.
        Example tickers: 
        ['LKR=X'] for USD to LKR exchange rate.
        ['AAPL', 'MSFT'] for Apple and Microsoft stocks.
        ['^GSPC'] for S&P 500 index.
        """
        log.info(f"MarketTool.fetch_data called for: {ticker_symbols}")
        results = {}
        for ticker_symbol in ticker_symbols:
            try:
                ticker = yf.Ticker(ticker_symbol)
                
                # Try to get fast_info first (much faster), fallback to info if needed
                current_price = ticker.fast_info.get("last_price")
                if not current_price:
                    current_price = ticker.info.get("regularMarketPrice")
                    
                if not current_price:
                    results[ticker_symbol] = {"error": f"Could not find price data for {ticker_symbol}"}
                    continue
                    
                # Fetch last 5 days of history to get exact dates and previous prices
                history_df = ticker.history(period="5d")
                historical_prices = {}
                if not history_df.empty:
                    # Iterate in reverse order (most recent first)
                    for date, row in history_df.iloc[::-1].iterrows():
                        date_str = date.strftime("%Y-%m-%d")
                        historical_prices[date_str] = round(row["Close"], 4)
                    
                results[ticker_symbol] = {
                    "current_price": round(current_price, 4),
                    "historical_close_prices": historical_prices,
                    "currency": ticker.info.get("currency", "Unknown"),
                    "name": ticker.info.get("shortName", ticker_symbol),
                    "retrieved_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                }
            except Exception as e:
                log.error(f"MarketTool failed for {ticker_symbol}: {e}")
                results[ticker_symbol] = {"error": f"Failed to fetch data. Error: {str(e)}"}
                
        return results
