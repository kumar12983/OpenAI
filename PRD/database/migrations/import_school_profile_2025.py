"""
Import School Profile 2025 data from Excel to PostgreSQL
Reads from School Profile 2025.xlsx and loads into gnaf.school_profile_2025 table
"""
import pandas as pd
import psycopg2
from psycopg2 import sql
from pathlib import Path
import sys
import os
from dotenv import load_dotenv


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


def load_school_profile_data(conn, excel_file):
    """Load School Profile 2025 data from Excel to PostgreSQL"""
    
    # Check if file exists
    excel_path = Path(excel_file)
    if not excel_path.exists():
        print(f"✗ File not found: {excel_file}")
        return 0
    
    print(f"\nLoading data from: {excel_file}")
    
    # Read Excel file
    try:
        df = pd.read_excel(excel_file, sheet_name='SchoolProfile 2025')
        print(f"✓ Read {len(df)} rows from Excel")
    except Exception as e:
        print(f"✗ Error reading Excel file: {e}")
        return 0
    
    # Display data types for debugging
    print(f"✓ Columns: {len(df.columns)}")
    print(f"✓ Null values: {df.isnull().sum().sum()} total")
    
    # Map Excel column names to database column names
    column_mapping = {
        'Calendar Year': 'calendar_year',
        'ACARA SML ID': 'acara_sml_id',
        'Location AGE ID': 'location_age_id',
        'School AGE ID': 'school_age_id',
        'School Name': 'school_name',
        'Suburb': 'suburb',
        'State': 'state',
        'Postcode': 'postcode',
        'School Sector': 'school_sector',
        'School Type': 'school_type',
        'Campus Type': 'campus_type',
        'Rolled Reporting Description': 'rolled_reporting_description',
        'School URL': 'school_url',
        'Governing Body': 'governing_body',
        'Governing Body URL': 'governing_body_url',
        'Year Range': 'year_range',
        'Geolocation': 'geolocation',
        'ICSEA': 'icsea',
        'ICSEA Percentile': 'icsea_percentile',
        'Bottom SEA Quarter (%)': 'bottom_seaquarter_pct',
        'Lower Middle SEA Quarter (%)': 'lower_middle_seaquarter_pct',
        'Upper Middle SEA Quarter (%)': 'upper_middle_seaquarter_pct',
        'Top SEA Quarter (%)': 'top_seaquarter_pct',
        'Teaching Staff': 'teaching_staff',
        'Full Time Equivalent Teaching Staff': 'full_time_equivalent_teaching_staff',
        'Non-Teaching Staff': 'non_teaching_staff',
        'Full Time Equivalent Non-Teaching Staff': 'full_time_equivalent_non_teaching_staff',
        'Total Enrolments': 'total_enrolments',
        'Girls Enrolments': 'girls_enrolments',
        'Boys Enrolments': 'boys_enrolments',
        'Full Time Equivalent Enrolments': 'full_time_equivalent_enrolments',
        'Indigenous Enrolments (%)': 'indigenous_enrolments_pct',
        'Language Background Other Than English - Yes (%)': 'language_background_other_than_english_yes_pct',
        'Language Background Other Than English - No (%)': 'language_background_other_than_english_no_pct',
        'Language Background Other Than English - Not Stated (%)': 'language_background_other_than_english_not_stated_pct',
    }
    
    # Rename columns to match database schema
    df_renamed = df.rename(columns=column_mapping)
    
    # Convert NaN to None for SQL NULL compatibility
    df_renamed = df_renamed.where(pd.notna(df_renamed), None)
    
    # Convert empty strings and 'nan' strings to None for proper NULL handling
    for col in df_renamed.columns:
        if df_renamed[col].dtype == 'object':  # String columns only
            df_renamed[col] = df_renamed[col].apply(
                lambda x: None if (isinstance(x, str) and (x.strip() == '' or x.lower() == 'nan')) else x
            )
    
    print(f"✓ Converted all blank values to NULL")
    
    # Truncate the table first
    cursor = conn.cursor()
    try:
        cursor.execute("TRUNCATE TABLE gnaf.school_profile_2025")
        conn.commit()
        print(f"✓ Truncated table gnaf.school_profile_2025")
    except psycopg2.Error as e:
        print(f"✗ Error truncating table: {e}")
        conn.rollback()
        cursor.close()
        return 0
    
    # Insert data into database
    cursor = conn.cursor()
    inserted_count = 0
    failed_count = 0
    
    # Get column names for insert statement
    db_columns = [column_mapping[col] for col in df.columns if col in column_mapping]
    
    insert_query = sql.SQL("""
        INSERT INTO gnaf.school_profile_2025 ({}) 
        VALUES ({})
    """).format(
        sql.SQL(', ').join(map(sql.Identifier, db_columns)),
        sql.SQL(', ').join(sql.Placeholder() * len(db_columns))
    )
    
    # Batch insert for better performance
    batch_size = 100
    for idx, row in df_renamed.iterrows():
        try:
            values = [row[col] for col in db_columns]
            cursor.execute(insert_query, values)
            inserted_count += 1
            
            # Commit every batch_size records
            if (idx + 1) % batch_size == 0:
                conn.commit()
                print(f"  Inserted {idx + 1}/{len(df)} records...")
        
        except psycopg2.Error as e:
            failed_count += 1
            if failed_count <= 5:  # Show first 5 errors
                print(f"  ✗ Error inserting row {idx + 1} (ACARA ID: {row.get('acara_sml_id')}): {e}")
            conn.rollback()
    
    # Final commit
    conn.commit()
    
    print(f"\n✓ Successfully inserted: {inserted_count} records")
    if failed_count > 0:
        print(f"✗ Failed records: {failed_count}")
    
    cursor.close()
    return inserted_count


def main():
    """Main function"""
    print("=" * 80)
    print("School Profile 2025 - Data Import to PostgreSQL")
    print("=" * 80)
    
    # Load environment variables
    load_dotenv()
    
    # Database connection parameters from .env
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'database': os.getenv('DB_NAME', 'gnaf_db'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', '')
    }
    
    excel_file = 'School Profile 2025.xlsx'
    
    # Connect to database
    conn = connect_to_db(**db_config)
    
    try:
        # Load data
        count = load_school_profile_data(conn, excel_file)
        
        if count > 0:
            print("\n✓ Data import completed successfully!")
        else:
            print("\n✗ No data was imported")
    
    finally:
        conn.close()
        print("\n✓ Database connection closed")


if __name__ == '__main__':
    main()
