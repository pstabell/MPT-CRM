"""
start_ai_sdr_integration.py — Easy startup script for AI SDR Phase 2
==================================================================

One-click startup for the AI SDR Discovery Integration system.
Validates setup, runs tests, and starts the API server.

Usage:
    python start_ai_sdr_integration.py [--test-only] [--skip-tests]
"""

import sys
import os
import subprocess
import time
from datetime import datetime

def print_banner():
    """Print startup banner"""
    print("\\n" + "="*70)
    print("🤖 AI SDR PHASE 2 - CRM DISCOVERY INTEGRATION STARTUP")
    print("="*70)
    print(f"Mission Control Card: 60ba5b82-db74-4d9c-b99f-6f6f22173908")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

def check_dependencies():
    """Check if required Python packages are installed"""
    print("\\n🔍 Checking dependencies...")
    
    required_packages = [
        'flask',
        'flask_cors',
        'requests'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\\n⚠️ Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    
    print("✅ All dependencies available")
    return True

def check_database_connection():
    """Check CRM database connectivity"""
    print("\\n🗄️ Checking database connection...")
    
    try:
        from db_service import db_is_connected, db_test_connection
        
        if db_is_connected():
            test_success, test_message = db_test_connection()
            if test_success:
                print("✅ Database connected and accessible")
                return True
            else:
                print(f"❌ Database test failed: {test_message}")
                return False
        else:
            print("❌ Database not connected - check .env file")
            return False
            
    except Exception as e:
        print(f"❌ Database check error: {str(e)}")
        return False

def run_integration_tests():
    """Run the test suite"""
    print("\\n🧪 Running integration tests...")
    
    try:
        # Import test module
        import ai_sdr_test
        
        # Run specific test functions
        print("\\n  📝 Testing data mapping...")
        mapping_success = ai_sdr_test.test_data_mapping()
        
        print("\\n  🎯 Testing lead scoring...")
        scoring_success = ai_sdr_test.test_lead_scoring()
        
        print("\\n  🔄 Testing integration processing...")
        processing_success = ai_sdr_test.test_integration_processing()
        
        # Overall result
        all_passed = mapping_success and scoring_success and processing_success
        
        if all_passed:
            print("\\n✅ All core tests passed!")
            return True
        else:
            print("\\n❌ Some tests failed - check output above")
            return False
            
    except Exception as e:
        print(f"\\n❌ Test error: {str(e)}")
        return False

def start_api_server():
    """Start the Flask API server"""
    print("\\n🚀 Starting API server...")
    print("\\nEndpoints will be available at:")
    print("• http://localhost:5001/api/discovery/process")
    print("• http://localhost:5001/api/discovery/health") 
    print("• http://localhost:5001/api/discovery/test")
    print("\\n" + "="*70)
    print("🟢 API SERVER RUNNING - Press Ctrl+C to stop")
    print("="*70)
    
    try:
        # Import and run the API
        import ai_sdr_api
        ai_sdr_api.app.run(
            host='0.0.0.0',
            port=5001,
            debug=False,  # Disable debug for production-like startup
            threaded=True
        )
    except KeyboardInterrupt:
        print("\\n\\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\\n❌ Server error: {str(e)}")

def main():
    """Main startup sequence"""
    # Parse command line arguments
    test_only = '--test-only' in sys.argv
    skip_tests = '--skip-tests' in sys.argv
    
    print_banner()
    
    # Step 1: Check dependencies
    if not check_dependencies():
        print("\\n❌ Setup incomplete - fix dependencies first")
        sys.exit(1)
    
    # Step 2: Check database
    db_ok = check_database_connection()
    if not db_ok:
        print("\\n⚠️ Database issues detected")
        print("   API will run but CRM features may not work")
        print("   Check Supabase connection in .env file")
    
    # Step 3: Run tests (unless skipped)
    if not skip_tests:
        tests_ok = run_integration_tests()
        if not tests_ok:
            print("\\n⚠️ Some tests failed")
            if not test_only:
                response = input("Continue to start server anyway? (y/N): ")
                if response.lower() != 'y':
                    print("Startup cancelled")
                    sys.exit(1)
    
    # If test-only mode, stop here
    if test_only:
        print("\\n✅ Test-only mode complete")
        sys.exit(0)
    
    # Step 4: Start server
    print("\\n⏳ Starting server in 3 seconds...")
    time.sleep(3)
    start_api_server()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        print(__doc__)
        print("\\nOptions:")
        print("  --test-only    Run tests only, don't start server")
        print("  --skip-tests   Start server without running tests")
        print("  --help, -h     Show this help")
        sys.exit(0)
    
    main()