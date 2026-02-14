#!/usr/bin/env python3
"""
Test database connection and verify new columns
"""

import os
from dotenv import load_dotenv
load_dotenv()

try:
    from supabase import create_client
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        print("ERROR: SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env file")
        exit(1)
    
    print(f"Connecting to: {url}")
    supabase = create_client(url, key)
    
    # Test basic connection
    print("Testing database connection...")
    response = supabase.table('contacts').select('id').limit(1).execute()
    print(f"Database connected successfully! Found {len(response.data)} contact(s)")
    
    # Check if new columns exist
    print("\nChecking for new columns...")
    try:
        # Try to select the new columns
        response = supabase.table('contacts').select(
            'id, first_name, last_name, card_image_url_2, '
            'physical_address_street, physical_address_city, '
            'mailing_address_street, billing_address_street'
        ).limit(1).execute()
        
        if response.data:
            contact = response.data[0]
            print("New columns found in database:")
            print(f"   - card_image_url_2: {'OK' if 'card_image_url_2' in contact else 'MISSING'}")
            print(f"   - physical_address_street: {'OK' if 'physical_address_street' in contact else 'MISSING'}")
            print(f"   - mailing_address_street: {'OK' if 'mailing_address_street' in contact else 'MISSING'}")
            print(f"   - billing_address_street: {'OK' if 'billing_address_street' in contact else 'MISSING'}")
        else:
            print("Query successful, but no contacts found to test with")
            
    except Exception as e:
        print(f"New columns not found - need to apply migration: {e}")
        print("\nTo add the new columns, run this SQL in Supabase SQL Editor:")
        print("   Open: https://supabase.com/dashboard/project/qgtjpdviboxxlrivwcan/sql/new")
        print("   Copy and paste the contents of: database/schema_update_v13_card_images_addresses.sql")
        print("\n   Or run the migration script: python run_migration.py")
        
except ImportError:
    print("Error: supabase package not installed. Run: pip install supabase")
except Exception as e:
    print(f"Error: {e}")

print("\nNext steps:")
print("1. Apply migration if columns are missing (see above)")  
print("2. Test the updated UI by running: streamlit run app.py")
print("3. Test uploading front and back business card images")
print("4. Test adding address information to contacts")