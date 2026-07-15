import httpx
import xml.etree.ElementTree as ET
from urllib.parse import quote
from typing import Optional
from app.db import db_manager

# Wikipedia and other public APIs require a User-Agent header to avoid 403 Forbidden errors
DEFAULT_HEADERS = {
    "User-Agent": "CognitiveCrossPollinator/1.0 (contact@example.com; educational recommender system)"
}

def fetch_wikipedia_summary(query: str) -> Optional[str]:
    """Fetches summary of a Wikipedia page using key-less REST API."""
    cached = db_manager.get_http_cache("wikipedia", query)
    if cached:
        return cached

    # Search for page title
    search_url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json",
        "utf8": 1
    }
    
    try:
        r = httpx.get(search_url, params=params, headers=DEFAULT_HEADERS, timeout=5.0)
        r.raise_for_status()
        search_data = r.json()
        search_results = search_data.get("query", {}).get("search", [])
        
        if not search_results:
            return None
            
        # Get top result title
        title = search_results[0]["title"]
        
        # Get page summary
        summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(title)}"
        r_summary = httpx.get(summary_url, headers=DEFAULT_HEADERS, timeout=5.0)
        r_summary.raise_for_status()
        summary_data = r_summary.json()
        summary_text = summary_data.get("extract", "")
        
        if summary_text:
            db_manager.set_http_cache("wikipedia", query, summary_text)
            return summary_text
            
    except Exception as e:
        print(f"Wikipedia search failed for '{query}': {e}")
        
    return None

def fetch_arxiv_summary(query: str) -> Optional[str]:
    """Fetches abstract of the top arXiv paper matching query."""
    cached = db_manager.get_http_cache("arxiv", query)
    if cached:
        return cached

    arxiv_url = f"http://export.arxiv.org/api/query?search_query=all:{quote(query)}&max_results=1"
    try:
        r = httpx.get(arxiv_url, headers=DEFAULT_HEADERS, timeout=5.0)
        r.raise_for_status()
        root = ET.fromstring(r.text)
        
        # Find summary tag
        namespaces = {"atom": "http://www.w3.org/2005/Atom"}
        entry = root.find("atom:entry", namespaces)
        if entry is not None:
            summary = entry.find("atom:summary", namespaces)
            if summary is not None and summary.text:
                summary_text = summary.text.strip().replace("\n", " ")
                db_manager.set_http_cache("arxiv", query, summary_text)
                return summary_text
    except Exception as e:
        print(f"arXiv search failed for '{query}': {e}")
        
    return None

def fetch_ddg_summary(query: str) -> Optional[str]:
    """Fetches Instant Answer from DuckDuckGo."""
    cached = db_manager.get_http_cache("duckduckgo", query)
    if cached:
        return cached

    url = f"https://api.duckduckgo.com/?q={quote(query)}&format=json&no_html=1"
    try:
        r = httpx.get(url, headers=DEFAULT_HEADERS, timeout=5.0)
        r.raise_for_status()
        data = r.json()
        abstract = data.get("AbstractText", "")
        if abstract:
            db_manager.set_http_cache("duckduckgo", query, abstract)
            return abstract
    except Exception as e:
        print(f"DuckDuckGo search failed for '{query}': {e}")
        
    return None

def retrieve_target_knowledge(query: str) -> str:
    """
    Orchestrates target knowledge retrieval from Wiki -> arXiv -> DDG.
    Falls back to a structured mock summary if all requests fail (or offline).
    """
    # 1. Try Wikipedia
    wiki = fetch_wikipedia_summary(query)
    if wiki:
        return wiki
        
    # 2. Try arXiv
    arxiv = fetch_arxiv_summary(query)
    if arxiv:
        return arxiv
        
    # 3. Try DuckDuckGo
    ddg = fetch_ddg_summary(query)
    if ddg:
        return ddg
        
    # Fallback mock text if everything fails (prevents breaking the agent flow)
    mock_summaries = {
        "mycorrhizal networks": (
            "Mycorrhizal networks (also known as common mycorrhizal networks or CMN) are underground hyphal networks "
            "created by mycorrhizal fungi that connect individual plants together and transfer water, carbon, nitrogen, "
            "and other nutrients. They also transmit warning signals of insect attacks or shade among plants."
        ),
        "semiconductor manufacturing": (
            "Semiconductor manufacturing is the process of creating integrated circuits on silicon wafers. It involves "
            "repeated steps of photolithography, deposition, etching, and chemical-mechanical planarization to layer "
            "microscopic electronic structures."
        )
    }
    
    query_lower = query.lower()
    for key, text in mock_summaries.items():
        if key in query_lower:
            return text
            
    return f"Information about '{query}': A complex, structured system with specific rules, entities, and causal logic."
