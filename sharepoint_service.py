"""
sharepoint_service.py — SharePoint Integration for MPT-CRM
==========================================================

Handles SharePoint folder operations via Microsoft Graph API.
Used for automatically moving prospect folders to client folders when deals are won.

Functions:
    - move_sharepoint_folder: Move a folder from Prospects to Clients
    - get_graph_access_token: Get authenticated Graph API token
    - extract_company_from_url: Extract company name from SharePoint URL
"""

import os
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path

# SharePoint configuration
SHAREPOINT_SITE = "metrotechnologysolutions805.sharepoint.com"
SITE_NAME = "MetroPointTechnology"
# Use root site instead of subsite
USE_ROOT_SITE = True
# Updated paths for Tech site
PROSPECTS_PATH = "SALES/Prospects"
CLIENTS_PATH = "SALES/Clients"

# Graph API endpoints
GRAPH_BASE = "https://graph.microsoft.com/v1.0"
TOKEN_CACHE_PATH = Path.home() / ".clawdbot" / "teams-search-token.json"


def load_graph_credentials():
    """Load Microsoft Graph API credentials from clawdbot config."""
    try:
        config_path = Path.home() / ".clawdbot" / "clawdbot.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        msteams = config.get('channels', {}).get('msteams', {})
        return {
            'tenant_id': msteams.get('tenantId'),
            'app_id': msteams.get('appId'),
            'app_password': msteams.get('appPassword')
        }
    except Exception as e:
        print(f"[sharepoint_service] Error loading credentials: {e}")
        return None


def get_cached_user_token():
    """Get cached user access token from teams-search tool."""
    try:
        if not TOKEN_CACHE_PATH.exists():
            return None
        
        with open(TOKEN_CACHE_PATH, 'r') as f:
            data = json.load(f)
        
        # Check if expired (with 5 min buffer)
        if data.get('expiresAt') and datetime.now().timestamp() * 1000 < data['expiresAt'] - 300000:
            return data.get('accessToken')
        
        return None
    except Exception as e:
        print(f"[sharepoint_service] Error loading cached token: {e}")
        return None


def get_app_only_token():
    """Get app-only access token for SharePoint operations."""
    creds = load_graph_credentials()
    if not creds or not all(creds.values()):
        print("[sharepoint_service] Missing Graph API credentials")
        return None
    
    try:
        token_url = f"https://login.microsoftonline.com/{creds['tenant_id']}/oauth2/v2.0/token"
        
        data = {
            'client_id': creds['app_id'],
            'client_secret': creds['app_password'],
            'grant_type': 'client_credentials',
            'scope': 'https://graph.microsoft.com/.default'
        }
        
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        
        token_data = response.json()
        return token_data.get('access_token')
        
    except Exception as e:
        print(f"[sharepoint_service] Error getting app token: {e}")
        return None


def get_graph_access_token():
    """Get the best available Graph API access token."""
    # Try cached user token first (has more permissions)
    token = get_cached_user_token()
    if token:
        return token
    
    # Fall back to app-only token
    return get_app_only_token()


def get_site_info():
    """Get SharePoint site information."""
    token = get_graph_access_token()
    if not token:
        return None
    
    try:
        headers = {'Authorization': f'Bearer {token}'}
        
        # Use the Tech subsite where the SALES folders are located
        url = f"{GRAPH_BASE}/sites/{SHAREPOINT_SITE}:/sites/Tech"
        print(f"[sharepoint_service] Getting site info from: {url}")
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        site_data = response.json()
        print(f"[sharepoint_service] Found site: {site_data.get('displayName', 'Unknown')}")
        
        # Try to get the default drive using the /drive endpoint
        drive_url = f"{url}/drive"
        drive_response = requests.get(drive_url, headers=headers)
        
        if drive_response.ok:
            drive_data = drive_response.json()
            site_data['drive'] = drive_data
            print(f"[sharepoint_service] Found default drive: {drive_data.get('name', 'Unknown')}")
            print(f"[sharepoint_service] Drive ID: {drive_data.get('id', 'Unknown')}")
        else:
            print(f"[sharepoint_service] Could not get default drive: {drive_response.status_code}")
            
            # Fallback: Try to get lists/document libraries
            lists_url = f"{url}/lists"
            lists_response = requests.get(lists_url, headers=headers)
            
            if lists_response.ok:
                lists_data = lists_response.json()
                if 'value' in lists_data:
                    print(f"[sharepoint_service] Found {len(lists_data['value'])} lists:")
                    for lst in lists_data['value'][:5]:
                        print(f"  - {lst.get('displayName', 'No name')} (Template: {lst.get('baseTemplate', 'Unknown')})")
        
        return site_data
        
    except Exception as e:
        print(f"[sharepoint_service] Error getting site info: {e}")
        return None


def explore_drive_structure(site_id, drive_id, path=""):
    """Explore the drive structure to understand folder layout."""
    token = get_graph_access_token()
    if not token:
        return None
    
    try:
        headers = {'Authorization': f'Bearer {token}'}
        
        if path:
            encoded_path = requests.utils.quote(path)
            url = f"{GRAPH_BASE}/sites/{site_id}/drives/{drive_id}/root:/{encoded_path}:/children"
        else:
            url = f"{GRAPH_BASE}/sites/{site_id}/drives/{drive_id}/root/children"
        
        print(f"[sharepoint_service] Exploring: {path or 'root'}")
        response = requests.get(url, headers=headers)
        
        if response.status_code == 404:
            print(f"[sharepoint_service] Path not found: {path}")
            return None
            
        response.raise_for_status()
        
        data = response.json()
        if 'value' in data:
            print(f"[sharepoint_service] Found {len(data['value'])} items:")
            for item in data['value']:
                item_type = "Folder" if 'folder' in item else "File"
                print(f"  - {item_type}: {item.get('name', 'Unknown')}")
        else:
            print("[sharepoint_service] No items found")
        
        return data
        
    except Exception as e:
        print(f"[sharepoint_service] Error exploring {path}: {e}")
        return None


def find_folder_by_path(site_id, drive_id, folder_path):
    """Find a folder by its path in SharePoint."""
    token = get_graph_access_token()
    if not token:
        return None
    
    try:
        headers = {'Authorization': f'Bearer {token}'}
        
        # URL encode the path
        encoded_path = requests.utils.quote(folder_path)
        url = f"{GRAPH_BASE}/sites/{site_id}/drives/{drive_id}/root:/{encoded_path}"
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 404:
            return None  # Folder not found
        
        response.raise_for_status()
        return response.json()
        
    except Exception as e:
        print(f"[sharepoint_service] Error finding folder {folder_path}: {e}")
        return None


def move_folder(site_id, drive_id, folder_id, new_parent_folder_id):
    """Move a folder to a new parent folder."""
    token = get_graph_access_token()
    if not token:
        return None
    
    try:
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # PATCH request to move the folder
        url = f"{GRAPH_BASE}/sites/{site_id}/drives/{drive_id}/items/{folder_id}"
        
        data = {
            'parentReference': {
                'id': new_parent_folder_id
            }
        }
        
        response = requests.patch(url, headers=headers, json=data)
        response.raise_for_status()
        
        return response.json()
        
    except Exception as e:
        print(f"[sharepoint_service] Error moving folder: {e}")
        return None


def extract_company_from_url(sharepoint_url):
    """Extract company name from SharePoint folder URL."""
    if not sharepoint_url:
        return None
    
    try:
        # Expected format: https://metrotechnologysolutions805.sharepoint.com/sites/MetroPointTechnology/Shared%20Documents/SALES/Prospects/CompanyName
        # Or: /sites/MetroPointTechnology/Shared Documents/SALES/Prospects/CompanyName
        
        if "/SALES/Prospects/" in sharepoint_url:
            # Split on Prospects/ and take the part after it
            parts = sharepoint_url.split("/SALES/Prospects/")
            if len(parts) > 1:
                # Get the company name (everything after Prospects/)
                company_part = parts[1].rstrip('/')
                # URL decode if needed
                company_name = requests.utils.unquote(company_part)
                return company_name
        
        return None
        
    except Exception as e:
        print(f"[sharepoint_service] Error extracting company from URL: {e}")
        return None


def build_sharepoint_url(site_id, drive_id, folder_path, folder_name):
    """Build a public SharePoint URL for a folder."""
    try:
        # Build the standard SharePoint URL format
        encoded_path = requests.utils.quote(f"{folder_path}/{folder_name}")
        return f"https://{SHAREPOINT_SITE}/sites/{SITE_NAME}/{encoded_path}"
    except Exception:
        return None


def move_sharepoint_folder(source_sharepoint_url, company_name):
    """
    Move a SharePoint folder from Prospects to Clients.
    
    Args:
        source_sharepoint_url: Current SharePoint URL of the prospect folder
        company_name: Name of the company (used for destination folder)
    
    Returns:
        dict: Result with 'success', 'new_url', and 'error' fields
    """
    result = {
        'success': False,
        'new_url': None,
        'error': None
    }
    
    try:
        # Extract company name from URL if not provided
        if not company_name:
            company_name = extract_company_from_url(source_sharepoint_url)
            if not company_name:
                result['error'] = "Could not extract company name from SharePoint URL"
                return result
        
        print(f"[sharepoint_service] Moving folder for company: {company_name}")
        
        # Get site information
        site_info = get_site_info()
        if not site_info:
            result['error'] = "Could not access SharePoint site"
            return result
        
        site_id = site_info['id']
        drive_id = site_info['drive']['id']
        
        print(f"[sharepoint_service] Site ID: {site_id}")
        print(f"[sharepoint_service] Drive ID: {drive_id}")
        
        # Find the source folder in Prospects
        prospects_folder_path = f"{PROSPECTS_PATH}/{company_name}"
        source_folder = find_folder_by_path(site_id, drive_id, prospects_folder_path)
        
        if not source_folder:
            result['error'] = f"Prospect folder not found: {prospects_folder_path}"
            return result
        
        print(f"[sharepoint_service] Found source folder: {source_folder['name']}")
        
        # Find the Clients parent folder
        clients_parent = find_folder_by_path(site_id, drive_id, CLIENTS_PATH)
        if not clients_parent:
            result['error'] = f"Clients folder not found: {CLIENTS_PATH}"
            return result
        
        print(f"[sharepoint_service] Found clients parent folder")
        
        # Check if folder already exists in Clients
        clients_folder_path = f"{CLIENTS_PATH}/{company_name}"
        existing_client_folder = find_folder_by_path(site_id, drive_id, clients_folder_path)
        
        if existing_client_folder:
            # Folder already exists in Clients - just return the URL
            result['success'] = True
            result['new_url'] = build_sharepoint_url(site_id, drive_id, CLIENTS_PATH, company_name)
            result['error'] = "Folder already exists in Clients folder"
            return result
        
        # Move the folder
        moved_folder = move_folder(site_id, drive_id, source_folder['id'], clients_parent['id'])
        
        if not moved_folder:
            result['error'] = "Failed to move folder"
            return result
        
        # Build new SharePoint URL
        new_url = build_sharepoint_url(site_id, drive_id, CLIENTS_PATH, company_name)
        
        result['success'] = True
        result['new_url'] = new_url
        
        print(f"[sharepoint_service] Successfully moved folder to: {new_url}")
        return result
        
    except Exception as e:
        result['error'] = f"Unexpected error: {str(e)}"
        print(f"[sharepoint_service] Error in move_sharepoint_folder: {e}")
        return result


# Test function
def test_move_folder():
    """Test the folder move functionality."""
    print("Testing SharePoint folder move...")
    
    # Test with a sample URL (replace with actual test data)
    test_url = "https://metrotechnologysolutions805.sharepoint.com/sites/MetroPointTechnology/Shared Documents/SALES/Prospects/TestCompany"
    test_company = "TestCompany"
    
    result = move_sharepoint_folder(test_url, test_company)
    
    print(f"Result: {result}")
    return result


if __name__ == "__main__":
    test_move_folder()