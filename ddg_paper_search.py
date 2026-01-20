from duckduckgo_search import DDGS
from typing import List, Dict
import re
import time

class DuckDuckGoSearch:
    """DuckDuckGo search wrapper for finding research papers"""
    
    def __init__(self):
        self.ddgs = DDGS()
    
    def search_papers(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Search for research papers using DuckDuckGo
        Returns list of paper info dicts
        """
        papers = []
        
        # Enhance query to focus on academic papers
        search_query = f"{query} research paper pdf"
        
        try:
            # Search with DuckDuckGo
            results = self.ddgs.text(
                keywords=search_query,
                max_results=max_results * 3  # Get more results to filter
            )
            
            for result in results:
                # Filter for academic-looking results
                if not self._is_academic_result(result):
                    continue
                
                # Extract paper information
                paper_info = self._extract_paper_info(result)
                if paper_info:
                    papers.append(paper_info)
                
                # Stop if we have enough papers
                if len(papers) >= max_results:
                    break
            
            # Small delay to be respectful to the service
            time.sleep(0.5)
            
        except Exception as e:
            print(f"  ⚠️  DuckDuckGo search error: {e}")
        
        return papers
    
    def _is_academic_result(self, result: Dict) -> bool:
        """Check if result looks like an academic paper"""
        url = result.get('href', '').lower()
        title = result.get('title', '').lower()
        
        # Prioritize academic domains
        academic_domains = [
            'arxiv.org',
            'doi.org',
            'scholar.google',
            'researchgate.net',
            'semanticscholar.org',
            'ieee.org',
            'acm.org',
            'springer.com',
            'sciencedirect.com',
            'nature.com',
            'plos.org',
            'biorxiv.org',
            'medrxiv.org',
            'openreview.net',
            'proceedings.mlr.press',
            'jmlr.org',
            'neurips.cc',
            'aclweb.org',
            'cvf.com'
        ]
        
        # Check if URL contains academic domains or PDF
        for domain in academic_domains:
            if domain in url:
                return True
        
        # Check for PDF links
        if '.pdf' in url or 'pdf' in url:
            return True
        
        # Check for academic keywords in title
        academic_keywords = ['paper', 'research', 'study', 'analysis', 'conference', 'journal']
        if any(keyword in title for keyword in academic_keywords):
            return True
        
        return False
    
    def _extract_paper_info(self, result: Dict) -> Dict:
        """Extract paper information from search result"""
        title = result.get('title', 'Unknown Title')
        body = result.get('body', '')
        url = result.get('href', '')
        
        # Try to extract year from title or body
        year = self._extract_year(title + ' ' + body)
        
        # Try to extract authors (basic heuristic)
        authors = self._extract_authors(body)
        
        # Determine publisher from URL or body
        publisher = self._extract_publisher(url, body)
        
        paper_info = {
            "title": title,
            "summary": body[:500] if body else "No summary available",  # Limit summary length
            "authors": authors,
            "year": year,
            "publisher": publisher,
            "categories": ["Web Search"],
            "link": url,
            "source": "DuckDuckGo"
        }
        
        return paper_info
    
    def _extract_year(self, text: str) -> str:
        """Extract publication year from text"""
        # Look for 4-digit years between 1990 and 2030
        year_pattern = r'\b(19[9]\d|20[0-3]\d)\b'
        matches = re.findall(year_pattern, text)
        
        if matches:
            # Return the most recent year found
            return max(matches)
        
        return "Unknown"
    
    def _extract_authors(self, text: str) -> List[str]:
        """Extract author names from text (basic heuristic)"""
        # This is a simple heuristic - look for patterns like "by Author Name"
        # In practice, this is difficult without structured data
        authors = []
        
        # Look for "by [Name]" pattern
        by_pattern = r'by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        matches = re.findall(by_pattern, text)
        
        if matches:
            authors = matches[:3]  # Limit to first 3 authors
        
        return authors if authors else ["Unknown"]
    
    def _extract_publisher(self, url: str, body: str) -> str:
        """Extract publisher/venue from URL or body"""
        url_lower = url.lower()
        
        # Map domains to publishers
        publisher_map = {
            'arxiv.org': 'arXiv',
            'ieee.org': 'IEEE',
            'acm.org': 'ACM',
            'springer.com': 'Springer',
            'sciencedirect.com': 'ScienceDirect',
            'nature.com': 'Nature',
            'researchgate.net': 'ResearchGate',
            'semanticscholar.org': 'Semantic Scholar',
            'openreview.net': 'OpenReview',
            'neurips.cc': 'NeurIPS',
            'proceedings.mlr.press': 'PMLR',
            'cvf.com': 'CVF'
        }
        
        for domain, publisher in publisher_map.items():
            if domain in url_lower:
                return publisher
        
        # Look for conference/journal names in body
        venue_keywords = ['conference', 'proceedings', 'journal', 'symposium', 'workshop']
        for keyword in venue_keywords:
            if keyword in body.lower():
                # Try to extract the venue name (simplified)
                pattern = rf'(\w+\s+{keyword})'
                match = re.search(pattern, body, re.IGNORECASE)
                if match:
                    return match.group(1)
        
        return "Web"
