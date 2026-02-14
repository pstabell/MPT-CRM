-- schema_update_v15_change_orders.sql
-- Create change_orders table for managing project scope changes
-- Run this in your Supabase SQL Editor

-- =====================================================
-- 1. CREATE CHANGE_ORDERS TABLE
-- =====================================================

CREATE TABLE change_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    
    -- Request tracking
    requested_by VARCHAR(200) NOT NULL,
    approved_by VARCHAR(200),
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    approved_at TIMESTAMP WITH TIME ZONE,
    
    -- Time and cost estimates
    estimated_hours DECIMAL(8, 2),
    actual_hours DECIMAL(8, 2),
    hourly_rate DECIMAL(8, 2) DEFAULT 150.00, -- Default MPT rate
    total_amount DECIMAL(12, 2),
    
    -- Impact and approval requirements
    impact_description TEXT,
    requires_client_approval BOOLEAN DEFAULT false,
    client_signature TEXT, -- Store signature data or approval confirmation
    
    -- Meta
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 2. ADD INDEXES FOR PERFORMANCE
-- =====================================================

CREATE INDEX idx_change_orders_project_id ON change_orders(project_id);
CREATE INDEX idx_change_orders_status ON change_orders(status);
CREATE INDEX idx_change_orders_requested_at ON change_orders(requested_at);

-- =====================================================
-- 3. CREATE UPDATED_AT TRIGGER
-- =====================================================

CREATE TRIGGER change_orders_updated_at
    BEFORE UPDATE ON change_orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- =====================================================
-- 4. ADD COMMENTS FOR DOCUMENTATION
-- =====================================================

COMMENT ON TABLE change_orders IS 'Change orders for managing project scope changes and additional work';
COMMENT ON COLUMN change_orders.project_id IS 'References the parent project';
COMMENT ON COLUMN change_orders.status IS 'Status: draft, pending, approved, rejected, completed';
COMMENT ON COLUMN change_orders.requested_by IS 'Person who requested the change order';
COMMENT ON COLUMN change_orders.approved_by IS 'Person who approved the change order';
COMMENT ON COLUMN change_orders.hourly_rate IS 'Hourly rate for this change order (defaults to $150)';
COMMENT ON COLUMN change_orders.total_amount IS 'Total amount calculated from hours * rate';
COMMENT ON COLUMN change_orders.requires_client_approval IS 'Whether this change requires client signature/approval';
COMMENT ON COLUMN change_orders.client_signature IS 'Client signature data or approval confirmation';

-- =====================================================
-- 5. CREATE SAMPLE DATA (OPTIONAL - FOR TESTING)
-- =====================================================

-- This will be populated when change orders are created through the UI

-- =====================================================
-- NOTES
-- =====================================================
-- Status workflow:
-- 1. draft → Initial creation, can be edited freely
-- 2. pending → Submitted for approval, locked from editing
-- 3. approved → Approved and ready for work
-- 4. rejected → Rejected, can return to draft for revision
-- 5. completed → Work is finished
--
-- Hourly rate defaults to $150 (MPT standard rate) but can be overridden per change order
-- total_amount should be automatically calculated from estimated_hours * hourly_rate