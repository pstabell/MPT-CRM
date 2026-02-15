-- E-Signature Documents Table Migration
-- Create table for managing e-signature document workflow

CREATE TABLE IF NOT EXISTS esign_documents (
    id UUID PRIMARY KEY,
    title TEXT NOT NULL,
    pdf_path TEXT NOT NULL,
    signer_email TEXT NOT NULL,
    signer_name TEXT NOT NULL,
    client_name TEXT,
    project_id UUID,
    created_by TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'signed', 'completed', 'expired', 'cancelled')),
    signing_token UUID NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sent_at TIMESTAMPTZ,
    signed_at TIMESTAMPTZ,
    signed_pdf_path TEXT,
    signature_hash TEXT,
    audit_trail JSONB DEFAULT '[]'::jsonb,
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '30 days'),
    
    -- Add foreign key constraint if projects table exists
    CONSTRAINT fk_esign_documents_project 
        FOREIGN KEY (project_id) 
        REFERENCES projects(id) 
        ON DELETE SET NULL
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_esign_documents_status ON esign_documents(status);
CREATE INDEX IF NOT EXISTS idx_esign_documents_created_by ON esign_documents(created_by);
CREATE INDEX IF NOT EXISTS idx_esign_documents_signing_token ON esign_documents(signing_token);
CREATE INDEX IF NOT EXISTS idx_esign_documents_signer_email ON esign_documents(signer_email);
CREATE INDEX IF NOT EXISTS idx_esign_documents_created_at ON esign_documents(created_at DESC);

-- Enable RLS (Row Level Security)
ALTER TABLE esign_documents ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Enable read access for all users" ON esign_documents FOR SELECT USING (true);
CREATE POLICY "Enable insert for authenticated users" ON esign_documents FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update for authenticated users" ON esign_documents FOR UPDATE USING (true);
CREATE POLICY "Enable delete for authenticated users" ON esign_documents FOR DELETE USING (true);

-- Grant permissions
GRANT ALL ON esign_documents TO anon;
GRANT ALL ON esign_documents TO authenticated;

-- Add comments
COMMENT ON TABLE esign_documents IS 'E-signature document workflow management';
COMMENT ON COLUMN esign_documents.signing_token IS 'Secure UUID token for public signing access';
COMMENT ON COLUMN esign_documents.signature_hash IS 'SHA-256 hash of PDF + signature + timestamp for verification';
COMMENT ON COLUMN esign_documents.audit_trail IS 'JSON array of audit events with timestamps';