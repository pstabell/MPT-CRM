#!/usr/bin/env python3
"""Create a test deal for Roger to test SharePoint integration."""

import sys
import os
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_service import db_create_deal, db_get_contact

def main():
    # Roger's contact ID from the previous check
    roger_id = "e8652795-4e75-4ca0-9142-81f28a5d24f0"
    
    # Verify Roger exists
    roger = db_get_contact(roger_id)
    if not roger:
        print(f"[ERROR] Could not find Roger's contact: {roger_id}")
        return
    
    print(f"[OK] Found Roger: {roger.get('first_name', '')} {roger.get('last_name', '')} ({roger.get('company', '')})")
    print(f"SharePoint URL: {roger.get('sharepoint_folder_url', 'None')}")
    
    # Create a test deal for Roger
    deal_data = {
        "title": "Vantage PTE SharePoint Test Deal",
        "contact_name": f"{roger.get('first_name', '')} {roger.get('last_name', '')}".strip(),
        "company_name": roger.get('company', ''),
        "contact_id": roger_id,
        "source": "Test",
        "value": 10000,
        "priority": "medium",
        "expected_close": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
        "stage": "proposal",  # Start at proposal so we can test moving to won
        "description": "Test deal created to test SharePoint folder automation when marked as won.",
        "days_in_stage": 1,
        "labels": ["test", "sharepoint"]
    }
    
    print(f"\n[ACTION] Creating test deal...")
    result = db_create_deal(deal_data)
    
    if result:
        print(f"[OK] Test deal created successfully!")
        print(f"Deal ID: {result.get('id')}")
        print(f"Title: {result.get('title')}")
        print(f"Stage: {result.get('stage')}")
        print(f"Contact: {result.get('contact_name')} ({result.get('company_name')})")
        print(f"\nThis deal is now ready for testing the 'won' workflow.")
        return result
    else:
        print(f"[ERROR] Failed to create test deal")
        return None

if __name__ == "__main__":
    main()