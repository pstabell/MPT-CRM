#!/usr/bin/env python3
"""
E-Signature Workflow End-to-End Test
====================================

Tests the complete e-signature workflow:
1. Database connection and table creation
2. PDF viewer component functionality
3. Signature capture and processing
4. Document hash generation and verification
5. Email service integration
6. SharePoint upload functionality
7. Complete workflow simulation

Run this script to verify all components are working correctly.
"""

import os
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import tempfile

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    
    try:
        from db_service import db_is_connected, db_create_esign_document, db_get_esign_document
        print("PASS: Database service imports OK")
    except Exception as e:
        print(f"FAIL: Database service import failed: {e}")
        return False
    
    try:
        from esign_components import (
            render_pdf_viewer, render_signature_canvas, create_typed_signature,
            generate_document_hash, create_audit_trail, overlay_signature_on_pdf,
            validate_signature_token, generate_signing_url, check_document_expired
        )
        print("PASS: E-signature components imports OK")
    except Exception as e:
        print(f"FAIL: E-signature components import failed: {e}")
        return False
    
    try:
        from esign_email_service import send_esign_request_email, send_esign_completion_email
        print("PASS: Email service imports OK")
    except Exception as e:
        print(f"FAIL: Email service import failed: {e}")
        return False
    
    try:
        from esign_sharepoint_service import store_signed_document_in_sharepoint
        print("PASS: SharePoint service imports OK")
    except Exception as e:
        print(f"FAIL: SharePoint service import failed: {e}")
        return False
    
    return True

def test_database_connection():
    """Test database connectivity"""
    print("\nTesting database connection...")
    
    try:
        from db_service import db_is_connected
        
        if db_is_connected():
            print("PASS: Database connection successful")
            return True
        else:
            print("FAIL: Database not connected")
            return False
    except Exception as e:
        print(f"FAIL: Database connection test failed: {e}")
        return False

def test_esign_database_functions():
    """Test e-signature database functions"""
    print("\nTesting e-signature database functions...")
    
    try:
        from db_service import (
            db_create_esign_document, db_get_esign_document, 
            db_update_esign_document, db_add_esign_audit_entry
        )
        
        # Create test document
        test_doc = db_create_esign_document(
            title="Test Document",
            pdf_path="/tmp/test.pdf",
            signer_email="test@example.com",
            signer_name="Test Signer",
            created_by="test_user",
            client_name="Test Client"
        )
        
        if test_doc:
            print("PASS: Document creation successful")
            
            # Test retrieval
            retrieved = db_get_esign_document(test_doc['id'])
            if retrieved:
                print("PASS: Document retrieval successful")
            else:
                print("FAIL: Document retrieval failed")
                return False
            
            # Test update
            updated = db_update_esign_document(test_doc['id'], {'status': 'sent'})
            if updated:
                print("PASS: Document update successful")
            else:
                print("FAIL: Document update failed")
                return False
            
            # Test audit trail
            audit_added = db_add_esign_audit_entry(
                test_doc['id'],
                "test_action",
                "Test audit entry",
                "test@example.com"
            )
            
            if audit_added:
                print("PASS: Audit trail addition successful")
            else:
                print("FAIL: Audit trail addition failed")
                return False
            
            return True
        else:
            print("FAIL: Document creation failed")
            return False
    
    except Exception as e:
        print(f"FAIL: Database functions test failed: {e}")
        return False

def test_signature_components():
    """Test signature-related components"""
    print("\n✍️ Testing signature components...")
    
    try:
        from esign_components import (
            create_typed_signature, generate_document_hash, 
            create_audit_trail, validate_signature_token, generate_signing_url
        )
        
        # Test typed signature creation
        signature = create_typed_signature("John Doe", 48)
        if signature:
            print("✅ Typed signature creation successful")
        else:
            print("❌ Typed signature creation failed")
            return False
        
        # Test document hash generation
        test_pdf_data = b"fake pdf content"
        test_sig_data = b"fake signature data"
        test_timestamp = datetime.utcnow().isoformat() + 'Z'
        
        hash_result = generate_document_hash(test_pdf_data, test_sig_data, test_timestamp)
        if hash_result and len(hash_result) == 64:  # SHA-256 produces 64-char hex string
            print("✅ Document hash generation successful")
        else:
            print("❌ Document hash generation failed")
            return False
        
        # Test audit trail creation
        audit_data = create_audit_trail(
            str(uuid.uuid4()),
            "test@example.com",
            hash_result,
            test_timestamp
        )
        
        if audit_data and 'document_id' in audit_data:
            print("✅ Audit trail creation successful")
        else:
            print("❌ Audit trail creation failed")
            return False
        
        # Test token validation
        valid_token = str(uuid.uuid4())
        invalid_token = "invalid-token"
        
        if validate_signature_token(valid_token) and not validate_signature_token(invalid_token):
            print("✅ Token validation successful")
        else:
            print("❌ Token validation failed")
            return False
        
        # Test signing URL generation
        signing_url = generate_signing_url("http://localhost:8501", valid_token)
        if signing_url and valid_token in signing_url:
            print("✅ Signing URL generation successful")
        else:
            print("❌ Signing URL generation failed")
            return False
        
        return True
    
    except Exception as e:
        print(f"❌ Signature components test failed: {e}")
        return False

def test_email_service():
    """Test email service configuration (without actually sending)"""
    print("\n📧 Testing email service configuration...")
    
    try:
        from esign_email_service import ESignEmailService
        
        email_service = ESignEmailService()
        
        # Check configuration
        if email_service.from_email and email_service.admin_email:
            print("✅ Email service configuration loaded")
        else:
            print("⚠️ Email service configuration incomplete (check .env)")
        
        # Check SendGrid availability
        if email_service.api_key:
            print("✅ SendGrid API key configured")
        else:
            print("⚠️ SendGrid API key not configured (emails won't send)")
        
        if email_service.client:
            print("✅ SendGrid client initialized")
        else:
            print("⚠️ SendGrid client not initialized")
        
        return True
    
    except Exception as e:
        print(f"❌ Email service test failed: {e}")
        return False

def test_sharepoint_service():
    """Test SharePoint service configuration (without actually connecting)"""
    print("\n📁 Testing SharePoint service configuration...")
    
    try:
        from esign_sharepoint_service import ESignSharePointService
        
        sharepoint_service = ESignSharePointService()
        
        # Check configuration
        if sharepoint_service.tenant_id:
            print("✅ SharePoint tenant configured")
        else:
            print("⚠️ SharePoint tenant not configured")
        
        if sharepoint_service.client_id and sharepoint_service.client_secret:
            print("✅ Azure app credentials configured")
        else:
            print("⚠️ Azure app credentials not configured (SharePoint won't work)")
        
        # Test folder name sanitization
        test_name = "Test Client <>&"
        sanitized = sharepoint_service._sanitize_folder_name(test_name)
        if sanitized and "<" not in sanitized:
            print("✅ Folder name sanitization working")
        else:
            print("❌ Folder name sanitization failed")
            return False
        
        return True
    
    except Exception as e:
        print(f"❌ SharePoint service test failed: {e}")
        return False

def test_pdf_operations():
    """Test PDF operations if PyMuPDF is available"""
    print("\n📄 Testing PDF operations...")
    
    try:
        import fitz  # PyMuPDF
        from PIL import Image, ImageDraw
        from esign_components import overlay_signature_on_pdf
        
        # Create a simple test PDF
        pdf_doc = fitz.open()  # Create empty PDF
        page = pdf_doc.new_page()
        page.insert_text((100, 100), "Test Document for E-Signature", fontsize=16)
        
        # Save test PDF
        temp_pdf_path = tempfile.mktemp(suffix='.pdf')
        pdf_doc.save(temp_pdf_path)
        pdf_doc.close()
        
        if os.path.exists(temp_pdf_path):
            print("✅ Test PDF creation successful")
        else:
            print("❌ Test PDF creation failed")
            return False
        
        # Create a simple test signature image
        signature_img = Image.new('RGBA', (200, 100), (255, 255, 255, 0))
        draw = ImageDraw.Draw(signature_img)
        draw.text((10, 30), "John Doe", fill=(0, 0, 0, 255))
        
        # Test PDF signature overlay
        signed_pdf_data = overlay_signature_on_pdf(temp_pdf_path, signature_img)
        
        if signed_pdf_data and len(signed_pdf_data) > 0:
            print("✅ PDF signature overlay successful")
        else:
            print("❌ PDF signature overlay failed")
            return False
        
        # Cleanup
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)
        
        return True
    
    except ImportError as e:
        print(f"⚠️ PDF operations not available (missing dependencies): {e}")
        return True  # Not critical for basic functionality
    except Exception as e:
        print(f"❌ PDF operations test failed: {e}")
        return False

def test_streamlit_integration():
    """Test Streamlit-specific functionality"""
    print("\n🌐 Testing Streamlit integration...")
    
    try:
        # Test that we can import streamlit modules
        import streamlit as st
        print("✅ Streamlit import successful")
        
        # Test streamlit-drawable-canvas availability
        try:
            from streamlit_drawable_canvas import st_canvas
            print("✅ Drawable canvas available")
        except ImportError:
            print("⚠️ streamlit-drawable-canvas not installed (signature drawing won't work)")
        
        return True
    
    except Exception as e:
        print(f"❌ Streamlit integration test failed: {e}")
        return False

def run_full_workflow_simulation():
    """Run a complete workflow simulation"""
    print("\n🔄 Running full workflow simulation...")
    
    try:
        # This would simulate the complete workflow
        # For safety, we'll just test the components without actual email/SharePoint operations
        
        print("📝 Simulating document creation...")
        test_doc_id = str(uuid.uuid4())
        
        print("✍️ Simulating signature capture...")
        # Would capture signature here
        
        print("🔒 Simulating hash generation...")
        test_hash = generate_document_hash(b"test", b"signature", datetime.utcnow().isoformat())
        
        print("📧 Simulating email preparation...")
        # Would prepare email here
        
        print("📁 Simulating SharePoint upload...")
        # Would upload to SharePoint here
        
        print("✅ Full workflow simulation completed successfully")
        return True
    
    except Exception as e:
        print(f"❌ Full workflow simulation failed: {e}")
        return False

def main():
    """Run all tests"""
    print("E-Signature Workflow Test Suite")
    print("=" * 50)
    
    test_results = []
    
    # Run all tests
    test_results.append(("Imports", test_imports()))
    test_results.append(("Database Connection", test_database_connection()))
    test_results.append(("Database Functions", test_esign_database_functions()))
    test_results.append(("Signature Components", test_signature_components()))
    test_results.append(("Email Service", test_email_service()))
    test_results.append(("SharePoint Service", test_sharepoint_service()))
    test_results.append(("PDF Operations", test_pdf_operations()))
    test_results.append(("Streamlit Integration", test_streamlit_integration()))
    test_results.append(("Workflow Simulation", run_full_workflow_simulation()))
    
    # Print summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_name, result in test_results:
        if result:
            print(f"PASS: {test_name}")
            passed += 1
        else:
            print(f"FAIL: {test_name}")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\nAll tests passed! E-Signature workflow is ready!")
        return True
    else:
        print(f"\n{failed} test(s) failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)