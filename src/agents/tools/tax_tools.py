import os
from typing import Dict, Any, List
from langchain_community.tools.tavily_search import TavilySearchResults
from src.infrastructure.config import TAX_DOMAINS
from src.infrastructure.log import log

class TaxTool:
    """
    Encapsulates tax-related web searching using Tavily.
    Searches are strictly limited to official Sri Lankan government tax sources
    (IRD, Treasury, Customs, CBSL) to ensure accuracy and reliability.
    """
    
    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY")
        if self.api_key and self.api_key != "your_tavily_key":
            self.search_client = TavilySearchResults(
                max_results=4,
                include_domains=TAX_DOMAINS
            )
        else:
            self.search_client = None

    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Search official Sri Lankan government tax portals for tax rates,
        regulations, deadlines, and compliance information.
        Strictly searches trusted domains: ird.gov.lk, treasury.gov.lk, customs.gov.lk, cbsl.gov.lk
        """
        log.info(f"TaxTool.search called: '{query}'")
        
        if not self.search_client:
            log.warning("Tavily API key is missing. Tax search disabled.")
            return [{"error": "TAVILY_API_KEY is missing or invalid in the .env file."}]

        try:
            results = self.search_client.invoke({"query": query})
            log.info(f"TaxTool found {len(results)} results from official sources.")
            return results
        except Exception as e:
            log.error(f"Tax search failed: {e}")
            return [{"error": f"Search failed: {str(e)}"}]
