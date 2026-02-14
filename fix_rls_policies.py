"""
Fix RLS policies for drip campaign tables
Based on schema_update_v11_lead_drip.sql
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_service import get_db

def fix_rls_policies():
    print("Fixing RLS policies for drip campaign tables...")
    
    db = get_db()
    if not db:
        print("ERROR: Database connection failed")
        return False
    
    # SQL commands to fix RLS policies
    rls_fixes = [
        # Fix RLS for campaign_enrollments
        """
        CREATE POLICY IF NOT EXISTS "Allow anon insert on campaign_enrollments"
            ON campaign_enrollments
            FOR INSERT
            TO anon
            WITH CHECK (true);
        """,
        """
        CREATE POLICY IF NOT EXISTS "Allow anon select on campaign_enrollments"
            ON campaign_enrollments
            FOR SELECT
            TO anon
            USING (true);
        """,
        """
        CREATE POLICY IF NOT EXISTS "Allow anon update on campaign_enrollments"
            ON campaign_enrollments
            FOR UPDATE
            TO anon
            USING (true)
            WITH CHECK (true);
        """,
        # Fix RLS for drip_campaign_templates
        """
        CREATE POLICY IF NOT EXISTS "Allow anon select on drip_campaign_templates"
            ON drip_campaign_templates
            FOR SELECT
            TO anon
            USING (true);
        """,
        """
        CREATE POLICY IF NOT EXISTS "Allow anon insert on drip_campaign_templates"
            ON drip_campaign_templates
            FOR INSERT
            TO anon
            WITH CHECK (true);
        """
    ]
    
    success_count = 0
    for i, sql in enumerate(rls_fixes, 1):
        try:
            result = db.rpc("exec_sql", {"sql": sql.strip()}).execute()
            print(f"  [OK] RLS policy {i}")
            success_count += 1
        except Exception as e:
            print(f"  [ERROR] RLS policy {i}: {e}")
            # Try alternative method for RLS policies
            try:
                # Use direct SQL execution if available
                print(f"    Trying alternative method...")
                # Note: This might not work with standard Supabase client
                # We may need to run these manually in Supabase SQL editor
                pass
            except:
                pass
    
    print(f"\nFixed {success_count}/{len(rls_fixes)} RLS policies")
    
    if success_count < len(rls_fixes):
        print("\nNOTE: Some RLS policies may need to be created manually in Supabase SQL Editor:")
        print("1. Go to Supabase Dashboard > SQL Editor")
        print("2. Run the following SQL:")
        print("-" * 50)
        for sql in rls_fixes:
            print(sql.strip())
            print()
    
    return success_count == len(rls_fixes)

if __name__ == "__main__":
    success = fix_rls_policies()
    if success:
        print("[SUCCESS] All RLS policies fixed!")
    else:
        print("[PARTIAL] Some RLS policies may need manual creation")