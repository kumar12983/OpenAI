-- ============================================
-- Performance Optimization Indexes for GNAF Database
-- ============================================
-- Run this script to improve address search performance
-- Expected improvement: 20 seconds -> under 1 second

-- Check if indexes already exist before creating
-- You can run this script multiple times safely

-- ============================================
-- Street Locality Indexes (for street name searches)
-- ============================================

-- Index for case-insensitive street name searches
CREATE INDEX IF NOT EXISTS idx_street_locality_name_upper 
ON gnaf.street_locality(UPPER(street_name));

-- Index for exact street name lookups
CREATE INDEX IF NOT EXISTS idx_street_locality_name 
ON gnaf.street_locality(street_name);

-- Index for active (non-retired) street records
CREATE INDEX IF NOT EXISTS idx_street_locality_active 
ON gnaf.street_locality(street_locality_pid) 
WHERE date_retired IS NULL;

-- Index on street_locality_pid for joins
CREATE INDEX IF NOT EXISTS idx_street_locality_pid 
ON gnaf.street_locality(street_locality_pid);


-- ============================================
-- Locality Indexes (for suburb searches)
-- ============================================

-- Index for case-insensitive locality name searches
CREATE INDEX IF NOT EXISTS idx_locality_name_upper 
ON gnaf.locality(UPPER(locality_name));

-- Index for exact locality name lookups
CREATE INDEX IF NOT EXISTS idx_locality_name 
ON gnaf.locality(locality_name);

-- Index on locality_pid for joins
CREATE INDEX IF NOT EXISTS idx_locality_pid 
ON gnaf.locality(locality_pid);


-- ============================================
-- Address Detail Indexes (for address searches)
-- ============================================

-- Index for street number searches
CREATE INDEX IF NOT EXISTS idx_address_number_first 
ON gnaf.address_detail(number_first);

-- Index for postcode searches
CREATE INDEX IF NOT EXISTS idx_address_postcode 
ON gnaf.address_detail(postcode);

-- Index for active (non-retired) addresses
CREATE INDEX IF NOT EXISTS idx_address_detail_active 
ON gnaf.address_detail(address_detail_pid) 
WHERE date_retired IS NULL;

-- Index on street_locality_pid for joins
CREATE INDEX IF NOT EXISTS idx_address_street_locality_pid 
ON gnaf.address_detail(street_locality_pid);

-- Index on locality_pid for joins
CREATE INDEX IF NOT EXISTS idx_address_locality_pid 
ON gnaf.address_detail(locality_pid);


-- ============================================
-- Composite Indexes (for multi-column searches)
-- ============================================

-- Composite index for street + suburb searches
CREATE INDEX IF NOT EXISTS idx_address_street_locality 
ON gnaf.address_detail(street_locality_pid, locality_pid) 
WHERE date_retired IS NULL;

-- Composite index for number + street searches
CREATE INDEX IF NOT EXISTS idx_address_number_street 
ON gnaf.address_detail(number_first, street_locality_pid) 
WHERE date_retired IS NULL;


-- ============================================
-- State Table Index
-- ============================================

CREATE INDEX IF NOT EXISTS idx_state_pid 
ON gnaf.state(state_pid);


-- ============================================
-- Authority Tables Indexes
-- ============================================

CREATE INDEX IF NOT EXISTS idx_flat_type_code 
ON gnaf.flat_type_aut(code);

CREATE INDEX IF NOT EXISTS idx_street_type_code 
ON gnaf.street_type_aut(code);


-- ============================================
-- Address Geocode Indexes
-- ============================================

CREATE INDEX IF NOT EXISTS idx_address_geocode_pid 
ON gnaf.address_default_geocode(address_detail_pid);


-- ============================================
-- Display Index Creation Summary
-- ============================================

SELECT 
    'Index creation complete!' as status,
    count(*) as total_indexes
FROM pg_indexes 
WHERE schemaname = 'gnaf' 
AND indexname LIKE 'idx_%';

-- Show index sizes
SELECT 
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(schemaname||'.'||indexname)) as index_size
FROM pg_indexes 
WHERE schemaname = 'gnaf' 
AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;

-- ============================================
-- Performance Testing Query
-- ============================================
-- Run this after creating indexes to test performance:
-- EXPLAIN ANALYZE
-- SELECT * FROM gnaf.address_detail ad
-- LEFT JOIN gnaf.street_locality sl ON ad.street_locality_pid = sl.street_locality_pid
-- WHERE UPPER(sl.street_name) LIKE UPPER('%GEORGE%')
-- AND ad.date_retired IS NULL
-- LIMIT 50;
