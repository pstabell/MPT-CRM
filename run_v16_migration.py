#!/usr/bin/env python3
"""
Run the v16 project stop/void migration
"""

import os
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from supabase import create_client

def main():
    """Run the migration"""
    load_dotenv()
    
    # Get database connection
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_key:
        print("Missing Supabase credentials in .env file")
        return False
    
    try:
        supabase = create_client(supabase_url, supabase_key)
        
        # Read the migration SQL
        migration_path = Path(__file__).parent / "database" / "schema_update_v16_project_stop_void.sql"
        with open(migration_path, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        print("Running migration: schema_update_v16_project_stop_void.sql")
        
        # Execute the migration
        # Note: Supabase client doesn't have a direct SQL execution method for DDL
        # We'll need to run this through the Supabase dashboard or use the REST API
        print("This migration needs to be run manually in the Supabase SQL editor.")
        print("Copy the following SQL and run it in your Supabase dashboard:")
        print("\n" + "="*60)
        print(migration_sql)
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)