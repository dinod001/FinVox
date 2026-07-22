import os
from typing import Dict, Any, List
from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from src.infrastructure.config import INVESTMENT_DOMAINS
from src.infrastructure.log import log

@tool
def search_investment_opportunities(query: str) -> List[Dict[str, Any]]:
    """
    Search for investment opportunities, surplus capital allocation strategies, 
    and reliable financial news. This tool strictly searches trusted Sri Lankan 
    financial sources (e.g., CBSL, CSE, LBO, Daily FT, Economy Next).
    
    Args:
        query: The search query (e.g., 'Current Treasury Bill Rates Sri Lanka', 
               'Best fixed deposit rates', 'Recent CSE market trends').
               
    Returns:
        A list of search results containing snippets, titles, and URLs from trusted domains.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key or api_key == "your_tavily_key":
        return [{"error": "TAVILY_API_KEY is missing or invalid in the .env file."}]

    try:
        # Initialize Tavily search restricted to our trusted domains
        search = TavilySearchResults(
            max_results=3, 
            include_domains=INVESTMENT_DOMAINS
        )
        
        log.info(f"Searching Tavily for investment info: '{query}'")
        results = search.invoke({"query": query})
        
        return results
    except Exception as e:
        log.error(f"Investment search failed: {e}")
        return [{"error": f"Search failed: {str(e)}"}]
