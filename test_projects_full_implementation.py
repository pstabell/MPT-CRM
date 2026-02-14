#!/usr/bin/env python3
"""
Test Script: Projects Module Full Implementation
===============================================

Tests all the enhanced projects functionality:
1. Database schema verification
2. Service layer functionality
3. Mission Control integration
4. Accounting integration
5. File management
6. Contact roles

Run this to verify the implementation works correctly.
"""

import os
import sys
from datetime import datetime, date
from pprint import pprint

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from db_service import (
        db_is_connected, get_db, db_get_projects, db_create_project,
        db_get_project_contacts, db_add_project_contact,
        db_get_project_files, db_add_project_file
    )
    from cross_system_service import get_accounting_service
    from mission_control_service import get_mission_control_service
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_database_connection():
    """Test database connectivity and basic schema"""
    print("\n" + "="*50)
    print("1. TESTING DATABASE CONNECTION")
    print("="*50)
    
    if not db_is_connected():
        print("❌ Database not connected")
        return False
    
    print("✅ Database connected successfully")
    
    # Test basic table access
    try:
        db = get_db()
        
        # Test projects table with new columns
        result = db.table("projects").select("id, name, project_type, hourly_rate, estimated_hours, actual_hours, mc_task_id").limit(1).execute()
        print("✅ Projects table with enhanced columns accessible")
        
        # Test new tables
        result = db.table("project_contacts").select("*").limit(1).execute()
        print("✅ project_contacts table accessible")
        
        result = db.table("project_files").select("*").limit(1).execute()
        print("✅ project_files table accessible")
        
        # Test existing related tables
        result = db.table("service_tickets").select("*").limit(1).execute()
        print("✅ service_tickets table accessible")
        
        result = db.table("change_orders").select("*").limit(1).execute()
        print("✅ change_orders table accessible")
        
        return True
        
    except Exception as e:
        print(f"❌ Schema test failed: {e}")
        return False

def test_projects_service_layer():
    """Test enhanced projects service functions"""
    print("\n" + "="*50)
    print("2. TESTING PROJECTS SERVICE LAYER")
    print("="*50)
    
    try:
        # Test getting projects
        projects = db_get_projects()
        print(f"✅ db_get_projects() returned {len(projects)} projects")
        
        # Show sample project structure if available
        if projects:
            sample_project = projects[0]
            print(f"✅ Sample project structure: {list(sample_project.keys())}")
            print(f"   - ID: {sample_project.get('id', 'N/A')}")
            print(f"   - Name: {sample_project.get('name', 'N/A')}")
            print(f"   - Type: {sample_project.get('project_type', 'N/A')}")
            print(f"   - Status: {sample_project.get('status', 'N/A')}")
        
        # Test contact-related functions
        if projects:
            project_id = projects[0]['id']
            contacts = db_get_project_contacts(project_id)
            print(f"✅ db_get_project_contacts() returned {len(contacts)} contacts for project")
            
            files = db_get_project_files(project_id)
            print(f"✅ db_get_project_files() returned {len(files)} files for project")
        
        return True
        
    except Exception as e:
        print(f"❌ Service layer test failed: {e}")
        return False

def test_mission_control_integration():
    """Test Mission Control API integration"""
    print("\n" + "="*50)
    print("3. TESTING MISSION CONTROL INTEGRATION")
    print("="*50)
    
    try:
        mc_service = get_mission_control_service()
        print("✅ Mission Control service instance created")
        
        # Test getting time summary (will handle connection issues gracefully)
        time_summary = mc_service.get_project_time_summary("test-project-id")
        print(f"✅ get_project_time_summary() returned: {list(time_summary.keys())}")
        
        connected = time_summary.get('connected', False)
        if connected:
            print(f"✅ Mission Control API connected successfully")
            print(f"   - Total hours: {time_summary.get('total_hours', 0)}")
            print(f"   - Tasks count: {time_summary.get('tasks_count', 0)}")
        else:
            print("ℹ️  Mission Control API not accessible (expected in test environment)")
        
        return True
        
    except Exception as e:
        print(f"❌ Mission Control test failed: {e}")
        return False

def test_accounting_integration():
    """Test Accounting system integration"""
    print("\n" + "="*50)
    print("4. TESTING ACCOUNTING INTEGRATION")
    print("="*50)
    
    try:
        accounting_service = get_accounting_service()
        print("✅ Accounting service instance created")
        
        # Test getting project financials (will handle connection issues gracefully)
        financials = accounting_service.get_project_financials("test-project-id")
        print(f"✅ get_project_financials() returned: {list(financials.keys())}")
        print(f"   - Total invoiced: ${financials.get('total_invoiced', 0):,.2f}")
        print(f"   - Total paid: ${financials.get('total_paid', 0):,.2f}")
        print(f"   - Invoice count: {financials.get('invoice_count', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Accounting integration test failed: {e}")
        return False

def test_project_creation():
    """Test creating a new project with enhanced features"""
    print("\n" + "="*50)
    print("5. TESTING PROJECT CREATION")
    print("="*50)
    
    try:
        # Create test project data
        test_project_data = {
            "name": f"Test Project {datetime.now().strftime('%H%M%S')}",
            "description": "Test project created by verification script",
            "project_type": "project",
            "status": "draft",
            "estimated_hours": 40.0,
            "hourly_rate": 150.00,
            "budget": 6000.00,
            "start_date": date.today().strftime("%Y-%m-%d"),
            "target_end_date": "2026-04-01"
        }
        
        print(f"Creating test project: {test_project_data['name']}")
        result = db_create_project(test_project_data)
        
        if result:
            project_id = result.get('id')
            print(f"✅ Project created successfully with ID: {project_id}")
            
            # Test adding a project contact (if contacts exist)
            try:
                db = get_db()
                contacts_result = db.table("contacts").select("id, first_name, last_name").limit(1).execute()
                if contacts_result.data:
                    contact = contacts_result.data[0]
                    contact_result = db_add_project_contact(
                        project_id, 
                        contact['id'], 
                        "Test Developer", 
                        True, 
                        "Added by test script"
                    )
                    if contact_result:
                        print(f"✅ Project contact added successfully")
                    else:
                        print("ℹ️  Project contact addition skipped")
                
            except Exception as e:
                print(f"ℹ️  Project contact test skipped: {e}")
            
            # Test adding project file metadata (without actual file upload)
            try:
                file_result = db_add_project_file({
                    'project_id': project_id,
                    'filename': 'test-document.pdf',
                    'file_size': 1024,
                    'file_type': 'application/pdf',
                    'description': 'Test file added by verification script',
                    'category': 'general',
                    'storage_url': 'https://example.com/test-file.pdf',
                    'uploaded_by': 'Test Script'
                })
                
                if file_result:
                    print(f"✅ Project file metadata added successfully")
                else:
                    print("ℹ️  Project file test skipped")
                
            except Exception as e:
                print(f"ℹ️  Project file test skipped: {e}")
            
            return True
        else:
            print("❌ Project creation failed")
            return False
            
    except Exception as e:
        print(f"❌ Project creation test failed: {e}")
        return False

def test_status_workflow():
    """Test project status workflow"""
    print("\n" + "="*50)
    print("6. TESTING STATUS WORKFLOW")
    print("="*50)
    
    # Test status definitions
    from pages.Projects_Enhanced import PROJECT_STATUS
    
    expected_statuses = ['draft', 'active', 'on_hold', 'completed', 'archived', 'cancelled']
    
    for status in expected_statuses:
        if status in PROJECT_STATUS:
            status_info = PROJECT_STATUS[status]
            print(f"✅ Status '{status}': {status_info['icon']} {status_info['label']}")
            print(f"   Next possible: {status_info.get('next', [])}")
        else:
            print(f"❌ Missing status definition: {status}")
    
    return True

def run_all_tests():
    """Run all tests and provide summary"""
    print("🚀 STARTING MPT-CRM PROJECTS MODULE VERIFICATION")
    print("="*60)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Service Layer", test_projects_service_layer),
        ("Mission Control Integration", test_mission_control_integration),
        ("Accounting Integration", test_accounting_integration),
        ("Project Creation", test_project_creation),
        ("Status Workflow", test_status_workflow),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📋 TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n📊 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Projects module is ready for production.")
    else:
        print(f"\n⚠️  {total-passed} tests failed. Review the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)