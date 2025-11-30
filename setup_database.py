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
        # Use DATABASE_URL if available (Heroku), otherwise use individual config
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
        
        # Split SQL into statements properly, handling:
        # - Dollar-quoted strings ($$...$$, $tag$...$tag$)
        # - Single-quoted strings ('...')
        # - Only split on semicolons outside of quotes
        
        def split_sql_statements(sql_text):
            """Split SQL text into individual statements, respecting quotes."""
            statements = []
            current = []
            i = 0
            in_single_quote = False
            in_dollar_quote = False
            dollar_tag = None
            
            while i < len(sql_text):
                char = sql_text[i]
                
                # Handle dollar-quoted strings ($$ or $tag$)
                if char == '$' and not in_single_quote:
                    # Find the tag
                    tag_start = i
                    i += 1
                    while i < len(sql_text) and sql_text[i] != '$':
                        i += 1
                    if i < len(sql_text):
                        tag = sql_text[tag_start:i+1]
                        if dollar_tag is None:
                            # Opening tag
                            dollar_tag = tag
                            in_dollar_quote = True
                            current.append(sql_text[tag_start:i+1])
                        elif tag == dollar_tag:
                            # Closing tag
                            dollar_tag = None
                            in_dollar_quote = False
                            current.append(sql_text[tag_start:i+1])
                        else:
                            current.append(sql_text[tag_start:i+1])
                        i += 1
                        continue
                
                # Handle single-quoted strings (only if not in dollar quote)
                if char == "'" and not in_dollar_quote:
                    # Check if it's escaped
                    if i > 0 and sql_text[i-1] == '\\':
                        current.append(char)
                        i += 1
                        continue
                    in_single_quote = not in_single_quote
                    current.append(char)
                    i += 1
                    continue
                
                # Check for statement terminator (semicolon outside quotes)
                if char == ';' and not in_single_quote and not in_dollar_quote:
                    current.append(char)
                    stmt = ''.join(current).strip()
                    if stmt and not stmt.startswith('--'):
                        statements.append(stmt)
                    current = []
                    i += 1
                    # Skip whitespace after semicolon
                    while i < len(sql_text) and sql_text[i] in ' \t\n\r':
                        i += 1
                    continue
                
                current.append(char)
                i += 1
            
            # Add remaining statement
            if current:
                stmt = ''.join(current).strip()
                if stmt and not stmt.startswith('--'):
                    statements.append(stmt)
            
            return statements
        
        statements = split_sql_statements(sql_content)
        print(f"  Parsed {len(statements)} SQL statements")
        
        executed_count = 0
        skipped_count = 0
        error_count = 0
        
        for i, statement in enumerate(statements, 1):
            if not statement.strip():
                continue
            try:
                cursor.execute(statement)
                executed_count += 1
                if i % 10 == 0:
                    print(f"  Processed {i}/{len(statements)} statements...")
            except psycopg2.Error as e:
                error_msg = str(e).lower()
                if 'already exists' in error_msg or 'duplicate' in error_msg:
                    skipped_count += 1
                    if i <= 5 or i % 20 == 0:
                        print(f"  Statement {i}: Already exists (skipping)")
                    continue
                else:
                    error_count += 1
                    if error_count <= 5:
                        print(f"  Error in statement {i}: {e}")
                    continue
        
        conn.commit()
        cursor.close()
        conn.close()
        print(f"\nSummary:")
        print(f"  Executed: {executed_count} statements")
        print(f"  Skipped (already exists): {skipped_count} statements")
        if error_count > 0:
            print(f"  Errors: {error_count} statements")
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
    print("This script will import COMMANDS_postgresql.sql and")
    print("additional_commands_postgressql.sql into PostgreSQL")
    print("Make sure your .env file is configured correctly.")
    print("=" * 60)
    print()
    
    # Try COMMANDS_postgresql.sql first (PostgreSQL version)
    sql_file = "COMMANDS_postgresql.sql"
    
    if not os.path.exists(sql_file):
        print(f"SQL file not found: {sql_file}")
        print(f"Current directory: {os.getcwd()}")
        print("Trying alternative file...")
        sql_file = "COMMANDS.sql"
        if not os.path.exists(sql_file):
            print(f"Alternative file also not found: {sql_file}")
            exit(1)
    
    print(f"Found SQL file: {sql_file}")
    print()
    
    # Execute the main SQL file
    success = execute_sql_file(sql_file)
    
    if not success:
        print("\n" + "=" * 60)
        print("Database setup encountered errors in main file. Check logs above.")
        print("=" * 60)
        exit(1)
    
    # Execute additional commands file if it exists
    additional_file = "additional_commands_postgressql.sql"
    if os.path.exists(additional_file):
        print("\n" + "=" * 60)
        print(f"Executing additional commands: {additional_file}")
        print("=" * 60)
        print()
        
        additional_success = execute_sql_file(additional_file)
        
        if not additional_success:
            print("\n" + "=" * 60)
            print("Warning: Additional commands file encountered errors.")
            print("Main database setup completed, but some additional data may be missing.")
            print("=" * 60)
            exit(1)
    else:
        print(f"\nNote: Additional commands file '{additional_file}' not found. Skipping.")
    
    print("\n" + "=" * 60)
    print("Database setup completed successfully!")
    print("=" * 60)
    exit(0)
