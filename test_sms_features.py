"""
SMS Features Test Script for MPT-CRM
====================================

Test the SMS functionality before deployment.
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def test_database_connection():
    """Test if we can connect to Supabase"""
    print("1. Testing database connection...")
    try:
        import db_service
        db = db_service.get_db()
        if db:
            print("   [OK] Database connection successful")
            return True
        else:
            print("   [ERROR] Database connection failed")
            return False
    except Exception as e:
        print(f"   [ERROR] Database error: {e}")
        return False

def test_sms_table_exists():
    """Test if sms_messages table exists"""
    print("2. Testing sms_messages table...")
    try:
        import db_service
        
        # Try to query the table (should not error even if empty)
        result = db_service.db_get_sms_messages("00000000-0000-0000-0000-000000000000", limit=1)
        print("   [OK] sms_messages table exists and queryable")
        return True
    except Exception as e:
        print(f"   [ERROR] SMS table error: {e}")
        print("   [INFO] Run the schema migration first: python run_sms_migration.py")
        return False

def test_phone_formatting():
    """Test phone number formatting functions"""
    print("3. Testing phone number formatting...")
    try:
        import db_service
        
        test_numbers = [
            "+12394267058",
            "2394267058", 
            "(239) 426-7058",
            "239-426-7058",
            "239.426.7058"
        ]
        
        for number in test_numbers:
            formatted = db_service.format_phone_for_display(number)
            print(f"   {number} -> {formatted}")
        
        print("   [OK] Phone formatting works")
        return True
    except Exception as e:
        print(f"   [ERROR] Phone formatting error: {e}")
        return False

def test_twilio_service():
    """Test Twilio service initialization"""
    print("4. Testing Twilio service...")
    try:
        from twilio_sms_service import TwilioSMSService
        
        sms_service = TwilioSMSService()
        print(f"   Account SID: {sms_service.account_sid[:10]}...")
        print(f"   From Number: {sms_service.from_number}")
        print("   [OK] Twilio service initialized")
        return True
    except Exception as e:
        print(f"   [ERROR] Twilio service error: {e}")
        return False

def test_contact_lookup():
    """Test finding contacts by phone number"""
    print("5. Testing contact phone lookup...")
    try:
        import db_service
        
        # Try to find a contact by phone (will return None if none exist)
        contact = db_service.db_find_contact_by_phone("+12394267058")
        if contact:
            print(f"   Found contact: {contact['first_name']} {contact['last_name']}")
        else:
            print("   No contact found with test number (this is OK for testing)")
        
        print("   [OK] Contact lookup function works")
        return True
    except Exception as e:
        print(f"   [ERROR] Contact lookup error: {e}")
        return False

def test_sms_record_creation():
    """Test creating SMS records in database"""
    print("6. Testing SMS record creation...")
    try:
        import db_service
        import uuid
        
        # Create a test SMS record (won't actually send)
        test_contact_id = str(uuid.uuid4())
        test_message = db_service.db_create_sms_message(
            contact_id=test_contact_id,
            body="Test message - ignore",
            direction="outbound",
            from_number="+12394267058",
            to_number="+15551234567",
            status="test"
        )
        
        if test_message:
            print(f"   Test message ID: {test_message['id'][:8]}...")
            print("   [OK] SMS record creation works")
            
            # Clean up test record
            try:
                db = db_service.get_db()
                db.table("sms_messages").delete().eq("id", test_message['id']).execute()
                print("   [CLEANUP] Test record cleaned up")
            except:
                print("   [WARN] Could not clean up test record (manual cleanup needed)")
            
            return True
        else:
            print("   [ERROR] Failed to create SMS record")
            return False
    except Exception as e:
        print(f"   [ERROR] SMS record creation error: {e}")
        return False

def run_all_tests():
    """Run all SMS feature tests"""
    print("[TEST] MPT-CRM SMS Features Test Suite")
    print("=" * 50)
    
    tests = [
        test_database_connection,
        test_sms_table_exists,
        test_phone_formatting,
        test_twilio_service,
        test_contact_lookup,
        test_sms_record_creation
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            print()
        except Exception as e:
            print(f"   [CRASH] Test crashed: {e}")
            print()
    
    print("=" * 50)
    print(f"[RESULTS] {passed}/{total} tests passed")
    
    if passed == total:
        print("[SUCCESS] All tests passed! SMS features are ready to use.")
        print("\n[NEXT STEPS]:")
        print("1. Start the Streamlit app: streamlit run app.py")
        print("2. Open a contact with a phone number")
        print("3. Try sending a text message")
        print("4. Start webhook server: python sms_webhook.py")
        print("5. Configure Twilio webhook URL in Twilio Console")
    else:
        print("[WARNING] Some tests failed. Fix issues before using SMS features.")
    
    return passed == total

if __name__ == "__main__":
    run_all_tests()