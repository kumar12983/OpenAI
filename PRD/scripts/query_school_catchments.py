"""
School Catchment Query Examples
Demonstrates how to query school catchments for GNAF addresses
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('webapp/.env')

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'gnaf_db')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'admin')

def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def find_school_catchment_by_coordinates(latitude, longitude, school_type='primary'):
    """
    Find which school catchment a specific address belongs to
    
    Args:
        latitude: Address latitude
        longitude: Address longitude
        school_type: 'primary', 'secondary', or 'future'
    
    Returns:
        School catchment details or None
    """
    table_name = f'school_catchments_{school_type}'
    
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    query = f"""
        SELECT 
            "USE_ID" as school_id,
            "USE_DESC" as school_name,
            "CATCH_TYPE" as catchment_type,
            "ADD_DATE" as added_date,
            "KINDERGART" as kindergart, "YEAR1" as year1, "YEAR2" as year2, "YEAR3" as year3, 
            "YEAR4" as year4, "YEAR5" as year5, "YEAR6" as year6,
            "YEAR7" as year7, "YEAR8" as year8, "YEAR9" as year9, 
            "YEAR10" as year10, "YEAR11" as year11, "YEAR12" as year12,
            "PRIORITY" as priority
        FROM {table_name}
        WHERE ST_Contains(geometry, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
        LIMIT 1
    """
    
    cursor.execute(query, (longitude, latitude))
    result = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return dict(result) if result else None

def find_addresses_in_school_catchment(school_name, school_type='primary', limit=20):
    """
    Find all addresses in a specific school catchment
    
    Args:
        school_name: Name of the school (use LIKE matching)
        school_type: 'primary', 'secondary', or 'future'
        limit: Maximum number of addresses to return
    
    Returns:
        List of addresses in the catchment
    """
    table_name = f'school_catchments_{school_type}'
    
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    query = f"""
        SELECT DISTINCT ON (ad.address_detail_pid)
            ad.address_detail_pid as gnaf_id,
            CONCAT_WS(' ',
                ad.number_first,
                CASE WHEN ad.number_last IS NOT NULL THEN CONCAT('-', ad.number_last) END,
                sl.street_name,
                st.name
            ) as full_address,
            l.locality_name as suburb,
            s.state_abbreviation as state,
            ad.postcode,
            adg.latitude,
            adg.longitude,
            sc."USE_DESC" as school_name,
            sc."CATCH_TYPE" as catchment_type
        FROM gnaf.address_detail ad
        LEFT JOIN gnaf.street_locality sl ON ad.street_locality_pid = sl.street_locality_pid
        LEFT JOIN gnaf.street_type_aut st ON sl.street_type_code = st.code
        LEFT JOIN gnaf.locality l ON ad.locality_pid = l.locality_pid
        LEFT JOIN gnaf.state s ON l.state_pid = s.state_pid
        LEFT JOIN gnaf.address_default_geocode adg ON ad.address_detail_pid = adg.address_detail_pid
        JOIN {table_name} sc ON ST_Contains(
            sc.geometry, 
            ST_SetSRID(ST_MakePoint(adg.longitude, adg.latitude), 4326)
        )
        WHERE ad.date_retired IS NULL
        AND UPPER(sc."USE_DESC") LIKE UPPER(%s)
        AND s.state_abbreviation = 'NSW'
        ORDER BY ad.address_detail_pid, l.locality_name, sl.street_name
        LIMIT %s
    """
    
    cursor.execute(query, (f'%{school_name}%', limit))
    results = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return [dict(r) for r in results]

def get_school_catchment_stats():
    """Get statistics about school catchments"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    stats = {}
    
    for school_type in ['primary', 'secondary', 'future']:
        table_name = f'school_catchments_{school_type}'
        cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
        stats[school_type] = cursor.fetchone()['count']
    
    cursor.close()
    conn.close()
    
    return stats

# Example usage
if __name__ == '__main__':
    print("=" * 60)
    print("School Catchment Query Examples")
    print("=" * 60)
    
    # Get statistics
    print("\n1. School Catchment Statistics:")
    stats = get_school_catchment_stats()
    print(f"   Primary schools: {stats['primary']}")
    print(f"   Secondary schools: {stats['secondary']}")
    print(f"   Future schools: {stats['future']}")
    
    # Example 1: Find catchment for a specific address
    print("\n2. Find school catchment for Sydney CBD coordinates:")
    catchment = find_school_catchment_by_coordinates(-33.8688, 151.2093, 'primary')
    if catchment:
        print(f"   School: {catchment['school_name']}")
        print(f"   Type: {catchment['catchment_type']}")
        print(f"   Years: ", end='')
        years = []
        for year in ['kindergart', 'year1', 'year2', 'year3', 'year4', 'year5', 'year6']:
            if catchment[year] and catchment[year].upper() == 'YES':
                years.append(year.replace('year', 'Y').replace('kindergart', 'K'))
        print(', '.join(years))
    else:
        print("   Not in any school catchment")
    
    # Example 2: Find addresses in a school catchment
    print("\n3. Find addresses in a specific school catchment (sample):")
    addresses = find_addresses_in_school_catchment('Hornsby', 'primary', limit=5)
    if addresses:
        for addr in addresses:
            print(f"   {addr['full_address']}, {addr['suburb']} {addr['postcode']}")
            print(f"      School: {addr['school_name']}")
    else:
        print("   No addresses found")
    
    print("\n" + "=" * 60)
    print("Integration Complete!")
    print("=" * 60)
    print("\nYou can now:")
    print("1. Query school catchments for any NSW address")
    print("2. Find all addresses in a specific school catchment")
    print("3. Add school catchment info to your web application")
