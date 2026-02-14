-- ============================================================
-- Schema Update v16: Project Stop/Void Functionality
-- ============================================================
-- Adds support for stopping (on-hold) and voiding (cancelled) projects
-- with reason tracking and history logging.
-- ============================================================

-- Add status change reason tracking
ALTER TABLE projects 
  ADD COLUMN IF NOT EXISTS status_reason TEXT,
  ADD COLUMN IF NOT EXISTS status_changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  ADD COLUMN IF NOT EXISTS status_changed_by VARCHAR(100) DEFAULT 'Metro Bot';

-- Create project history table for status change tracking
CREATE TABLE IF NOT EXISTS project_history (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    old_status VARCHAR(50),
    new_status VARCHAR(50),
    reason TEXT,
    changed_by VARCHAR(100) DEFAULT 'Metro Bot',
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Update CHECK constraint to include new status values
-- First drop existing constraint if it exists
DO $$ 
BEGIN 
    IF EXISTS (SELECT 1 FROM information_schema.table_constraints 
               WHERE constraint_name = 'chk_project_status' 
               AND table_name = 'projects') THEN
        ALTER TABLE projects DROP CONSTRAINT chk_project_status;
    END IF;
END $$;

-- Add updated constraint with all valid status values
ALTER TABLE projects 
  ADD CONSTRAINT chk_project_status 
  CHECK (status IN ('planning', 'active', 'on-hold', 'voided', 'completed', 'maintenance'));

-- Index for project history queries
CREATE INDEX IF NOT EXISTS idx_project_history_project_id ON project_history(project_id);
CREATE INDEX IF NOT EXISTS idx_project_history_changed_at ON project_history(changed_at);

-- Function to automatically log status changes
CREATE OR REPLACE FUNCTION log_project_status_change()
RETURNS TRIGGER AS $$
BEGIN
    -- Only log if status actually changed
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO project_history (project_id, old_status, new_status, reason, changed_by)
        VALUES (NEW.id, OLD.status, NEW.status, NEW.status_reason, NEW.status_changed_by);
        
        -- Update the changed_at timestamp
        NEW.status_changed_at = NOW();
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically log status changes
DROP TRIGGER IF EXISTS project_status_change_trigger ON projects;
CREATE TRIGGER project_status_change_trigger
    BEFORE UPDATE ON projects
    FOR EACH ROW
    EXECUTE FUNCTION log_project_status_change();

-- Comments for documentation
COMMENT ON COLUMN projects.status_reason IS 'Reason for the current status (required for on-hold/voided)';
COMMENT ON COLUMN projects.status_changed_at IS 'When the status was last changed';
COMMENT ON COLUMN projects.status_changed_by IS 'Who changed the status';
COMMENT ON TABLE project_history IS 'Audit log of all project status changes';