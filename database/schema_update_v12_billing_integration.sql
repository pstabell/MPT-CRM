-- ============================================================
-- Schema Update v12: Billing Integration Fields  
-- ============================================================
-- Adds billing tracking fields to projects table for the
-- 3-way integration with Mission Control and MPT-Accounting.
-- 
-- This enables tracking of:
-- - Total billed amount (from invoices)
-- - Total internal cost (non-billable time)  
-- - Project profitability calculation
--
-- Run this against your Supabase database.
-- ============================================================

-- Add billing tracking columns to projects table
ALTER TABLE projects
  ADD COLUMN IF NOT EXISTS total_billed DECIMAL(12,2) DEFAULT 0.00,
  ADD COLUMN IF NOT EXISTS total_internal_cost DECIMAL(12,2) DEFAULT 0.00,
  ADD COLUMN IF NOT EXISTS mission_control_task_id VARCHAR(100),
  ADD COLUMN IF NOT EXISTS last_sync_at TIMESTAMP WITH TIME ZONE;

-- Add constraints and indexes for performance
CREATE INDEX IF NOT EXISTS idx_projects_billing ON projects (total_billed, total_internal_cost);
CREATE INDEX IF NOT EXISTS idx_projects_mc_task ON projects (mission_control_task_id);
CREATE INDEX IF NOT EXISTS idx_projects_last_sync ON projects (last_sync_at);

-- Add helpful comments for documentation
COMMENT ON COLUMN projects.total_billed IS 'Total amount billed to client from completed Mission Control tasks';
COMMENT ON COLUMN projects.total_internal_cost IS 'Total internal cost from non-billable Mission Control tasks';
COMMENT ON COLUMN projects.mission_control_task_id IS 'Link to Mission Control task that created this project';
COMMENT ON COLUMN projects.last_sync_at IS 'Last time billing data was synced from accounting system';

-- Create a view for project profitability analysis
CREATE OR REPLACE VIEW project_profitability AS
SELECT 
    id,
    name,
    client_name,
    status,
    project_type,
    hourly_rate,
    estimated_hours,
    hours_logged,
    total_billed,
    total_internal_cost,
    (total_billed - total_internal_cost) AS net_profit,
    CASE 
        WHEN total_billed > 0 THEN 
            ROUND(((total_billed - total_internal_cost) / total_billed * 100), 2)
        ELSE 0 
    END AS profit_margin_percent,
    CASE
        WHEN estimated_hours > 0 AND hourly_rate > 0 THEN 
            (estimated_hours * hourly_rate) - total_billed
        ELSE NULL 
    END AS remaining_budget,
    created_at,
    updated_at,
    last_sync_at
FROM projects
ORDER BY total_billed DESC;

COMMENT ON VIEW project_profitability IS 'Project profitability analysis with calculated metrics';

-- Create function to calculate project metrics
CREATE OR REPLACE FUNCTION calculate_project_metrics(project_uuid UUID)
RETURNS TABLE (
    project_id UUID,
    total_value DECIMAL(12,2),
    profit_margin DECIMAL(5,2),
    budget_remaining DECIMAL(12,2),
    is_profitable BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        (p.total_billed + p.total_internal_cost) as total_value,
        CASE 
            WHEN p.total_billed > 0 THEN 
                ROUND(((p.total_billed - p.total_internal_cost) / p.total_billed * 100), 2)
            ELSE 0 
        END as profit_margin,
        CASE
            WHEN p.estimated_hours > 0 AND p.hourly_rate > 0 THEN 
                (p.estimated_hours * p.hourly_rate) - p.total_billed
            ELSE NULL 
        END as budget_remaining,
        (p.total_billed > p.total_internal_cost) as is_profitable
    FROM projects p
    WHERE p.id = project_uuid;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION calculate_project_metrics IS 'Calculate key financial metrics for a project';

-- Insert sample data to test the new fields (optional)
-- UPDATE projects SET 
--     total_billed = 0.00,
--     total_internal_cost = 0.00,
--     last_sync_at = NOW()
-- WHERE total_billed IS NULL;

-- Output confirmation
SELECT 'Schema update v12 completed successfully - Added billing integration fields to projects table' as status;