from paper_fetcher import search_arxiv_papers
from semantic_scholar import SemanticScholarSearch
from ddg_paper_search import DuckDuckGoSearch
from typing import List, Dict, Union

def search_all_sources(query: Union[str, Dict[str, str]], max_results: int = 10) -> List[Dict]:
    """
    Search papers from multiple sources and merge results
    
    Args:
        query: Either a string (same query for all) or dict with keys:
               {'semantic_scholar': '...', 'arxiv': '...', 'duckduckgo': '...'}
        max_results: Maximum number of results to return
    """
    all_papers = []
    seen_titles = set()
    
    # Handle both string and dict queries
    if isinstance(query, str):
        queries = {
            'semantic_scholar': query,
            'arxiv': query,
            'duckduckgo': query
        }
    else:
        queries = query
    
    # Search Semantic Scholar first (broader coverage)
    print(f"🔍 Searching Semantic Scholar...")
    print(f"  Query: {queries.get('semantic_scholar', queries.get('arxiv', ''))}")
    ss_search = SemanticScholarSearch()
    ss_papers = ss_search.search_papers(queries.get('semantic_scholar', ''), max_results=max_results)
    
    for paper in ss_papers:
        title_lower = paper["title"].lower()
        if title_lower not in seen_titles:
            seen_titles.add(title_lower)
            all_papers.append(paper)
    
    print(f"  Found {len(ss_papers)} papers from Semantic Scholar")
    
    # Search arXiv
    print(f"🔍 Searching arXiv...")
    print(f"  Query: {queries.get('arxiv', '')}")
    arxiv_papers = search_arxiv_papers(queries.get('arxiv', ''), max_results=max_results)
    
    for paper in arxiv_papers:
        title_lower = paper["title"].lower()
        if title_lower not in seen_titles:
            seen_titles.add(title_lower)
            all_papers.append(paper)
    
    print(f"  Found {len(arxiv_papers)} papers from arXiv")
    
    # Search DuckDuckGo
    print(f"🔍 Searching DuckDuckGo...")
    print(f"  Query: {queries.get('duckduckgo', '')}")
    ddg_search = DuckDuckGoSearch()
    ddg_papers = ddg_search.search_papers(queries.get('duckduckgo', ''), max_results=max_results)
    
    for paper in ddg_papers:
        title_lower = paper["title"].lower()
        if title_lower not in seen_titles:
            seen_titles.add(title_lower)
            all_papers.append(paper)
    
    print(f"  Found {len(ddg_papers)} papers from DuckDuckGo")
    print(f"📚 Total unique papers: {len(all_papers)}")
    
    return all_papers[:max_results]  # Limit to requested number
