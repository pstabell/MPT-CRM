# E-Signature Phase 3 Testing Script
# Test signature capture and PDF overlay functionality

import os
import sys
import tempfile
from datetime import datetime
from esign_signature_service import (
    SignatureData, 
    process_signature_application,
    get_signature_records,
    check_field_signed
)


def create_test_pdf():
    """Create a simple test PDF for signature testing"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        # Create test PDF
        test_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        
        c = canvas.Canvas(test_pdf.name, pagesize=letter)
        c.drawString(100, 750, "E-Signature Test Document")
        c.drawString(100, 700, "Please sign below:")
        
        # Draw a rectangle where signature should go
        c.rect(100, 600, 200, 50)
        c.drawString(105, 620, "SIGNATURE FIELD")
        
        c.save()
        
        return test_pdf.name
        
    except ImportError:
        print("ReportLab not installed. Cannot create test PDF.")
        return None


def test_drawn_signature():
    """Test applying a drawn signature to PDF"""
    print("\n=== Testing Drawn Signature ===")
    
    # Create test PDF
    pdf_path = create_test_pdf()
    if not pdf_path:
        print("❌ Failed to create test PDF")
        return False
    
    output_path = tempfile.NamedTemporaryFile(suffix='_signed.pdf', delete=False).name
    
    # Create test signature data (simple base64 image)
    # This is a minimal base64 PNG - in reality, this would come from canvas.toDataURL()
    test_signature_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    
    signature_data = SignatureData(
        pdf_field_id="test_field_1",
        document_id="test_doc_1",
        signature_type="draw",
        signature_data=test_signature_b64,
        x_coordinate=100.0,
        y_coordinate=600.0,
        width=200.0,
        height=50.0,
        page_number=1
    )
    
    # Test signature application
    result = process_signature_application(
        signature_data.__dict__,
        pdf_path,
        output_path
    )
    
    if result['success']:
        print(f"✅ Drawn signature applied successfully")
        print(f"   Output PDF: {output_path}")
        return True
    else:
        print(f"❌ Failed to apply drawn signature: {result['error']}")
        return False


def test_typed_signature():
    """Test applying a typed signature to PDF"""
    print("\n=== Testing Typed Signature ===")
    
    # Create test PDF
    pdf_path = create_test_pdf()
    if not pdf_path:
        print("❌ Failed to create test PDF")
        return False
    
    output_path = tempfile.NamedTemporaryFile(suffix='_typed_signed.pdf', delete=False).name
    
    signature_data = SignatureData(
        pdf_field_id="test_field_2",
        document_id="test_doc_2",
        signature_type="type",
        signature_data="John Doe",
        x_coordinate=100.0,
        y_coordinate=600.0,
        width=200.0,
        height=50.0,
        page_number=1,
        font_family="cursive",
        font_size=18
    )
    
    # Test signature application
    result = process_signature_application(
        signature_data.__dict__,
        pdf_path,
        output_path
    )
    
    if result['success']:
        print(f"✅ Typed signature applied successfully")
        print(f"   Output PDF: {output_path}")
        return True
    else:
        print(f"❌ Failed to apply typed signature: {result['error']}")
        return False


def test_database_operations():
    """Test database signature operations"""
    print("\n=== Testing Database Operations ===")
    
    try:
        from db_service import (
            db_create_signature,
            db_get_signature_by_field,
            db_get_signatures_by_document
        )
        
        # Test creating signature record
        signature_record = {
            "pdf_field_id": "test_field_db",
            "document_id": "test_doc_db",
            "signature_type": "type",
            "signature_data": "Test Signature",
            "x_coordinate": 100.0,
            "y_coordinate": 200.0,
            "width": 150.0,
            "height": 40.0,
            "page_number": 1,
            "font_family": "serif",
            "font_size": 16
        }
        
        created = db_create_signature(signature_record)
        if created:
            print("✅ Signature record created in database")
            
            # Test retrieving signature
            retrieved = db_get_signature_by_field("test_field_db")
            if retrieved:
                print("✅ Signature record retrieved by field ID")
            else:
                print("❌ Failed to retrieve signature by field ID")
            
            # Test retrieving by document
            doc_signatures = db_get_signatures_by_document("test_doc_db")
            if doc_signatures:
                print(f"✅ Retrieved {len(doc_signatures)} signatures for document")
            else:
                print("❌ Failed to retrieve signatures by document ID")
                
            return True
        else:
            print("❌ Failed to create signature record in database")
            return False
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False


def run_all_tests():
    """Run all signature tests"""
    print("🧪 E-Signature Phase 3 Testing Suite")
    print("=====================================")
    
    tests_passed = 0
    total_tests = 3
    
    # Test drawn signature
    if test_drawn_signature():
        tests_passed += 1
    
    # Test typed signature  
    if test_typed_signature():
        tests_passed += 1
    
    # Test database operations
    if test_database_operations():
        tests_passed += 1
    
    print(f"\n📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! E-Signature Phase 3 is working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Check the implementation.")
        return False


def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking Dependencies...")
    
    missing_deps = []
    
    try:
        import reportlab
        print("✅ ReportLab installed")
    except ImportError:
        missing_deps.append("reportlab")
    
    try:
        import PyPDF2
        print("✅ PyPDF2 installed")
    except ImportError:
        missing_deps.append("PyPDF2")
    
    try:
        from PIL import Image
        print("✅ Pillow installed")
    except ImportError:
        missing_deps.append("Pillow")
    
    if missing_deps:
        print(f"\n❌ Missing dependencies: {', '.join(missing_deps)}")
        print("Install with: pip install " + " ".join(missing_deps))
        return False
    
    print("✅ All dependencies are installed")
    return True


if __name__ == "__main__":
    print("E-Signature Phase 3 Test Suite")
    print("===============================")
    
    if not check_dependencies():
        print("Please install missing dependencies before testing.")
        sys.exit(1)
    
    success = run_all_tests()
    
    if success:
        print("\n🚀 Ready for production!")
        sys.exit(0)
    else:
        print("\n🔧 Fix issues before deployment.")
        sys.exit(1)