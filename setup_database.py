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
        
        # Split SQL into statements, respecting dollar-quoted strings
        def split_sql(sql_text):
            """Split SQL into statements, handling $$ blocks and ' strings."""
            statements = []
            current = []
            i = 0
            in_dollar = False
            dollar_tag = None
            in_quote = False
            
            while i < len(sql_text):
                char = sql_text[i]
                
                # Handle dollar-quoted strings ($$ or $tag$)
                if char == '$' and not in_quote:
                    start = i
                    i += 1
                    # Read the tag (until next $)
                    while i < len(sql_text) and sql_text[i] != '$':
                        i += 1
                    if i < len(sql_text):
                        tag = sql_text[start:i+1]  # Includes both $ signs
                        current.append(tag)
                        if not in_dollar:
                            # Opening tag
                            dollar_tag = tag
                            in_dollar = True
                        elif tag == dollar_tag:
                            # Closing tag
                            dollar_tag = None
                            in_dollar = False
                        i += 1
                        continue
                
                # Handle single quotes (only if not in dollar quote)
                if char == "'" and not in_dollar:
                    # Check for escaped quote
                    if i > 0 and sql_text[i-1] == '\\':
                        current.append(char)
                        i += 1
                        continue
                    in_quote = not in_quote
                    current.append(char)
                    i += 1
                    continue
                
                # Statement terminator (semicolon outside quotes)
                if char == ';' and not in_dollar and not in_quote:
                    current.append(char)
                    stmt = ''.join(current).strip()
                    if stmt and not stmt.startswith('--'):
                        statements.append(stmt)
                    current = []
                    i += 1
                    continue
                
                current.append(char)
                i += 1
            
            # Add final statement
            if current:
                stmt = ''.join(current).strip()
                if stmt:
                    statements.append(stmt)
            
            return statements
        
        statements = split_sql(sql_content)
        # Filter out empty statements
        statements = [s for s in statements if s.strip() and not s.strip().startswith('--')]
        print(f"Parsed {len(statements)} statements")
        
        executed = 0
        skipped = 0
        errors = 0
        
        for i, stmt in enumerate(statements, 1):
            try:
                cursor.execute(stmt)
                executed += 1
            except psycopg2.Error as e:
                err_str = str(e).lower()
                # Skip "already exists" errors - these are expected on reruns
                if 'already exists' in err_str or 'duplicate' in err_str:
                    skipped += 1
                else:
                    errors += 1
                    if errors <= 10:
                        print(f"  Error in statement {i}: {e}")
                        # Show first 100 chars of problematic statement
                        preview = stmt[:100].replace('\n', ' ')
                        print(f"    Preview: {preview}...")
        
        cursor.close()
        conn.close()
        
        print(f"Executed: {executed}, Skipped: {skipped}, Errors: {errors}")
        if errors > 0:
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
