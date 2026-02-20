-- E-Signature Phase 3: Signatures Table
-- Stores individual signatures applied to PDF fields

CREATE TABLE IF NOT EXISTS signatures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pdf_field_id TEXT NOT NULL,           -- ID of the field this signature is for
    document_id UUID NOT NULL,            -- Reference to esign_documents table
    signature_type TEXT NOT NULL CHECK (signature_type IN ('draw', 'type')),
    signature_data TEXT NOT NULL,         -- Base64 image data OR text content
    x_coordinate FLOAT NOT NULL,          -- X position on PDF page
    y_coordinate FLOAT NOT NULL,          -- Y position on PDF page
    width FLOAT NOT NULL,                 -- Width of signature area
    height FLOAT NOT NULL,                -- Height of signature area
    page_number INTEGER NOT NULL,         -- PDF page number (1-based)
    font_family TEXT,                     -- For typed signatures
    font_size INTEGER,                    -- For typed signatures
    applied_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT fk_signatures_document 
        FOREIGN KEY (document_id) 
        REFERENCES esign_documents(id) 
        ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_signatures_document_id ON signatures(document_id);
CREATE INDEX IF NOT EXISTS idx_signatures_pdf_field_id ON signatures(pdf_field_id);
CREATE INDEX IF NOT EXISTS idx_signatures_applied_at ON signatures(applied_at DESC);

-- Enable RLS (Row Level Security)
ALTER TABLE signatures ENABLE ROW LEVEL SECURITY;

-- RLS Policies (same as parent esign_documents)
CREATE POLICY "Enable read access for all users" ON signatures FOR SELECT USING (true);
CREATE POLICY "Enable insert for authenticated users" ON signatures FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update for authenticated users" ON signatures FOR UPDATE USING (true);
CREATE POLICY "Enable delete for authenticated users" ON signatures FOR DELETE USING (true);

-- Grant permissions
GRANT ALL ON signatures TO anon;
GRANT ALL ON signatures TO authenticated;

-- Add comments
COMMENT ON TABLE signatures IS 'Individual signatures applied to PDF document fields';
COMMENT ON COLUMN signatures.pdf_field_id IS 'Unique identifier of the PDF field this signature fills';
COMMENT ON COLUMN signatures.signature_data IS 'Base64 image data for drawn signatures OR plain text for typed signatures';
COMMENT ON COLUMN signatures.signature_type IS 'Type of signature: draw (canvas) or type (text input)';