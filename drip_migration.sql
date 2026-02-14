-- ROCK 5: Complete Drip Campaign Migration
-- Run this in Supabase SQL Editor to set up all drip campaign infrastructure

-- =====================================================
-- 1. FIX RLS POLICIES
-- =====================================================

-- Allow anon operations on campaign_enrollments (needed for CRM app)
CREATE POLICY IF NOT EXISTS "Allow anon insert on campaign_enrollments"
    ON campaign_enrollments
    FOR INSERT
    TO anon
    WITH CHECK (true);

CREATE POLICY IF NOT EXISTS "Allow anon select on campaign_enrollments"
    ON campaign_enrollments
    FOR SELECT
    TO anon
    USING (true);

CREATE POLICY IF NOT EXISTS "Allow anon update on campaign_enrollments"
    ON campaign_enrollments
    FOR UPDATE
    TO anon
    USING (true)
    WITH CHECK (true);

-- Allow anon operations on drip_campaign_templates
CREATE POLICY IF NOT EXISTS "Allow anon select on drip_campaign_templates"
    ON drip_campaign_templates
    FOR SELECT
    TO anon
    USING (true);

CREATE POLICY IF NOT EXISTS "Allow anon insert on drip_campaign_templates"
    ON drip_campaign_templates
    FOR INSERT
    TO anon
    WITH CHECK (true);

CREATE POLICY IF NOT EXISTS "Allow anon update on drip_campaign_templates"
    ON drip_campaign_templates
    FOR UPDATE
    TO anon
    USING (true)
    WITH CHECK (true);

-- =====================================================
-- 2. INSERT NETWORKING DRIP CAMPAIGN (8 EMAILS)
-- =====================================================

INSERT INTO drip_campaign_templates (campaign_id, name, description, email_sequence, auto_enroll_contact_types)
VALUES (
    'networking-drip-6week',
    'Networking Follow-Up (6 Week)',
    'Automated 8-email follow-up sequence for networking contacts. Day 0 (immediate), 3, 7, 14, 21, 28, 35, 42. Focuses on building relationship and asking for referrals.',
    '[
        {"day": 0, "purpose": "thank_you", "subject": "Great meeting you!"},
        {"day": 3, "purpose": "value_add", "subject": "Quick resource I thought you''d find useful"},
        {"day": 7, "purpose": "coffee_invite", "subject": "Let''s grab coffee"},
        {"day": 14, "purpose": "check_in", "subject": "Quick check-in"},
        {"day": 21, "purpose": "expertise_share", "subject": "Something I''ve been working on"},
        {"day": 28, "purpose": "reconnect", "subject": "Checking in - how''s business?"},
        {"day": 35, "purpose": "referral_soft", "subject": "Quick thought"},
        {"day": 42, "purpose": "referral_ask", "subject": "One last thing"}
    ]'::jsonb,
    ARRAY['networking']
)
ON CONFLICT (campaign_id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    email_sequence = EXCLUDED.email_sequence,
    auto_enroll_contact_types = EXCLUDED.auto_enroll_contact_types,
    updated_at = NOW();

-- =====================================================
-- 3. INSERT LEAD NURTURE DRIP CAMPAIGN (6 EMAILS)
-- =====================================================

INSERT INTO drip_campaign_templates (campaign_id, name, description, email_sequence, auto_enroll_contact_types)
VALUES (
    'lead-drip',
    'Lead Nurture (4 Week)',
    'Automated 6-email nurture sequence for inbound leads from the website. Day 0 (immediate), 2, 5, 10, 18, 28. Focuses on demonstrating value, sharing case studies, and offering a free consultation.',
    '[
        {"day": 0, "purpose": "introduction", "subject": "How we help local businesses save time & grow"},
        {"day": 2, "purpose": "pain_point_awareness", "subject": "Is this eating up your time?"},
        {"day": 5, "purpose": "case_study", "subject": "How a local business cut admin time by 60%"},
        {"day": 10, "purpose": "consultation_offer", "subject": "Free 30-minute strategy call — no strings attached"},
        {"day": 18, "purpose": "overcome_objections", "subject": "The #1 concern I hear from business owners"},
        {"day": 28, "purpose": "final_push", "subject": "Quick offer before the month wraps up"}
    ]'::jsonb,
    ARRAY['lead']
)
ON CONFLICT (campaign_id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    email_sequence = EXCLUDED.email_sequence,
    auto_enroll_contact_types = EXCLUDED.auto_enroll_contact_types,
    updated_at = NOW();

-- =====================================================
-- 4. INSERT PROSPECT CONVERSION DRIP CAMPAIGN (6 EMAILS)
-- =====================================================

INSERT INTO drip_campaign_templates (campaign_id, name, description, email_sequence, auto_enroll_contact_types)
VALUES (
    'prospect-drip',
    'Prospect Conversion (5 Week)',
    'Automated 6-email conversion sequence for prospects. Day 0, 3, 7, 14, 21, 35. Focuses on ROI, proposals, and social proof.',
    '[
        {"day": 0, "purpose": "personalized_followup", "subject": "Following up on our conversation"},
        {"day": 3, "purpose": "relevant_case_study", "subject": "A project that reminded me of your situation"},
        {"day": 7, "purpose": "roi_breakdown", "subject": "The numbers behind automation (they''re pretty compelling)"},
        {"day": 14, "purpose": "proposal_offer", "subject": "Ready to put something concrete together for you"},
        {"day": 21, "purpose": "social_proof_urgency", "subject": "Our schedule is filling up — wanted to let you know"},
        {"day": 35, "purpose": "last_chance", "subject": "The door is always open"}
    ]'::jsonb,
    ARRAY['prospect']
)
ON CONFLICT (campaign_id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    email_sequence = EXCLUDED.email_sequence,
    auto_enroll_contact_types = EXCLUDED.auto_enroll_contact_types,
    updated_at = NOW();

-- =====================================================
-- 5. INSERT CLIENT SUCCESS DRIP CAMPAIGN (6 EMAILS)
-- =====================================================

INSERT INTO drip_campaign_templates (campaign_id, name, description, email_sequence, auto_enroll_contact_types)
VALUES (
    'client-drip',
    'Client Success (8 Week)',
    'Automated 6-email success sequence for new clients. Day 0, 7, 14, 28, 42, 56. Focuses on onboarding, satisfaction, upselling, and referrals.',
    '[
        {"day": 0, "purpose": "welcome_onboarding", "subject": "Welcome aboard — here''s what to expect!"},
        {"day": 7, "purpose": "check_in", "subject": "Quick check-in — how''s everything going?"},
        {"day": 14, "purpose": "tips_best_practices", "subject": "Tips to get the most out of your new solution"},
        {"day": 28, "purpose": "satisfaction_review", "subject": "How are we doing? (+ a quick favor)"},
        {"day": 42, "purpose": "upsell_awareness", "subject": "Have you thought about this?"},
        {"day": 56, "purpose": "referral_ask", "subject": "Know anyone who could use our help?"}
    ]'::jsonb,
    ARRAY['client']
)
ON CONFLICT (campaign_id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    email_sequence = EXCLUDED.email_sequence,
    auto_enroll_contact_types = EXCLUDED.auto_enroll_contact_types,
    updated_at = NOW();

-- =====================================================
-- 6. VERIFY INSTALLATION
-- =====================================================

-- Check that all templates were created
SELECT campaign_id, name, array_length(email_sequence, 1) as email_count
FROM drip_campaign_templates
ORDER BY campaign_id;