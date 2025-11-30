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
        print(f"Error: File not found: {file_path}")
        return False
    
    print(f"Reading SQL file: {file_path}")
    
    # Read SQL file
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            sql_content = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return False
    
    # Connect to database
    try:
        print("Connecting to database...")
        if Config.DATABASE_URL:
            conn = psycopg2.connect(Config.DATABASE_URL)
        else:
            conn = psycopg2.connect(
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME
            )
        conn.autocommit = True
        print("Connected to database")
    except Exception as e:
        print(f"Connection error: {e}")
        return False
    
    # Execute SQL file
    try:
        cursor = conn.cursor()
        print("Executing SQL...")
        
        # Try executing the whole file first (works for well-formed SQL)
        try:
            cursor.execute(sql_content)
            cursor.close()
            conn.close()
            print("SQL file executed successfully")
            return True
        except psycopg2.Error:
            # If that fails, execute statement by statement
            cursor.close()
            cursor = conn.cursor()
            
            # Simple split - PostgreSQL procedures/functions need special handling
            # Split on semicolons but be aware this may break inside $$ blocks
            statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]
            
            executed = 0
            errors = 0
            
            for i, stmt in enumerate(statements, 1):
                try:
                    cursor.execute(stmt)
                    executed += 1
                except psycopg2.Error as e:
                    # Skip "already exists" errors
                    if 'already exists' not in str(e).lower() and 'duplicate' not in str(e).lower():
                        errors += 1
                        if errors <= 5:
                            print(f"  Error in statement {i}: {e}")
            
            cursor.close()
            conn.close()
            
            print(f"Executed {executed} statements")
            if errors > 0:
                print(f"Encountered {errors} errors")
                return False
            return True
        
    except Exception as e:
        print(f"Error executing SQL: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Database Setup Script")
    print("=" * 60)
    print()
    
    # Execute main SQL file
    sql_file = "COMMANDS_postgresql.sql"
    if not os.path.exists(sql_file):
        sql_file = "COMMANDS.sql"
        if not os.path.exists(sql_file):
            print(f"Error: SQL file not found")
            exit(1)
    
    print(f"Executing: {sql_file}")
    if not execute_sql_file(sql_file):
        print("\nError: Failed to execute main SQL file")
        exit(1)
    
    # Execute additional SQL file if exists
    additional_file = "additional_commands_postgressql.sql"
    if os.path.exists(additional_file):
        print(f"\nExecuting: {additional_file}")
        if not execute_sql_file(additional_file):
            print("\nError: Failed to execute additional SQL file")
            exit(1)
    
    print("\n" + "=" * 60)
    print("Database setup completed successfully!")
    print("=" * 60)
