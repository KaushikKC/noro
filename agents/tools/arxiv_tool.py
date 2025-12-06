"""
arXiv API Tool for fetching scientific papers
"""
import requests
import feedparser
from typing import Dict, List, Any
import json

try:
    from spoon_ai.tools.base import BaseTool
except ImportError:
    # Fallback for when spoon-ai-sdk is not installed
    class BaseTool:
        pass


def fetch_arxiv(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch papers from arXiv API
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
        
    Returns:
        List of paper dictionaries with title, abstract, authors, etc.
    """
    base_url = "http://export.arxiv.org/api/query"
    
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending"
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        
        # Parse Atom feed
        feed = feedparser.parse(response.content)
        
        papers = []
        for entry in feed.entries[:max_results]:
            papers.append({
                "id": entry.id.split("/")[-1],
                "title": entry.title,
                "summary": entry.summary,
                "authors": [author.name for author in entry.authors],
                "published": entry.published,
                "link": entry.link,
                "query": query
            })
        
        return papers
        
    except Exception as e:
        print(f"Error fetching arXiv data: {e}")
        return []


class ArxivTool(BaseTool):
    """Tool wrapper for arXiv searches"""
    
    name: str = "arxiv_search"
    description: str = "Search arXiv database for scientific papers and preprints. Use this to find recent research papers related to a prediction market question."
    parameters: dict = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query string (e.g., 'all:machine learning AND all:cancer')"
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
        Execute arXiv search
        
        Args:
            query: Search query
            max_results: Maximum results to return
            
        Returns:
            JSON string with search results
        """
        papers = fetch_arxiv(query, max_results)
        return json.dumps({
            "papers": papers,
            "count": len(papers),
            "query": query
        }, indent=2)

