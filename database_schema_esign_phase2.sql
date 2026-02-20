-- E-Signature Phase 2: Field Positions and Templates
-- Run this SQL in your Supabase SQL Editor to create the necessary tables

-- Table for storing field layouts (both document-specific and templates)
CREATE TABLE IF NOT EXISTS esign_field_layouts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES esign_documents(id) ON DELETE CASCADE, -- NULL for templates
    template_name TEXT, -- NULL for document-specific layouts
    field_data JSONB NOT NULL, -- JSON containing field positions and metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_esign_field_layouts_document_id ON esign_field_layouts(document_id);
CREATE INDEX IF NOT EXISTS idx_esign_field_layouts_template_name ON esign_field_layouts(template_name) WHERE template_name IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_esign_field_layouts_created_at ON esign_field_layouts(created_at DESC);

-- Ensure template names are unique
ALTER TABLE esign_field_layouts 
ADD CONSTRAINT unique_template_name 
UNIQUE (template_name) 
DEFERRABLE INITIALLY DEFERRED;

-- Sample field_data JSON structure (for reference):
/*
{
    "fields": [
        {
            "id": "field_1234567890_abc123",
            "type": "signature", 
            "page": 1,
            "x": 300,
            "y": 400,
            "width": 120,
            "height": 30
        },
        {
            "id": "field_1234567891_def456", 
            "type": "date",
            "page": 1,
            "x": 500,
            "y": 500,
            "width": 120,
            "height": 30
        }
    ],
    "totalPages": 3,
    "timestamp": "2024-02-20T10:30:00.000Z"
}
*/

-- Enable Row Level Security (RLS) if needed
-- ALTER TABLE esign_field_layouts ENABLE ROW LEVEL SECURITY;

-- Create RLS policies if needed (adjust based on your security requirements)
-- CREATE POLICY "esign_field_layouts_policy" ON esign_field_layouts
--     FOR ALL USING (auth.uid() IS NOT NULL);

-- Add some example templates (optional)
INSERT INTO esign_field_layouts (template_name, field_data) VALUES 
(
    'Standard Contract',
    '{
        "fields": [
            {
                "id": "client_signature",
                "type": "signature",
                "page": 1,
                "x": 300,
                "y": 700,
                "width": 150,
                "height": 40
            },
            {
                "id": "client_date", 
                "type": "date",
                "page": 1,
                "x": 500,
                "y": 700,
                "width": 100,
                "height": 30
            }
        ],
        "totalPages": 1,
        "timestamp": "2024-02-20T10:00:00.000Z"
    }'
),
(
    'Service Agreement',
    '{
        "fields": [
            {
                "id": "client_signature",
                "type": "signature", 
                "page": 2,
                "x": 200,
                "y": 650,
                "width": 150,
                "height": 40
            },
            {
                "id": "client_initials_page1",
                "type": "initials",
                "page": 1,
                "x": 550,
                "y": 750,
                "width": 60,
                "height": 30
            },
            {
                "id": "service_date",
                "type": "date",
                "page": 2,
                "x": 400,
                "y": 650,
                "width": 100,
                "height": 30
            }
        ],
        "totalPages": 2,
        "timestamp": "2024-02-20T10:00:00.000Z"
    }'
)
ON CONFLICT (template_name) DO NOTHING;

-- Update function to automatically set updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_esign_field_layouts_updated_at 
    BEFORE UPDATE ON esign_field_layouts 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();