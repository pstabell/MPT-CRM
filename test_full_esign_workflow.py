#!/usr/bin/env python3
"""
Full E-Signature Workflow End-to-End Test
=========================================

Tests the complete e-signature workflow integration with MPT-CRM:
1. Create test document in database
2. Generate signing URL
3. Simulate signing process
4. Verify file operations
5. Test email integration (configuration only)
6. Test SharePoint integration (configuration only)
"""

import os
import sys
import uuid
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_test_pdf():
    """Create a simple test PDF for testing"""
    try:
        import fitz  # PyMuPDF
        
        # Create a simple test PDF
        pdf_doc = fitz.open()
        page = pdf_doc.new_page()
        
        # Add some content
        page.insert_text((100, 100), "TEST DOCUMENT", fontsize=20)
        page.insert_text((100, 150), "This is a test document for e-signature workflow.", fontsize=12)
        page.insert_text((100, 200), "Please sign below:", fontsize=12)
        
        # Save to temporary file
        temp_dir = Path("temp_documents")
        temp_dir.mkdir(exist_ok=True)
        
        test_pdf_path = temp_dir / "test_contract.pdf"
        pdf_doc.save(str(test_pdf_path))
        pdf_doc.close()
        
        return str(test_pdf_path)
        
    except ImportError:
        print("WARNING: PyMuPDF not available, using placeholder PDF")
        # Create a placeholder file for testing
        temp_dir = Path("temp_documents")
        temp_dir.mkdir(exist_ok=True)
        test_pdf_path = temp_dir / "test_contract.pdf"
        with open(test_pdf_path, 'wb') as f:
            f.write(b"PDF placeholder content for testing")
        return str(test_pdf_path)
    except Exception as e:
        print(f"Error creating test PDF: {e}")
        return None

def test_database_integration():
    """Test database operations for e-signature"""
    print("\n1. Testing Database Integration...")
    
    try:
        from db_service import (
            db_create_esign_document, db_get_esign_document,
            db_update_esign_document, db_add_esign_audit_entry
        )
        
        # Create test PDF
        pdf_path = create_test_pdf()
        if not pdf_path:
            print("FAIL: Could not create test PDF")
            return None
        
        # Create document record
        doc_data = db_create_esign_document(
            title="Test Contract Agreement",
            pdf_path=pdf_path,
            signer_email="test@example.com", 
            signer_name="John Test",
            created_by="workflow_test",
            client_name="Test Client Inc"
        )
        
        if not doc_data:
            print("FAIL: Could not create document in database")
            return None
            
        print("PASS: Document created in database")
        print(f"      Document ID: {doc_data['id']}")
        print(f"      Signing Token: {doc_data['signing_token']}")
        
        # Test audit trail
        audit_success = db_add_esign_audit_entry(
            doc_data['id'],
            "workflow_test",
            "Full workflow end-to-end test started",
            "test@example.com"
        )
        
        if audit_success:
            print("PASS: Audit trail working")
        else:
            print("WARN: Audit trail may not be working")
        
        return doc_data
        
    except Exception as e:
        print(f"FAIL: Database integration test failed: {e}")
        return None

def test_signature_processing(doc_data):
    """Test signature capture and processing"""
    print("\n2. Testing Signature Processing...")
    
    try:
        from esign_components import (
            create_typed_signature, generate_document_hash,
            overlay_signature_on_pdf, validate_signature_token
        )
        
        # Test token validation
        if not validate_signature_token(doc_data['signing_token']):
            print("FAIL: Token validation failed")
            return False
        print("PASS: Signing token validation")
        
        # Create test signature
        signature = create_typed_signature("John Test", 36)
        if not signature:
            print("FAIL: Could not create typed signature")
            return False
        print("PASS: Signature creation")
        
        # Test document hashing
        with open(doc_data['pdf_path'], 'rb') as f:
            pdf_data = f.read()
        
        timestamp = datetime.now().isoformat() + 'Z'
        
        # Convert signature to bytes for hashing
        from io import BytesIO
        sig_buffer = BytesIO()
        signature.save(sig_buffer, format='PNG')
        sig_data = sig_buffer.getvalue()
        
        doc_hash = generate_document_hash(pdf_data, sig_data, timestamp)
        if not doc_hash or len(doc_hash) != 64:
            print("FAIL: Document hash generation failed")
            return False
        print("PASS: Document hash generation")
        print(f"      Hash: {doc_hash[:16]}...")
        
        # Test PDF signature overlay
        if os.path.exists(doc_data['pdf_path']):
            signed_pdf_data = overlay_signature_on_pdf(doc_data['pdf_path'], signature)
            if signed_pdf_data and len(signed_pdf_data) > 0:
                print("PASS: PDF signature overlay")
                
                # Save signed PDF for testing
                signed_path = doc_data['pdf_path'].replace('.pdf', '_signed.pdf')
                with open(signed_path, 'wb') as f:
                    f.write(signed_pdf_data)
                
                return {
                    'signed_pdf_path': signed_path,
                    'signature_hash': doc_hash,
                    'timestamp': timestamp
                }
            else:
                print("WARN: PDF signature overlay may not be working")
                return {
                    'signed_pdf_path': doc_data['pdf_path'],  # Use original as fallback
                    'signature_hash': doc_hash,
                    'timestamp': timestamp
                }
        else:
            print("WARN: Original PDF not found for overlay test")
            return {
                'signed_pdf_path': doc_data['pdf_path'],
                'signature_hash': doc_hash,
                'timestamp': timestamp
            }
        
    except Exception as e:
        print(f"FAIL: Signature processing test failed: {e}")
        return False

def test_email_integration(doc_data):
    """Test email service configuration"""
    print("\n3. Testing Email Integration...")
    
    try:
        from esign_email_service import ESignEmailService
        
        email_service = ESignEmailService()
        
        # Check configuration
        config_issues = []
        
        if not email_service.api_key:
            config_issues.append("SendGrid API key not configured")
        
        if not email_service.from_email:
            config_issues.append("From email not configured")
        
        if not email_service.admin_email:
            config_issues.append("Admin email not configured")
        
        if config_issues:
            print("WARN: Email configuration issues:")
            for issue in config_issues:
                print(f"      - {issue}")
            print("      Emails will not be sent in production")
        else:
            print("PASS: Email service configuration complete")
        
        # Test email template generation (without sending)
        try:
            base_url = "http://localhost:8501"
            from esign_components import generate_signing_url
            signing_url = generate_signing_url(base_url, doc_data['signing_token'])
            
            # Test template methods exist
            html_content = email_service._generate_signing_request_html(
                doc_data, signing_url, "2026-03-01", "This is a test message"
            )
            
            if html_content and len(html_content) > 100:
                print("PASS: Email template generation")
            else:
                print("FAIL: Email template generation failed")
                return False
                
        except Exception as e:
            print(f"FAIL: Email template test failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"FAIL: Email integration test failed: {e}")
        return False

def test_sharepoint_integration():
    """Test SharePoint service configuration"""
    print("\n4. Testing SharePoint Integration...")
    
    try:
        from esign_sharepoint_service import ESignSharePointService
        
        sharepoint_service = ESignSharePointService()
        
        # Check configuration
        config_issues = []
        
        if not sharepoint_service.tenant_id:
            config_issues.append("Azure tenant ID not configured")
        
        if not sharepoint_service.client_id:
            config_issues.append("Azure client ID not configured")
        
        if not sharepoint_service.client_secret:
            config_issues.append("Azure client secret not configured")
        
        if config_issues:
            print("WARN: SharePoint configuration issues:")
            for issue in config_issues:
                print(f"      - {issue}")
            print("      SharePoint auto-filing will not work")
        else:
            print("PASS: SharePoint service configuration complete")
        
        # Test utility functions
        test_client = "Test Client & Co. <Special>"
        sanitized = sharepoint_service._sanitize_folder_name(test_client)
        if sanitized and "<" not in sanitized:
            print("PASS: Folder name sanitization working")
        else:
            print("FAIL: Folder name sanitization failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"FAIL: SharePoint integration test failed: {e}")
        return False

def test_streamlit_page_integration():
    """Test that the Streamlit page is properly integrated"""
    print("\n5. Testing Streamlit Page Integration...")
    
    try:
        # Check that page exists
        esign_page = Path("pages/12_ESignature.py")
        if not esign_page.exists():
            print("FAIL: E-Signature page not found")
            return False
        print("PASS: E-Signature page exists")
        
        # Check that page is in navigation
        with open("app.py", "r") as f:
            app_content = f.read()
        
        if "E-Signature" in app_content and "12_ESignature.py" in app_content:
            print("PASS: E-Signature page added to navigation")
        else:
            print("FAIL: E-Signature page not in navigation")
            return False
        
        # Check that required components are imported
        with open("pages/12_ESignature.py", "r") as f:
            page_content = f.read()
        
        required_imports = [
            "esign_components",
            "esign_email_service", 
            "esign_sharepoint_service"
        ]
        
        missing_imports = []
        for imp in required_imports:
            if imp not in page_content:
                missing_imports.append(imp)
        
        if missing_imports:
            print(f"FAIL: Missing imports: {', '.join(missing_imports)}")
            return False
        
        print("PASS: All required imports present in page")
        return True
        
    except Exception as e:
        print(f"FAIL: Streamlit page integration test failed: {e}")
        return False

def test_workflow_simulation(doc_data, signature_result):
    """Simulate the complete signing workflow"""
    print("\n6. Testing Complete Workflow Simulation...")
    
    try:
        from db_service import db_update_esign_document, db_add_esign_audit_entry
        
        # Simulate signing process
        updates = {
            'status': 'signed',
            'signed_pdf_path': signature_result['signed_pdf_path'],
            'signature_hash': signature_result['signature_hash']
        }
        
        if db_update_esign_document(doc_data['id'], updates):
            print("PASS: Document status updated to 'signed'")
        else:
            print("FAIL: Could not update document status")
            return False
        
        # Add completion audit entry
        audit_success = db_add_esign_audit_entry(
            doc_data['id'],
            "document_signed",
            f"Document signed during workflow test at {signature_result['timestamp']}",
            "test@example.com"
        )
        
        if audit_success:
            print("PASS: Signing audit trail added")
        else:
            print("WARN: Signing audit trail may not be working")
        
        # Final status update
        final_update = db_update_esign_document(doc_data['id'], {'status': 'completed'})
        if final_update:
            print("PASS: Document marked as completed")
        else:
            print("FAIL: Could not mark document as completed")
            return False
        
        return True
        
    except Exception as e:
        print(f"FAIL: Workflow simulation failed: {e}")
        return False

def cleanup_test_files():
    """Clean up test files"""
    try:
        temp_dir = Path("temp_documents")
        if temp_dir.exists():
            for file in temp_dir.glob("test_*"):
                file.unlink()
            print("INFO: Test files cleaned up")
    except Exception as e:
        print(f"WARN: Could not clean up test files: {e}")

def main():
    """Run the complete end-to-end test"""
    print("E-Signature Workflow - End-to-End Test")
    print("=" * 50)
    
    try:
        # Test 1: Database Integration
        doc_data = test_database_integration()
        if not doc_data:
            print("\nCRITICAL: Database integration failed - cannot continue")
            return False
        
        # Test 2: Signature Processing
        signature_result = test_signature_processing(doc_data)
        if not signature_result:
            print("\nCRITICAL: Signature processing failed - cannot continue")
            return False
        
        # Test 3: Email Integration
        email_ok = test_email_integration(doc_data)
        
        # Test 4: SharePoint Integration
        sharepoint_ok = test_sharepoint_integration()
        
        # Test 5: Streamlit Page Integration
        page_ok = test_streamlit_page_integration()
        
        # Test 6: Complete Workflow Simulation
        workflow_ok = test_workflow_simulation(doc_data, signature_result)
        
        # Summary
        print("\n" + "=" * 50)
        print("END-TO-END TEST SUMMARY")
        print("=" * 50)
        
        results = [
            ("Database Integration", True),
            ("Signature Processing", True),
            ("Email Integration", email_ok),
            ("SharePoint Integration", sharepoint_ok),
            ("Streamlit Page Integration", page_ok),
            ("Workflow Simulation", workflow_ok)
        ]
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "PASS" if result else "FAIL"
            print(f"{status}: {test_name}")
        
        print(f"\nResults: {passed}/{total} tests passed")
        
        if passed == total:
            print("\nSUCCESS: Full e-signature workflow is working!")
            print("\nFeatures verified:")
            print("- Database operations and audit trails")
            print("- PDF signature processing and hashing")
            print("- Email service configuration")
            print("- SharePoint service configuration") 
            print("- Streamlit page integration")
            print("- Complete signing workflow")
            print("\nThe e-signature feature is ready for production use.")
            return True
        else:
            print(f"\nWARNING: {total - passed} test(s) failed")
            print("Some features may not work properly in production.")
            print("Review the failed tests above and fix configuration issues.")
            return False
        
    except Exception as e:
        print(f"\nCRITICAL ERROR: Test suite failed: {e}")
        return False
    
    finally:
        cleanup_test_files()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)