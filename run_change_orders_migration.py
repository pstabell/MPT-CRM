"""
Run the change_orders table migration
"""
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def run_migration():
    # Get Supabase connection
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        print("ERROR: Missing Supabase credentials")
        return False
    
    supabase = create_client(url, key)
    
    # Read the schema file
    schema_file = "database/schema_update_v15_change_orders.sql"
    with open(schema_file, 'r') as f:
        sql_content = f.read()
    
    try:
        # Execute the SQL
        print("Creating change_orders table...")
        result = supabase.rpc('exec_sql', {'sql': sql_content}).execute()
        print("✅ Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False

if __name__ == "__main__":
    run_migration()