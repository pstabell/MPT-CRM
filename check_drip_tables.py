"""
Check if drip campaign tables exist in the database
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_service import get_db

def check_drip_tables():
    print("Checking drip campaign database tables...")
    
    db = get_db()
    if not db:
        print("ERROR: Database connection failed")
        return False
    
    # Check if drip_campaign_templates table exists
    try:
        response = db.table("drip_campaign_templates").select("*").limit(1).execute()
        print(f"drip_campaign_templates table: EXISTS ({len(response.data)} records)")
        
        # List existing templates
        all_templates = db.table("drip_campaign_templates").select("campaign_id, name").execute()
        if all_templates.data:
            print("Existing templates:")
            for template in all_templates.data:
                print(f"  - {template['campaign_id']}: {template['name']}")
        else:
            print("No templates found in database")
        
    except Exception as e:
        print(f"drip_campaign_templates table: ERROR - {e}")
        return False
    
    # Check if campaign_enrollments table exists
    try:
        response = db.table("campaign_enrollments").select("*").limit(1).execute()
        print(f"campaign_enrollments table: EXISTS ({len(response.data)} records)")
    except Exception as e:
        print(f"campaign_enrollments table: ERROR - {e}")
        return False
    
    return True

if __name__ == "__main__":
    check_drip_tables()