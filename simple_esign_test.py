#!/usr/bin/env python3
"""
Simple E-Signature Test
======================

Basic test to verify e-signature components are working.
"""

import os
import sys
import uuid
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_basic_imports():
    """Test basic imports"""
    print("Testing imports...")
    
    try:
        from db_service import db_is_connected
        print("PASS: Database service import")
    except Exception as e:
        print(f"FAIL: Database service - {e}")
        return False
    
    try:
        from esign_components import generate_document_hash, validate_signature_token
        print("PASS: E-signature components import")
    except Exception as e:
        print(f"FAIL: E-signature components - {e}")
        return False
    
    try:
        from esign_email_service import ESignEmailService
        print("PASS: Email service import")
    except Exception as e:
        print(f"FAIL: Email service - {e}")
        return False
    
    try:
        from esign_sharepoint_service import ESignSharePointService
        print("PASS: SharePoint service import")
    except Exception as e:
        print(f"FAIL: SharePoint service - {e}")
        return False
    
    return True

def test_hash_generation():
    """Test document hash generation"""
    print("Testing hash generation...")
    
    try:
        from esign_components import generate_document_hash
        
        test_pdf = b"fake pdf data"
        test_sig = b"fake signature data"
        test_time = datetime.utcnow().isoformat()
        
        hash_result = generate_document_hash(test_pdf, test_sig, test_time)
        
        if hash_result and len(hash_result) == 64:
            print("PASS: Hash generation working")
            return True
        else:
            print("FAIL: Invalid hash result")
            return False
    except Exception as e:
        print(f"FAIL: Hash generation - {e}")
        return False

def test_token_validation():
    """Test token validation"""
    print("Testing token validation...")
    
    try:
        from esign_components import validate_signature_token
        
        valid_token = str(uuid.uuid4())
        invalid_token = "not-a-uuid"
        
        if validate_signature_token(valid_token) and not validate_signature_token(invalid_token):
            print("PASS: Token validation working")
            return True
        else:
            print("FAIL: Token validation not working correctly")
            return False
    except Exception as e:
        print(f"FAIL: Token validation - {e}")
        return False

def main():
    """Run basic tests"""
    print("E-Signature Basic Test")
    print("=" * 30)
    
    tests = [
        test_basic_imports,
        test_hash_generation,
        test_token_validation
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"ERROR: Test failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 30)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("All basic tests passed!")
        return True
    else:
        print("Some tests failed - check above for details")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)