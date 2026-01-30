-- MPT-CRM Schema Update v3 - Add Archive Support for Contacts
-- Run this in Supabase SQL Editor

-- Add archived column to contacts table
ALTER TABLE contacts
ADD COLUMN IF NOT EXISTS archived BOOLEAN DEFAULT FALSE;

-- Add archived_at timestamp for tracking when archived
ALTER TABLE contacts
ADD COLUMN IF NOT EXISTS archived_at TIMESTAMP WITH TIME ZONE;

-- Create index for efficient archived filtering
CREATE INDEX IF NOT EXISTS idx_contacts_archived ON contacts(archived);

-- Optional: Add archived column to deals for future use
ALTER TABLE deals
ADD COLUMN IF NOT EXISTS archived BOOLEAN DEFAULT FALSE;

ALTER TABLE deals
ADD COLUMN IF NOT EXISTS archived_at TIMESTAMP WITH TIME ZONE;

CREATE INDEX IF NOT EXISTS idx_deals_archived ON deals(archived);
