"""
Simple ROCK 5: Drip Campaign Infrastructure Test
=============================================
"""

import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_service import (
    db_is_connected, 
    db_get_drip_campaign_template, 
    send_email_via_sendgrid
)

def test_basic_infrastructure():
    print("ROCK 5 Drip Campaign Infrastructure Test")
    print("=" * 50)
    
    # Test 1: Database Connection
    print("1. Testing database connection...")
    connected = db_is_connected()
    print(f"   Database connected: {connected}")
    
    # Test 2: Campaign Templates
    print("\n2. Testing campaign templates...")
    campaigns = ['networking-drip-6week', 'lead-drip', 'prospect-drip', 'client-drip']
    templates_found = 0
    
    for campaign_id in campaigns:
        template = db_get_drip_campaign_template(campaign_id)
        if template:
            templates_found += 1
            print(f"   [OK] {campaign_id}")
        else:
            print(f"   [MISSING] {campaign_id}")
    
    print(f"   Templates found: {templates_found}/{len(campaigns)}")
    
    # Test 3: SendGrid Configuration
    print("\n3. Testing SendGrid configuration...")
    api_key = os.getenv("SENDGRID_API_KEY")
    from_email = os.getenv("SENDGRID_FROM_EMAIL")
    from_name = os.getenv("SENDGRID_FROM_NAME")
    
    print(f"   SENDGRID_API_KEY: {'CONFIGURED' if api_key else 'MISSING'}")
    print(f"   SENDGRID_FROM_EMAIL: {from_email or 'MISSING'}")
    print(f"   SENDGRID_FROM_NAME: {from_name or 'MISSING'}")
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    
    all_good = connected and templates_found == len(campaigns) and api_key and from_email
    
    if all_good:
        print("STATUS: All core infrastructure is working!")
        print("\nCOMPLETED CHECKLIST:")
        print("  [DONE] Database connected")
        print("  [DONE] Campaign templates available")
        print("  [DONE] SendGrid API configured")
        print("  [DONE] Core drip engine functions exist")
        
        print("\nREMAINING WORK (needs Patrick's input):")
        print("  - Email content for 4 campaign sequences")
        print("  - MPT-specific email templates")
        print("  - Campaign analytics UI")
        
    else:
        print("STATUS: Some components need attention")
        if not connected:
            print("  - Database connection failed")
        if templates_found < len(campaigns):
            print(f"  - Missing {len(campaigns) - templates_found} campaign templates")
        if not (api_key and from_email):
            print("  - SendGrid configuration incomplete")
    
    return all_good

if __name__ == "__main__":
    test_basic_infrastructure()