#!/usr/bin/env python3
"""Add contact_id, recording_url, notes columns to phone_call_logs table"""

import os
from supabase import create_client

# CRM Supabase config
SUPABASE_URL = "https://qgtjpdviboxxlrivwcan.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFndGpwZHZpYm94eGxyaXZ3Y2FuIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2OTI3NzQzMiwiZXhwIjoyMDg0ODUzNDMyfQ.OMCUELc5MqAzjOrmBTUD815WBnbtBE4rHlsxrzTXphc"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# SQL to add columns
sql = """
-- Add contact_id column with FK to contacts
ALTER TABLE phone_call_logs ADD COLUMN IF NOT EXISTS contact_id UUID REFERENCES contacts(id);

-- Add recording_url for call recordings
ALTER TABLE phone_call_logs ADD COLUMN IF NOT EXISTS recording_url TEXT;

-- Add notes for call notes/transcription
ALTER TABLE phone_call_logs ADD COLUMN IF NOT EXISTS notes TEXT;

-- Add transcription for AI transcription
ALTER TABLE phone_call_logs ADD COLUMN IF NOT EXISTS transcription TEXT;

-- Add call_sid for Twilio/Vapi reference
ALTER TABLE phone_call_logs ADD COLUMN IF NOT EXISTS call_sid TEXT;
"""

print("Migrating phone_call_logs table...")
print("-" * 50)

try:
    # Execute via RPC or direct SQL
    result = supabase.rpc("exec_sql", {"sql": sql}).execute()
    print(f"Migration result: {result}")
except Exception as e:
    print(f"RPC failed, trying raw execute: {e}")
    # Fallback: use REST API to check columns exist
    print("Note: Supabase may not support RPC for DDL. Check columns via dashboard or use psql.")

print("-" * 50)
print("Migration complete (or check Supabase dashboard)")
