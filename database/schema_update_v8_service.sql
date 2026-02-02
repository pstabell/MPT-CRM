-- ============================================================
-- Schema Update v8: Service Tickets
-- Post-delivery work tracking: Change Orders, Maintenance, Service Tickets
-- ============================================================

-- Service tickets table
CREATE TABLE IF NOT EXISTS service_tickets (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    ticket_type VARCHAR(50) NOT NULL,           -- 'change_order', 'maintenance', 'service'
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    client_name VARCHAR(200),
    status VARCHAR(50) DEFAULT 'open',
    priority VARCHAR(20) DEFAULT 'medium',
    estimated_hours DECIMAL(5,2),
    actual_hours DECIMAL(5,2) DEFAULT 0,
    hourly_rate DECIMAL(8,2) DEFAULT 150.00,
    is_billable BOOLEAN DEFAULT TRUE,
    requested_by VARCHAR(200),
    maintenance_type VARCHAR(50),               -- for maintenance tickets: 'vendor_update', 'security_patch', 'health_check', 'dependency_update', 'other'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_service_tickets_ticket_type ON service_tickets(ticket_type);
CREATE INDEX IF NOT EXISTS idx_service_tickets_status ON service_tickets(status);
CREATE INDEX IF NOT EXISTS idx_service_tickets_project_id ON service_tickets(project_id);
CREATE INDEX IF NOT EXISTS idx_service_tickets_is_billable ON service_tickets(is_billable);
CREATE INDEX IF NOT EXISTS idx_service_tickets_created_at ON service_tickets(created_at DESC);

-- Auto-update updated_at trigger
CREATE OR REPLACE FUNCTION update_service_tickets_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_service_tickets_updated_at ON service_tickets;
CREATE TRIGGER trigger_update_service_tickets_updated_at
    BEFORE UPDATE ON service_tickets
    FOR EACH ROW
    EXECUTE FUNCTION update_service_tickets_updated_at();

-- Enable RLS (Row Level Security) - match existing pattern
ALTER TABLE service_tickets ENABLE ROW LEVEL SECURITY;

-- Allow all operations for authenticated users (single-tenant CRM)
CREATE POLICY "Allow all for authenticated users" ON service_tickets
    FOR ALL
    USING (true)
    WITH CHECK (true);
