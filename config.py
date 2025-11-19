"""
Configuration file for NYU Course Planner application.
Loads environment variables and sets Flask configuration.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file with encoding error handling
env_path = os.path.join(os.path.dirname(__file__), '.env')

if os.path.exists(env_path):
    # Try to read .env file with encoding error handling
    try:
        # First try standard load_dotenv
        load_dotenv(encoding='utf-8')
    except (UnicodeDecodeError, Exception):
        # If that fails, read manually with error handling
        try:
            with open(env_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    os.environ[key] = value
        except Exception:
            pass
else:
    # If .env file doesn't exist, try standard load_dotenv
    try:
        load_dotenv()
    except Exception:
        pass

class Config:
    """Application configuration class."""
    
    # Flask configuration
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'course_planner')
    
    # Session configuration
    SESSION_PERMANENT = False
    SESSION_TYPE = 'filesystem'
    
    @staticmethod
    def get_db_config():
        """Return database configuration as a dictionary."""
        return {
            'host': Config.DB_HOST,
            'port': Config.DB_PORT,
            'user': Config.DB_USER,
            'password': Config.DB_PASSWORD,
            'database': Config.DB_NAME
        }
