-- ============================================
-- Create Materialized View for Statistics
-- ============================================
-- This pre-calculates statistics for instant loading
-- Refresh this view periodically (daily/weekly) to update stats

-- Drop existing view if it exists
DROP MATERIALIZED VIEW IF EXISTS gnaf.stats_summary CASCADE;

-- Create materialized view with all statistics
CREATE MATERIALIZED VIEW gnaf.stats_summary AS
SELECT
    -- Total localities
    (SELECT COUNT(DISTINCT locality_pid) 
     FROM gnaf.locality 
     WHERE date_retired IS NULL) as total_localities,
    
    -- Total addresses
    (SELECT COUNT(DISTINCT address_detail_pid) 
     FROM gnaf.address_detail 
     WHERE date_retired IS NULL) as total_addresses,
    
    -- Total streets
    (SELECT COUNT(DISTINCT street_locality_pid) 
     FROM gnaf.street_locality 
     WHERE date_retired IS NULL) as total_streets,
    
    -- Last refresh timestamp
    NOW() as last_refreshed;

-- Create index on the materialized view for faster access
CREATE UNIQUE INDEX idx_stats_summary ON gnaf.stats_summary ((1));

-- Create materialized view for state breakdown
DROP MATERIALIZED VIEW IF EXISTS gnaf.stats_by_state CASCADE;

CREATE MATERIALIZED VIEW gnaf.stats_by_state AS
SELECT 
    s.state_name as state_abbreviation,
    COUNT(DISTINCT l.locality_pid) as count
FROM gnaf.locality l
JOIN gnaf.state s ON l.state_pid = s.state_pid
WHERE l.date_retired IS NULL
GROUP BY s.state_name
ORDER BY s.state_name;

-- Create index on state stats
CREATE INDEX idx_stats_by_state ON gnaf.stats_by_state (state_abbreviation);

-- Grant permissions (adjust as needed)
-- GRANT SELECT ON gnaf.stats_summary TO your_user;
-- GRANT SELECT ON gnaf.stats_by_state TO your_user;

-- Display results
SELECT 
    'Materialized views created successfully!' as status,
    total_localities,
    total_addresses,
    total_streets,
    last_refreshed
FROM gnaf.stats_summary;

SELECT * FROM gnaf.stats_by_state;


-- DROP MATERIALIZED VIEW IF EXISTS gnaf.total_address_summary;
CREATE MATERIALIZED VIEW IF NOT EXISTS gnaf.total_address_summary
TABLESPACE pg_default
AS
select state_name, count(distinct ad.street_locality_pid) as streets, count(distinct ad.locality_pid) as localities
, count(distinct address_detail_pid) as addresses
, now() as last_refreshed
from address_detail ad 
INNER JOIN locality l on ad.locality_pid = l.locality_pid 
INNER JOIN state s on s.state_pid = l.state_pid
GROUP BY 1
WITH DATA
;

ALTER TABLE IF EXISTS gnaf.total_address_summary
    OWNER TO postgres;

CREATE UNIQUE INDEX idx_addreses_stats_summary
    ON gnaf.total_address_summary USING btree
    (state_name)
    TABLESPACE pg_default;

-- ============================================
-- Refresh Commands (run these periodically)
-- ============================================
-- To refresh the statistics, run these commands:
-- REFRESH MATERIALIZED VIEW gnaf.stats_summary;
-- REFRESH MATERIALIZED VIEW gnaf.stats_by_state;

-- Or refresh both concurrently (faster):
-- REFRESH MATERIALIZED VIEW CONCURRENTLY gnaf.stats_summary;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY gnaf.stats_by_state;
