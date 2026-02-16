#!/usr/bin/env python3
"""Debug deal-contact relationship."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_service import db_get_deals, db_get_deal, db_get_contact

def main():
    print("=== Debugging Deal-Contact Relationship ===\n")
    
    # Get all deals with and without contacts
    deals_with_contacts = db_get_deals(include_contacts=True)
    deals_without_contacts = db_get_deals(include_contacts=False)
    
    print(f"Deals without contact join: {len(deals_without_contacts)}")
    print(f"Deals with contact join: {len(deals_with_contacts)}")
    
    print("\n=== Deals without contact join ===")
    for deal in deals_without_contacts:
        title = deal.get('title', 'Untitled')
        stage = deal.get('stage', 'no stage')
        contact_id = deal.get('contact_id', 'No contact_id')
        contact_name = deal.get('contact_name', 'No contact_name')
        company_name = deal.get('company_name', 'No company_name')
        
        print(f"- {title} [{stage}]")
        print(f"  Contact ID: {contact_id}")
        print(f"  Contact Name: {contact_name}")
        print(f"  Company: {company_name}")
        
        # If there's a contact_id, try to get the contact directly
        if contact_id and contact_id != 'No contact_id':
            contact = db_get_contact(contact_id)
            if contact:
                has_sp = bool(contact.get('sharepoint_folder_url'))
                sp_url = contact.get('sharepoint_folder_url', 'None')
                print(f"  Contact exists: YES")
                print(f"  Has SharePoint: {has_sp}")
                if has_sp:
                    print(f"  SharePoint URL: {sp_url}")
            else:
                print(f"  Contact exists: NO")
        print()
    
    print("\n=== Deals with contact join ===")
    for deal in deals_with_contacts:
        title = deal.get('title', 'Untitled')
        stage = deal.get('stage', 'no stage')
        contacts = deal.get('contacts', 'No contacts')
        
        print(f"- {title} [{stage}]")
        print(f"  Contacts field: {type(contacts)} = {contacts}")
        
        if contacts and contacts != 'No contacts':
            has_sp = bool(contacts.get('sharepoint_folder_url'))
            print(f"  Has SharePoint: {has_sp}")
            if has_sp:
                print(f"  SharePoint URL: {contacts.get('sharepoint_folder_url')}")
        print()

if __name__ == "__main__":
    main()