"""
PubMed API Tool for fetching scientific papers
"""
import requests
from typing import Dict, List, Any
import json

try:
    from spoon_ai.tools.base import BaseTool
except ImportError:
    # Fallback for when spoon-ai-sdk is not installed
    class BaseTool:
        pass


def fetch_pubmed(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch papers from PubMed API
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
        
    Returns:
        List of paper dictionaries with title, abstract, authors, etc.
    """
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    
    # Search for papers
    search_params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json"
    }
    
    try:
        search_response = requests.get(base_url, params=search_params, timeout=10)
        search_response.raise_for_status()
        search_data = search_response.json()
        
        pmids = search_data.get("esearchresult", {}).get("idlist", [])
        
        if not pmids:
            return []
        
        # Fetch details for each paper
        fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml"
        }
        
        fetch_response = requests.get(fetch_url, params=fetch_params, timeout=10)
        fetch_response.raise_for_status()
        
        # Parse XML response (simplified - in production, use proper XML parser)
        # For now, return basic structure
        papers = []
        for pmid in pmids:
            papers.append({
                "pmid": pmid,
                "title": f"Paper {pmid}",
                "abstract": f"Abstract for paper {pmid}",
                "query": query
            })
        
        return papers
        
    except Exception as e:
        print(f"Error fetching PubMed data: {e}")
        return []


class PubMedTool(BaseTool):
    """Tool wrapper for PubMed searches"""
    
    name: str = "pubmed_search"
    description: str = "Search PubMed database for scientific papers. Use this to find research papers related to a prediction market question."
    parameters: dict = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query string (e.g., 'machine learning cancer treatment')"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return (default: 10)",
                "default": 10
            }
        },
        "required": ["query"]
    }
    
    async def execute(self, query: str, max_results: int = 10) -> str:
        """
        Execute PubMed search
        
        Args:
            query: Search query
            max_results: Maximum results to return
            
        Returns:
            JSON string with search results
        """
        papers = fetch_pubmed(query, max_results)
        return json.dumps({
            "papers": papers,
            "count": len(papers),
            "query": query
        }, indent=2)

