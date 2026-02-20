-- Schema Update v18: SMS Messages Table
-- Add SMS messaging capabilities to MPT-CRM

-- ============================================
-- SMS MESSAGES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS sms_messages (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    contact_id UUID REFERENCES contacts(id) ON DELETE CASCADE,
    
    -- Message content
    body TEXT NOT NULL,
    direction VARCHAR(20) NOT NULL CHECK (direction IN ('inbound', 'outbound')),
    
    -- Twilio fields
    twilio_message_sid VARCHAR(100) UNIQUE,
    from_number VARCHAR(20) NOT NULL,
    to_number VARCHAR(20) NOT NULL,
    
    -- Status tracking
    status VARCHAR(50) DEFAULT 'sending',
    -- Possible values: sending, sent, delivered, undelivered, failed, received
    
    -- Metadata
    error_code VARCHAR(50),
    error_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE
);

-- ============================================
-- INDEXES for performance
-- ============================================
CREATE INDEX IF NOT EXISTS idx_sms_messages_contact ON sms_messages(contact_id);
CREATE INDEX IF NOT EXISTS idx_sms_messages_direction ON sms_messages(direction);
CREATE INDEX IF NOT EXISTS idx_sms_messages_created ON sms_messages(created_at);
CREATE INDEX IF NOT EXISTS idx_sms_messages_twilio_sid ON sms_messages(twilio_message_sid);

-- ============================================
-- Add phone number validation helper function
-- ============================================
CREATE OR REPLACE FUNCTION format_phone_number(phone_input TEXT)
RETURNS TEXT AS $$
DECLARE
    cleaned_phone TEXT;
    formatted_phone TEXT;
BEGIN
    -- Remove all non-digit characters
    cleaned_phone := REGEXP_REPLACE(phone_input, '[^0-9]', '', 'g');
    
    -- Add +1 if it's a 10-digit US number
    IF LENGTH(cleaned_phone) = 10 THEN
        formatted_phone := '+1' || cleaned_phone;
    ELSIF LENGTH(cleaned_phone) = 11 AND LEFT(cleaned_phone, 1) = '1' THEN
        formatted_phone := '+' || cleaned_phone;
    ELSE
        formatted_phone := '+' || cleaned_phone;
    END IF;
    
    RETURN formatted_phone;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- Add SMS message to activities when inserted
-- ============================================
CREATE OR REPLACE FUNCTION log_sms_activity()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO activities (
        type,
        description,
        contact_id,
        created_at
    )
    VALUES (
        CASE 
            WHEN NEW.direction = 'outbound' THEN 'sms_sent'
            ELSE 'sms_received'
        END,
        CASE 
            WHEN NEW.direction = 'outbound' THEN 'SMS sent: ' || LEFT(NEW.body, 100) || CASE WHEN LENGTH(NEW.body) > 100 THEN '...' ELSE '' END
            ELSE 'SMS received: ' || LEFT(NEW.body, 100) || CASE WHEN LENGTH(NEW.body) > 100 THEN '...' ELSE '' END
        END,
        NEW.contact_id,
        NEW.created_at
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER sms_activity_log
    AFTER INSERT ON sms_messages
    FOR EACH ROW EXECUTE FUNCTION log_sms_activity();

-- ============================================
-- Sample data for testing (optional)
-- ============================================
-- This will be populated by the application, not by migration