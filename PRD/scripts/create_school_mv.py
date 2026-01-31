import psycopg2
from psycopg2 import sql
import time

# Database connection parameters
DB_PARAMS = {
    'dbname': 'gnaf_db',
    'user': 'postgres',
    'password': '$omething!',
    'host': 'localhost',
    'port': '5432'
}

def create_materialized_view():
    """Create materialized view for school catchment addresses"""
    print("Connecting to database...")
    conn = psycopg2.connect(**DB_PARAMS)
    conn.autocommit = True
    cursor = conn.cursor()
    
    print("\nReading SQL file...")
    with open('create_school_address_mv.sql', 'r') as f:
        sql_content = f.read()
    
    print("\nThis will create a materialized view mapping addresses to school catchments.")
    print("This may take several minutes depending on the dataset size...")
    print("\nStarting creation...\n")
    
    start_time = time.time()
    
    try:
        # Execute the SQL (it contains multiple statements)
        cursor.execute(sql_content)
        
        elapsed_time = time.time() - start_time
        print(f"\n✓ Materialized view created successfully in {elapsed_time:.2f} seconds")
        
    except Exception as e:
        print(f"\n✗ Error creating materialized view: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    create_materialized_view()
