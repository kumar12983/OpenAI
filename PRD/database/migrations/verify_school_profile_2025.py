"""Verify imported School Profile 2025 data"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

db_config = {
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

conn = psycopg2.connect(**db_config)
cur = conn.cursor()

print("=" * 80)
print("School Profile 2025 - Data Verification")
print("=" * 80)

# Total records
cur.execute('SELECT COUNT(*) FROM gnaf.school_profile_2025')
total = cur.fetchone()[0]
print(f"\n✓ Total records: {total:,}")

# School sectors and types
cur.execute('SELECT COUNT(DISTINCT school_sector) as sectors, COUNT(DISTINCT school_type) as types FROM gnaf.school_profile_2025')
sectors, types = cur.fetchone()
print(f"✓ School sectors: {sectors}")
print(f"✓ School types: {types}")

# Sample records
cur.execute('SELECT school_name, suburb, postcode, school_sector FROM gnaf.school_profile_2025 LIMIT 5')
print(f"\n✓ Sample records (first 5):")
for row in cur.fetchall():
    print(f"  - {row[0]} ({row[3]}), {row[1]} {row[2]}")

# Data completeness
cur.execute('''
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN school_url IS NOT NULL THEN 1 END) as has_url,
        COUNT(CASE WHEN icsea IS NOT NULL THEN 1 END) as has_icsea,
        COUNT(CASE WHEN total_enrolments IS NOT NULL THEN 1 END) as has_enrolments
    FROM gnaf.school_profile_2025
''')
total, with_url, with_icsea, with_enrolments = cur.fetchone()
print(f"\n✓ Data completeness:")
print(f"  - Records with School URL: {with_url:,}/{total:,}")
print(f"  - Records with ICSEA: {with_icsea:,}/{total:,}")
print(f"  - Records with Enrolment data: {with_enrolments:,}/{total:,}")

# States represented
cur.execute('SELECT state, COUNT(*) as count FROM gnaf.school_profile_2025 GROUP BY state ORDER BY count DESC')
print(f"\n✓ Records by State:")
for state, count in cur.fetchall():
    print(f"  - {state}: {count:,}")

cur.close()
conn.close()
print("\n" + "=" * 80)
print("✓ Verification complete!")
print("=" * 80)
