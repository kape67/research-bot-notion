import requests
from typing import List, Dict, Optional

class SemanticScholarSearch:
    """Semantic Scholar API wrapper for paper search"""
    
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    
    def __init__(self, api_key=None):
        import os
        self.api_key = api_key or os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
        
        self.session = requests.Session()
        # Add User-Agent and API Key if available
        headers = {
            "User-Agent": "PaperBot/1.0 (mailto:user@example.com)"
        }
        if self.api_key:
            headers["x-api-key"] = self.api_key
            print("  ✅ Using Semantic Scholar API Key")
        
        self.session.headers.update(headers)
        
    def search_papers(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Search papers using Semantic Scholar API
        Returns list of paper info dicts
        """
        papers = []
        
        # Search endpoint
        url = f"{self.BASE_URL}/paper/search"
        params = {
            "query": query,
            "limit": max_results,
            "fields": "title,authors,year,abstract,venue,publicationVenue,externalIds,openAccessPdf,citationCount"
        }
        
        import time
        for attempt in range(3):
            try:
                response = self.session.get(url, params=params, timeout=10)
                if response.status_code == 429:
                    print(f"  ⚠️  Semantic Scholar rate limit. Retrying in 2 seconds... (Attempt {attempt+1}/3)")
                    time.sleep(2)
                    continue
                
                response.raise_for_status()
                data = response.json()
                
                for item in data.get("data", []):
                    # Extract paper info
                    paper_info = {
                        "title": item.get("title", "Unknown Title"),
                        "summary": item.get("abstract", "No abstract available"),
                        "authors": [author.get("name", "") for author in item.get("authors", [])],
                        "year": item.get("year", "Unknown"),
                        "publisher": item.get("venue", "") or item.get("publicationVenue", {}).get("name", "Unknown"),
                        "categories": [],  # Semantic Scholar doesn't have categories like arXiv
                        "link": None,
                        "source": "Semantic Scholar",
                        "citation_count": item.get("citationCount", 0)
                    }
                    
                    # Get PDF link if available
                    if item.get("openAccessPdf"):
                        paper_info["link"] = item["openAccessPdf"].get("url")
                    elif item.get("externalIds", {}).get("ArXiv"):
                        arxiv_id = item["externalIds"]["ArXiv"]
                        paper_info["link"] = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
                    elif item.get("externalIds", {}).get("DOI"):
                        paper_info["link"] = f"https://doi.org/{item['externalIds']['DOI']}"
                    
                    # Add venue as category if available
                    if paper_info["publisher"] and paper_info["publisher"] != "Unknown":
                        paper_info["categories"] = [paper_info["publisher"]]
                    
                    papers.append(paper_info)
                
                break # Success, exit retry loop
                    
            except Exception as e:
                print(f"Error searching Semantic Scholar: {e}")
                break
            
        return papers
