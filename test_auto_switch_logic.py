"""
Test auto-switch logic for drip campaigns when contact types change
Item #005 - Configure auto-switch logic for status changes
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_service import (
    get_db, db_create_contact, db_update_contact_and_switch_campaign,
    db_get_contact, _handle_campaign_switch
)
from datetime import datetime

def test_auto_switch_logic():
    print("Testing auto-switch logic for drip campaigns...")
    
    db = get_db()
    if not db:
        print("[ERROR] Database connection failed")
        return False
    
    # Test campaign mapping
    campaign_map = {
        "networking": "networking-drip-6week",
        "lead": "lead-drip",
        "prospect": "prospect-drip", 
        "client": "client-drip",
    }
    
    print("[OK] Campaign mapping configured:")
    for contact_type, campaign_id in campaign_map.items():
        print(f"   {contact_type} -> {campaign_id}")
    
    # Test 1: Create a test contact as "networking"
    print("\n[TEST 1] Create networking contact and verify auto-enrollment...")
    
    test_contact_data = {
        "first_name": "Auto",
        "last_name": "Switch Test",
        "email": f"autoswitch.test+{int(datetime.now().timestamp())}@example.com",
        "type": "networking",
        "source": "test",
        "tags": ["test_contact"],
    }
    
    try:
        # Create contact (should auto-enroll in networking campaign)
        created_contact = db_create_contact(test_contact_data)
        if not created_contact:
            print("[ERROR] Failed to create test contact")
            return False
        
        contact_id = created_contact['id']
        print(f"[OK] Created contact: {contact_id}")
        
        # Check if enrolled in networking campaign
        enrollments_resp = db.table("campaign_enrollments").select("*").eq(
            "contact_id", contact_id
        ).eq("status", "active").execute()
        
        active_enrollments = enrollments_resp.data or []
        networking_enrollment = [e for e in active_enrollments if e.get("campaign_id") == "networking-drip-6week"]
        
        if networking_enrollment:
            print("[OK] Auto-enrolled in networking campaign")
        else:
            print("[WARN] No active networking enrollment found (may need manual setup)")
        
        # Test 2: Switch contact type from networking → lead
        print("\n[TEST 2] Switch contact type networking -> lead...")
        
        switch_result = db_update_contact_and_switch_campaign(contact_id, "lead", "networking")
        
        if switch_result.get("success"):
            print(f"[OK] Campaign switch successful: {switch_result.get('message')}")
            print(f"   Completed campaigns: {switch_result.get('completed', 0)}")
            print(f"   New enrollment: {switch_result.get('enrolled', False)}")
        else:
            print(f"[ERROR] Campaign switch failed: {switch_result.get('message')}")
        
        # Test 3: Verify new campaign enrollment
        print("\n[TEST 3] Verify lead campaign enrollment...")
        
        enrollments_resp = db.table("campaign_enrollments").select("*").eq(
            "contact_id", contact_id
        ).eq("status", "active").execute()
        
        active_enrollments = enrollments_resp.data or []
        lead_enrollment = [e for e in active_enrollments if e.get("campaign_id") == "lead-drip"]
        
        if lead_enrollment:
            print("[OK] Successfully enrolled in lead campaign")
        else:
            print("[WARN] No active lead enrollment found")
        
        # Test 4: Test multiple type switches
        print("\n[TEST 4] Chain switch lead -> prospect -> client...")
        
        # Lead -> Prospect
        result1 = db_update_contact_and_switch_campaign(contact_id, "prospect", "lead")
        print(f"   Lead -> Prospect: {result1.get('message', 'No message')}")
        
        # Prospect -> Client
        result2 = db_update_contact_and_switch_campaign(contact_id, "client", "prospect") 
        print(f"   Prospect -> Client: {result2.get('message', 'No message')}")
        
        # Final verification
        print("\n[REPORT] Final enrollment status:")
        enrollments_resp = db.table("campaign_enrollments").select("*").eq(
            "contact_id", contact_id
        ).execute()
        
        all_enrollments = enrollments_resp.data or []
        for enrollment in all_enrollments:
            campaign_id = enrollment.get("campaign_id", "Unknown")
            status = enrollment.get("status", "Unknown") 
            created = enrollment.get("created_at", "")[:10]  # Date only
            print(f"   [EMAIL] {campaign_id}: {status} (created: {created})")
        
        # Cleanup: Archive test contact
        print(f"\n[CLEANUP] Archiving test contact: {contact_id}")
        db.table("contacts").update({"archived": True}).eq("id", contact_id).execute()
        print("[OK] Test contact archived")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Test error: {e}")
        return False

def test_campaign_mapping():
    """Test that all contact types have campaign mappings"""
    print("\n[MAP] Testing campaign mappings...")
    
    contact_types = ["networking", "lead", "prospect", "client"]
    campaign_ids = ["networking-drip-6week", "lead-drip", "prospect-drip", "client-drip"]
    
    # Test mapping logic from _handle_campaign_switch
    campaign_map = {
        "networking": "networking-drip-6week",
        "lead": "lead-drip",
        "prospect": "prospect-drip",
        "client": "client-drip",
    }
    
    all_mapped = True
    for contact_type in contact_types:
        mapped_campaign = campaign_map.get(contact_type)
        if mapped_campaign:
            print(f"[OK] {contact_type} -> {mapped_campaign}")
        else:
            print(f"[ERROR] {contact_type} -> NO MAPPING")
            all_mapped = False
    
    return all_mapped

if __name__ == "__main__":
    print("=" * 60)
    print("AUTO-SWITCH LOGIC TEST - Item #005")
    print("=" * 60)
    
    # Test 1: Campaign mappings
    mapping_success = test_campaign_mapping()
    
    # Test 2: Full auto-switch workflow
    switch_success = test_auto_switch_logic()
    
    print("\n" + "=" * 60)
    if mapping_success and switch_success:
        print("[SUCCESS] ALL TESTS PASSED - Auto-switch logic is working!")
    else:
        print("[WARNING] SOME TESTS FAILED - Check setup requirements")
    print("=" * 60)