"""
Database connection and helper functions for NYU Course Planner.
Handles PostgreSQL database connections and query execution.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool, errors
from config import Config
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Connection pool (optional - for production use)
# connection_pool = None

def get_db_connection():
    """
    Create and return a database connection.
    
    Returns:
        psycopg2.connection: Database connection object
        
    Raises:
        psycopg2.Error: If connection fails
    """
    try:
        conn = psycopg2.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        return conn
    except psycopg2.Error as e:
        logger.error(f"Database connection error: {e}")
        raise


def execute_query(query, params=None, fetch=False):
    """
    Execute a SQL query and optionally fetch results.
    
    Args:
        query (str): SQL query string with %s placeholders
        params (tuple/list, optional): Parameters for the query
        fetch (bool): If True, fetch and return results. If False, commit the transaction.
    
    Returns:
        list: Query results if fetch=True, None otherwise
        
    Raises:
        psycopg2.Error: If query execution fails
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute(query, params)
        
        if fetch:
            result = cur.fetchall()
            # Convert RealDictRow to regular dict for easier JSON serialization
            result = [dict(row) for row in result]
        else:
            conn.commit()
            result = None
        
        cur.close()
        return result
        
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Query execution error: {e}")
        logger.error(f"Query: {query}")
        logger.error(f"Params: {params}")
        raise e
    finally:
        if conn:
            conn.close()


def execute_query_single(query, params=None):
    """
    Execute a SQL query and fetch a single result.
    
    Args:
        query (str): SQL query string with %s placeholders
        params (tuple/list, optional): Parameters for the query
    
    Returns:
        dict: Single row result as dictionary, or None if no results
        
    Raises:
        psycopg2.Error: If query execution fails
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute(query, params)
        result = cur.fetchone()
        
        cur.close()
        
        if result:
            return dict(result)
        return None
        
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Query execution error: {e}")
        logger.error(f"Query: {query}")
        logger.error(f"Params: {params}")
        raise e
    finally:
        if conn:
            conn.close()


def call_procedure(procedure_name, params=None):
    """
    Call a PostgreSQL stored procedure (PostgreSQL 11+).
    
    Args:
        procedure_name (str): Name of the stored procedure
        params (tuple/list, optional): Parameters for the procedure
    
    Returns:
        list: Procedure results as list of dictionaries
        
    Raises:
        psycopg2.Error: If procedure call fails
    """
    if params is None:
        params = ()
    
    placeholders = ', '.join(['%s'] * len(params))
    query = f"CALL {procedure_name}({placeholders})"
    
    return execute_query(query, params, fetch=True)


def call_function(function_name, params=None):
    """
    Call a PostgreSQL function.
    
    Args:
        function_name (str): Name of the function
        params (tuple/list, optional): Parameters for the function
    
    Returns:
        list: Function results as list of dictionaries
        
    Raises:
        psycopg2.Error: If function call fails
    """
    if params is None:
        params = ()
    
    placeholders = ', '.join(['%s'] * len(params))
    query = f"SELECT * FROM {function_name}({placeholders})"
    
    return execute_query(query, params, fetch=True)


def test_connection():
    """
    Test database connection.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()
        cur.close()
        conn.close()
        logger.info(f"Database connection successful. PostgreSQL version: {version[0]}")
        return True
    except psycopg2.Error as e:
        logger.error(f"Database connection test failed: {e}")
        return False


def check_table_exists(table_name):
    """
    Check if a table exists in the database.
    
    Args:
        table_name (str): Name of the table to check
    
    Returns:
        bool: True if table exists, False otherwise
    """
    try:
        query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            );
        """
        result = execute_query_single(query, (table_name,))
        return result['exists'] if result else False
    except psycopg2.Error as e:
        logger.error(f"Error checking table existence: {e}")
        return False


def check_procedure_exists(procedure_name):
    """
    Check if a stored procedure exists in the database.
    
    Args:
        procedure_name (str): Name of the procedure to check
    
    Returns:
        bool: True if procedure exists, False otherwise
    """
    try:
        query = """
            SELECT EXISTS (
                SELECT FROM information_schema.routines 
                WHERE routine_schema = 'public' 
                AND routine_name = %s
                AND routine_type = 'PROCEDURE'
            );
        """
        result = execute_query_single(query, (procedure_name,))
        return result['exists'] if result else False
    except psycopg2.Error as e:
        logger.error(f"Error checking procedure existence: {e}")
        return False


def check_function_exists(function_name):
    """
    Check if a function exists in the database.
    
    Args:
        function_name (str): Name of the function to check
    
    Returns:
        bool: True if function exists, False otherwise
    """
    try:
        query = """
            SELECT EXISTS (
                SELECT FROM information_schema.routines 
                WHERE routine_schema = 'public' 
                AND routine_name = %s
                AND routine_type = 'FUNCTION'
            );
        """
        result = execute_query_single(query, (function_name,))
        return result['exists'] if result else False
    except psycopg2.Error as e:
        logger.error(f"Error checking function existence: {e}")
        return False

