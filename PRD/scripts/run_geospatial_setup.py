"""
Run the GNAF geospatial setup script to add geometry columns and spatial indexes.
This will enable all geospatial query capabilities.
"""

import psycopg2
from psycopg2 import sql
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()


def run_sql_file(cursor, filepath):
    """Execute a SQL file, handling errors gracefully."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Split by semicolons but keep multi-line statements together
        statements = []
        current_statement = []
        
        for line in sql_content.split('\n'):
            # Skip comment-only lines
            if line.strip().startswith('--') and not current_statement:
                continue
            
            current_statement.append(line)
            
            # Check if line ends with semicolon (end of statement)
            if line.strip().endswith(';'):
                statement = '\n'.join(current_statement)
                if statement.strip() and not statement.strip().startswith('--'):
                    statements.append(statement)
                current_statement = []
        
        return statements
    except Exception as e:
        print(f"Error reading SQL file: {e}")
        return []


def setup_geospatial():
    """Run the GNAF geospatial setup script."""
    
    # Get connection parameters
    conn_params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'gnaf_db'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
        'port': int(os.getenv('DB_PORT', 5432))
    }
    
    sql_file = Path('realestate/gnaf_geospatial_setup.sql')
    
    if not sql_file.exists():
        print(f"✗ SQL file not found: {sql_file}")
        return False
    
    try:
        print("="*70)
        print("GNAF Geospatial Setup - Adding Geometry Columns and Indexes")
        print("="*70)
        print(f"\nConnecting to {conn_params['database']}...")
        
        conn = psycopg2.connect(**conn_params)
        conn.autocommit = False  # Use transactions
        cursor = conn.cursor()
        
        print(f"✓ Connected\n")
        
        # Read and parse SQL file
        print(f"Reading SQL file: {sql_file}")
        statements = run_sql_file(cursor, sql_file)
        print(f"✓ Found {len(statements)} SQL statements\n")
        
        # Execute statements
        total = len(statements)
        success_count = 0
        
        for i, statement in enumerate(statements, 1):
            # Extract meaningful description from statement
            lines = [l.strip() for l in statement.split('\n') if l.strip() and not l.strip().startswith('--')]
            first_line = lines[0][:60] + '...' if lines and len(lines[0]) > 60 else lines[0] if lines else 'SQL statement'
            
            try:
                print(f"[{i}/{total}] Executing: {first_line}")
                
                start_time = time.time()
                cursor.execute(statement)
                elapsed = time.time() - start_time
                
                # Check if there's a result to fetch
                if cursor.description:
                    results = cursor.fetchall()
                    if results:
                        for row in results:
                            print(f"        → {row}")
                
                print(f"        ✓ Done ({elapsed:.2f}s)")
                success_count += 1
                
                # Commit after each successful statement
                conn.commit()
                
            except psycopg2.Error as e:
                # Check if error is acceptable (e.g., already exists)
                error_msg = str(e).lower()
                if any(x in error_msg for x in ['already exists', 'does not exist', 'if exists']):
                    print(f"        ℹ Skipped (already done)")
                    conn.rollback()
                    success_count += 1
                else:
                    print(f"        ✗ Error: {e}")
                    conn.rollback()
                    # Continue with next statement
            except Exception as e:
                print(f"        ✗ Unexpected error: {e}")
                conn.rollback()
        
        print("\n" + "="*70)
        print(f"Setup Complete: {success_count}/{total} statements executed successfully")
        print("="*70)
        
        # Verify geometry columns were added
        print("\nVerifying geometry columns...")
        cursor.execute("""
            SELECT f_table_name, f_geometry_column, srid, type,
                   (SELECT COUNT(*) FROM information_schema.columns c 
                    WHERE c.table_schema = g.f_table_schema 
                    AND c.table_name = g.f_table_name 
                    AND c.column_name = g.f_geometry_column) as exists
            FROM geometry_columns g
            WHERE f_table_schema = 'gnaf'
            ORDER BY f_table_name;
        """)
        geom_cols = cursor.fetchall()
        
        if geom_cols:
            print(f"✓ {len(geom_cols)} geometry columns added:")
            for col in geom_cols:
                status = "✓" if col[4] > 0 else "✗"
                print(f"  {status} {col[0]}.{col[1]} ({col[3]}, SRID: {col[2]})")
        
        # Check spatial indexes
        print("\nVerifying spatial indexes...")
        cursor.execute("""
            SELECT schemaname, tablename, indexname
            FROM pg_indexes
            WHERE schemaname = 'gnaf'
            AND indexname LIKE '%geom%'
            ORDER BY tablename, indexname;
        """)
        indexes = cursor.fetchall()
        
        if indexes:
            print(f"✓ {len(indexes)} spatial indexes created:")
            for idx in indexes:
                print(f"  ✓ {idx[1]}.{idx[2]}")
        
        # Count geocoded records
        print("\nChecking geocoded data...")
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(geom) as geocoded,
                ROUND(100.0 * COUNT(geom) / NULLIF(COUNT(*), 0), 2) as percent
            FROM gnaf.address_default_geocode;
        """)
        stats = cursor.fetchone()
        print(f"✓ address_default_geocode: {stats[1]:,} / {stats[0]:,} records geocoded ({stats[2]}%)")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*70)
        print("✓ Geospatial Setup Complete!")
        print("="*70)
        print("\nYou can now run geospatial queries!")
        print("\nTry running queries from:")
        print("  realestate/gnaf_geospatial_queries.sql")
        print("\nOr use Python to query geocoded addresses:")
        print("  - Find nearest addresses")
        print("  - Calculate distances")
        print("  - Search within radius")
        print("  - Export to GeoJSON")
        
        return True
        
    except psycopg2.Error as e:
        print(f"\n✗ Database Error: {e}")
        if conn:
            conn.rollback()
        return False
    except Exception as e:
        print(f"\n✗ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()


if __name__ == "__main__":
    success = setup_geospatial()
    sys.exit(0 if success else 1)
