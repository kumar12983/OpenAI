
set search_path to gnaf, public;
-- Freemium Model Database Schema
-- Creates tables for user management, subscriptions, and usage tracking

-- Create schema for webapp if it doesn't exist
CREATE SCHEMA IF NOT EXISTS webapp;

-- Subscription tiers table
CREATE TABLE IF NOT EXISTS webapp.subscription_tiers (
    tier_id SERIAL PRIMARY KEY,
    tier_name VARCHAR(50) UNIQUE NOT NULL,
    monthly_price DECIMAL(10, 2) NOT NULL,
    searches_per_month INTEGER, -- NULL means unlimited
    can_export_data BOOLEAN DEFAULT FALSE,
    can_access_analytics BOOLEAN DEFAULT FALSE,
    can_access_school_catchments BOOLEAN DEFAULT FALSE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users table
CREATE TABLE IF NOT EXISTS webapp.users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    tier_id INTEGER REFERENCES webapp.subscription_tiers(tier_id) DEFAULT 1,
    stripe_customer_id VARCHAR(255) UNIQUE,
    subscription_status VARCHAR(50) DEFAULT 'active', -- active, cancelled, expired
    subscription_start_date TIMESTAMP,
    subscription_end_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Usage tracking table
CREATE TABLE IF NOT EXISTS webapp.usage_tracking (
    usage_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES webapp.users(user_id) ON DELETE CASCADE,
    endpoint VARCHAR(255) NOT NULL,
    search_type VARCHAR(100), -- 'suburb', 'postcode', 'address', 'school'
    search_query TEXT,
    request_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    response_status INTEGER,
    ip_address VARCHAR(45)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON webapp.users(email);
CREATE INDEX IF NOT EXISTS idx_users_tier ON webapp.users(tier_id);
CREATE INDEX IF NOT EXISTS idx_usage_user_id ON webapp.usage_tracking(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_timestamp ON webapp.usage_tracking(request_timestamp);

-- Insert default subscription tiers
INSERT INTO webapp.subscription_tiers (tier_name, monthly_price, searches_per_month, can_export_data, can_access_analytics, can_access_school_catchments, description)
VALUES 
    ('Free', 0.00, 10, FALSE, FALSE, FALSE, 'Basic access: 10 searches per month, view property and suburb data'),
    ('Premium', 9.99, NULL, TRUE, TRUE, TRUE, 'Unlimited searches, export data, advanced analytics, school catchment information, no ads')
ON CONFLICT (tier_name) DO NOTHING;

-- Create a view for monthly usage counts
CREATE OR REPLACE VIEW webapp.monthly_usage AS
SELECT 
    user_id,
    DATE_TRUNC('month', request_timestamp) as month,
    COUNT(*) as search_count,
    COUNT(DISTINCT search_type) as unique_search_types
FROM webapp.usage_tracking
GROUP BY user_id, DATE_TRUNC('month', request_timestamp);

COMMENT ON TABLE webapp.users IS 'User accounts for freemium real estate analytics platform';
COMMENT ON TABLE webapp.subscription_tiers IS 'Subscription tier definitions (Free, Premium, etc.)';
COMMENT ON TABLE webapp.usage_tracking IS 'Tracks API usage per user for rate limiting';
COMMENT ON VIEW webapp.monthly_usage IS 'Monthly usage summary per user';
