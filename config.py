import os
<<<<<<< HEAD
import secrets
=======
>>>>>>> 20dac40646ecb456f1bdc39aa36c2952699ee397
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration class"""
<<<<<<< HEAD
    # CRITICAL: SECRET_KEY must be set in environment - no defaults
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        # In development, generate a temporary key (will change on restart)
        # In production, this will cause the app to fail fast
        if os.getenv('FLASK_ENV') == 'production':
            raise ValueError("SECRET_KEY must be set in production environment!")
        else:
            SECRET_KEY = secrets.token_hex(32)
            print("WARNING: Using temporary SECRET_KEY. Set SECRET_KEY in .env file!")
    
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
    
    # Validate required environment variables
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set!")
    
    # Flask settings
    DEBUG = False  # Default to False for security
    TESTING = False
    
    # Session configuration - secure defaults
    SESSION_COOKIE_SECURE = True  # Require HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'  # Stronger CSRF protection
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes (reduced from 1 hour)
    
    # Rate limiting settings
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = "memory://"
=======
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production-12345')
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
    
    # Flask settings
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    TESTING = False
    
    # Session configuration
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
>>>>>>> 20dac40646ecb456f1bdc39aa36c2952699ee397
    
    # Database settings (if you add a database later)
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    # Mobile/SMS settings (if you add SMS functionality)
    SMS_API_KEY = os.getenv('SMS_API_KEY')
    SMS_SENDER_ID = os.getenv('SMS_SENDER_ID')
<<<<<<< HEAD
    
    # File upload settings
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB max file size
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'txt'}

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    TESTING = False
    SESSION_COOKIE_SECURE = False  # Allow HTTP in development (use HTTPS in production!)
    
=======

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

>>>>>>> 20dac40646ecb456f1bdc39aa36c2952699ee397
class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
<<<<<<< HEAD
    # Production session settings - enforce HTTPS
    SESSION_COOKIE_SECURE = True  # Requires HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    
    # Ensure SECRET_KEY is set
    if not os.getenv('SECRET_KEY'):
        raise ValueError("SECRET_KEY environment variable must be set in production!")
=======
    # Production session settings
    SESSION_COOKIE_SECURE = True  # Requires HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
>>>>>>> 20dac40646ecb456f1bdc39aa36c2952699ee397

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
<<<<<<< HEAD
    SESSION_COOKIE_SECURE = False
=======
>>>>>>> 20dac40646ecb456f1bdc39aa36c2952699ee397

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
