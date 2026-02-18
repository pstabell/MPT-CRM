-- Create crm_sms_history table for SMS message tracking
-- Run this in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS crm_sms_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    contact_id UUID REFERENCES contacts(id) ON DELETE CASCADE,
    phone_number TEXT NOT NULL,
    message TEXT NOT NULL,
    twilio_sid TEXT,
    status TEXT NOT NULL DEFAULT 'sent',
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_crm_sms_history_contact_id ON crm_sms_history(contact_id);
CREATE INDEX IF NOT EXISTS idx_crm_sms_history_sent_at ON crm_sms_history(sent_at DESC);
CREATE INDEX IF NOT EXISTS idx_crm_sms_history_status ON crm_sms_history(status);

-- Enable Row Level Security
ALTER TABLE crm_sms_history ENABLE ROW LEVEL SECURITY;

-- Allow anonymous access for the CRM app (using anon key)
DROP POLICY IF EXISTS "Allow all operations for anon users" ON crm_sms_history;
CREATE POLICY "Allow all operations for anon users" 
ON crm_sms_history FOR ALL 
TO anon 
USING (true) 
WITH CHECK (true);

-- Create trigger for updated_at
CREATE OR REPLACE FUNCTION update_crm_sms_history_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_crm_sms_history_updated_at ON crm_sms_history;
CREATE TRIGGER trigger_update_crm_sms_history_updated_at
    BEFORE UPDATE ON crm_sms_history
    FOR EACH ROW
    EXECUTE FUNCTION update_crm_sms_history_updated_at();