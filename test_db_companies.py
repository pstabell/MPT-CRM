#!/usr/bin/env python3
"""
Test database connection and run companies schema update
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

def test_connection():
    """Test Supabase connection"""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_ANON_KEY')
    
    if not url or not key:
        print("Missing Supabase credentials in .env file")
        return False
    
    try:
        client = create_client(url, key)
        # Test with a simple query
        result = client.table('contacts').select('id').limit(1).execute()
        print(f"Connection successful! Found {len(result.data)} test record(s)")
        return client
    except Exception as e:
        print(f"Connection failed: {str(e)}")
        return False

def create_companies_table(client):
    """Create the companies table if it doesn't exist"""
    schema_sql = """
-- Create companies table
CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    website TEXT,
    industry TEXT,
    phone TEXT,
    
    -- Physical Address
    physical_street TEXT,
    physical_city TEXT,
    physical_state TEXT,
    physical_zip TEXT,
    
    -- Mailing Address  
    mailing_street TEXT,
    mailing_city TEXT,
    mailing_state TEXT,
    mailing_zip TEXT,
    
    -- Billing Address
    billing_street TEXT,
    billing_city TEXT,
    billing_state TEXT,
    billing_zip TEXT,
    
    -- Meta
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name);

-- Add columns to contacts table
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS company_id UUID REFERENCES companies(id) ON DELETE SET NULL;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS role TEXT;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS card_image_url_2 TEXT;

-- Create updated_at trigger for companies
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER companies_updated_at
    BEFORE UPDATE ON companies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
"""
    
    try:
        # Execute the schema using supabase rpc
        result = client.rpc('exec_sql', {'sql': schema_sql}).execute()
        print("Companies table and schema updates created successfully!")
        return True
    except Exception as e:
        print(f"Schema creation failed: {str(e)}")
        # Try alternative method - individual statements
        try:
            statements = schema_sql.split(';')
            for stmt in statements:
                stmt = stmt.strip()
                if stmt:
                    client.rpc('exec_sql', {'sql': stmt}).execute()
            print("Schema created with alternative method!")
            return True
        except Exception as e2:
            print(f"Alternative method also failed: {str(e2)}")
            return False

if __name__ == '__main__':
    print("Testing database connection and creating schema...")
    
    client = test_connection()
    if not client:
        sys.exit(1)
    
    if create_companies_table(client):
        print("Schema setup completed successfully!")
        print("You can now run the migration script.")
    else:
        print("Schema setup failed. You may need to run the SQL manually in Supabase.")
        sys.exit(1)