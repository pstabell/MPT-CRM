#!/usr/bin/env python3
"""
E-Signature Documents Table Migration Script
============================================

Creates the esign_documents table in Supabase for the e-signature workflow.
"""

import os
from supabase import create_client

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def run_migration():
    """Run the e-signature documents table migration"""
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_key:
        print("ERROR: Missing Supabase credentials. Check .env file.")
        return False
    
    try:
        # Initialize Supabase client
        supabase = create_client(supabase_url, supabase_key)
        
        # Read SQL migration file
        with open("create_esign_documents_table.sql", "r") as f:
            migration_sql = f.read()
        
        print("Running e-signature documents table migration...")
        
        # Execute migration
        result = supabase.rpc('exec_sql', {'sql': migration_sql}).execute()
        
        if result.data:
            print("SUCCESS: E-signature documents table created successfully!")
            print("Table includes:")
            print("   - Document metadata and status tracking")
            print("   - Secure signing tokens")
            print("   - Audit trail logging")
            print("   - Legal compliance features")
            return True
        else:
            print("WARNING: Migration may have run, but no data returned")
            return True
            
    except Exception as e:
        print(f"ERROR: Migration failed: {e}")
        if "already exists" in str(e):
            print("INFO: Table may already exist - this is OK")
            return True
        return False

if __name__ == "__main__":
    success = run_migration()
    if success:
        print("\nReady to build e-signature workflow!")
    else:
        print("\nMigration failed. Check error messages above.")