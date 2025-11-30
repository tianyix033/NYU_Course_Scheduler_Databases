"""
Simple script to import SQL file using Python.
Works on Windows without psql in PATH.
"""

import psycopg2
from config import Config
import os

def split_sql_statements(sql_text):
    """
    Split SQL text into individual statements, handling:
    - Dollar-quoted strings ($$...$$ or $tag$...$tag$)
    - Single-quoted strings ('...')
    - Comments (-- and /* */)
    """
    statements = []
    current = []
    i = 0
    in_dollar = False
    dollar_tag = None
    in_single = False
    
    while i < len(sql_text):
        char = sql_text[i]
        
        # Handle dollar-quoted strings: $tag$ or $$
        if char == '$' and not in_single:
            start_pos = i
            i += 1
            # Read until we find the closing $
            tag_chars = []
            while i < len(sql_text) and sql_text[i] != '$':
                tag_chars.append(sql_text[i])
                i += 1
            
            if i < len(sql_text):
                # Found closing $, create the full tag
                tag = '$' + ''.join(tag_chars) + '$'
                current.append(tag)
                
                if not in_dollar:
                    # Opening dollar quote
                    dollar_tag = tag
                    in_dollar = True
                elif tag == dollar_tag:
                    # Closing dollar quote (must match opening tag)
                    in_dollar = False
                    dollar_tag = None
                
                i += 1
                continue
        
        # Handle single-quoted strings
        if char == "'" and not in_dollar:
            # Check for escaped quote
            if i > 0 and sql_text[i-1] == '\\':
                current.append(char)
                i += 1
                continue
            in_single = not in_single
            current.append(char)
            i += 1
            continue
        
        # Handle line comments (--)
        if char == '-' and not in_dollar and not in_single:
            if i + 1 < len(sql_text) and sql_text[i+1] == '-':
                # Skip until end of line
                while i < len(sql_text) and sql_text[i] != '\n':
                    i += 1
                if i < len(sql_text):
                    i += 1  # Skip the newline
                continue
        
        # Statement terminator
        if char == ';' and not in_dollar and not in_single:
            current.append(char)
            stmt = ''.join(current).strip()
            if stmt and not stmt.startswith('--'):
                statements.append(stmt)
            current = []
            i += 1
            continue
        
        # Regular character
        current.append(char)
        i += 1
    
    # Final statement (if any)
    if current:
        stmt = ''.join(current).strip()
        if stmt and not stmt.startswith('--'):
            statements.append(stmt)
    
    return statements

def execute_sql_file(file_path):
    """Execute a SQL file using psycopg2."""
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return False
    
    print(f"Reading SQL file: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            sql_content = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return False
    
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
    
    try:
        cursor = conn.cursor()
        print("Executing SQL...")
        
        statements = split_sql_statements(sql_content)
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
                if 'already exists' in err_str or 'duplicate' in err_str:
                    skipped += 1
                else:
                    errors += 1
                    if errors <= 10:
                        print(f"  Error {errors} (stmt {i}): {str(e)[:150]}")
        
        cursor.close()
        conn.close()
        
        print(f"Results: {executed} executed, {skipped} skipped, {errors} errors")
        if errors > 0:
            return False
        return True
        
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        print(f"Error executing SQL: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Database Setup Script")
    print("=" * 60)
    print()
    
    sql_file = "COMMANDS_postgresql.sql"
    if not os.path.exists(sql_file):
        sql_file = "COMMANDS.sql"
        if not os.path.exists(sql_file):
            print("Error: SQL file not found")
            exit(1)
    
    print(f"Executing: {sql_file}")
    success = execute_sql_file(sql_file)
    
    if not success:
        print("\nError: Failed to execute main SQL file")
        exit(1)
    
    additional_file = "additional_commands_postgressql.sql"
    if os.path.exists(additional_file):
        print(f"\nExecuting: {additional_file}")
        if not execute_sql_file(additional_file):
            print("\nError: Failed to execute additional SQL file")
            exit(1)
    
    print("\n" + "=" * 60)
    print("Database setup completed successfully!")
    print("=" * 60)
