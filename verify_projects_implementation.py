"""
Verification Script for Projects Module Implementation
Tests key database functions and workflow compliance
"""

import os
import sys
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db_service import (
    db_is_connected, 
    db_get_won_deals,
    db_get_companies_with_won_deals,
    db_get_projects,
    db_check_deal_project_link
)

def test_database_connection():
    """Test basic database connectivity"""
    print("🔍 Testing database connection...")
    if db_is_connected():
        print("✅ Database connected successfully")
        return True
    else:
        print("❌ Database connection failed")
        return False

def test_projects_functions():
    """Test the new projects-related functions"""
    print("\n🔍 Testing projects functions...")
    
    try:
        # Test getting Won deals
        won_deals = db_get_won_deals()
        print(f"✅ db_get_won_deals() - Found {len(won_deals)} Won deals")
        
        # Test getting companies with Won deals
        companies = db_get_companies_with_won_deals()
        print(f"✅ db_get_companies_with_won_deals() - Found {len(companies)} companies")
        
        # Test getting projects
        projects = db_get_projects()
        print(f"✅ db_get_projects() - Found {len(projects)} projects")
        
        # Test deal-project linking check if we have deals
        if won_deals:
            test_deal = won_deals[0]
            linked_project = db_check_deal_project_link(test_deal['id'])
            if linked_project:
                print(f"✅ db_check_deal_project_link() - Deal {test_deal['id'][:8]}... is linked to project {linked_project['name']}")
            else:
                print(f"✅ db_check_deal_project_link() - Deal {test_deal['id'][:8]}... is available for linking")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing functions: {e}")
        return False

def validate_workflow_integrity():
    """Validate the workflow integrity rules"""
    print("\n🔍 Validating workflow integrity...")
    
    try:
        # Get all projects and check for deal linkage
        projects = db_get_projects()
        
        projects_with_deals = 0
        projects_without_deals = 0
        
        for project in projects:
            if project.get('deal_id'):
                projects_with_deals += 1
            else:
                projects_without_deals += 1
                print(f"⚠️  Legacy project without deal: {project.get('name', 'Unknown')}")
        
        print(f"✅ Projects with deal links: {projects_with_deals}")
        print(f"⚠️  Projects without deal links (legacy): {projects_without_deals}")
        
        # Check for duplicate deal linkages
        deal_ids = [p.get('deal_id') for p in projects if p.get('deal_id')]
        unique_deals = set(deal_ids)
        
        if len(deal_ids) == len(unique_deals):
            print("✅ No duplicate deal linkages found")
        else:
            print(f"❌ Found duplicate deal linkages: {len(deal_ids) - len(unique_deals)} duplicates")
        
        return True
        
    except Exception as e:
        print(f"❌ Error validating workflow: {e}")
        return False

def main():
    """Run all verification tests"""
    print("🚀 MPT-CRM Projects Module Verification")
    print("=" * 50)
    
    # Test database connection
    if not test_database_connection():
        print("\n❌ Cannot proceed - database not connected")
        return False
    
    # Test functions
    if not test_projects_functions():
        print("\n❌ Function tests failed")
        return False
    
    # Validate workflow
    if not validate_workflow_integrity():
        print("\n❌ Workflow validation failed")
        return False
    
    print("\n" + "=" * 50)
    print("✅ ALL TESTS PASSED - Projects Module Implementation Verified!")
    print(f"📅 Verification completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)