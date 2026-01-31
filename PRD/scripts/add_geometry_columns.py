"""
Add geometry columns to GNAF tables and populate them with coordinate data.
This is Step 1 of the geospatial setup.
"""

import psycopg2
import os
import sys
from dotenv import load_dotenv
import time

load_dotenv()


def add_geometry_columns():
    """Add and populate geometry columns in GNAF tables."""
    
    conn_params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'gnaf_db'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
        'port': int(os.getenv('DB_PORT', 5432))
    }
    
    try:
        print("="*70)
        print("Adding Geometry Columns to GNAF Tables")
        print("="*70)
        
        conn = psycopg2.connect(**conn_params)
        conn.autocommit = False
        cursor = conn.cursor()
        
        print("\n✓ Connected to database\n")
        
        # Set search path
        cursor.execute("SET search_path TO gnaf, public;")
        conn.commit()
        
        # Step 1: Add geometry column to address_default_geocode
        print("[1/6] Adding geometry column to address_default_geocode...")
        try:
            cursor.execute("""
                ALTER TABLE address_default_geocode 
                ADD COLUMN IF NOT EXISTS geom geometry(Point, 4326);
            """)
            conn.commit()
            print("      ✓ Column added")
        except Exception as e:
            print(f"      ℹ {e}")
            conn.rollback()
        
        # Step 2: Populate geometry in address_default_geocode
        print("\n[2/6] Populating geometry from latitude/longitude...")
        print("      This may take a few minutes for 16+ million records...")
        
        start_time = time.time()
        cursor.execute("""
            UPDATE address_default_geocode 
            SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
            WHERE longitude IS NOT NULL 
              AND latitude IS NOT NULL
              AND geom IS NULL;
        """)
        updated = cursor.rowcount
        conn.commit()
        elapsed = time.time() - start_time
        
        print(f"      ✓ Updated {updated:,} records in {elapsed:.1f} seconds")
        
        # Step 3: Add geometry column to address_site_geocode
        print("\n[3/6] Adding geometry column to address_site_geocode...")
        try:
            cursor.execute("""
                ALTER TABLE address_site_geocode 
                ADD COLUMN IF NOT EXISTS geom geometry(Point, 4326);
            """)
            conn.commit()
            print("      ✓ Column added")
        except Exception as e:
            print(f"      ℹ {e}")
            conn.rollback()
        
        # Step 4: Populate geometry in address_site_geocode
        print("\n[4/6] Populating geometry in address_site_geocode...")
        
        start_time = time.time()
        cursor.execute("""
            UPDATE address_site_geocode 
            SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
            WHERE longitude IS NOT NULL 
              AND latitude IS NOT NULL
              AND geom IS NULL;
        """)
        updated = cursor.rowcount
        conn.commit()
        elapsed = time.time() - start_time
        
        print(f"      ✓ Updated {updated:,} records in {elapsed:.1f} seconds")
        
        # Step 5: Create spatial indexes
        print("\n[5/6] Creating spatial index on address_default_geocode...")
        start_time = time.time()
        try:
            cursor.execute("DROP INDEX IF EXISTS gnaf.idx_address_default_geocode_geom;")
            cursor.execute("""
                CREATE INDEX idx_address_default_geocode_geom 
                ON address_default_geocode USING GIST(geom);
            """)
            conn.commit()
            elapsed = time.time() - start_time
            print(f"      ✓ Index created in {elapsed:.1f} seconds")
        except Exception as e:
            print(f"      ✗ Error: {e}")
            conn.rollback()
        
        print("\n[6/6] Creating spatial index on address_site_geocode...")
        start_time = time.time()
        try:
            cursor.execute("DROP INDEX IF EXISTS gnaf.idx_address_site_geocode_geom;")
            cursor.execute("""
                CREATE INDEX idx_address_site_geocode_geom 
                ON address_site_geocode USING GIST(geom);
            """)
            conn.commit()
            elapsed = time.time() - start_time
            print(f"      ✓ Index created in {elapsed:.1f} seconds")
        except Exception as e:
            print(f"      ✗ Error: {e}")
            conn.rollback()
        
        # Verify setup
        print("\n" + "="*70)
        print("Verification")
        print("="*70)
        
        cursor.execute("""
            SELECT f_table_name, f_geometry_column, srid, type
            FROM geometry_columns
            WHERE f_table_schema = 'gnaf'
            ORDER BY f_table_name;
        """)
        geom_cols = cursor.fetchall()
        
        if geom_cols:
            print(f"\n✓ Geometry columns registered:")
            for col in geom_cols:
                print(f"  - {col[0]}.{col[1]} ({col[3]}, SRID: {col[2]})")
        
        # Count geocoded records
        print(f"\n Geocoded Records:")
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(geom) as geocoded,
                ROUND(100.0 * COUNT(geom) / NULLIF(COUNT(*), 0), 2) as percent
            FROM address_default_geocode;
        """)
        stats = cursor.fetchone()
        print(f"  - address_default_geocode: {stats[1]:,} / {stats[0]:,} ({stats[2]}%)")
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(geom) as geocoded,
                ROUND(100.0 * COUNT(geom) / NULLIF(COUNT(*), 0), 2) as percent
            FROM address_site_geocode;
        """)
        stats = cursor.fetchone()
        print(f"  - address_site_geocode: {stats[1]:,} / {stats[0]:,} ({stats[2]}%)")
        
        # Check indexes
        cursor.execute("""
            SELECT schemaname, tablename, indexname
            FROM pg_indexes
            WHERE schemaname = 'gnaf'
            AND indexname LIKE '%geom%'
            ORDER BY tablename;
        """)
        indexes = cursor.fetchall()
        
        if indexes:
            print(f"\n✓ Spatial indexes created:")
            for idx in indexes:
                print(f"  - {idx[2]} on {idx[1]}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*70)
        print("✓ Geometry Columns Successfully Added!")
        print("="*70)
        print("\nNext steps:")
        print("1. Run: python create_materialized_view.py")
        print("2. Try example queries from: realestate/gnaf_geospatial_queries.sql")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.rollback()
        return False


if __name__ == "__main__":
    success = add_geometry_columns()
    sys.exit(0 if success else 1)
