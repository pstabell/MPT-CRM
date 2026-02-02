-- schema_update_v10_settings.sql
-- Add settings table for application configuration
-- Run this in your Supabase SQL Editor

CREATE TABLE IF NOT EXISTS settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "key" VARCHAR UNIQUE NOT NULL,
    value TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO settings ("key", value)
VALUES ('auth_password_hash', NULL)
ON CONFLICT ("key") DO NOTHING;
