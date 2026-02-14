-- schema_update_v13_card_images_addresses.sql
-- Add second card image URL and address fields to contacts table
-- Run this in your Supabase SQL Editor

-- =====================================================
-- 1. ADD SECOND CARD IMAGE URL COLUMN
-- =====================================================

-- Add card_image_url_2 for storing back-of-card images
ALTER TABLE contacts 
ADD COLUMN IF NOT EXISTS card_image_url_2 TEXT;

COMMENT ON COLUMN contacts.card_image_url_2 IS 'URL for the second/back side business card image';

-- =====================================================
-- 2. ADD PHYSICAL ADDRESS COLUMNS  
-- =====================================================

ALTER TABLE contacts 
ADD COLUMN IF NOT EXISTS physical_address_street TEXT;

ALTER TABLE contacts 
ADD COLUMN IF NOT EXISTS physical_address_city VARCHAR(100);

ALTER TABLE contacts 
ADD COLUMN IF NOT EXISTS physical_address_state VARCHAR(50);

ALTER TABLE contacts 
ADD COLUMN IF NOT EXISTS physical_address_zip VARCHAR(20);

-- =====================================================
-- 3. ADD MAILING ADDRESS COLUMNS
-- =====================================================

ALTER TABLE contacts 
ADD COLUMN IF NOT EXISTS mailing_address_street TEXT;

ALTER TABLE contacts 
ADD COLUMN IF NOT EXISTS mailing_address_city VARCHAR(100);

ALTER TABLE contacts 
ADD COLUMN IF NOT EXISTS mailing_address_state VARCHAR(50);

ALTER TABLE contacts 
ADD COLUMN IF NOT EXISTS mailing_address_zip VARCHAR(20);

-- =====================================================
-- 4. ADD BILLING ADDRESS COLUMNS
-- =====================================================

ALTER TABLE contacts 
ADD COLUMN IF NOT EXISTS billing_address_street TEXT;

ALTER TABLE contacts 
ADD COLUMN IF NOT EXISTS billing_address_city VARCHAR(100);

ALTER TABLE contacts 
ADD COLUMN IF NOT EXISTS billing_address_state VARCHAR(50);

ALTER TABLE contacts 
ADD COLUMN IF NOT EXISTS billing_address_zip VARCHAR(20);

-- =====================================================
-- 5. ADD COMMENTS FOR DOCUMENTATION
-- =====================================================

COMMENT ON COLUMN contacts.physical_address_street IS 'Physical/office address street and number';
COMMENT ON COLUMN contacts.physical_address_city IS 'Physical address city';  
COMMENT ON COLUMN contacts.physical_address_state IS 'Physical address state/province';
COMMENT ON COLUMN contacts.physical_address_zip IS 'Physical address postal/zip code';

COMMENT ON COLUMN contacts.mailing_address_street IS 'Mailing address street and number (if different from physical)';
COMMENT ON COLUMN contacts.mailing_address_city IS 'Mailing address city';
COMMENT ON COLUMN contacts.mailing_address_state IS 'Mailing address state/province';  
COMMENT ON COLUMN contacts.mailing_address_zip IS 'Mailing address postal/zip code';

COMMENT ON COLUMN contacts.billing_address_street IS 'Billing address street and number (if different from physical)';
COMMENT ON COLUMN contacts.billing_address_city IS 'Billing address city';
COMMENT ON COLUMN contacts.billing_address_state IS 'Billing address state/province';
COMMENT ON COLUMN contacts.billing_address_zip IS 'Billing address postal/zip code';

-- =====================================================
-- 6. ADD INDEXES FOR PERFORMANCE (OPTIONAL)
-- =====================================================

-- Add index on physical address city for location-based queries
CREATE INDEX IF NOT EXISTS idx_contacts_physical_city ON contacts(physical_address_city);

-- Add index on mailing address city  
CREATE INDEX IF NOT EXISTS idx_contacts_mailing_city ON contacts(mailing_address_city);

-- Migration completed successfully
-- New columns added:
-- - card_image_url_2 (TEXT) - for back of card images
-- - physical_address_street, physical_address_city, physical_address_state, physical_address_zip 
-- - mailing_address_street, mailing_address_city, mailing_address_state, mailing_address_zip
-- - billing_address_street, billing_address_city, billing_address_state, billing_address_zip