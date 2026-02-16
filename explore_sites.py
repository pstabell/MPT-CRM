#!/usr/bin/env python3
"""Explore SharePoint sites to find the correct one."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sharepoint_service import get_graph_access_token, GRAPH_BASE
import requests

def list_all_sites():
    """List all available SharePoint sites."""
    token = get_graph_access_token()
    if not token:
        print("Could not get access token")
        return
    
    headers = {'Authorization': f'Bearer {token}'}
    url = f"{GRAPH_BASE}/sites"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        sites_data = response.json()
        if 'value' in sites_data:
            print(f"Found {len(sites_data['value'])} sites:")
            for site in sites_data['value']:
                name = site.get('displayName', 'No name')
                url = site.get('webUrl', 'No URL')
                site_id = site.get('id', 'No ID')
                print(f"  - {name}")
                print(f"    URL: {url}")
                print(f"    ID: {site_id}")
                print()
        else:
            print("No sites found")
            
    except Exception as e:
        print(f"Error: {e}")

def search_for_tech_site():
    """Search for a site with 'Tech' in the name."""
    token = get_graph_access_token()
    if not token:
        print("Could not get access token")
        return
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # Try to access the Tech subsite directly
    tech_url = f"{GRAPH_BASE}/sites/metrotechnologysolutions805.sharepoint.com:/sites/Tech"
    
    try:
        print(f"Trying: {tech_url}")
        response = requests.get(tech_url, headers=headers)
        response.raise_for_status()
        
        site_data = response.json()
        print(f"Found Tech site: {site_data.get('displayName', 'Unknown')}")
        print(f"Site ID: {site_data.get('id', 'Unknown')}")
        
        # Get its drive
        if 'drive' in site_data:
            drive_id = site_data['drive']['id']
            print(f"Drive ID: {drive_id}")
        else:
            drives_url = f"{tech_url}/drives"
            drives_response = requests.get(drives_url, headers=headers)
            if drives_response.ok:
                drives_data = drives_response.json()
                print(f"Found drives: {[d.get('name') for d in drives_data.get('value', [])]}")
        
        return site_data
        
    except Exception as e:
        print(f"Tech site error: {e}")
        return None

if __name__ == "__main__":
    print("=== All Sites ===")
    list_all_sites()
    
    print("\n=== Tech Site Search ===")
    search_for_tech_site()