import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection parameters
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER") 
DB_NAME = os.getenv("DB_NAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT")

try:
    # Connect to PostgreSQL
    conn = psycopg2.connect(
        host=DB_HOST,
        user=DB_USER,
        database=DB_NAME,
        password=DB_PASSWORD,
        port=DB_PORT
    )
    
    cursor = conn.cursor()
    
    # Check existing tables
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    
    tables = cursor.fetchall()
    print("Existing tables in database:")
    for table in tables:
        print(f"- {table[0]}")
    
    # Get table schemas
    for table in tables:
        table_name = table[0]
        print(f"\n--- Schema for {table_name} ---")
        cursor.execute(f"""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = '{table_name}'
        """)
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
    
    cursor.close()
    conn.close()
    print("\nDatabase connection successful!")
    
except Exception as e:
    print(f"Error connecting to database: {e}")
