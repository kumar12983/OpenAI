set search_path to gnaf, public;
set default_text_search_config = 'pg_catalog.simple';
SELECT 
  --  ad.address_detail_pid,
  DISTINCT  CONCAT_WS(' ',
        ad.number_first,
        sl.street_name,
        st.name
    ) AS street_address,
    l.locality_name,
    s.state_abbreviation--,
    --l.postcode
    
FROM address_detail ad
LEFT JOIN street_locality sl ON ad.street_locality_pid = sl.street_locality_pid
LEFT JOIN street_type_aut st ON sl.street_type_code = st.code
LEFT JOIN locality l ON ad.locality_pid = l.locality_pid
LEFT JOIN state s ON l.state_pid = s.state_pid
WHERE 
    UPPER(l.locality_name) = 'BEECROFT'           -- Change to your suburb
    AND UPPER(sl.street_name) = 'BINGARA'        -- Change to your street name
    AND s.state_abbreviation = 'NSW'            -- Change to your state
ORDER BY street_address
--ORDER BY ad.number_first::INTEGER;

select * from information_schema.columns where column_name = 'postcode';

SELECT 
    --ad.address_detail_pid,
 DISTINCT   ad.number_first,
    sl.street_name,
	sl.street_type_code,
   -- st.name AS street_type,
    l.locality_name,
    s.state_abbreviation,
    ad.postcode
    
FROM address_detail ad
LEFT JOIN street_locality sl ON ad.street_locality_pid = sl.street_locality_pid
LEFT JOIN street_type_aut st ON sl.street_type_code = st.code
LEFT JOIN locality l ON ad.locality_pid = l.locality_pid
LEFT JOIN state s ON l.state_pid = s.state_pid
WHERE ad.postcode = '2119' and street_name = 'BINGARA'  -- Change to your postcode
 

select * FROM street_type_aut