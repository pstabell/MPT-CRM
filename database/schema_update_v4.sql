-- MPT-CRM Schema Update v4 - Client Intake Support
-- Run this in Supabase SQL Editor

-- ============================================
-- CLIENT INTAKES TABLE
-- Stores full intake questionnaire data
-- ============================================
CREATE TABLE IF NOT EXISTS client_intakes (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    contact_id UUID REFERENCES contacts(id) ON DELETE CASCADE,
    intake_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Company Details
    company_website VARCHAR(500),
    industry VARCHAR(100),
    company_size VARCHAR(50),
    years_in_business VARCHAR(50),

    -- Project Vision
    project_types TEXT[] DEFAULT '{}',
    pain_points TEXT,
    current_solution TEXT,
    desired_outcome TEXT,
    must_have_features TEXT,
    nice_to_have_features TEXT,
    inspiration TEXT,

    -- Technical Scope
    user_types TEXT,
    estimated_users VARCHAR(50),
    login_required VARCHAR(100),
    integrations TEXT[] DEFAULT '{}',
    integration_details TEXT,
    data_migration VARCHAR(100),
    data_details TEXT,
    content_ready VARCHAR(100),
    branding VARCHAR(100),
    domain_status VARCHAR(100),
    domain_name VARCHAR(255),
    hosting VARCHAR(100),
    special_requirements TEXT,

    -- Timeline & Budget
    deadline_type VARCHAR(100),
    target_date DATE,
    deadline_reason VARCHAR(500),
    urgency VARCHAR(50),
    budget_range VARCHAR(50),
    budget_flexibility VARCHAR(100),
    payment_preference VARCHAR(100),
    ongoing_support VARCHAR(100),
    future_phases TEXT,

    -- Decision Making
    decision_maker VARCHAR(100),
    other_stakeholders TEXT,
    decision_timeline VARCHAR(100),
    competing_quotes VARCHAR(100),

    -- Internal Notes
    meeting_notes TEXT,
    red_flags TEXT,
    confidence_level VARCHAR(50),
    next_steps TEXT,
    follow_up_date DATE,

    -- Status
    status VARCHAR(50) DEFAULT 'new',
    proposal_sent BOOLEAN DEFAULT FALSE,
    proposal_sent_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Status options: new, proposal_pending, proposal_sent, negotiating, won, lost

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_intakes_contact ON client_intakes(contact_id);
CREATE INDEX IF NOT EXISTS idx_intakes_status ON client_intakes(status);
CREATE INDEX IF NOT EXISTS idx_intakes_date ON client_intakes(intake_date);

-- ============================================
-- CLIENT ATTACHMENTS TABLE
-- For storing references to client files/documents
-- ============================================
CREATE TABLE IF NOT EXISTS client_attachments (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    contact_id UUID REFERENCES contacts(id) ON DELETE CASCADE,
    intake_id UUID REFERENCES client_intakes(id) ON DELETE SET NULL,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,

    file_name VARCHAR(500) NOT NULL,
    file_path TEXT NOT NULL,  -- Local path or cloud storage URL
    file_type VARCHAR(100),   -- pdf, docx, png, etc.
    file_size INTEGER,        -- Size in bytes
    description TEXT,

    -- Categorization
    category VARCHAR(100),    -- 'requirements', 'branding', 'content', 'contract', 'invoice', 'other'

    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    uploaded_by VARCHAR(100) DEFAULT 'Patrick'
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_attachments_contact ON client_attachments(contact_id);
CREATE INDEX IF NOT EXISTS idx_attachments_intake ON client_attachments(intake_id);
CREATE INDEX IF NOT EXISTS idx_attachments_project ON client_attachments(project_id);

-- ============================================
-- UPDATE TRIGGER
-- ============================================
CREATE TRIGGER intakes_updated_at
    BEFORE UPDATE ON client_intakes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
