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
        print(f"File not found: {file_path}")
        print(f"Current directory: {os.getcwd()}")
        return False
    
    print(f"Reading SQL file: {file_path}")
    
    # Read SQL file with encoding error handling
    sql_content = None
    for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
        try:
            with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                sql_content = f.read()
            print(f"Successfully read file with encoding: {encoding}")
            break
        except Exception:
            continue
    
    if sql_content is None:
        print(f"Could not read file")
        return False
    
    # Connect to database
    try:
        print("Connecting to database...")
        conn = psycopg2.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        print("Connected to database")
    except psycopg2.OperationalError as e:
        # Handle error messages that might be in system locale encoding (GBK)
        try:
            error_msg = str(e)
        except UnicodeDecodeError:
            import locale
            system_encoding = locale.getpreferredencoding() or 'gbk'
            if hasattr(e, 'args') and e.args and isinstance(e.args[0], bytes):
                error_msg = e.args[0].decode(system_encoding, errors='replace')
            else:
                error_msg = "Connection error (could not decode error message)"
        print(f"Connection error: {error_msg}")
        print("\nTroubleshooting:")
        print("1. Make sure PostgreSQL is running")
        print("2. Verify your .env file has correct credentials")
        print("3. Check if the database 'course_planner' exists")
        print("   If not, create it: CREATE DATABASE course_planner;")
        return False
    except UnicodeDecodeError as e:
        # Handle encoding errors when processing error messages
        import locale
        system_encoding = locale.getpreferredencoding() or 'gbk'
        print("Encoding error occurred while processing database error message.")
        try:
            if len(e.args) >= 2 and isinstance(e.args[1], bytes):
                actual_error = e.args[1].decode(system_encoding, errors='replace')
                print(f"Actual error: {actual_error}")
        except Exception:
            pass
        print("\nTroubleshooting:")
        print("1. Make sure PostgreSQL is running")
        print("2. Create the database 'course_planner' if it doesn't exist")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    try:
        cursor = conn.cursor()
        print("Executing SQL statements...")
        
        # Split SQL into statements by semicolon
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip() and not stmt.strip().startswith('--')]
        
        executed_count = 0
        for i, statement in enumerate(statements, 1):
            try:
                cursor.execute(statement)
                executed_count += 1
            except psycopg2.Error as e:
                error_msg = str(e).lower()
                if 'already exists' in error_msg or 'duplicate' in error_msg:
                    print(f"Statement {i}: Object already exists (skipping)")
                    continue
                else:
                    print(f"Error in statement {i}: {e}")
                    continue
        
        conn.commit()
        cursor.close()
        conn.close()
        print(f"Executed {executed_count} SQL statements successfully!")
        print("Database setup complete")
        return True
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        print(f"Error executing SQL: {e}")
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
        print(f"SQL file not found: {sql_file}")
        print(f"Current directory: {os.getcwd()}")
    else:
        print(f"Found SQL file: {sql_file}")
        print()
        execute_sql_file(sql_file)
