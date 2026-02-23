-- Create fax history table for MPT-CRM
-- Tracks all fax attempts with email fallback support

CREATE TABLE IF NOT EXISTS crm_fax_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contact_id UUID REFERENCES contacts(id) ON DELETE SET NULL,
    fax_number VARCHAR(20) NOT NULL,
    email_address VARCHAR(255),
    sinch_fax_id VARCHAR(100),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    delivery_method VARCHAR(50) NOT NULL DEFAULT 'fax',
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    delivered_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_fax_history_contact ON crm_fax_history(contact_id);
CREATE INDEX IF NOT EXISTS idx_fax_history_status ON crm_fax_history(status);
CREATE INDEX IF NOT EXISTS idx_fax_history_sent_at ON crm_fax_history(sent_at DESC);
CREATE INDEX IF NOT EXISTS idx_fax_history_sinch_id ON crm_fax_history(sinch_fax_id);

-- RLS policies
ALTER TABLE crm_fax_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow full access to authenticated users" ON crm_fax_history
    FOR ALL
    TO authenticated
    USING (true)
    WITH CHECK (true);

-- Updated trigger
CREATE TRIGGER update_fax_history_updated_at
    BEFORE UPDATE ON crm_fax_history
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE crm_fax_history IS 'Tracks all fax sends with email fallback support';
COMMENT ON COLUMN crm_fax_history.status IS 'sent, delivered, failed, delivered_via_email';
COMMENT ON COLUMN crm_fax_history.delivery_method IS 'fax, email_fallback, both_failed';
