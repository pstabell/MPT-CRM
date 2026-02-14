-- schema_update_v17_mission_control_integration.sql
-- Add Mission Control integration fields to service_tickets
-- Run this in your Supabase SQL Editor

-- =====================================================
-- 1. ADD MISSION CONTROL INTEGRATION FIELDS
-- =====================================================

-- Add Mission Control card ID reference to service_tickets
ALTER TABLE service_tickets 
ADD COLUMN IF NOT EXISTS mission_control_card_id UUID;

-- Add index for Mission Control lookups
CREATE INDEX IF NOT EXISTS idx_service_tickets_mc_card_id 
ON service_tickets(mission_control_card_id);

-- =====================================================
-- 2. ADD SIMILAR FIELD TO CHANGE_ORDERS IF TABLE EXISTS
-- =====================================================

-- Check if change_orders table exists and add field
DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'change_orders') THEN
        -- Add Mission Control card ID reference to change_orders
        ALTER TABLE change_orders 
        ADD COLUMN IF NOT EXISTS mission_control_card_id UUID;
        
        -- Add index for Mission Control lookups
        CREATE INDEX IF NOT EXISTS idx_change_orders_mc_card_id 
        ON change_orders(mission_control_card_id);
    END IF;
END
$$;

-- =====================================================
-- 3. ADD COMMENTS FOR DOCUMENTATION
-- =====================================================

COMMENT ON COLUMN service_tickets.mission_control_card_id 
IS 'UUID reference to Mission Control card created from this ticket';

-- Add comment to change_orders if table exists
DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'change_orders') THEN
        EXECUTE 'COMMENT ON COLUMN change_orders.mission_control_card_id IS ''UUID reference to Mission Control card created from this change order''';
    END IF;
END
$$;

-- =====================================================
-- NOTES
-- =====================================================
-- This migration enables:
-- 1. CRM tickets automatically create Mission Control cards
-- 2. Bidirectional linking between CRM and Mission Control
-- 3. Mission Control becomes source of truth for work execution
-- 4. CRM maintains visibility into work progress via card links
--
-- Workflow:
-- 1. User creates Service Ticket/Change Order in CRM
-- 2. CRM automatically calls Mission Control API to create card
-- 3. Mission Control card ID is stored back in CRM record
-- 4. Users can click through from CRM to Mission Control for work tracking