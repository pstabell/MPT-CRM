"""
SMS Migration Script - Apply v18 schema update for SMS messaging
================================================================

Run this to add the sms_messages table and related functions to Supabase.
"""

import os
from dotenv import load_dotenv
from supabase import create_client

def run_sms_migration():
    """Apply the SMS messages schema update to Supabase."""
    load_dotenv()
    
    # Get Supabase connection
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY") 
    
    if not url or not key:
        print("[ERROR] Missing SUPABASE_URL or SUPABASE_ANON_KEY in .env")
        return False
    
    try:
        # Create Supabase client
        supabase = create_client(url, key)
        print(f"[OK] Connected to Supabase: {url}")
        
        # Read the migration SQL
        migration_file = "database/schema_update_v18_sms_messages.sql"
        if not os.path.exists(migration_file):
            print(f"[ERROR] Migration file not found: {migration_file}")
            return False
            
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        print(f"[INFO] Loaded migration SQL ({len(migration_sql)} chars)")
        
        # Execute the migration
        print("[INFO] Applying SMS migration...")
        
        # Split SQL by semicolon and execute each statement
        statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
        
        for i, statement in enumerate(statements):
            if statement and not statement.startswith('--'):
                try:
                    # Use rpc to execute raw SQL
                    result = supabase.rpc('exec_sql', {'sql': statement}).execute()
                    print(f"  [OK] Statement {i+1}/{len(statements)} executed")
                except Exception as e:
                    # Some statements might fail if they already exist - that's OK
                    print(f"  [WARN] Statement {i+1} error (might be OK): {str(e)}")
        
        print("[SUCCESS] SMS migration completed!")
        
        # Test the table exists by trying to select from it
        try:
            result = supabase.table('sms_messages').select('id').limit(1).execute()
            print("[OK] sms_messages table verified - ready for SMS features!")
            return True
        except Exception as e:
            print(f"[WARN] Could not verify table (might need manual setup): {e}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        return False

if __name__ == "__main__":
    print("=== SMS Migration for MPT-CRM ===")
    success = run_sms_migration()
    if success:
        print("\n[NEXT] Next steps:")
        print("1. Update db_service.py with SMS functions")
        print("2. Add SMS UI to Contact page")  
        print("3. Setup Twilio webhook handler")
        print("4. Test send/receive end-to-end")
    else:
        print("\n[ERROR] Migration failed - check errors above")