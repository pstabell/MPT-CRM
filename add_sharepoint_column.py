#!/usr/bin/env python3
"""
Add sharepoint_folder_url column to contacts table
"""
import os
from dotenv import load_dotenv
from supabase import create_client

def add_sharepoint_column():
    # Load environment variables
    load_dotenv()
    
    # Get Supabase credentials
    url = os.getenv("SUPABASE_URL_CRM") or os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY_CRM") or os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        print("❌ Missing Supabase credentials in .env file")
        print("Need: SUPABASE_URL and SUPABASE_ANON_KEY")
        return False
    
    try:
        # Create Supabase client
        supabase = create_client(url, key)
        
        # Check if column already exists by trying to select it
        try:
            result = supabase.table("contacts").select("sharepoint_folder_url").limit(1).execute()
            print("✅ Column sharepoint_folder_url already exists in contacts table")
            return True
        except Exception:
            # Column doesn't exist, need to add it
            pass
        
        # Execute SQL to add the column
        sql_query = """
        ALTER TABLE contacts 
        ADD COLUMN sharepoint_folder_url TEXT;
        """
        
        # Note: Supabase Python client doesn't have direct SQL execution
        # This would need to be run through the Supabase dashboard or PostgREST API
        print("⚠️  Column needs to be added manually via Supabase dashboard")
        print("SQL to run:")
        print(sql_query)
        print("\nSteps:")
        print("1. Go to Supabase dashboard")
        print("2. Navigate to SQL Editor")
        print("3. Run the SQL command above")
        
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    add_sharepoint_column()