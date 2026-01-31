"""
Load GNAF CSV data into PostgreSQL database
Loads suburb-postcode mappings from CSV files into the GNAF database
"""
import psycopg2
from psycopg2 import sql
import csv
from pathlib import Path
import sys


def connect_to_db(host='localhost', port=5432, database='gnaf_db', user='postgres', password=''):
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        print(f"✓ Connected to database: {database}")
        return conn
    except psycopg2.Error as e:
        print(f"✗ Error connecting to database: {e}")
        sys.exit(1)


def load_suburb_postcode_csv(conn, csv_file, state='NSW'):
    """Load suburb-postcode data from CSV file"""
    csv_path = Path(csv_file)
    
    if not csv_path.exists():
        print(f"✗ File not found: {csv_file}")
        return 0
    
    print(f"\nLoading data from: {csv_file}")
    
    cursor = conn.cursor()
    loaded_count = 0
    skipped_count = 0
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Determine column names (handle both 'suburb,postcode' and 'postcode,suburb')
        fieldnames = reader.fieldnames
        if not fieldnames:
            print("✗ No header found in CSV")
            return 0
        
        # Normalize column names
        fieldnames_lower = [fn.lower().strip() for fn in fieldnames]
        
        if 'suburb' not in fieldnames_lower or 'postcode' not in fieldnames_lower:
            print(f"✗ CSV must have 'suburb' and 'postcode' columns. Found: {fieldnames}")
            return 0
        
        suburb_col = fieldnames[fieldnames_lower.index('suburb')]
        postcode_col = fieldnames[fieldnames_lower.index('postcode')]
        
        for row in reader:
            suburb = row.get(suburb_col, '').strip()
            postcode = row.get(postcode_col, '').strip()
            
            # Skip invalid data
            if not suburb or not postcode:
                skipped_count += 1
                continue
            
            # Skip non-numeric postcodes
            if not postcode.isdigit() or len(postcode) != 4:
                skipped_count += 1
                continue
            
            # Skip junk data (from web scraping artifacts)
            junk_keywords = [
                'search', 'home', 'territory', 'urban centres', 'time zones',
                'postcode lists', 'hotels', 'faq', 'contact', 'recently viewed',
                'sign in', 'register', 'menu'
            ]
            if any(keyword in suburb.lower() for keyword in junk_keywords):
                skipped_count += 1
                continue
            
            try:
                # Insert into suburb_postcode table
                cursor.execute("""
                    INSERT INTO gnaf.suburb_postcode (suburb, postcode, state)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (suburb, postcode) DO NOTHING
                """, (suburb.upper(), postcode, state))
                
                if cursor.rowcount > 0:
                    loaded_count += 1
                else:
                    skipped_count += 1
                    
            except psycopg2.Error as e:
                print(f"✗ Error inserting {suburb}, {postcode}: {e}")
                skipped_count += 1
    
    conn.commit()
    cursor.close()
    
    print(f"✓ Loaded {loaded_count} records")
    print(f"  Skipped {skipped_count} records (duplicates or invalid data)")
    
    return loaded_count


def load_localities_from_suburb_postcode(conn):
    """Create locality records from suburb_postcode data"""
    print("\nCreating locality records from suburb_postcode data...")
    
    cursor = conn.cursor()
    
    # Insert unique suburbs as localities
    cursor.execute("""
        INSERT INTO gnaf.localities (locality_name, primary_postcode, state_abbreviation)
        SELECT DISTINCT 
            sp.suburb,
            sp.postcode,
            sp.state
        FROM gnaf.suburb_postcode sp
        WHERE NOT EXISTS (
            SELECT 1 FROM gnaf.localities l 
            WHERE UPPER(l.locality_name) = UPPER(sp.suburb) 
            AND l.primary_postcode = sp.postcode
        )
        ON CONFLICT DO NOTHING
    """)
    
    inserted = cursor.rowcount
    conn.commit()
    cursor.close()
    
    print(f"✓ Created {inserted} locality records")
    return inserted


def show_statistics(conn):
    """Display database statistics"""
    print("\n" + "="*60)
    print("DATABASE STATISTICS")
    print("="*60)
    
    cursor = conn.cursor()
    
    # Total records
    cursor.execute("SELECT COUNT(*) FROM gnaf.suburb_postcode")
    total_mappings = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT suburb) FROM gnaf.suburb_postcode")
    unique_suburbs = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT postcode) FROM gnaf.suburb_postcode")
    unique_postcodes = cursor.fetchone()[0]
    
    print(f"\nSuburb-Postcode Mappings: {total_mappings}")
    print(f"Unique Suburbs: {unique_suburbs}")
    print(f"Unique Postcodes: {unique_postcodes}")
    
    # By state
    print("\nBreakdown by State:")
    cursor.execute("""
        SELECT state, COUNT(*) as count
        FROM gnaf.suburb_postcode
        GROUP BY state
        ORDER BY state
    """)
    
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} mappings")
    
    # Sample data
    print("\nSample Data (first 10 records):")
    cursor.execute("""
        SELECT suburb, postcode, state
        FROM gnaf.suburb_postcode
        ORDER BY suburb
        LIMIT 10
    """)
    
    for row in cursor.fetchall():
        print(f"  {row[0]}, {row[1]} ({row[2]})")
    
    cursor.close()
    print("="*60)


def main():
    """Main function"""
    print("="*60)
    print("GNAF Database Loader")
    print("="*60)
    
    # Database connection parameters
    # Modify these to match your PostgreSQL setup
    DB_HOST = 'localhost'
    DB_PORT = 5432
    DB_NAME = 'gnaf_db'
    DB_USER = 'postgres'
    DB_PASSWORD = input("Enter PostgreSQL password (or press Enter if none): ").strip()
    
    # Connect to database
    conn = connect_to_db(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    
    # Load CSV files
    csv_files = [
        ('nsw_suburbs_postcodes.csv', 'NSW'),
        ('nsw_postcodes_suburbs.csv', 'NSW'),
    ]
    
    total_loaded = 0
    for csv_file, state in csv_files:
        if Path(csv_file).exists():
            count = load_suburb_postcode_csv(conn, csv_file, state)
            total_loaded += count
        else:
            print(f"⚠ File not found, skipping: {csv_file}")
    
    # Create locality records
    if total_loaded > 0:
        load_localities_from_suburb_postcode(conn)
    
    # Show statistics
    show_statistics(conn)
    
    # Close connection
    conn.close()
    print("\n✓ Database connection closed")
    print("✓ Data loading complete!")


if __name__ == '__main__':
    main()
