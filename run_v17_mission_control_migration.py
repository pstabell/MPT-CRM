#!/usr/bin/env python3
"""
Run v17 Mission Control Integration Migration
=============================================

Adds mission_control_card_id fields to service_tickets and change_orders tables.
"""

import os
import sys
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_migration():
    """Run the Mission Control integration migration"""
    
    # Get Supabase credentials
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not url or not key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables")
        print("Check your .env file or environment variables")
        return False
    
    # Create Supabase client
    try:
        supabase: Client = create_client(url, key)
        print(f"✅ Connected to Supabase: {url}")
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        return False
    
    # Read migration file
    migration_file = Path(__file__).parent / "database" / "schema_update_v17_mission_control_integration.sql"
    
    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return False
    
    print(f"📄 Reading migration from: {migration_file}")
    
    try:
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
    except Exception as e:
        print(f"❌ Failed to read migration file: {e}")
        return False
    
    # Execute migration
    print("🚀 Executing migration...")
    
    try:
        # Execute the SQL - Note: Supabase Python client doesn't have direct SQL execution
        # You'll need to run this manually in Supabase SQL Editor
        print("⚠️  Manual execution required:")
        print("   1. Open Supabase SQL Editor")
        print("   2. Copy and paste the migration SQL")
        print("   3. Run the migration")
        print()
        print("Migration SQL:")
        print("=" * 50)
        print(sql_content)
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


if __name__ == "__main__":
    print("Mission Control Integration Migration v17")
    print("=" * 50)
    
    success = run_migration()
    
    if success:
        print("✅ Migration preparation complete")
        print("   Run the SQL manually in Supabase SQL Editor")
    else:
        print("❌ Migration preparation failed")
        sys.exit(1)