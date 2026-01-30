-- MPT-CRM Schema Update v6 - Performance Optimization
-- Run this in Supabase SQL Editor to add missing indexes

-- Add index on client_intakes.contact_id for faster lookups
-- This should already exist from v4, but we're ensuring it's there
CREATE INDEX IF NOT EXISTS idx_intakes_contact ON client_intakes(contact_id);
CREATE INDEX IF NOT EXISTS idx_intakes_status ON client_intakes(status);
CREATE INDEX IF NOT EXISTS idx_intakes_date ON client_intakes(intake_date DESC);

-- Add index on contacts table for common queries
CREATE INDEX IF NOT EXISTS idx_contacts_type ON contacts(type);
CREATE INDEX IF NOT EXISTS idx_contacts_email_status ON contacts(email_status);
CREATE INDEX IF NOT EXISTS idx_contacts_created_at ON contacts(created_at DESC);

-- Add index on deals for faster contact lookups
CREATE INDEX IF NOT EXISTS idx_deals_contact ON deals(contact_id);
CREATE INDEX IF NOT EXISTS idx_deals_stage ON deals(stage);

-- Add index on activities for contact lookups
CREATE INDEX IF NOT EXISTS idx_activities_contact ON activities(contact_id) WHERE contact_id IS NOT NULL;

-- Analyze tables to update statistics
ANALYZE client_intakes;
ANALYZE contacts;
ANALYZE deals;
ANALYZE activities;
