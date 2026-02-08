"""
Test script for school search autocomplete functionality
Tests the new school-specific autocomplete endpoints
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'gnaf_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'port': int(os.getenv('DB_PORT', '5432'))
}

def test_connection():
    """Test database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✓ Database connection successful")
        conn.close()
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

def test_school_catchment_streets_exists():
    """Check if school_catchment_streets materialized view exists"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM public.school_catchment_streets 
            LIMIT 1
        """)
        result = cursor.fetchone()
        conn.close()
        print(f"✓ school_catchment_streets view exists and is accessible")
        return True
    except Exception as e:
        print(f"✗ school_catchment_streets view check failed: {e}")
        return False

def test_school_autocomplete_streets(school_id='2060', query='B'):
    """Test school-specific street autocomplete"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT DISTINCT 
                scs.street_name,
                st.name as street_type
            FROM public.school_catchment_streets scs
            LEFT JOIN gnaf.street_type_aut st ON scs.street_type_code = st.code
            WHERE scs.school_id = %s
            AND UPPER(scs.street_name) LIKE UPPER(%s)
            ORDER BY scs.street_name
            LIMIT 20
        """, (school_id, f'{query}%'))
        
        results = cursor.fetchall()
        conn.close()
        
        print(f"\n✓ School {school_id} - Street autocomplete for '{query}':")
        for i, row in enumerate(results[:5], 1):
            street_full = f"{row['street_name']} {row['street_type']}" if row['street_type'] else row['street_name']
            print(f"  {i}. {street_full}")
        print(f"  ... ({len(results)} total results)")
        return True
    except Exception as e:
        print(f"✗ Street autocomplete test failed: {e}")
        return False

def test_school_autocomplete_suburbs(school_id='2060', query=''):
    """Test school-specific suburb autocomplete"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get all suburbs for the school if no query
        if not query:
            cursor.execute("""
                SELECT DISTINCT 
                    scs.locality_name as suburb,
                    scs.postcode
                FROM public.school_catchment_streets scs
                WHERE scs.school_id = %s
                ORDER BY scs.locality_name
                LIMIT 20
            """, (school_id,))
        else:
            cursor.execute("""
                SELECT DISTINCT 
                    scs.locality_name as suburb,
                    scs.postcode
                FROM public.school_catchment_streets scs
                WHERE scs.school_id = %s
                AND UPPER(scs.locality_name) LIKE UPPER(%s)
                ORDER BY scs.locality_name
                LIMIT 20
            """, (school_id, f'{query}%'))
        
        results = cursor.fetchall()
        conn.close()
        
        print(f"\n✓ School {school_id} - Suburb autocomplete" + (f" for '{query}':" if query else ":"))
        for i, row in enumerate(results[:5], 1):
            print(f"  {i}. {row['suburb']} ({row['postcode']})")
        print(f"  ... ({len(results)} total results)")
        return True
    except Exception as e:
        print(f"✗ Suburb autocomplete test failed: {e}")
        return False

def test_school_autocomplete_postcodes(school_id='2060', query=''):
    """Test school-specific postcode autocomplete"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get all postcodes for the school if no query
        if not query:
            cursor.execute("""
                SELECT DISTINCT 
                    scs.postcode,
                    scs.locality_name as suburb
                FROM public.school_catchment_streets scs
                WHERE scs.school_id = %s
                ORDER BY scs.postcode
                LIMIT 20
            """, (school_id,))
        else:
            cursor.execute("""
                SELECT DISTINCT 
                    scs.postcode,
                    scs.locality_name as suburb
                FROM public.school_catchment_streets scs
                WHERE scs.school_id = %s
                AND scs.postcode LIKE %s
                ORDER BY scs.postcode
                LIMIT 20
            """, (school_id, f'{query}%'))
        
        results = cursor.fetchall()
        conn.close()
        
        print(f"\n✓ School {school_id} - Postcode autocomplete" + (f" for '{query}':" if query else ":"))
        for i, row in enumerate(results[:5], 1):
            print(f"  {i}. {row['postcode']} ({row['suburb']})")
        print(f"  ... ({len(results)} total results)")
        return True
    except Exception as e:
        print(f"✗ Postcode autocomplete test failed: {e}")
        return False

def test_school_info(school_id='2060'):
    """Test getting school info"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT DISTINCT
            ... (truncated for brevity)
