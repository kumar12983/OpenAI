-- ============================================
-- GNAF Geospatial Query Examples
-- ============================================
-- Prerequisites: Run gnaf_geospatial_setup.sql first
-- ============================================

SET search_path TO gnaf, public;

-- ********************************************************************************************
-- Query 1: Find Nearest Addresses to a Point
-- ********************************************************************************************
-- Example: Find 10 nearest addresses to Sydney Opera House (-33.8568, 151.2153)

SELECT 
    address_detail_pid,
    full_address,
    locality_name,
    postcode,
    latitude,
    longitude,
    ROUND(
        ST_Distance(
            geom::geography,
            ST_SetSRID(ST_MakePoint(151.2153, -33.8568), 4326)::geography
        )::numeric,
        2
    ) AS distance_meters,
    ROUND(
        ST_Distance(
            geom::geography,
            ST_SetSRID(ST_MakePoint(151.2153, -33.8568), 4326)::geography
        )::numeric / 1000,
        2
    ) AS distance_km
FROM mv_addresses_geocoded
WHERE geom IS NOT NULL
ORDER BY geom <-> ST_SetSRID(ST_MakePoint(151.2153, -33.8568), 4326)
LIMIT 10;


-- ********************************************************************************************
-- Query 2: Find All Addresses Within Radius
-- ********************************************************************************************
-- Example: Find all addresses within 500 meters of a location

SELECT 
    address_detail_pid,
    full_address,
    ROUND(
        ST_Distance(
            geom::geography,
            ST_SetSRID(ST_MakePoint(151.2153, -33.8568), 4326)::geography
        )::numeric,
        2
    ) AS distance_meters
FROM mv_addresses_geocoded
WHERE ST_DWithin(
    geom::geography,
    ST_SetSRID(ST_MakePoint(151.2153, -33.8568), 4326)::geography,
    500  -- radius in meters
)
ORDER BY distance_meters;


-- ********************************************************************************************
-- Query 3: Distance Between Two Specific Addresses
-- ********************************************************************************************
-- Calculate distance between two addresses by their PIDs

SELECT 
    a1.full_address as address_1,
    a2.full_address as address_2,
    ROUND(
        ST_Distance(a1.geom::geography, a2.geom::geography)::numeric,
        2
    ) AS distance_meters,
    ROUND(
        ST_Distance(a1.geom::geography, a2.geom::geography)::numeric / 1000,
        2
    ) AS distance_km
FROM mv_addresses_geocoded a1
CROSS JOIN mv_addresses_geocoded a2
WHERE a1.address_detail_pid = 'GAACT714845933'  -- Replace with actual PID
  AND a2.address_detail_pid = 'GAACT714845934'; -- Replace with actual PID


-- ********************************************************************************************
-- Query 4: Find Addresses in a Bounding Box
-- ********************************************************************************************
-- Find all addresses within a rectangular area (min_lon, min_lat, max_lon, max_lat)
-- Example: Small area around Sydney CBD

SELECT 
    address_detail_pid,
    full_address,
    latitude,
    longitude
FROM mv_addresses_geocoded
WHERE geom && ST_MakeEnvelope(
    151.20, -33.87,  -- min_lon, min_lat (southwest corner)
    151.22, -33.85,  -- max_lon, max_lat (northeast corner)
    4326             -- SRID
)
LIMIT 100;


-- ********************************************************************************************
-- Query 5: Nearest Neighbor Analysis
-- ********************************************************************************************
-- For each address in a specific suburb, find its nearest neighbor

WITH target_addresses AS (
    SELECT address_detail_pid, full_address, geom
    FROM mv_addresses_geocoded
    WHERE locality_name = 'SYDNEY'  -- Change to your suburb
    LIMIT 20  -- Limit for performance
)
SELECT DISTINCT ON (t1.address_detail_pid)
    t1.address_detail_pid,
    t1.full_address as address,
    t2.full_address as nearest_address,
    ROUND(
        ST_Distance(t1.geom::geography, t2.geom::geography)::numeric,
        2
    ) AS distance_meters
FROM target_addresses t1
CROSS JOIN LATERAL (
    SELECT address_detail_pid, full_address, geom
    FROM mv_addresses_geocoded
    WHERE address_detail_pid != t1.address_detail_pid
    ORDER BY geom <-> t1.geom
    LIMIT 1
) t2
ORDER BY t1.address_detail_pid;


-- ********************************************************************************************
-- Query 6: Addresses Along a Route (Buffer Analysis)
-- ********************************************************************************************
-- Find addresses within 100m of a line (e.g., a road or path)

WITH route AS (
    SELECT ST_MakeLine(ARRAY[
        ST_SetSRID(ST_MakePoint(151.2100, -33.8700), 4326),
        ST_SetSRID(ST_MakePoint(151.2150, -33.8650), 4326),
        ST_SetSRID(ST_MakePoint(151.2200, -33.8600), 4326)
    ]) as line_geom
)
SELECT 
    a.address_detail_pid,
    a.full_address,
    ROUND(
        ST_Distance(a.geom::geography, r.line_geom::geography)::numeric,
        2
    ) AS distance_to_route_meters
FROM mv_addresses_geocoded a
CROSS JOIN route r
WHERE ST_DWithin(
    a.geom::geography,
    r.line_geom::geography,
    100  -- buffer distance in meters
)
ORDER BY distance_to_route_meters
LIMIT 50;


-- ********************************************************************************************
-- Query 7: Density Analysis - Count Addresses in Grid Cells
-- ********************************************************************************************
-- Create a grid and count addresses in each cell

SELECT 
    ST_X(cell_center) as lon,
    ST_Y(cell_center) as lat,
    address_count
FROM (
    SELECT 
        ST_Centroid(grid.geom) as cell_center,
        COUNT(a.address_detail_pid) as address_count
    FROM (
        -- Generate a grid covering Sydney area
        SELECT (ST_SquareGrid(0.01, ST_MakeEnvelope(151.0, -34.0, 151.3, -33.7, 4326))).geom
    ) AS grid
    LEFT JOIN mv_addresses_geocoded a ON ST_Contains(grid.geom, a.geom)
    GROUP BY grid.geom
    HAVING COUNT(a.address_detail_pid) > 0
) AS density
ORDER BY address_count DESC
LIMIT 20;


-- ********************************************************************************************
-- Query 8: Postcode Centroids and Boundaries
-- ********************************************************************************************
-- Calculate the center point and extent of each postcode

SELECT 
    postcode,
    locality_name,
    COUNT(*) as address_count,
    ST_X(ST_Centroid(ST_Collect(geom))) as center_longitude,
    ST_Y(ST_Centroid(ST_Collect(geom))) as center_latitude,
    ROUND(
        ST_Area(ST_ConvexHull(ST_Collect(geom))::geography)::numeric / 1000000,
        2
    ) as approximate_area_km2
FROM mv_addresses_geocoded
WHERE state_abbreviation = 'NSW'
  AND postcode IS NOT NULL
GROUP BY postcode, locality_name
HAVING COUNT(*) > 10  -- Only postcodes with multiple addresses
ORDER BY address_count DESC
LIMIT 20;


-- ********************************************************************************************
-- Query 9: Find Addresses Between Two Points
-- ********************************************************************************************
-- Find addresses that fall along a corridor between two locations

WITH endpoints AS (
    SELECT 
        ST_SetSRID(ST_MakePoint(151.2100, -33.8700), 4326) as point_a,
        ST_SetSRID(ST_MakePoint(151.2200, -33.8600), 4326) as point_b
)
SELECT 
    a.address_detail_pid,
    a.full_address,
    ROUND(
        ST_Distance(
            a.geom::geography,
            ST_MakeLine(e.point_a, e.point_b)::geography
        )::numeric,
        2
    ) AS distance_to_line_meters
FROM mv_addresses_geocoded a
CROSS JOIN endpoints e
WHERE ST_DWithin(
    a.geom::geography,
    ST_MakeLine(e.point_a, e.point_b)::geography,
    200  -- corridor width in meters
)
ORDER BY distance_to_line_meters
LIMIT 50;


-- ********************************************************************************************
-- Query 10: Export to GeoJSON
-- ********************************************************************************************
-- Export addresses as GeoJSON for use in web maps, QGIS, etc.

SELECT jsonb_build_object(
    'type', 'FeatureCollection',
    'features', jsonb_agg(
        jsonb_build_object(
            'type', 'Feature',
            'geometry', ST_AsGeoJSON(geom)::jsonb,
            'properties', jsonb_build_object(
                'address_pid', address_detail_pid,
                'address', full_address,
                'suburb', locality_name,
                'postcode', postcode,
                'state', state_abbreviation
            )
        )
    )
) as geojson
FROM mv_addresses_geocoded
WHERE state_abbreviation = 'NSW'
  AND locality_name = 'SYDNEY'  -- Change to your area
LIMIT 100;  -- Limit for performance


-- ********************************************************************************************
-- Query 11: Using Custom Functions
-- ********************************************************************************************

-- Example 1: Get distance between two addresses using helper function
SELECT gnaf.get_distance_between_addresses(
    'GAACT714845933',  -- Replace with actual PID
    'GAACT714845934'   -- Replace with actual PID
) AS distance_meters;

-- Example 2: Find addresses within radius using helper function
SELECT *
FROM gnaf.find_addresses_within_radius(
    -33.8568,   -- latitude (Sydney Opera House)
    151.2153,   -- longitude
    1000        -- radius in meters
)
LIMIT 10;


-- ********************************************************************************************
-- Query 12: Suburb/Locality Coverage Statistics
-- ********************************************************************************************
-- Analyze geocoding coverage by suburb

SELECT 
    l.locality_name,
    s.state_abbreviation,
    COUNT(DISTINCT ad.address_detail_pid) as total_addresses,
    COUNT(DISTINCT adg.address_detail_pid) as geocoded_addresses,
    ROUND(
        100.0 * COUNT(DISTINCT adg.address_detail_pid) / 
        NULLIF(COUNT(DISTINCT ad.address_detail_pid), 0),
        2
    ) as geocoding_percentage
FROM locality l
JOIN state s ON l.state_pid = s.state_pid
LEFT JOIN address_detail ad ON ad.locality_pid = l.locality_pid
LEFT JOIN address_default_geocode adg ON ad.address_detail_pid = adg.address_detail_pid 
    AND adg.geom IS NOT NULL
WHERE s.state_abbreviation = 'NSW'
GROUP BY l.locality_name, s.state_abbreviation
HAVING COUNT(DISTINCT ad.address_detail_pid) > 100
ORDER BY geocoding_percentage DESC, total_addresses DESC
LIMIT 50;


-- ********************************************************************************************
-- Query 13: Create Convex Hull Around Addresses in a Suburb
-- ********************************************************************************************
-- Generate a boundary polygon around all addresses in a locality

SELECT 
    locality_name,
    postcode,
    ST_AsGeoJSON(ST_ConvexHull(ST_Collect(geom)))::jsonb as boundary_geojson,
    COUNT(*) as address_count
FROM mv_addresses_geocoded
WHERE locality_name = 'SYDNEY'  -- Change to your suburb
GROUP BY locality_name, postcode;


-- ********************************************************************************************
-- PERFORMANCE TIPS
-- ********************************************************************************************
-- 1. Always use spatial indexes (created in setup script)
-- 2. Use the <-> operator for nearest neighbor queries (KNN)
-- 3. Use ST_DWithin instead of ST_Distance with WHERE clause
-- 4. Cast to geography for accurate distance calculations in meters
-- 5. Use materialized views for frequently accessed data
-- 6. Refresh materialized view periodically:
--    REFRESH MATERIALIZED VIEW gnaf.mv_addresses_geocoded;

