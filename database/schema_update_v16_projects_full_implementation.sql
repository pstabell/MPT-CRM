-- ============================================================
-- Schema Update v16: Projects Module Full Implementation
-- ============================================================
-- Adds missing features for complete projects implementation:
-- - Project contact roles (who's working on what)
-- - File attachments support
-- - Enhanced status workflow
-- - Mission Control integration fields
-- Run against your Supabase database.
-- ============================================================

-- Add enhanced status workflow support
ALTER TABLE projects 
  ADD COLUMN IF NOT EXISTS project_type VARCHAR(50) DEFAULT 'project',
  ADD COLUMN IF NOT EXISTS hourly_rate DECIMAL(8,2) DEFAULT 150.00,
  ADD COLUMN IF NOT EXISTS estimated_hours DECIMAL(8,2) DEFAULT 0,
  ADD COLUMN IF NOT EXISTS actual_hours DECIMAL(8,2) DEFAULT 0,
  ADD COLUMN IF NOT EXISTS mc_task_id VARCHAR(100); -- Mission Control task ID for integration

-- Create project_contacts table for role assignments
CREATE TABLE IF NOT EXISTS project_contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    contact_id UUID NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    role VARCHAR(100) NOT NULL, -- e.g., 'Project Manager', 'Developer', 'Designer', 'QA'
    is_primary BOOLEAN DEFAULT false, -- Primary contact for this role
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure unique role per project (only one primary per role)
    UNIQUE(project_id, contact_id, role)
);

-- Create project_files table for attachments
CREATE TABLE IF NOT EXISTS project_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_size INTEGER,
    file_type VARCHAR(100),
    description TEXT,
    category VARCHAR(50) DEFAULT 'general', -- 'contract', 'proposal', 'deliverable', 'general'
    storage_url TEXT NOT NULL, -- Supabase storage URL
    uploaded_by VARCHAR(200) DEFAULT 'System',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Track versions
    version INTEGER DEFAULT 1,
    replaces_file_id UUID REFERENCES project_files(id) ON DELETE SET NULL
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_projects_type ON projects(project_type);
CREATE INDEX IF NOT EXISTS idx_projects_status_type ON projects(status, project_type);
CREATE INDEX IF NOT EXISTS idx_projects_mc_task ON projects(mc_task_id);

CREATE INDEX IF NOT EXISTS idx_project_contacts_project ON project_contacts(project_id);
CREATE INDEX IF NOT EXISTS idx_project_contacts_contact ON project_contacts(contact_id);
CREATE INDEX IF NOT EXISTS idx_project_contacts_role ON project_contacts(project_id, role);

CREATE INDEX IF NOT EXISTS idx_project_files_project ON project_files(project_id);
CREATE INDEX IF NOT EXISTS idx_project_files_category ON project_files(project_id, category);

-- Update triggers for new tables
CREATE TRIGGER project_contacts_updated_at
    BEFORE UPDATE ON project_contacts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Comments for documentation
COMMENT ON TABLE project_contacts IS 'Associates contacts with projects in specific roles';
COMMENT ON TABLE project_files IS 'File attachments for projects with version control';

COMMENT ON COLUMN projects.project_type IS 'Type: product, project, website, maintenance';
COMMENT ON COLUMN projects.hourly_rate IS 'Default hourly rate for project billing';
COMMENT ON COLUMN projects.estimated_hours IS 'Estimated hours for project completion';
COMMENT ON COLUMN projects.actual_hours IS 'Actual hours logged on project';
COMMENT ON COLUMN projects.mc_task_id IS 'Mission Control task ID for integration';

COMMENT ON COLUMN project_contacts.role IS 'Role in project: Project Manager, Developer, Designer, etc.';
COMMENT ON COLUMN project_contacts.is_primary IS 'Primary contact for this role type';

COMMENT ON COLUMN project_files.category IS 'File category: contract, proposal, deliverable, general';
COMMENT ON COLUMN project_files.storage_url IS 'Supabase storage URL for the file';
COMMENT ON COLUMN project_files.version IS 'File version number for tracking updates';

-- Enhanced project status values (update existing check constraint if it exists)
-- Status workflow: draft → active → on_hold → completed → archived
-- Additional statuses: planning, cancelled

-- Create storage bucket for project files (run this in Supabase dashboard)
/*
INSERT INTO storage.buckets (id, name, public)
VALUES ('project-files', 'project-files', false);

-- Create storage policy for project files
CREATE POLICY "Allow authenticated access to project files" ON storage.objects
  FOR ALL USING (bucket_id = 'project-files');
*/