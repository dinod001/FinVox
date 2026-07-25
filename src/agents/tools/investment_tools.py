import os
from typing import Dict, Any, List
from langchain_community.tools.tavily_search import TavilySearchResults
from src.infrastructure.config import INVESTMENT_DOMAINS
from src.infrastructure.log import log

class InvestmentTool:
    """
    Encapsulates investment searching (Tavily).
    API key is read at invocation or init. 
    """
    
    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY")
        if self.api_key and self.api_key != "your_tavily_key":
            self.search_client = TavilySearchResults(
                max_results=3, 
                include_domains=INVESTMENT_DOMAINS
            )
        else:
            self.search_client = None

    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for investment opportunities, surplus capital allocation strategies, 
        and reliable financial news. This strictly searches trusted Sri Lankan financial sources.
        """
        log.info(f"InvestmentTool.search called: '{query}'")
        
        if not self.search_client:
            log.warning("Tavily API key is missing. Investment search disabled.")
            return [{"error": "TAVILY_API_KEY is missing or invalid in the .env file."}]

        try:
            results = self.search_client.invoke({"query": query})
            return results
        except Exception as e:
            log.error(f"Investment search failed: {e}")
            return [{"error": f"Search failed: {str(e)}"}]
