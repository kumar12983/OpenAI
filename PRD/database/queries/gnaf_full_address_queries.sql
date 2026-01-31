-- 
-- GNAF Full Address Construction Queries
-- 
-- These queries show how to construct a complete address from GNAF tables
--

-- ********************************************************************************************
-- Query 1: Complete Address with All Components
-- ********************************************************************************************
-- This query builds a full address including unit, level, street number, street, locality, state, postcode
set search_path to gnaf, public;
set default_text_search_config = 'pg_catalog.simple';
SELECT 
    ad.address_detail_pid,
    
    -- Unit/Flat
    CONCAT_WS(' ', 
        flat.name,              -- FLAT_TYPE_AUT (e.g., "Unit", "Apartment")
        ad.flat_number_prefix,
        ad.flat_number,
        ad.flat_number_suffix
    ) AS unit_part,
    
    -- Level
    CONCAT_WS(' ', 
        lt.name,                -- LEVEL_TYPE_AUT (e.g., "Level", "Floor")
        ad.level_number_prefix,
        ad.level_number,
        ad.level_number_suffix
    ) AS level_part,
    
    -- House/Street Number
    CONCAT_WS(' ',
        ad.number_first_prefix,
        ad.number_first,
        ad.number_first_suffix,
        CASE WHEN ad.number_last IS NOT NULL 
            THEN CONCAT('-', ad.number_last, ad.number_last_suffix) 
        END
    ) AS street_number,
    
    -- Street
    CONCAT_WS(' ',
        sl.street_name,
        st.name,                -- STREET_TYPE_AUT (e.g., "Street", "Road")
        ss.name                 -- STREET_SUFFIX_AUT (e.g., "North", "East")
    ) AS street,
    
    -- Locality/Suburb
    l.locality_name,
    
    -- State
    s.state_abbreviation,
    
    -- Postcode
    ad.postcode,
    
    -- Full Address (all parts combined)
    CONCAT_WS(', ',
        NULLIF(TRIM(CONCAT_WS(' ', flat.name, ad.flat_number)), ''),
        NULLIF(TRIM(CONCAT_WS(' ', lt.name, ad.level_number)), ''),
        TRIM(CONCAT_WS(' ',
            ad.number_first,
            CASE WHEN ad.number_last IS NOT NULL THEN CONCAT('-', ad.number_last) END,
            sl.street_name,
            st.name,
            ss.name
        )),
        l.locality_name,
        CONCAT(s.state_abbreviation, ' ', ad.postcode)
    ) AS full_address
    
FROM address_detail ad
LEFT JOIN flat_type_aut flat ON ad.flat_type_code = flat.code
LEFT JOIN level_type_aut lt ON ad.level_type_code = lt.code
LEFT JOIN street_locality sl ON ad.street_locality_pid = sl.street_locality_pid
LEFT JOIN street_type_aut st ON sl.street_type_code = st.code
LEFT JOIN street_suffix_aut ss ON sl.street_suffix_code = ss.code
LEFT JOIN locality l ON ad.locality_pid = l.locality_pid
LEFT JOIN state s ON l.state_pid = s.state_pid
-- WHERE ad.address_detail_pid = 'YOUR_PID_HERE'  -- Uncomment to filter by specific address
LIMIT 100;  -- Remove or adjust limit as needed


-- ********************************************************************************************
-- Query 2: Simple Address Query (Most Common Fields)
-- ********************************************************************************************
-- Quick query for basic address information

SELECT 
    ad.address_detail_pid,
    ad.flat_number,
    ad.number_first,
    ad.number_last,
    sl.street_name,
    l.locality_name,
    s.state_abbreviation,
    ad.postcode,
    
    -- Simple full address
    CONCAT_WS(' ',
        CASE WHEN ad.flat_number IS NOT NULL THEN CONCAT('Unit ', ad.flat_number, ',') END,
        ad.number_first,
        sl.street_name,
        l.locality_name,
        s.state_abbreviation,
        ad.postcode
    ) AS simple_address
    
FROM address_detail ad
LEFT JOIN street_locality sl ON ad.street_locality_pid = sl.street_locality_pid
LEFT JOIN locality l ON ad.locality_pid = l.locality_pid
LEFT JOIN state s ON l.state_pid = s.state_pid
LIMIT 100;


-- ********************************************************************************************
-- Query 3: Search Address by Suburb and Street
-- ********************************************************************************************
-- Find addresses in a specific suburb and street

SELECT 
    ad.address_detail_pid,
    ad.flat_number,
    CONCAT_WS(' ',
        CASE WHEN ad.flat_number IS NOT NULL THEN CONCAT('Unit ', ad.flat_number, ',') END,
        ad.number_first,
        sl.street_name,
        st.name
    ) AS street_address,
    l.locality_name,
    s.state_abbreviation,
    ad.postcode
    
FROM address_detail ad
LEFT JOIN street_locality sl ON ad.street_locality_pid = sl.street_locality_pid
LEFT JOIN street_type_aut st ON sl.street_type_code = st.code
LEFT JOIN locality l ON ad.locality_pid = l.locality_pid
LEFT JOIN state s ON l.state_pid = s.state_pid
WHERE 
    UPPER(l.locality_name) = 'SYDNEY'           -- Change to your suburb
    AND UPPER(sl.street_name) = 'GEORGE'        -- Change to your street name
    AND s.state_abbreviation = 'NSW'            -- Change to your state
ORDER BY ad.number_first::INTEGER;


-- ********************************************************************************************
-- Query 4: Search Address by Postcode
-- ********************************************************************************************
-- Find all addresses in a specific postcode

SELECT 
    ad.address_detail_pid,
    ad.flat_number,
    ad.number_first,
    sl.street_name,
    st.name AS street_type,
    l.locality_name,
    s.state_abbreviation,
    ad.postcode,
    
    -- Full address with unit
    CONCAT_WS(' ',
        CASE WHEN ad.flat_number IS NOT NULL THEN CONCAT('Unit ', ad.flat_number, ',') END,
        ad.number_first,
        sl.street_name,
        st.name,
        l.locality_name,
        s.state_abbreviation,
        ad.postcode
    ) AS full_address
    
FROM address_detail ad
LEFT JOIN street_locality sl ON ad.street_locality_pid = sl.street_locality_pid
LEFT JOIN street_type_aut st ON sl.street_type_code = st.code
LEFT JOIN locality l ON ad.locality_pid = l.locality_pid
LEFT JOIN state s ON l.state_pid = s.state_pid
WHERE ad.postcode = '2000'  -- Change to your postcode
LIMIT 100;


-- ********************************************************************************************
-- Query 5: Address with Geocode Information
-- ********************************************************************************************
-- Get address with latitude/longitude from default geocode

SELECT 
    ad.address_detail_pid,
    ad.flat_number,
    CONCAT_WS(' ',
        CASE WHEN ad.flat_number IS NOT NULL THEN CONCAT('Unit ', ad.flat_number, ',') END,
        ad.number_first,
        sl.street_name,
        st.name,
        l.locality_name,
        s.state_abbreviation,
        ad.postcode
    ) AS full_address,
    
    -- Geocode information
    adg.latitude,
    adg.longitude,
    gt.name AS geocode_type,
    adg.geocode_type_code
    
FROM address_detail ad
LEFT JOIN street_locality sl ON ad.street_locality_pid = sl.street_locality_pid
LEFT JOIN street_type_aut st ON sl.street_type_code = st.code
LEFT JOIN locality l ON ad.locality_pid = l.locality_pid
LEFT JOIN state s ON l.state_pid = s.state_pid
LEFT JOIN address_default_geocode adg ON ad.address_detail_pid = adg.address_detail_pid
LEFT JOIN geocode_type_aut gt ON adg.geocode_type_code = gt.code
WHERE adg.latitude IS NOT NULL
LIMIT 100;


-- ********************************************************************************************
-- Query 6: Count Addresses by Locality
-- ********************************************************************************************
-- Get statistics on addresses per suburb

SELECT 
    l.locality_name,
    s.state_abbreviation,
    ad.postcode,
    COUNT(*) AS address_count
    
FROM address_detail ad
JOIN locality l ON ad.locality_pid = l.locality_pid
JOIN state s ON l.state_pid = s.state_pid
WHERE s.state_abbreviation = 'NSW'  -- Filter by state
GROUP BY l.locality_name, s.state_abbreviation, ad.postcode
ORDER BY address_count DESC
LIMIT 50;


-- ********************************************************************************************
-- Notes:
-- ********************************************************************************************
-- 
-- Key GNAF Tables:
-- - address_detail: Core address information
-- - street_locality: Street names within localities
-- - locality: Suburbs/towns
-- - state: States/territories
-- - address_default_geocode: Latitude/longitude coordinates
-- - *_aut tables: Authority/lookup tables for codes
--
-- Common Filters:
-- - Filter by state: s.state_abbreviation = 'NSW'
-- - Filter by postcode: l.postcode = '2000'
-- - Filter by suburb: UPPER(l.locality_name) = 'SYDNEY'
-- - Filter by street: UPPER(sl.street_name) = 'GEORGE'
--
-- All table and column names are lowercase in this schema
-- Use UPPER() for case-insensitive string comparisons
--
