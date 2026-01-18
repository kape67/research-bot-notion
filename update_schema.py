import os
import notion_client

api_key = os.environ.get("NOTION_API_KEY")
client = notion_client.Client(auth=api_key)

data_source_id = "8e7716b9302f40faa13cac4da23e45ca"

print("Updating Data Source properties...")

try:
    # First, remove old properties and add new ones
    updated = client.data_sources.update(
        data_source_id=data_source_id,
        properties={
            # Keep Name (it's the title, can't be removed)
            "Keyword": {"multi_select": {}},
            "Publisher & Year": {"rich_text": {}},
            "Link": {"url": {}},
            "Summary(한글)": {"rich_text": {}},
            "Architecture & Figures": {"rich_text": {}}
        }
    )
    
    print("✅ Properties updated!")
    print("New schema:")
    for prop_name, prop_data in updated.get('properties', {}).items():
        print(f"  ✓ {prop_name}: {prop_data['type']}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
