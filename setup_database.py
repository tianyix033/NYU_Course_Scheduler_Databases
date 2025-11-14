"""
Simple script to import SQL file using Python.
Works on Windows without psql in PATH.
"""

import psycopg2
from config import Config
import os

def execute_sql_file(file_path):
    """Execute a SQL file using psycopg2."""
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        print(f"Current directory: {os.getcwd()}")
        return False
    
    print(f"Reading SQL file: {file_path}")
    
    # Read the entire SQL file
    with open(file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Connect to database
    try:
        conn = psycopg2.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        print("✓ Connected to database")
    except psycopg2.OperationalError as e:
        print(f"❌ Connection error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure PostgreSQL is running (check Windows Services)")
        print("2. Verify your .env file has correct credentials")
        print("3. Check if the database 'course_planner' exists")
        print("4. Verify the password matches your PostgreSQL installation password")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    try:
        cursor = conn.cursor()
        # Execute the SQL file content
        print("Executing SQL statements... (this may take a moment)")
        cursor.execute(sql_content)
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ SQL file executed successfully!")
        print("✓ Database setup complete")
        return True
    except Exception as e:
        conn.rollback()
        print(f"❌ Error executing SQL: {e}")
        print("\nCommon issues:")
        print("- Some objects may already exist (this is usually OK)")
        print("- Check the error message above for specific issues")
        cursor.close()
        conn.close()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Database Setup Script")
    print("=" * 60)
    print("This script will import COMMANDS_postgresql.sql into PostgreSQL")
    print("Make sure your .env file is configured correctly.")
    print("=" * 60)
    print()
    
    sql_file = "COMMANDS_postgresql.sql"
    
    if not os.path.exists(sql_file):
        print(f"❌ SQL file not found: {sql_file}")
        print(f"\nCurrent directory: {os.getcwd()}")
        print("\nMake sure:")
        print("1. COMMANDS_postgresql.sql is in the project directory")
        print("2. You're running this script from the project root directory")
    else:
        print(f"✓ Found SQL file: {sql_file}")
        print()
        execute_sql_file(sql_file)

