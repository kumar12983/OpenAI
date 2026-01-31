"""
Script to load PSV (pipe-separated values) files into PostgreSQL tables.
Automatically finds matching table name, truncates it, and loads the data.
"""

import psycopg2
from psycopg2 import sql
import pandas as pd
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class PSVLoader:
    def __init__(self, host, database, user, password, port=5432):
        """Initialize database connection parameters."""
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.port = port
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password,
                port=self.port
            )
            self.cursor = self.conn.cursor()
            print(f"✓ Connected to database: {self.database}")
        except Exception as e:
            print(f"✗ Error connecting to database: {e}")
            sys.exit(1)
    
    def close(self):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            print("✓ Database connection closed")
    
    def get_table_name_from_file(self, file_path):
        """
        Extract table name from PSV file name.
        Supported formats:
        1. <statename>_<tablename>_psv.psv -> tablename
        2. Authority_Code_<tablename>_psv.psv -> tablename (fallback)
        Examples: 
        - nsw_address_detail_psv.psv -> address_detail
        - Authority_Code_address_type_aut_psv.psv -> address_type_aut
        """
        file_name = Path(file_path).stem  # Get filename without extension
        
        # Split by underscore
        parts = file_name.split('_')
        
        # Check if format is state_table_psv (but NOT Authority_Code)
        if len(parts) >= 3 and parts[-1] == 'psv' and not (parts[0] == 'Authority' and parts[1] == 'Code'):
            # Remove first part (state) and last part (psv)
            table_parts = parts[1:-1]
            table_name = '_'.join(table_parts)
        # Check if format is Authority_Code_<filename>_psv.psv
        elif len(parts) >= 4 and parts[0] == 'Authority' and parts[1] == 'Code' and parts[-1] == 'psv':
            # Remove 'Authority_Code' prefix (first 2 parts) and '_psv' suffix (last part)
            table_parts = parts[2:-1]
            table_name = '_'.join(table_parts)
        else:
            # Fallback to original behavior if format doesn't match
            table_name = file_name
        
        # Convert to lowercase for PostgreSQL convention
        table_name = table_name.lower()
        print(f"✓ Extracted table name: {table_name}")
        return table_name
    
    def find_matching_table(self, table_name, schema='gnaf'):
        """
        Search for matching table in information_schema.
        Supports exact match or partial match.
        """
        try:
            # Try exact match first
            query = """
                SELECT table_name, table_schema
                FROM information_schema.tables
                WHERE table_schema = %s 
                AND LOWER(table_name) = LOWER(%s)
                AND table_type = 'BASE TABLE'
            """
            self.cursor.execute(query, (schema, table_name))
            result = self.cursor.fetchone()
            
            if result:
                print(f"✓ Found exact match: {result[1]}.{result[0]}")
                return result[0], result[1]
            
            # Try partial match if exact match fails
            print(f"⚠ No exact match found. Searching for partial matches...")
            query = """
                SELECT table_name, table_schema
                FROM information_schema.tables
                WHERE table_schema = %s 
                AND LOWER(table_name) LIKE LOWER(%s)
                AND table_type = 'BASE TABLE'
            """
            self.cursor.execute(query, (schema, f'%{table_name}%'))
            results = self.cursor.fetchall()
            
            if not results:
                print(f"✗ No matching table found for: {table_name}")
                return None, None
            
            if len(results) == 1:
                print(f"✓ Found partial match: {results[0][1]}.{results[0][0]}")
                return results[0][0], results[0][1]
            
            # Multiple matches - let user choose
            print(f"\n⚠ Found {len(results)} matching tables:")
            for idx, (tbl, sch) in enumerate(results, 1):
                print(f"  {idx}. {sch}.{tbl}")
            
            choice = input("\nEnter table number to use (or 0 to cancel): ")
            try:
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(results):
                    selected = results[choice_idx]
                    print(f"✓ Selected: {selected[1]}.{selected[0]}")
                    return selected[0], selected[1]
            except ValueError:
                pass
            
            print("✗ Invalid selection")
            return None, None
            
        except Exception as e:
            print(f"✗ Error finding table: {e}")
            return None, None
    
    def get_table_columns(self, table_name, schema='public'):
        """Get column names from the table."""
        try:
            query = """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = %s 
                AND table_name = %s
                ORDER BY ordinal_position
            """
            self.cursor.execute(query, (schema, table_name))
            columns = [row[0] for row in self.cursor.fetchall()]
            print(f"✓ Table has {len(columns)} columns")
            return columns
        except Exception as e:
            print(f"✗ Error getting table columns: {e}")
            return None
    
    def truncate_table(self, table_name, schema='public', cascade=False):
        """Truncate the table before loading data."""
        try:
            cascade_clause = "CASCADE" if cascade else ""
            query = sql.SQL("TRUNCATE TABLE {}.{} {}").format(
                sql.Identifier(schema),
                sql.Identifier(table_name),
                sql.SQL(cascade_clause)
            )
            self.cursor.execute(query)
            self.conn.commit()
            print(f"✓ Table {schema}.{table_name} truncated")
            return True
        except Exception as e:
            print(f"✗ Error truncating table: {e}")
            self.conn.rollback()
            return False
    
    def load_psv_file(self, file_path, table_name, schema='public', 
                      has_header=True, encoding='utf-8', batch_size=1000):
        """
        Load PSV file into PostgreSQL table using COPY command or INSERT.
        """
        try:
            # Read PSV file
            print(f"✓ Reading PSV file: {file_path}")
            df = pd.read_csv(
                file_path,
                sep='|',
                encoding=encoding,
                dtype=str,  # Read all as string initially
                keep_default_na=False  # Don't convert empty strings to NaN
            )
            
            print(f"✓ Loaded {len(df)} rows from PSV file")
            print(f"✓ File columns: {', '.join(df.columns.tolist())}")
            
            # Convert empty strings to None (NULL in database)
            # This is especially important for date fields and numeric fields
            df = df.replace('', None)
            df = df.replace(r'^\s*$', None, regex=True)  # Also handle whitespace-only values
            
            # Get table columns
            table_columns = self.get_table_columns(table_name, schema)
            if not table_columns:
                return False
            
            # Check if columns match
            if len(df.columns) != len(table_columns):
                print(f"⚠ Warning: Column count mismatch!")
                print(f"  File has {len(df.columns)} columns")
                print(f"  Table has {len(table_columns)} columns")
                
                # Map columns if user confirms
                proceed = input("Proceed anyway? (y/n): ")
                if proceed.lower() != 'y':
                    return False
            
            # Use COPY command for better performance
            try:
                # Create a temporary file-like object
                from io import StringIO
                buffer = StringIO()
                # na_rep='\\N' will write None values as \N which PostgreSQL interprets as NULL
                df.to_csv(buffer, sep='|', index=False, header=False, na_rep='\\N')
                buffer.seek(0)
                
                # Use COPY command
                columns_str = ','.join([f'"{col}"' for col in table_columns[:len(df.columns)]])
                copy_sql = f"COPY {schema}.{table_name} ({columns_str}) FROM STDIN WITH (FORMAT TEXT, DELIMITER '|', NULL '\\N')"
                
                self.cursor.copy_expert(copy_sql, buffer)
                self.conn.commit()
                print(f"✓ Loaded {len(df)} rows using COPY command")
                
            except Exception as copy_error:
                print(f"⚠ COPY command failed: {copy_error}")
                print(f"⚠ Falling back to INSERT method...")
                self.conn.rollback()
                
                # Fallback to batch INSERT
                columns_list = table_columns[:len(df.columns)]
                placeholders = ','.join(['%s'] * len(columns_list))
                columns_str = ','.join([f'"{col}"' for col in columns_list])
                insert_sql = f"INSERT INTO {schema}.{table_name} ({columns_str}) VALUES ({placeholders})"
                
                # Insert in batches
                total_inserted = 0
                for i in range(0, len(df), batch_size):
                    batch = df.iloc[i:i+batch_size]
                    # Convert rows to tuples, pandas None will be passed as Python None which psycopg2 converts to NULL
                    data = [tuple(None if pd.isna(val) else val for val in row) for row in batch.values]
                    self.cursor.executemany(insert_sql, data)
                    total_inserted += len(batch)
                    if i % (batch_size * 10) == 0:
                        print(f"  Inserted {total_inserted}/{len(df)} rows...")
                
                self.conn.commit()
                print(f"✓ Loaded {total_inserted} rows using INSERT method")
            
            return True
            
        except Exception as e:
            print(f"✗ Error loading PSV file: {e}")
            self.conn.rollback()
            return False


def main():
    """Main execution function."""
    
    # Database configuration from environment variables
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'gnaf_db'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD'),
        'port': int(os.getenv('DB_PORT', '5432'))
    }
    
    # Default PSV directory
    DEFAULT_PSV_DIR = r"C:\data\downloads\g-naf_nov25_allstates_gda2020_psv_1021\G-NAF\G-NAF NOVEMBER 2025\Standard"
    
    # Get PSV file path or directory from command line or prompt
    if len(sys.argv) > 1:
        psv_path = sys.argv[1].strip('"').strip("'")
    else:
        print(f"\nDefault directory: {DEFAULT_PSV_DIR}")
        psv_path = input("Enter PSV file path (or press Enter for default directory): ").strip('"').strip("'")
        if not psv_path:
            psv_path = DEFAULT_PSV_DIR
    
    # Check if path is a directory or file
    if os.path.isdir(psv_path):
        # It's a directory - get all PSV files
        psv_files = [f for f in Path(psv_path).glob('*_psv.psv')]
        if not psv_files:
            print(f"✗ No PSV files found in directory: {psv_path}")
            sys.exit(1)
        
        print(f"\n✓ Found {len(psv_files)} PSV files in directory")
        for idx, f in enumerate(psv_files, 1):
            print(f"  {idx}. {f.name}")
        
        choice = input("\nLoad ALL files? (yes/no) or enter file number: ").strip().lower()
        
        if choice in ['yes', 'y']:
            files_to_load = psv_files
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(psv_files):
                files_to_load = [psv_files[idx]]
            else:
                print("✗ Invalid file number")
                sys.exit(1)
        else:
            print("✗ Operation cancelled")
            sys.exit(0)
    elif os.path.isfile(psv_path):
        # It's a single file
        files_to_load = [Path(psv_path)]
    else:
        print(f"✗ Path not found: {psv_path}")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"PSV to PostgreSQL Loader")
    print(f"{'='*60}\n")
    
    # Initialize loader
    loader = PSVLoader(**DB_CONFIG)
    
    try:
        # Connect to database
        loader.connect()
        
        # Process each file
        total_files = len(files_to_load)
        successful = 0
        failed = 0
        
        for idx, psv_file in enumerate(files_to_load, 1):
            print(f"\n{'='*60}")
            print(f"Processing file {idx}/{total_files}: {psv_file.name}")
            print(f"{'='*60}\n")
            
            try:
                # Extract table name from file
                table_name = loader.get_table_name_from_file(str(psv_file))
                
                # Find matching table in database
                matched_table, schema = loader.find_matching_table(table_name)
                
                if not matched_table:
                    print(f"✗ Unable to find matching table for {psv_file.name}. Skipping.")
                    failed += 1
                    continue
                
                # TRUNCATE DISABLED - Data will be appended to existing table
                # # Confirm truncate for first file or all files
                # if idx == 1 or total_files == 1:
                #     print(f"\n⚠ WARNING: This will TRUNCATE table(s) before loading")
                #     confirm = input("Continue? (yes/no): ")
                #     if confirm.lower() not in ['yes', 'y']:
                #         print("✗ Operation cancelled")
                #         sys.exit(0)
                
                # # Truncate table
                # if not loader.truncate_table(matched_table, schema):
                #     print(f"✗ Failed to truncate table {matched_table}. Skipping.")
                #     failed += 1
                #     continue
                
                # Load data
                success = loader.load_psv_file(str(psv_file), matched_table, schema)
                
                if success:
                    print(f"✓ Successfully loaded {psv_file.name}")
                    successful += 1
                else:
                    print(f"✗ Failed to load {psv_file.name}")
                    failed += 1
                    
            except Exception as file_error:
                print(f"✗ Error processing {psv_file.name}: {file_error}")
                failed += 1
        
        # Summary
        print(f"\n{'='*60}")
        print(f"SUMMARY")
        print(f"{'='*60}")
        print(f"Total files: {total_files}")
        print(f"✓ Successful: {successful}")
        print(f"✗ Failed: {failed}")
        print(f"{'='*60}\n")
        
    except KeyboardInterrupt:
        print("\n\n✗ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)
    finally:
        loader.close()


if __name__ == "__main__":
    main()
