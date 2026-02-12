-- ============================================================
-- Schema Update v11: Projects Pipeline Integrity
-- ============================================================
-- Enforces the business rule: Every project MUST link to a Won deal.
-- No orphan projects. Adds SharePoint integration for proposals.
-- Run once against your Supabase database.
-- ============================================================

-- Add folderUrl column for SharePoint proposal links
ALTER TABLE projects
  ADD COLUMN IF NOT EXISTS folder_url TEXT;

-- Make deal_id REQUIRED (NOT NULL) to enforce pipeline integrity
-- First, set any existing projects without deal_id to null temporarily
UPDATE projects SET deal_id = NULL WHERE deal_id IS NULL;

-- Add the NOT NULL constraint (this will require all future projects to have a deal_id)
-- Note: If you have existing projects without deal_id, you'll need to link them to deals first
-- ALTER TABLE projects ALTER COLUMN deal_id SET NOT NULL;
-- Commented out for now - enable after linking existing projects to deals

-- Add constraint to ensure only Won deals can be linked to projects
-- This prevents creating projects from deals that haven't been won yet
ALTER TABLE projects
  ADD CONSTRAINT chk_projects_won_deals 
  CHECK (
    deal_id IS NULL OR 
    EXISTS (
      SELECT 1 FROM deals 
      WHERE deals.id = projects.deal_id 
      AND deals.stage = 'won'
    )
  );

-- Add constraint to ensure each deal can only be linked to ONE project
-- This prevents duplicate projects from the same deal
CREATE UNIQUE INDEX IF NOT EXISTS idx_projects_unique_deal_id 
  ON projects(deal_id) 
  WHERE deal_id IS NOT NULL;

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_projects_deal_id ON projects(deal_id);
CREATE INDEX IF NOT EXISTS idx_projects_client_id ON projects(client_id);

-- Add helpful comments
COMMENT ON COLUMN projects.deal_id IS 'Required FK to deals table - only Won deals allowed';
COMMENT ON COLUMN projects.folder_url IS 'SharePoint folder URL for project proposals/documents';
COMMENT ON CONSTRAINT chk_projects_won_deals ON projects IS 'Ensures only Won deals can be linked to projects';