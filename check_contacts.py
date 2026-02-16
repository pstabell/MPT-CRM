#!/usr/bin/env python3
"""Check contacts and their SharePoint URLs."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_service import db_get_contacts, db_get_deals

def main():
    contacts = db_get_contacts()
    sp_contacts = [c for c in contacts if c.get('sharepoint_folder_url')]
    
    print(f"Total contacts: {len(contacts)}")
    print(f"Contacts with SharePoint: {len(sp_contacts)}")
    
    for c in sp_contacts:
        name = f"{c.get('first_name', '')} {c.get('last_name', '')}".strip()
        company = c.get('company', '')
        contact_id = c.get('id')
        url = c.get('sharepoint_folder_url', '')
        
        print(f"- {name} ({company})")
        print(f"  ID: {contact_id}")
        print(f"  URL: {url}")
        print()
    
    # Also check deals
    deals = db_get_deals(include_contacts=True)
    print(f"Total deals: {len(deals)}")
    
    deals_with_sp = []
    for deal in deals:
        if deal.get('contacts') and deal['contacts'].get('sharepoint_folder_url'):
            deals_with_sp.append(deal)
    
    print(f"Deals with SharePoint contacts: {len(deals_with_sp)}")
    
    for deal in deals_with_sp:
        print(f"- Deal: {deal.get('title', 'Untitled')} [{deal.get('stage', 'no stage')}]")
        contact = deal['contacts']
        print(f"  Contact: {contact.get('first_name', '')} {contact.get('last_name', '')} ({contact.get('company', '')})")
        print()

if __name__ == "__main__":
    main()