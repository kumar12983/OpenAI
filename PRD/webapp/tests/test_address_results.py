"""Test address search results (moved to tests folder)"""
import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(
    host='localhost', 
    database='gnaf_db', 
    user='postgres', 
    password='', 
    port=5432
)

cursor = conn.cursor(cursor_factory=RealDictCursor)

# Test address search for streets found in autocomplete
print("Testing address search for BACON ST in school 2060:")
print("=" * 70)

cursor.execute("""
    SELECT 
        ad.address_detail_pid,
        CONCAT_WS(' ',
            CONCAT(ad.number_first, COALESCE(ad.number_first_suffix, '')),
            CASE WHEN ad.number_last IS NOT NULL 
                THEN CONCAT('-', ad.number_last, COALESCE(ad.number_last_suffix, '')) 
            END
        ) as street_number,
        sl.street_name,
        st.name as street_type,
        l.locality_name as suburb,
        ad.postcode,
        adg.latitude,
        adg.longitude
    FROM public.school_catchment_addresses ca
    INNER JOIN gnaf.address_detail ad ON ca.address_detail_pid = ad.address_detail_pid
    LEFT JOIN gnaf.street_locality sl ON ad.street_locality_pid = sl.street_locality_pid
    LEFT JOIN gnaf.street_type_aut st ON sl.street_type_code = st.code
    LEFT JOIN gnaf.locality l ON ad.locality_pid = l.locality_pid
    LEFT JOIN gnaf.address_default_geocode adg ON ad.address_detail_pid = adg.address_detail_pid
    WHERE ca.school_id = '2060'
    AND sl.street_name ILIKE %s
    LIMIT 10
""", ('%BACON%',))

results = cursor.fetchall()

if results:
    for i, row in enumerate(results, 1):
        street_full = f"{row['street_name']} {row['street_type']}" if row['street_type'] else row['street_name']
        print(f"{i}. {row['street_number']} {street_full}, {row['suburb']} {row['postcode']}")
        if row['latitude'] and row['longitude']:
            print(f"   Location: {row['latitude']}, {row['longitude']}")
    print(f"\nTotal: {len(results)} addresses found")
else:
    print("No addresses found")

print("\n" + "=" * 70)
print("Testing address search for GRAFTON suburb in school 2060:")
print("=" * 70)

cursor.execute("""
    SELECT 
        ad.address_detail_pid,
        CONCAT_WS(' ',
            CONCAT(ad.number_first, COALESCE(ad.number_first_suffix, '')),
            CASE WHEN ad.number_last IS NOT NULL 
                THEN CONCAT('-', ad.number_last, COALESCE(ad.number_last_suffix, '')) 
            END
        ) as street_number,
        sl.street_name,
        st.name as street_type,
        l.locality_name as suburb,
        ad.postcode
    FROM public.school_catchment_addresses ca
    INNER JOIN gnaf.address_detail ad ON ca.address_detail_pid = ad.address_detail_pid
    LEFT JOIN gnaf.street_locality sl ON ad.street_locality_pid = sl.street_locality_pid
    LEFT JOIN gnaf.street_type_aut st ON sl.street_type_code = st.code
    LEFT JOIN gnaf.locality l ON ad.locality_pid = l.locality_pid
    WHERE ca.school_id = '2060'
    AND l.locality_name ILIKE %s
    LIMIT 10
""", ('%GRAFTON%',))

results = cursor.fetchall()

if results:
    for i, row in enumerate(results, 1):
        street_full = f"{row['street_name']} {row['street_type']}" if row['street_type'] else row['street_name']
        print(f"{i}. {row['street_number']} {street_full}, {row['suburb']} {row['postcode']}")
    print(f"\nTotal: {len(results)} addresses found")
else:
    print("No addresses found")

conn.close()
print("\n✓ Address search tests completed")
