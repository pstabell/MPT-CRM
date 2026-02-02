-- ============================================================
-- Schema Update v7: Project Pricing & Portfolio Tracking
-- ============================================================
-- Adds pricing, billing, and classification columns to projects.
-- MPT is its own client — every project gets a dollar value.
-- Project Value = estimated_hours x hourly_rate. Simple.
-- Run once against your Supabase database.
-- ============================================================

-- New columns on the projects table
ALTER TABLE projects
  ADD COLUMN IF NOT EXISTS hourly_rate DECIMAL(8,2) DEFAULT 150.00,
  ADD COLUMN IF NOT EXISTS estimated_hours DECIMAL(8,2),
  ADD COLUMN IF NOT EXISTS project_type VARCHAR(50),
  ADD COLUMN IF NOT EXISTS client_name VARCHAR(200),
  ADD COLUMN IF NOT EXISTS hours_logged DECIMAL(8,2) DEFAULT 0;

-- Add a CHECK constraint for project_type
ALTER TABLE projects
  ADD CONSTRAINT chk_project_type
  CHECK (project_type IN ('product', 'project', 'website'));

-- Index for quick filtering by type and status
CREATE INDEX IF NOT EXISTS idx_projects_type ON projects (project_type);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects (status);

-- Comment for documentation
COMMENT ON COLUMN projects.hourly_rate IS 'Billing rate per hour (default $150)';
COMMENT ON COLUMN projects.estimated_hours IS 'Total estimated hours for the project';
COMMENT ON COLUMN projects.project_type IS 'Classification: product, internal, or website';
COMMENT ON COLUMN projects.client_name IS 'Denormalized client name for display';
COMMENT ON COLUMN projects.hours_logged IS 'Cached total hours from time_entries';
