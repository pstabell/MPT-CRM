-- schema_update_v5.sql
-- Business Card Scanner & Drip Campaign Enrollments
-- Run this in your Supabase SQL Editor

-- =====================================================
-- ADD CARD IMAGE URL TO CONTACTS
-- =====================================================

ALTER TABLE contacts ADD COLUMN IF NOT EXISTS card_image_url TEXT;

-- =====================================================
-- CAMPAIGN ENROLLMENTS TABLE
-- Tracks contacts enrolled in drip campaigns
-- =====================================================

CREATE TABLE IF NOT EXISTS campaign_enrollments (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    contact_id UUID REFERENCES contacts(id) ON DELETE CASCADE,
    campaign_id VARCHAR(100) NOT NULL,  -- e.g., 'networking-drip-6week'
    campaign_name VARCHAR(200) NOT NULL,

    -- Enrollment status
    status VARCHAR(50) DEFAULT 'active',  -- active, paused, completed, unsubscribed
    enrolled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Campaign progress tracking
    current_step INTEGER DEFAULT 0,       -- 0 = Day 0 email, 1 = Day 7, etc.
    total_steps INTEGER DEFAULT 5,        -- Total emails in sequence

    -- Step schedule (stores scheduled dates and sent status for each step)
    -- Format: [{"step": 0, "day": 0, "scheduled_for": "2026-01-25", "sent_at": null}, ...]
    step_schedule JSONB DEFAULT '[]',

    -- Source tracking
    source VARCHAR(100),                  -- 'business_card_scanner', 'manual', etc.
    source_detail TEXT,                   -- Event name, notes, etc.

    -- Email tracking
    last_email_sent_at TIMESTAMP WITH TIME ZONE,
    next_email_scheduled TIMESTAMP WITH TIME ZONE,
    emails_sent INTEGER DEFAULT 0,
    emails_opened INTEGER DEFAULT 0,
    emails_clicked INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_enrollments_contact ON campaign_enrollments(contact_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_campaign ON campaign_enrollments(campaign_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_status ON campaign_enrollments(status);
CREATE INDEX IF NOT EXISTS idx_enrollments_next_email ON campaign_enrollments(next_email_scheduled);

-- Trigger for updated_at (uses existing function from schema.sql)
DROP TRIGGER IF EXISTS enrollments_updated_at ON campaign_enrollments;
CREATE TRIGGER enrollments_updated_at
    BEFORE UPDATE ON campaign_enrollments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- =====================================================
-- DRIP CAMPAIGN TEMPLATES TABLE
-- Stores reusable drip campaign definitions
-- =====================================================

CREATE TABLE IF NOT EXISTS drip_campaign_templates (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    campaign_id VARCHAR(100) UNIQUE NOT NULL,  -- 'networking-drip-6week'
    name VARCHAR(200) NOT NULL,
    description TEXT,

    -- Email sequence (JSONB array)
    -- Format: [{"day": 0, "purpose": "thank_you", "subject": "...", "body": "..."}, ...]
    email_sequence JSONB NOT NULL,

    -- Settings
    is_active BOOLEAN DEFAULT TRUE,
    auto_enroll_contact_types TEXT[] DEFAULT '{}',  -- ['networking']

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Trigger for updated_at
DROP TRIGGER IF EXISTS drip_templates_updated_at ON drip_campaign_templates;
CREATE TRIGGER drip_templates_updated_at
    BEFORE UPDATE ON drip_campaign_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- =====================================================
-- INSERT DEFAULT 6-WEEK NETWORKING CAMPAIGN
-- =====================================================

INSERT INTO drip_campaign_templates (campaign_id, name, description, email_sequence, auto_enroll_contact_types)
VALUES (
    'networking-drip-6week',
    'Networking Follow-Up (6 Week)',
    'Automated follow-up sequence for networking contacts. Focuses on building relationship and asking for referrals.',
    '[
        {
            "day": 0,
            "purpose": "thank_you",
            "subject": "Great meeting you!",
            "body": "Hi {{first_name}},\n\nIt was great meeting you today. I enjoyed our conversation and learning about what you do.\n\nI''m the owner of Metro Point Technology - we build custom software, websites, and business automation tools for local businesses.\n\nI''d love to stay connected. Feel free to reach out anytime if there''s ever anything I can help with.\n\nBest,\n{{your_name}}\nMetro Point Technology, LLC\n{{your_phone}}\n{{your_email}}"
        },
        {
            "day": 7,
            "purpose": "value_add",
            "subject": "Quick resource I thought you''d find useful",
            "body": "Hi {{first_name}},\n\nI came across something that made me think of our conversation last week and wanted to share it with you.\n\nHope you find it useful! Let me know if you''d like to chat more about it.\n\nBest,\n{{your_name}}\n{{your_phone}}"
        },
        {
            "day": 14,
            "purpose": "coffee_invite",
            "subject": "Let''s grab coffee",
            "body": "Hi {{first_name}},\n\nI hope things have been going well!\n\nI''d love to continue our conversation over coffee. Are you free sometime this week or next? I''m usually flexible in the mornings or early afternoons.\n\nThere''s a great spot near downtown Cape Coral if that works for you, or I''m happy to come to you.\n\nLet me know what works!\n\nBest,\n{{your_name}}\n{{your_phone}}"
        },
        {
            "day": 30,
            "purpose": "check_in",
            "subject": "Quick check-in",
            "body": "Hi {{first_name}},\n\nJust wanted to touch base and see how things are going!\n\nIt''s been about a month since we connected, and I wanted to keep the relationship warm. If there''s anything I can help with - technology questions, introductions to people in my network, or just bouncing ideas around - don''t hesitate to reach out.\n\nHope business is treating you well!\n\nBest,\n{{your_name}}\n{{your_phone}}"
        },
        {
            "day": 45,
            "purpose": "referral_ask",
            "subject": "Quick favor to ask",
            "body": "Hi {{first_name}},\n\nI hope all is well! I wanted to reach out with a quick ask.\n\nI''m always looking to connect with business owners who might benefit from custom software, websites, or automation tools. If you know anyone who''s mentioned struggling with:\n- Outdated or clunky software\n- Manual processes that eat up their time\n- A website that needs updating\n- Data scattered across multiple systems\n\nI''d really appreciate an introduction. No pressure at all - just thought I''d put it out there!\n\nAnd of course, if there''s ever anything I can do for you, just let me know.\n\nBest,\n{{your_name}}\nMetro Point Technology, LLC\n{{your_phone}}\n{{your_email}}"
        }
    ]'::jsonb,
    ARRAY['networking']
)
ON CONFLICT (campaign_id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    email_sequence = EXCLUDED.email_sequence,
    auto_enroll_contact_types = EXCLUDED.auto_enroll_contact_types,
    updated_at = NOW();
