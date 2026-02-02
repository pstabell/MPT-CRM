-- schema_update_v9_drip_schedule.sql
-- Update the drip campaign template to use the new 8-email schedule
-- Day 0, 3, 7, 14, 21, 28, 35, 42
-- Run this in your Supabase SQL Editor

-- Update the existing networking drip campaign template
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
