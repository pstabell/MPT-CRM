#!/usr/bin/env python3
"""Debug the Tech site structure."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sharepoint_service import get_site_info, explore_drive_structure

def main():
    site = get_site_info()
    
    if not site:
        print("Could not get site info")
        return
    
    print(f"\nSite info:")
    print(f"  ID: {site.get('id', 'Unknown')}")
    print(f"  Name: {site.get('displayName', 'Unknown')}")
    print(f"  Has drive: {'drive' in site}")
    
    if 'drive' in site:
        print(f"  Drive ID: {site['drive']['id']}")
        print(f"  Drive name: {site['drive'].get('name', 'Unknown')}")
        
        # Explore root
        print("\nExploring root folder:")
        explore_drive_structure(site['id'], site['drive']['id'])
        
        # Try SALES folder
        print("\nExploring SALES folder:")
        explore_drive_structure(site['id'], site['drive']['id'], "SALES")
        
    else:
        print("No drive found in site data")
        print(f"Available keys: {list(site.keys())}")

if __name__ == "__main__":
    main()