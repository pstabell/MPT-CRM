-- schema_update_v14_companies.sql
-- Create companies table and add company relationships to contacts
-- Run this in your Supabase SQL Editor

-- =====================================================
-- 1. CREATE COMPANIES TABLE
-- =====================================================

CREATE TABLE companies (
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

-- =====================================================
-- 2. ADD INDEXES FOR PERFORMANCE
-- =====================================================

CREATE INDEX idx_companies_name ON companies(name);
CREATE INDEX idx_companies_industry ON companies(industry);
CREATE INDEX idx_companies_physical_city ON companies(physical_city);

-- =====================================================
-- 3. ADD COMPANY RELATIONSHIP TO CONTACTS
-- =====================================================

-- Add company_id foreign key (nullable - allows individual contacts)
ALTER TABLE contacts 
ADD COLUMN IF NOT EXISTS company_id UUID REFERENCES companies(id) ON DELETE SET NULL;

-- Add role field for contact's role at the company
ALTER TABLE contacts 
ADD COLUMN IF NOT EXISTS role TEXT;

-- Add second card image URL if not already added
ALTER TABLE contacts 
ADD COLUMN IF NOT EXISTS card_image_url_2 TEXT;

-- =====================================================
-- 4. CREATE UPDATED_AT TRIGGER FOR COMPANIES
-- =====================================================

CREATE TRIGGER companies_updated_at
    BEFORE UPDATE ON companies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- =====================================================
-- 5. ADD COMMENTS FOR DOCUMENTATION
-- =====================================================

COMMENT ON TABLE companies IS 'Companies table - centralizes company information and addresses';
COMMENT ON COLUMN companies.name IS 'Company name';
COMMENT ON COLUMN companies.website IS 'Company website URL';
COMMENT ON COLUMN companies.industry IS 'Industry/business type';
COMMENT ON COLUMN companies.phone IS 'Main company phone number';
COMMENT ON COLUMN companies.physical_street IS 'Physical office address';
COMMENT ON COLUMN companies.mailing_street IS 'Mailing address (if different from physical)';
COMMENT ON COLUMN companies.billing_street IS 'Billing address (if different from physical)';

COMMENT ON COLUMN contacts.company_id IS 'Foreign key to companies table (nullable for individual contacts)';
COMMENT ON COLUMN contacts.role IS 'Contact role at company: Owner, Billing, Technical, Project, General';
COMMENT ON COLUMN contacts.card_image_url_2 IS 'URL for back of business card image';

-- =====================================================
-- NOTES
-- =====================================================
-- After running this schema:
-- 1. Run the data migration script to populate companies from existing contact.company values
-- 2. Update UI to use company-level addresses instead of contact-level addresses
-- 3. Keep contact-level address columns temporarily for reference during migration