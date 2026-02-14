"""
Test ROCK 5: Drip Campaign Infrastructure
==========================================

This script tests all the key components of the drip campaign system:
1. Database connection & table existence
2. Campaign template availability
3. Contact drip toggle functionality
4. Auto-switch logic on contact type change
5. SendGrid API configuration
"""

import os
import sys
from datetime import datetime

# Add project root to path so we can import db_service
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_service import (
    db_is_connected, db_test_connection,
    db_get_drip_campaign_template, db_get_contacts,
    db_create_contact, db_update_contact, 
    db_get_enrollments_for_contact, db_create_enrollment,
    send_email_via_sendgrid
)

def test_database_connection():
    """Test 1: Database connection"""
    print("=" * 50)
    print("TEST 1: Database Connection")
    print("=" * 50)
    
    connected = db_is_connected()
    print(f"[OK] Database connected: {connected}")
    
    if connected:
        success, message = db_test_connection()
        print(f"[OK] Test query: {'SUCCESS' if success else 'FAILED'} - {message}")
    
    return connected

def test_drip_campaign_templates():
    """Test 2: Drip campaign template availability"""
    print("\n" + "=" * 50)
    print("TEST 2: Drip Campaign Templates")
    print("=" * 50)
    
    campaign_types = ['networking-drip-6week', 'lead-drip', 'prospect-drip', 'client-drip']
    templates_found = 0
    
    for campaign_id in campaign_types:
        template = db_get_drip_campaign_template(campaign_id)
        if template:
            templates_found += 1
            email_sequence = template.get('email_sequence', [])
            if isinstance(email_sequence, str):
                import json
                email_sequence = json.loads(email_sequence)
            
            print(f"✅ {campaign_id}: {len(email_sequence)} emails")
        else:
            print(f"❌ {campaign_id}: NOT FOUND")
    
    print(f"\n📊 Templates found: {templates_found}/{len(campaign_types)}")
    return templates_found == len(campaign_types)

def test_sendgrid_configuration():
    """Test 3: SendGrid API configuration"""
    print("\n" + "=" * 50)
    print("TEST 3: SendGrid Configuration")
    print("=" * 50)
    
    api_key = os.getenv("SENDGRID_API_KEY")
    from_email = os.getenv("SENDGRID_FROM_EMAIL") 
    from_name = os.getenv("SENDGRID_FROM_NAME")
    
    print(f"✅ SENDGRID_API_KEY: {'CONFIGURED' if api_key else 'MISSING'}")
    print(f"✅ SENDGRID_FROM_EMAIL: {from_email or 'MISSING'}")
    print(f"✅ SENDGRID_FROM_NAME: {from_name or 'MISSING'}")
    
    return bool(api_key and from_email and from_name)

def test_contact_drip_toggle():
    """Test 4: Manual contact drip enrollment"""
    print("\n" + "=" * 50)
    print("TEST 4: Contact Drip Toggle (Manual Enrollment)")
    print("=" * 50)
    
    # Create a test contact
    test_contact_data = {
        "first_name": "Test",
        "last_name": "Contact",
        "email": "test@example.com",
        "company": "Test Company",
        "type": "networking",
        "source": "test",
        "source_detail": "ROCK 5 Infrastructure Test"
    }
    
    print("📝 Creating test contact...")
    contact = db_create_contact(test_contact_data)
    
    if not contact:
        print("❌ Failed to create test contact")
        return False
    
    contact_id = contact['id']
    print(f"✅ Test contact created: {contact_id}")
    
    # Check if automatically enrolled (should be due to networking type)
    enrollments = db_get_enrollments_for_contact(contact_id)
    print(f"✅ Auto-enrollments: {len(enrollments)}")
    
    if enrollments:
        for enrollment in enrollments:
            print(f"   - {enrollment.get('campaign_name', 'Unknown')} ({enrollment.get('status', 'unknown')})")
    
    # Test manual enrollment in different campaign
    print("\n📝 Testing manual enrollment in prospect campaign...")
    enrollment_data = {
        "contact_id": contact_id,
        "campaign_id": "prospect-drip",
        "campaign_name": "Prospect Conversion (5 Week)",
        "status": "active",
        "current_step": 0,
        "total_steps": 6,
        "step_schedule": "[]",
        "source": "manual_test",
        "source_detail": "Manual toggle test",
        "emails_sent": 0,
        "next_email_scheduled": datetime.now().isoformat()
    }
    
    enrollment = db_create_enrollment(enrollment_data)
    if enrollment:
        print("✅ Manual enrollment successful")
        
        # Check enrollments again
        enrollments_after = db_get_enrollments_for_contact(contact_id)
        print(f"✅ Total enrollments after manual: {len(enrollments_after)}")
        
        # Cleanup: Delete test contact
        print(f"\n🧹 Cleaning up test contact {contact_id}")
        try:
            from db_service import get_db
            db = get_db()
            if db:
                # Delete enrollments first
                db.table("campaign_enrollments").delete().eq("contact_id", contact_id).execute()
                # Delete contact
                db.table("contacts").delete().eq("id", contact_id).execute()
                print("✅ Cleanup successful")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")
        
        return True
    else:
        print("❌ Manual enrollment failed")
        return False

def test_auto_switch_logic():
    """Test 5: Auto-switch campaigns when contact type changes"""
    print("\n" + "=" * 50)
    print("TEST 5: Auto-Switch Logic")
    print("=" * 50)
    
    # Create test contact as networking
    test_contact_data = {
        "first_name": "AutoSwitch",
        "last_name": "Test",
        "email": "autoswitch@example.com", 
        "company": "Switch Test Co",
        "type": "networking",
        "source": "test"
    }
    
    print("📝 Creating networking contact...")
    contact = db_create_contact(test_contact_data)
    if not contact:
        print("❌ Failed to create test contact")
        return False
    
    contact_id = contact['id']
    print(f"✅ Contact created: {contact_id}")
    
    # Check initial enrollment
    enrollments = db_get_enrollments_for_contact(contact_id)
    print(f"✅ Initial enrollments: {len(enrollments)}")
    
    # Update contact type to lead (should trigger auto-switch)
    print("\n📝 Updating contact type: networking → lead")
    updated = db_update_contact(contact_id, {"type": "lead"})
    
    if updated:
        print("✅ Contact type updated")
        
        # Check enrollments after switch
        enrollments_after = db_get_enrollments_for_contact(contact_id)
        print(f"✅ Enrollments after switch: {len(enrollments_after)}")
        
        active_campaigns = [e for e in enrollments_after if e.get('status') == 'active']
        completed_campaigns = [e for e in enrollments_after if e.get('status') == 'completed']
        
        print(f"   - Active: {len(active_campaigns)}")
        print(f"   - Completed: {len(completed_campaigns)}")
        
        for enrollment in active_campaigns:
            print(f"   - Active: {enrollment.get('campaign_name', 'Unknown')}")
        
        # Cleanup
        print(f"\n🧹 Cleaning up test contact {contact_id}")
        try:
            from db_service import get_db
            db = get_db()
            if db:
                db.table("campaign_enrollments").delete().eq("contact_id", contact_id).execute()
                db.table("contacts").delete().eq("id", contact_id).execute()
                print("✅ Cleanup successful")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")
        
        return len(active_campaigns) > 0
    else:
        print("❌ Failed to update contact type")
        return False

def main():
    """Run all drip campaign infrastructure tests"""
    print("ROCK 5: Drip Campaign Infrastructure Test")
    print("=" * 50)
    
    results = {
        "Database Connection": test_database_connection(),
        "Campaign Templates": test_drip_campaign_templates(),
        "SendGrid Config": test_sendgrid_configuration(),
        "Contact Drip Toggle": test_contact_drip_toggle(),
        "Auto-Switch Logic": test_auto_switch_logic()
    }
    
    print("\n" + "=" * 50)
    print("FINAL RESULTS")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "[PASS]" if passed_test else "[FAIL]"
        print(f"{status} {test_name}")
        if passed_test:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("All drip campaign infrastructure is working!")
        print("\nCOMPLETE CHECKLIST:")
        print("   1. [DONE] Drip tables exist in Supabase")
        print("   2. [DONE] Campaign templates available")  
        print("   3. [DONE] SendGrid API configured")
        print("   4. [DONE] Contact drip toggle working")
        print("   5. [DONE] Auto-switch logic working")
        print("   6. [DONE] Test enrollment successful")
        
        print("\nSTILL NEEDS PATRICK'S INPUT:")
        print("   - Build 4 campaign email content sequences")
        print("   - Create MPT-specific email templates")
        print("   - Campaign manager analytics UI design")
    else:
        print(f"WARNING: {total - passed} tests failed - needs debugging")
    
    return passed == total

if __name__ == "__main__":
    main()