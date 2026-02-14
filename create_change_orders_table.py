"""
Create the change_orders table manually
"""
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def create_table():
    # Get Supabase connection
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        print("ERROR: Missing Supabase credentials")
        return False
    
    supabase = create_client(url, key)
    
    # Create table SQL
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS change_orders (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
        title VARCHAR(200) NOT NULL,
        description TEXT,
        status VARCHAR(50) NOT NULL DEFAULT 'draft',
        
        requested_by VARCHAR(200) NOT NULL,
        approved_by VARCHAR(200),
        requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        approved_at TIMESTAMP WITH TIME ZONE,
        
        estimated_hours DECIMAL(8, 2),
        actual_hours DECIMAL(8, 2),
        hourly_rate DECIMAL(8, 2) DEFAULT 150.00,
        total_amount DECIMAL(12, 2),
        
        impact_description TEXT,
        requires_client_approval BOOLEAN DEFAULT false,
        client_signature TEXT,
        
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    
    # Create indexes SQL
    indexes_sql = [
        "CREATE INDEX IF NOT EXISTS idx_change_orders_project_id ON change_orders(project_id);",
        "CREATE INDEX IF NOT EXISTS idx_change_orders_status ON change_orders(status);",
        "CREATE INDEX IF NOT EXISTS idx_change_orders_requested_at ON change_orders(requested_at);"
    ]
    
    try:
        # First, let's test if we can query the projects table to make sure connection works
        projects = supabase.table('projects').select('id').limit(1).execute()
        print("Connection to database successful")
        
        # Since we can't execute arbitrary SQL, we'll need to create this manually through the UI
        print("Note: This table needs to be created manually in Supabase SQL Editor")
        print("Copy the SQL from database/schema_update_v15_change_orders.sql")
        return True
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    create_table()