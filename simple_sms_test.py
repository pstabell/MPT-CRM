"""
Simple SMS test for MPT-CRM (no Unicode characters)
"""

import os
import sys

# Add current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if all imports work"""
    print("Testing imports...")
    
    try:
        from services.sms_service import validate_phone_number
        print("SMS service import: OK")
        return True
    except ImportError as e:
        print(f"SMS service import FAILED: {e}")
        return False
    except Exception as e:
        print(f"SMS service error: {e}")
        return False

def test_phone_validation():
    """Test phone number validation"""
    print("Testing phone validation...")
    
    try:
        from services.sms_service import validate_phone_number
        
        test_cases = [
            "+12396008159",
            "2396008159",
            "(239) 600-8159",
            "239-600-8159"
        ]
        
        for phone in test_cases:
            result = validate_phone_number(phone)
            print(f"Phone: {phone} -> Valid: {result['valid']}, Formatted: {result.get('formatted', 'N/A')}")
        
        return True
    
    except Exception as e:
        print(f"Phone validation failed: {e}")
        return False

if __name__ == "__main__":
    print("=== Simple SMS Test ===")
    
    test1 = test_imports()
    if test1:
        test2 = test_phone_validation()
    else:
        test2 = False
    
    print("\n=== Results ===")
    print(f"Imports: {'OK' if test1 else 'FAILED'}")
    print(f"Phone validation: {'OK' if test2 else 'FAILED'}")
    
    if not test1:
        print("\nTroubleshooting:")
        print("1. Check if services/sms_service.py exists")
        print("2. Install dependencies: pip install twilio supabase")
        print("3. Create .streamlit/secrets.toml with Twilio credentials")
    
    print("Test complete.")