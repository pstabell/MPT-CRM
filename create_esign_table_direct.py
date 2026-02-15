#!/usr/bin/env python3
"""
Create E-Signature Documents Table Directly
===========================================

Creates the esign_documents table using direct SQL execution.
"""

import os
from supabase import create_client

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def create_esign_table():
    """Create the esign_documents table directly"""
    
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_key:
        print("ERROR: Missing Supabase credentials")
        return False
    
    try:
        # Initialize Supabase client
        supabase = create_client(supabase_url, supabase_key)
        
        # Check if table exists by trying to select from it
        try:
            result = supabase.table("esign_documents").select("id").limit(1).execute()
            print("INFO: esign_documents table already exists")
            return True
        except Exception:
            print("INFO: esign_documents table does not exist, creating...")
        
        # Since we can't execute DDL directly, we'll create a test record to trigger table creation
        # This is a workaround - the proper way is to create the table in Supabase dashboard
        
        print("MANUAL STEP REQUIRED:")
        print("Please create the esign_documents table in your Supabase dashboard with this SQL:")
        print("\n" + "="*60)
        
        sql = """
-- Create E-Signature Documents Table
CREATE TABLE IF NOT EXISTS esign_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    pdf_path TEXT NOT NULL,
    signer_email TEXT NOT NULL,
    signer_name TEXT NOT NULL,
    client_name TEXT,
    project_id UUID,
    created_by TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'signed', 'completed', 'expired', 'cancelled')),
    signing_token UUID NOT NULL DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sent_at TIMESTAMPTZ,
    signed_at TIMESTAMPTZ,
    signed_pdf_path TEXT,
    signature_hash TEXT,
    audit_trail JSONB DEFAULT '[]'::jsonb,
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '30 days'),
    sharepoint_url TEXT,
    sharepoint_folder TEXT
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_esign_documents_status ON esign_documents(status);
CREATE INDEX IF NOT EXISTS idx_esign_documents_created_by ON esign_documents(created_by);
CREATE INDEX IF NOT EXISTS idx_esign_documents_signing_token ON esign_documents(signing_token);
CREATE INDEX IF NOT EXISTS idx_esign_documents_signer_email ON esign_documents(signer_email);

-- Enable RLS
ALTER TABLE esign_documents ENABLE ROW LEVEL SECURITY;

-- RLS Policies (allow all operations for now)
CREATE POLICY "Enable all operations for esign_documents" ON esign_documents FOR ALL USING (true);

-- Grant permissions
GRANT ALL ON esign_documents TO anon;
GRANT ALL ON esign_documents TO authenticated;
"""
        
        print(sql)
        print("="*60)
        print("\nAfter running this SQL in Supabase dashboard, re-run the test.")
        
        return False  # Indicates manual step required
        
    except Exception as e:
        print(f"ERROR: Failed to check/create table: {e}")
        return False

if __name__ == "__main__":
    create_esign_table()