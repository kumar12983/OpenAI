"""
Create the School Type Lookup Table in PostgreSQL
Executes the SQL to build the lookup table with school profile integration
"""
import psycopg2
import os
from dotenv import load_dotenv
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

db_config = {
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

def create_school_lookup_table():
    """Create the school_type_lookup table"""
    
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    
    try:
        # Read the SQL file
        with open('create_school_lookup_table.sql', 'r') as f:
            sql = f.read()
        
        print("=" * 80)
        print("Creating School Type Lookup Table")
        print("=" * 80)
        
        # Execute the SQL
        cursor.execute(sql)
        conn.commit()
        
        # Fetch summary results
        cursor.execute("""
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT school_id) as unique_schools,
            COUNT(acara_sml_id) as matched_with_profile,
            COUNT(DISTINCT state) as states_covered
        FROM gnaf.school_type_lookup;
        """)
        
        summary = cursor.fetchone()
        
        print("\n✓ School Type Lookup Table Created Successfully!")
        print("\nSummary Statistics:")
        print(f"  Total Records: {summary[0]:,}")
        print(f"  Unique Schools: {summary[1]:,}")
        print(f"  Matched with Profile: {summary[2]:,}")
        print(f"  States Covered: {summary[3]}")
        
        # Show sample data
        print("\n" + "=" * 80)
        print("Sample Data (First 5 records)")
        print("=" * 80)
        
        cursor.execute("""
        SELECT 
            school_id,
            catchment_school_name,
            school_type_name,
            profile_school_name,
            school_sector,
            icsea,
            state
        FROM gnaf.school_type_lookup
        LIMIT 5;
        """)
        
        cols = [desc[0] for desc in cursor.description]
        print(f"\n{cols[0]:<12} {cols[1]:<30} {cols[2]:<20} {cols[3]:<30} {cols[4]:<15} {cols[5]:<10} {cols[6]:<8}")
        print("-" * 130)
        
        for row in cursor.fetchall():
            school_id, catchment_name, type_name, profile_name, sector, icsea, state = row
            c_name = str(catchment_name)[:29] if catchment_name else ""
            t_name = str(type_name)[:19] if type_name else ""
            p_name = str(profile_name)[:29] if profile_name else ""
            s_name = str(sector)[:14] if sector else ""
            i_val = str(icsea)[:9] if icsea else ""
            st = str(state)[:8] if state else ""
            print(f"{school_id:<12} {c_name:<30} {t_name:<20} {p_name:<30} {s_name:<15} {i_val:<10} {st:<8}")
        
        # Show statistics by state
        print("\n" + "=" * 80)
        print("Schools by State")
        print("=" * 80)
        
        cursor.execute("""
        SELECT 
            state,
            COUNT(DISTINCT school_id) as school_count,
            COUNT(acara_sml_id) as profile_matched
        FROM gnaf.school_type_lookup
        GROUP BY state
        ORDER BY school_count DESC;
        """)
        
        print(f"\n{'State':<10} {'Schools':<15} {'Profile Matched':<15}")
        print("-" * 40)
        for row in cursor.fetchall():
            state, count, matched = row
            state_str = str(state) if state else "N/A"
            print(f"{state_str:<10} {count:<15} {matched:<15}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error creating lookup table: {e}")
        import traceback
        traceback.print_exc()
        cursor.close()
        conn.close()
        return False


if __name__ == '__main__':
    success = create_school_lookup_table()
    exit(0 if success else 1)
