#!/usr/bin/env python3
"""
Test SharePoint Integration for MPT-CRM
=======================================

Test the SharePoint folder move functionality when a deal is marked as "won".
"""

import sys
import os
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from sharepoint_service import move_sharepoint_folder, get_graph_access_token, extract_company_from_url, get_site_info, explore_drive_structure
    from db_service import db_is_connected, db_get_deals, db_get_contacts, db_update_deal_stage
    print("[OK] Successfully imported SharePoint and database services")
except ImportError as e:
    print(f"[ERROR] Import error: {e}")
    sys.exit(1)


def test_graph_authentication():
    """Test if we can authenticate with Microsoft Graph API."""
    print("\n[TEST] Testing Graph API Authentication...")
    token = get_graph_access_token()
    if token:
        print("[OK] Successfully obtained Graph API access token")
        print(f"Token preview: {token[:20]}...")
        return True
    else:
        print("[ERROR] Failed to obtain Graph API access token")
        return False


def test_database_connection():
    """Test database connection."""
    print("\n[TEST] Testing Database Connection...")
    if db_is_connected():
        print("[OK] Database connected successfully")
        return True
    else:
        print("[ERROR] Database not connected")
        return False


def test_extract_company_name():
    """Test extracting company name from SharePoint URL."""
    print("\n[TEST] Testing Company Name Extraction...")
    test_urls = [
        "https://metrotechnologysolutions805.sharepoint.com/sites/MetroPointTechnology/Shared Documents/SALES/Prospects/TestCompany",
        "/sites/MetroPointTechnology/Shared Documents/SALES/Prospects/AnotherCompany",
        "https://metrotechnologysolutions805.sharepoint.com/sites/MetroPointTechnology/Shared%20Documents/SALES/Prospects/Company%20With%20Spaces"
    ]
    
    for url in test_urls:
        company = extract_company_from_url(url)
        print(f"URL: {url}")
        print(f"Extracted Company: {company}")
        print()


def list_current_deals():
    """List current deals to see if any can be tested."""
    print("\n[INFO] Current Deals in Database...")
    deals = db_get_deals(include_contacts=True)
    
    if not deals:
        print("No deals found in database")
        return []
    
    print(f"Found {len(deals)} deals:")
    for deal in deals[:5]:  # Show first 5
        contact_info = ""
        if deal.get('contacts'):
            contact = deal['contacts']
            contact_info = f" - {contact.get('first_name', '')} {contact.get('last_name', '')} ({contact.get('company', '')})"
        
        print(f"  • {deal.get('title', 'Untitled')} [{deal.get('stage', 'no stage')}]{contact_info}")
        
        # Show SharePoint URL if available
        if deal.get('contacts') and deal['contacts'].get('sharepoint_folder_url'):
            print(f"    SharePoint: {deal['contacts']['sharepoint_folder_url']}")
    
    return deals


def list_contacts_with_sharepoint():
    """List contacts that have SharePoint folder URLs."""
    print("\n[INFO] Contacts with SharePoint Folders...")
    contacts = db_get_contacts()
    
    sharepoint_contacts = [c for c in contacts if c.get('sharepoint_folder_url')]
    
    if not sharepoint_contacts:
        print("No contacts found with SharePoint folder URLs")
        return []
    
    print(f"Found {len(sharepoint_contacts)} contacts with SharePoint folders:")
    for contact in sharepoint_contacts:
        name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()
        company = contact.get('company', '')
        url = contact.get('sharepoint_folder_url', '')
        
        print(f"  - {name} ({company})")
        print(f"    URL: {url}")
    
    return sharepoint_contacts


def explore_sharepoint_structure():
    """Explore SharePoint drive structure."""
    print("\n[INFO] Exploring SharePoint Drive Structure...")
    
    site_info = get_site_info()
    if not site_info:
        print("[ERROR] Could not get site info")
        return
    
    site_id = site_info['id']
    drive_id = site_info['drive']['id']
    
    print(f"Site ID: {site_id}")
    print(f"Drive ID: {drive_id}")
    
    # Explore root
    explore_drive_structure(site_id, drive_id)
    
    # Try to find SALES folder
    try:
        explore_drive_structure(site_id, drive_id, "SALES")
        explore_drive_structure(site_id, drive_id, "SALES/Prospects")
        explore_drive_structure(site_id, drive_id, "SALES/Clients")
    except:
        print("[INFO] SALES folder structure not found at expected location")


def test_sharepoint_move(test_url=None, company_name=None):
    """Test SharePoint folder move with a test URL."""
    print("\n[TEST] Testing SharePoint Folder Move...")
    
    if not test_url:
        # Use a test URL - this won't actually exist but tests the API calls
        test_url = "https://metrotechnologysolutions805.sharepoint.com/sites/MetroPointTechnology/Shared Documents/SALES/Prospects/TestCompany"
        company_name = "TestCompany"
    
    print(f"Testing move for: {company_name}")
    print(f"Source URL: {test_url}")
    
    result = move_sharepoint_folder(test_url, company_name)
    
    print(f"\nResult: {result}")
    
    if result.get('success'):
        print(f"[OK] Move successful!")
        print(f"New URL: {result.get('new_url')}")
    else:
        print(f"[ERROR] Move failed: {result.get('error')}")
    
    return result


def main():
    """Run all tests."""
    print("SharePoint Integration Test Suite")
    print("=" * 50)
    
    # Test 1: Database connection
    db_ok = test_database_connection()
    
    # Test 2: Graph API authentication
    auth_ok = test_graph_authentication()
    
    # Test 3: Company name extraction
    test_extract_company_name()
    
    # Test 4: List current deals
    deals = list_current_deals()
    
    # Test 5: List contacts with SharePoint
    sharepoint_contacts = list_contacts_with_sharepoint()
    
    # Test 6: Explore SharePoint structure
    if auth_ok:
        explore_sharepoint_structure()
    
    # Test 7: Test SharePoint move (with test data)
    if auth_ok:
        test_sharepoint_move()
    else:
        print("\n[SKIP] Skipping SharePoint move test - authentication failed")
    
    print("\n" + "=" * 50)
    print("Test Summary")
    print(f"Database: {'OK' if db_ok else 'ERROR'}")
    print(f"Graph Auth: {'OK' if auth_ok else 'ERROR'}")
    print(f"Deals in DB: {len(deals)}")
    print(f"Contacts with SharePoint: {len(sharepoint_contacts)}")
    
    if db_ok and auth_ok:
        print("\n[OK] Integration appears ready for testing with real data!")
    else:
        print("\n[ERROR] Fix the above issues before testing with real data.")


if __name__ == "__main__":
    main()