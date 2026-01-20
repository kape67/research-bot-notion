from paper_fetcher import search_arxiv_papers
from semantic_scholar import SemanticScholarSearch
from ddg_paper_search import DuckDuckGoSearch
from typing import List, Dict

def search_all_sources(query: str, max_results: int = 10) -> List[Dict]:
    """
    Search papers from multiple sources and merge results
    """
    all_papers = []
    seen_titles = set()
    
    # Search Semantic Scholar first (broader coverage)
    print(f"🔍 Searching Semantic Scholar...")
    ss_search = SemanticScholarSearch()
    ss_papers = ss_search.search_papers(query, max_results=max_results)
    
    for paper in ss_papers:
        title_lower = paper["title"].lower()
        if title_lower not in seen_titles:
            seen_titles.add(title_lower)
            all_papers.append(paper)
    
    print(f"  Found {len(ss_papers)} papers from Semantic Scholar")
    
    # Search arXiv
    print(f"🔍 Searching arXiv...")
    arxiv_papers = search_arxiv_papers(query, max_results=max_results)
    
    for paper in arxiv_papers:
        title_lower = paper["title"].lower()
        if title_lower not in seen_titles:
            seen_titles.add(title_lower)
            all_papers.append(paper)
    
    print(f"  Found {len(arxiv_papers)} papers from arXiv")
    
    # Search DuckDuckGo
    print(f"🔍 Searching DuckDuckGo...")
    ddg_search = DuckDuckGoSearch()
    ddg_papers = ddg_search.search_papers(query, max_results=max_results)
    
    for paper in ddg_papers:
        title_lower = paper["title"].lower()
        if title_lower not in seen_titles:
            seen_titles.add(title_lower)
            all_papers.append(paper)
    
    print(f"  Found {len(ddg_papers)} papers from DuckDuckGo")
    print(f"📚 Total unique papers: {len(all_papers)}")
    
    return all_papers[:max_results]  # Limit to requested number
