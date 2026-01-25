-- MPT-CRM Schema Update v2
-- Adds missing columns to deals table to match app functionality
-- Run this in Supabase SQL Editor: https://supabase.com/dashboard/project/qgtjpdviboxxlrivwcan/sql

-- Add new columns to deals table
ALTER TABLE deals
ADD COLUMN IF NOT EXISTS priority VARCHAR(20) DEFAULT 'medium',
ADD COLUMN IF NOT EXISTS source VARCHAR(100),
ADD COLUMN IF NOT EXISTS labels TEXT[] DEFAULT '{}',
ADD COLUMN IF NOT EXISTS days_in_stage INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS contact_name VARCHAR(200),
ADD COLUMN IF NOT EXISTS company_name VARCHAR(200);

-- Add comments explaining the columns
COMMENT ON COLUMN deals.priority IS 'Deal priority: low, medium, high';
COMMENT ON COLUMN deals.source IS 'Lead source: Networking, Referral, Website, LinkedIn, Cold Outreach, etc.';
COMMENT ON COLUMN deals.labels IS 'Array of label strings for categorization';
COMMENT ON COLUMN deals.days_in_stage IS 'Number of days deal has been in current stage';
COMMENT ON COLUMN deals.contact_name IS 'Denormalized contact name for quick display';
COMMENT ON COLUMN deals.company_name IS 'Denormalized company name for quick display';

-- Create index on priority for filtering
CREATE INDEX IF NOT EXISTS idx_deals_priority ON deals(priority);

-- Verify the changes
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'deals'
ORDER BY ordinal_position;
