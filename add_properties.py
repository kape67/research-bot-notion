import os
import notion_client

api_key = os.environ.get("NOTION_API_KEY")
client = notion_client.Client(auth=api_key)

# Use the database
db_id = "8c802dc2-6519-4a38-a485-fe52c7b6175f"

db = client.databases.retrieve(db_id)
data_source_id = db['data_sources'][0]['id']

print(f"Updating data source {data_source_id}...")

try:
    updated = client.data_sources.update(
        data_source_id=data_source_id,
        properties={
            "Link": {"url": {}},
            "Summary": {"rich_text": {}},
            "Category": {"multi_select": {}}
        }
    )
    
    print("✅ Properties added!")
    print("All properties:")
    for prop_name, prop_data in updated.get('properties', {}).items():
        print(f"  ✓ {prop_name}: {prop_data['type']}")
        
    print(f"\n🎉 SUCCESS! Use this data source ID:")
    print(f"export NOTION_DB_ID=\"{data_source_id}\"")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
