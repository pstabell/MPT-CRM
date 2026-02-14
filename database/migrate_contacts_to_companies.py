#!/usr/bin/env python3
"""
Data Migration: Contacts to Companies Architecture
Migrates existing contact.company TEXT field to companies table and links contacts
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client
import uuid

# Load environment variables
load_dotenv()

def create_supabase_client() -> Client:
    """Create Supabase client"""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_ANON_KEY')
    
    if not url or not key:
        raise Exception("Missing Supabase credentials in .env file")
    
    return create_client(url, key)

def migrate_contacts_to_companies():
    """Main migration function"""
    client = create_supabase_client()
    
    print("Starting contacts to companies migration...")
    
    # Step 1: Get all unique company names from contacts
    print("Fetching existing contacts with company names...")
    
    result = client.table('contacts').select('id, company, first_name, last_name').execute()
    contacts = result.data
    
    print(f"   Found {len(contacts)} contacts")
    
    # Step 2: Extract unique company names (exclude nulls and empty strings)
    company_names = set()
    individual_contacts = []
    
    for contact in contacts:
        company = contact.get('company')
        if company and company.strip():
            company_names.add(company.strip())
        else:
            individual_contacts.append(contact)
    
    print(f"   Found {len(company_names)} unique company names")
    print(f"   Found {len(individual_contacts)} individual contacts (no company)")
    
    # Step 3: Create companies
    print("Creating companies...")
    
    company_mappings = {}  # Maps company_name -> company_id
    
    for company_name in company_names:
        # Check if company already exists
        existing = client.table('companies').select('id, name').eq('name', company_name).execute()
        
        if existing.data:
            company_id = existing.data[0]['id']
            print(f"   Company '{company_name}' already exists (ID: {company_id})")
        else:
            # Create new company
            new_company = {
                'name': company_name,
                'notes': f'Migrated from contact records on {os.environ.get("DATE", "unknown date")}'
            }
            
            result = client.table('companies').insert(new_company).execute()
            company_id = result.data[0]['id']
            print(f"   Created company '{company_name}' (ID: {company_id})")
        
        company_mappings[company_name] = company_id
    
    # Step 4: Update contacts with company_id references
    print("Linking contacts to companies...")
    
    updates_made = 0
    
    for contact in contacts:
        company = contact.get('company')
        
        if company and company.strip() and company.strip() in company_mappings:
            company_id = company_mappings[company.strip()]
            
            # Default role to 'General' for migrated contacts
            update_data = {
                'company_id': company_id,
                'role': 'General'
            }
            
            result = client.table('contacts').update(update_data).eq('id', contact['id']).execute()
            
            if result.data:
                updates_made += 1
                print(f"   Linked {contact['first_name']} {contact['last_name']} -> {company.strip()}")
    
    print(f"Migration completed!")
    print(f"   Companies created: {len(company_mappings)}")
    print(f"   Contacts linked: {updates_made}")
    print(f"   Individual contacts: {len(individual_contacts)}")
    
    return {
        'companies_created': len(company_mappings),
        'contacts_linked': updates_made,
        'individual_contacts': len(individual_contacts)
    }

if __name__ == '__main__':
    try:
        stats = migrate_contacts_to_companies()
        print("\nMigration Summary:")
        print(f"   + {stats['companies_created']} companies created")
        print(f"   + {stats['contacts_linked']} contacts linked to companies") 
        print(f"   + {stats['individual_contacts']} individual contacts (no company)")
        print("\nNext steps:")
        print("   1. Review companies in the UI")
        print("   2. Update contact roles as needed")
        print("   3. Add company addresses and details")
        print("   4. Test the new Companies page")
        
    except Exception as e:
        print(f"Migration failed: {str(e)}")
        sys.exit(1)