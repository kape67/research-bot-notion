import os
import notion_client
from typing import List, Optional

class NotionManager:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("NOTION_API_KEY")
        if not self.api_key:
            raise ValueError("NOTION_API_KEY is not set in environment or provided.")
        self.client = notion_client.Client(auth=self.api_key)

    def ensure_database(self, target_id: str) -> str:
        """
        Ensures a database exists. If target_id is a Page, creates a database inside it.
        Returns the Database ID to use.
        """
        try:
            obj = self.client.blocks.retrieve(target_id)
            if obj["object"] == "page" or (obj["object"] == "block" and obj["type"] == "child_page"):
                # Check if "Research Papers" database already exists as a child
                children = self.client.blocks.children.list(block_id=target_id).get("results", [])
                for child in children:
                    if child["type"] == "child_database":
                        # We need to retrieve the database to check the title
                        try:
                            db = self.client.databases.retrieve(child["id"])
                            if db.get("archived"):
                                continue
                            # Validate schema: checks if "Category" property exists
                            if "Category" not in db["properties"]:
                                print(f"Skipping incomplete database: {db['id']}")
                                continue
                                
                            if db["title"] and db["title"][0]["plain_text"] == "Research Papers":
                                print(f"Found existing valid 'Research Papers' database: {db['id']}")
                                return db['id']
                        except:
                            pass

                # If not found, create it
                print(f"Creating a new Database 'Research Papers' inside page {target_id}...")
                
                # 1. Create with minimal properties (just Name/Title)
                new_db = self.client.databases.create(
                    parent={"type": "page_id", "page_id": target_id},
                    title=[{"type": "text", "text": {"content": "Research Papers"}}],
                    properties={
                        "Name": {"title": {}}
                    }
                )
                print(f"Created base Database: {new_db['id']}")
                
                # 2. Update to add other properties
                # This ensures we don't fail silently on creation
                try:
                    self.client.databases.update(
                        database_id=new_db['id'],
                        properties={
                            "Link": {"url": {}},
                            "Summary": {"rich_text": {}},
                            "Category": {"multi_select": {}}
                        }
                    )
                    print("Successfully added properties to database.")
                except Exception as e:
                    print(f"Error adding properties to DB: {e}")
                    # Try to continue, maybe some worked?
                
                return new_db['id']
            else:
                return target_id
        except Exception as e:
            # If retrieve fails, it might be a database ID
            try:
                self.client.databases.retrieve(target_id)
                return target_id
            except:
                print(f"Could not resolve ID {target_id}. Assuming it is a Database ID.")
                return target_id
    
    def create_database(self, parent_page_id: str, title: str) -> str:
        """
        Create a new database inside a page with the given title.
        Returns the data source ID.
        """
        print(f"Creating new database '{title}' in page {parent_page_id}...")
        
        try:
            # Create database
            new_db = self.client.databases.create(
                parent={"type": "page_id", "page_id": parent_page_id},
                title=[{"type": "text", "text": {"content": title}}],
                properties={
                    "Name": {"title": {}}
                }
            )
            
            db_id = new_db['id']
            print(f"  Created database: {db_id}")
            
            # Get data source ID
            data_source_id = new_db['data_sources'][0]['id']
            print(f"  Data source ID: {data_source_id}")
            
            # Add properties to data source
            try:
                self.client.data_sources.update(
                    data_source_id=data_source_id,
                    properties={
                        "Keyword": {"multi_select": {}},
                        "Publisher & Year": {"rich_text": {}},
                        "Link": {"url": {}},
                        "Summary(한글)": {"rich_text": {}},
                        "Generated By": {"rich_text": {}},  # LLM model tracking
                        "Source": {"rich_text": {}}  # Search engine source
                    }
                )
                print(f"  ✓ Properties added to data source")
            except Exception as e:
                print(f"  Warning: Could not add properties: {e}")
            
            return data_source_id
            
        except Exception as e:
            print(f"Error creating database: {e}")
            raise


    def add_paper(self, database_id: str, title: str, short_summary_kr: str, link: str, 
                  keywords: List[str], publisher_year: str, 
                  detailed_summary_kr: str = "", architecture_desc: str = "", llm_model: str = "none", source: str = "Unknown"):
        """
        Adds a new paper entry to the Notion database with page content.
        """
        if not database_id:
             raise ValueError("Database ID is required.")
        
        # Ensure we have a database ID, not a page ID
        real_db_id = self.ensure_database(database_id)

        properties = {
            "Name": {
                "title": [
                    {
                        "text": {
                            "content": title
                        }
                    }
                ]
            },
            "Link": {
                "url": link if link else None
            },
            "Summary(한글)": {
                "rich_text": [
                    {
                        "text": {
                            "content": short_summary_kr[:2000]
                        }
                    }
                ]
            },
            "Keyword": {
                "multi_select": [{"name": kw} for kw in keywords]
            },
            "Publisher & Year": {
                "rich_text": [
                    {
                        "text": {
                            "content": publisher_year
                        }
                    }
                ]
            },
            "Generated By": {
                "rich_text": [
                    {
                        "text": {
                            "content": llm_model
                        }
                    }
                ]
            },
            "Source": {
                "rich_text": [
                    {
                        "text": {
                            "content": source
                        }
                    }
                ]
            }
        }

        try:
            page = self.client.pages.create(
                parent={"data_source_id": real_db_id},
                properties=properties
            )
            print(f"Successfully added paper: {title}")
            
            # Add page content blocks
            if detailed_summary_kr or architecture_desc:
                self.add_page_content(page["id"], detailed_summary_kr, architecture_desc)
            
        except Exception as e:
            print(f"Error adding paper to Notion: {e}")
            raise
    
    def add_page_content(self, page_id: str, detailed_summary: str, architecture: str):
        """Add content blocks to a page"""
        try:
            children = []
            
            if detailed_summary:
                children.extend([
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{"type": "text", "text": {"content": "📝 상세 요약"}}]
                        }
                    },
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": detailed_summary[:2000]}}]
                        }
                    }
                ])
            
            if architecture:
                children.extend([
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{"type": "text", "text": {"content": "🏗️ Architecture"}}]
                        }
                    },
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": architecture[:2000]}}]
                        }
                    }
                ])
            
            if children:
                self.client.blocks.children.append(block_id=page_id, children=children)
                print(f"  ✓ Added page content")
                
        except Exception as e:
            print(f"  Warning: Could not add page content: {e}")
