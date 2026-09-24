import os
import sys
import psycopg2

def migrate():
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("Error: DATABASE_URL environment variable is missing.")
        print("Make sure you are running this in the Railway environment where the Postgres plugin is attached.")
        sys.exit(1)
        
    print(f"Connecting to database...")
    try:
        conn = psycopg2.connect(url)
        conn.autocommit = True
        cursor = conn.cursor()
    except Exception as e:
        print(f"Failed to connect: {e}")
        sys.exit(1)
    
    dump_path = os.path.join(os.path.dirname(__file__), "prod_dump.sql")
    if not os.path.exists(dump_path):
        print(f"Error: {dump_path} not found.")
        sys.exit(1)
        
    print(f"Reading SQL dump ({os.path.getsize(dump_path) / 1024 / 1024:.2f} MB)...")
    with open(dump_path, 'r', encoding='utf-8') as f:
        sql = f.read()
        
    print("Executing SQL dump... This might take a minute.")
    try:
        cursor.execute(sql)
        print("✅ Success! The production database has been fully migrated and populated.")
    except Exception as e:
        print(f"❌ Failed to execute SQL: {e}")
        sys.exit(1)
    
    conn.close()

if __name__ == "__main__":
    migrate()
