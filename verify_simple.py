"""
Simple verification script for Projects Module Implementation
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from db_service import (
        db_is_connected, 
        db_get_won_deals,
        db_get_companies_with_won_deals,
        db_get_projects
    )
    
    print("MPT-CRM Projects Module Verification")
    print("=" * 40)
    
    # Test database connection
    if db_is_connected():
        print("OK - Database connected")
        
        # Test functions
        won_deals = db_get_won_deals()
        print(f"OK - Found {len(won_deals)} Won deals")
        
        companies = db_get_companies_with_won_deals()
        print(f"OK - Found {len(companies)} companies with Won deals")
        
        projects = db_get_projects()
        print(f"OK - Found {len(projects)} projects")
        
        # Check deal linkage
        projects_with_deals = sum(1 for p in projects if p.get('deal_id'))
        projects_without_deals = len(projects) - projects_with_deals
        
        print(f"OK - Projects with deal links: {projects_with_deals}")
        print(f"INFO - Legacy projects: {projects_without_deals}")
        
        print("=" * 40)
        print("SUCCESS - All tests passed!")
        
    else:
        print("ERROR - Database not connected")
        print("Check .env file and Supabase configuration")
        
except Exception as e:
    print(f"ERROR - {e}")
    print("Check that the database service is properly configured")