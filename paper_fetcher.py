import arxiv
from typing import List, Dict, Any

def search_arxiv_papers(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Searches arXiv for papers matching the query.

    Args:
        query: Search query string.
        max_results: Maximum number of papers to return.

    Returns:
        List of dictionaries containing paper metadata.
    """
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance
    )

    papers = []
    client = arxiv.Client()
    
    for result in client.results(search):
        # Format summary to be brief? User asked for "contribution" only.
        # It's hard to auto-extract only contribution from abstract, but we can shorten it or provide full.
        # We will use the full abstract but truncate if super long, or let Notion display it.
        # The user wanted "Link" -> preferably PDF link or Abstract Page.
        
        paper_info = {
            "title": result.title,
            "summary": result.summary.replace("\n", " "), # Remove newlines in abstract
            "link": result.pdf_url,
            "authors": [author.name for author in result.authors],
            "published": result.published.strftime("%Y-%m-%d"),
            "year": result.published.year,
            "publisher": result.primary_category,  # arXiv category as publisher
            "categories": [result.primary_category] # arXiv categories (e.g. cs.CV)
        }
        papers.append(paper_info)
    
    return papers
