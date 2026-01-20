import argparse
import os
import sys
from datetime import datetime
from multi_source_search import search_all_sources
from notion_client_wrapper import NotionManager
from llm_translator import GeminiTranslator

def main():
    parser = argparse.ArgumentParser(description="Search papers from multiple sources and save to Notion.")
    parser.add_argument("--query", type=str, required=True, help="Search query for papers")
    parser.add_argument("--limit", type=int, default=20, help="Number of papers to fetch")
    
    args = parser.parse_args()
    
    # Use NOTION_PAGE_ID (parent page where databases will be created)
    notion_page_id = os.environ.get("NOTION_PAGE_ID") or os.environ.get("NOTION_DB_ID")
    if not notion_page_id:
        print("Error: NOTION_PAGE_ID not found in environment variables.")
        print("Please set: export NOTION_PAGE_ID='your_notion_page_id'")
        sys.exit(1)
        
    manager = NotionManager()
    
    # Initialize Gemini translator
    try:
        translator = GeminiTranslator()
        print("✓ Gemini translator initialized")
    except Exception as e:
        print(f"Warning: Could not initialize Gemini translator: {e}")
        print("Korean summaries will be unavailable.")
        translator = None
    
    # Create database for this query
    today = datetime.now().strftime("%Y-%m-%d")
    db_title = f"{args.query} - {today}"
    
    try:
        data_source_id = manager.create_database(notion_page_id, db_title)
    except Exception as e:
        print(f"Failed to create database: {e}")
        sys.exit(1)
    
    # Search papers from all sources
    print(f"\n{'='*60}")
    print(f"Query: {args.query}")
    print(f"{'='*60}\n")
    
    papers = search_all_sources(args.query, max_results=args.limit)
    
    if not papers:
        print("No papers found.")
        return

    print(f"\n📋 Found {len(papers)} papers:\n")
    for idx, paper in enumerate(papers):
        source_emoji = "📄" if paper.get("source") == "Semantic Scholar" else "📑"
        print(f"{idx+1}. {source_emoji} {paper['title']}")
        print(f"   Publisher: {paper.get('publisher', 'Unknown')} ({paper.get('year', 'N/A')})")
        if paper.get('link'):
            print(f"   Link: {paper['link'][:50]}...")
        print("-" * 60)
        
    print(f"\n📋 Found {len(papers)} papers. Saving all of them...\n")
    
    # Batch process summaries if translator available
    summaries = []
    used_model = "none"
    if translator:
        print(f"  📝 Generating Korean summaries for {len(papers)} papers (Batch mode)...")
        try:
            papers_data = [
                {
                    'title': p['title'],
                    'abstract': p.get('summary', ''),
                    'authors': p.get('authors', [])
                }
                for p in papers
            ]
            summaries, used_model = translator.analyze_papers_batch(papers_data)
            print(f"  ✅ All summaries generated using {used_model}!")
        except Exception as e:
            print(f"  ⚠️  Batch summary failed: {e}")
            # Fallback to empty summaries
            summaries = [{"short_summary": "요약 없음", "detailed_summary": "", "architecture": ""} for _ in papers]
    else:
        summaries = [{"short_summary": "요약 없음", "detailed_summary": "", "architecture": ""} for _ in papers]
    
    # Save papers to Notion
    for i, p in enumerate(papers):
        print(f"\n{'='*60}")
        print(f"Processing {i+1}/{len(papers)}: {p['title']}")
        print(f"{'='*60}")
        
        # Get pre-generated summary
        summary = summaries[i] if i < len(summaries) else {"short_summary": "요약 없음", "detailed_summary": "", "architecture": ""}
        short_summary_kr = summary.get("short_summary", "요약 없음")
        detailed_summary_kr = summary.get("detailed_summary", "")
        architecture_desc = summary.get("architecture", "")
            
        # Prepare data
        keywords = p.get('categories', [])
        if not keywords and p.get('publisher'):
            keywords = [p['publisher']]
            
        publisher_year = f"{p.get('publisher', 'Unknown')} ({p.get('year', 'N/A')})"
        
        print(f"  💾 Saving to Notion...")
        try:
            manager.add_paper(
                database_id=data_source_id,
                title=p['title'],
                short_summary_kr=short_summary_kr,
                link=p.get('link', ''),
                keywords=keywords,
                publisher_year=publisher_year,
                detailed_summary_kr=detailed_summary_kr,
                architecture_desc=architecture_desc,
                llm_model=used_model,
                source=p.get('source', 'Unknown')
            )
        except Exception as e:
            print(f"  ❌ Failed to save: {e}")
            continue
    
    print(f"\n🎉 Completed! {len(papers)} papers saved to database: '{db_title}'")

if __name__ == "__main__":
    main()
