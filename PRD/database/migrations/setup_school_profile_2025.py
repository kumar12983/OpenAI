"""
Setup and import School Profile 2025 data
1. Create the table if it doesn't exist
2. Import data from Excel
"""
import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv


def create_table(conn):
    """Create the school_profile_2025 table"""
    create_table_sql = """
    DROP TABLE IF EXISTS gnaf.school_profile_2025;
    
    CREATE TABLE gnaf.school_profile_2025 (
        -- Identifiers
        calendar_year INT NOT NULL,
        acara_sml_id INT NOT NULL PRIMARY KEY,
        location_age_id NUMERIC,
        school_age_id NUMERIC,
        
        -- School Information
        school_name VARCHAR(255) NOT NULL,
        suburb VARCHAR(100) NOT NULL,
        state VARCHAR(10) NOT NULL,
        postcode INT NOT NULL,
        school_sector VARCHAR(100),
        school_type VARCHAR(100),
        campus_type VARCHAR(100),
        rolled_reporting_description VARCHAR(255),
        year_range VARCHAR(50),
        
        -- School URLs and Governance
        school_url TEXT,
        governing_body VARCHAR(255),
        governing_body_url TEXT,
        
        -- Geographic Data
        geolocation VARCHAR(255),
        
        -- School Quality Index (ICSEA)
        icsea NUMERIC,
        icsea_percentile NUMERIC,
        bottom_seaquarter_pct NUMERIC,
        lower_middle_seaquarter_pct NUMERIC,
        upper_middle_seaquarter_pct NUMERIC,
        top_seaquarter_pct NUMERIC,
        
        -- Staffing Data
        teaching_staff NUMERIC,
        full_time_equivalent_teaching_staff NUMERIC,
        non_teaching_staff NUMERIC,
        full_time_equivalent_non_teaching_staff NUMERIC,
        
        -- Enrolment Data
        total_enrolments NUMERIC,
        girls_enrolments NUMERIC,
        boys_enrolments NUMERIC,
        full_time_equivalent_enrolments NUMERIC,
        
        -- Demographic Data
        indigenous_enrolments_pct NUMERIC,
        language_background_other_than_english_yes_pct NUMERIC,
        language_background_other_than_english_no_pct NUMERIC,
        language_background_other_than_english_not_stated_pct NUMERIC,
        
        -- Metadata
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Create indexes for common queries
    CREATE INDEX idx_school_profile_2025_school_name ON gnaf.school_profile_2025(school_name);
    CREATE INDEX idx_school_profile_2025_postcode ON gnaf.school_profile_2025(postcode);
    CREATE INDEX idx_school_profile_2025_suburb ON gnaf.school_profile_2025(suburb);
    CREATE INDEX idx_school_profile_2025_state ON gnaf.school_profile_2025(state);
    CREATE INDEX idx_school_profile_2025_school_sector ON gnaf.school_profile_2025(school_sector);
    CREATE INDEX idx_school_profile_2025_school_type ON gnaf.school_profile_2025(school_type);
    CREATE INDEX idx_school_profile_2025_calendar_year ON gnaf.school_profile_2025(calendar_year);
    """
    
    cursor = conn.cursor()
    try:
        for statement in create_table_sql.split(';'):
            statement = statement.strip()
            if statement:
                cursor.execute(statement)
        conn.commit()
        print("✓ Table created successfully")
        return True
    except psycopg2.Error as e:
        print(f"✗ Error creating table: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()


def main():
    """Main function"""
    print("=" * 80)
    print("Setup: Create school_profile_2025 table")
    print("=" * 80)
    
    # Load environment variables
    load_dotenv()
    
    # Database connection parameters
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'database': os.getenv('DB_NAME', 'gnaf_db'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', '')
    }
    
    # Connect to database
    try:
        conn = psycopg2.connect(**db_config)
        print(f"✓ Connected to {db_config['database']}")
    except psycopg2.Error as e:
        print(f"✗ Error connecting to database: {e}")
        return
    
    try:
        # Create table
        if create_table(conn):
            print("\n✓ Table setup completed successfully!")
        else:
            print("\n✗ Failed to create table")
    
    finally:
        conn.close()
        print("✓ Database connection closed")


if __name__ == '__main__':
    main()
