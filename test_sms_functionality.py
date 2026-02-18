"""
Test SMS functionality for MPT-CRM
Sends a test SMS to Patrick and verifies the service works
"""

import os
import sys
from datetime import datetime

# Add current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_sms_service():
    """Test the SMS service functionality"""
    
    print("=== MPT-CRM SMS Service Test ===")
    
    try:
        # Import SMS service
        from services.sms_service import SMSService, validate_phone_number
        
        print("✅ SMS service imported successfully")
        
        # Test phone validation
        test_phone = "+12396008159"
        validation_result = validate_phone_number(test_phone)
        
        print(f"\n📱 Phone Validation Test:")
        print(f"Input: {test_phone}")
        print(f"Valid: {validation_result['valid']}")
        print(f"Formatted: {validation_result['formatted']}")
        
        if not validation_result['valid']:
            print(f"❌ Phone validation failed: {validation_result['error']}")
            return False
        
        # Initialize SMS service
        print(f"\n🔧 Initializing SMS service...")
        try:
            sms_service = SMSService()
            print("✅ SMS service initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize SMS service: {str(e)}")
            print("💡 Make sure Twilio credentials are properly configured in .streamlit/secrets.toml")
            return False
        
        # Test message
        test_message = f"Test SMS from MPT-CRM - {datetime.now().strftime('%I:%M %p')}"
        print(f"\n📤 Sending test SMS:")
        print(f"To: {validation_result['formatted']}")
        print(f"Message: {test_message}")
        print(f"Characters: {len(test_message)}/160")
        
        # Send SMS
        result = sms_service.send_sms(
            to_phone=validation_result['formatted'],
            message=test_message,
            contact_id="test-contact-id"  # Using test contact ID
        )
        
        # Check result
        if result['success']:
            print(f"✅ SMS sent successfully!")
            print(f"📨 Message ID: {result['message_id']}")
            print(f"📊 Status: {result['status']}")
            print(f"📝 History logged: {result['history_logged']}")
            
            # Test SMS history retrieval
            print(f"\n📋 Testing SMS history retrieval...")
            history = sms_service.get_sms_history("test-contact-id", limit=5)
            
            if history:
                print(f"✅ Retrieved {len(history)} SMS history records")
                latest = history[0]
                print(f"Latest SMS: {latest.get('message', '')[:50]}...")
                print(f"Sent at: {latest.get('sent_at', 'Unknown')}")
                print(f"Status: {latest.get('status', 'Unknown')}")
            else:
                print("⚠️ No SMS history found (might take a moment to appear)")
            
            return True
            
        else:
            print(f"❌ SMS failed to send: {result['error']}")
            return False
    
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        print("💡 Make sure the services directory and sms_service.py exist")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def test_streamlit_secrets():
    """Test if Streamlit secrets are properly configured"""
    
    print("\n=== Testing Streamlit Secrets Configuration ===")
    
    try:
        # Try to simulate streamlit secrets loading
        import streamlit as st
        
        # Check if secrets are accessible
        if hasattr(st, 'secrets'):
            try:
                twilio_config = st.secrets.get('twilio', {})
                
                if not twilio_config:
                    print("❌ No [twilio] section found in secrets.toml")
                    return False
                
                required_keys = ['TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'TWILIO_PHONE_NUMBER']
                missing_keys = []
                
                for key in required_keys:
                    if key not in twilio_config:
                        missing_keys.append(key)
                
                if missing_keys:
                    print(f"❌ Missing Twilio configuration keys: {', '.join(missing_keys)}")
                    return False
                
                print("✅ Twilio secrets configuration found")
                print(f"📞 Phone: {twilio_config['TWILIO_PHONE_NUMBER']}")
                print(f"🔑 SID: {twilio_config['TWILIO_ACCOUNT_SID'][:8]}...")
                return True
                
            except Exception as e:
                print(f"❌ Error accessing secrets: {str(e)}")
                return False
        else:
            print("⚠️ Cannot access secrets outside of Streamlit context")
            return True  # This is expected when running outside Streamlit
    
    except ImportError:
        print("❌ Streamlit not available")
        return False

def manual_credentials_test():
    """Test with manual credentials (for development)"""
    
    print("\n=== Manual Credentials Test ===")
    print("⚠️ This test uses placeholder credentials and will fail")
    print("💡 Update secrets.toml with real Twilio credentials to make SMS work")
    
    # This will fail with placeholder credentials, but tests the code path
    return False

if __name__ == "__main__":
    print("🚀 Starting MPT-CRM SMS functionality tests...")
    
    # Test 1: Streamlit secrets
    secrets_ok = test_streamlit_secrets()
    
    # Test 2: SMS service (will fail without real credentials)
    if secrets_ok:
        sms_ok = test_sms_service()
    else:
        print("\n⚠️ Skipping SMS service test due to secrets configuration issues")
        sms_ok = manual_credentials_test()
    
    # Summary
    print(f"\n=== Test Summary ===")
    print(f"Secrets configuration: {'✅ OK' if secrets_ok else '❌ Failed'}")
    print(f"SMS service test: {'✅ OK' if sms_ok else '❌ Failed'}")
    
    if not sms_ok:
        print(f"\n💡 To enable SMS functionality:")
        print(f"1. Get Twilio Account SID and Auth Token from Twilio Console")
        print(f"2. Update .streamlit/secrets.toml with real credentials:")
        print(f"   TWILIO_ACCOUNT_SID = 'your_real_sid'")
        print(f"   TWILIO_AUTH_TOKEN = 'your_real_token'")
        print(f"3. Create crm_sms_history table in Supabase (run the SQL file)")
        print(f"4. Install dependencies: pip install twilio")
    
    print(f"\n🏁 Test complete!")