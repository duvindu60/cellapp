from flask import Flask, session
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from routes.auth import auth_bp
from routes.main import main_bp
from routes.api import api_bp
from config import config
import os
from datetime import timedelta

# Initialize extensions
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

def create_app(config_name=None):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    config_name = config_name or os.getenv('FLASK_ENV', 'default')
    config_obj = config[config_name]
    app.config.from_object(config_obj)
    
    # CRITICAL: Ensure SECRET_KEY is set before CSRF initialization
    if not app.config.get('SECRET_KEY'):
        raise ValueError("SECRET_KEY must be set in configuration!")
    
    # Session configuration - explicitly use config class values
    # This ensures DevelopmentConfig.SESSION_COOKIE_SECURE=False is respected
    app.config['SESSION_COOKIE_SECURE'] = getattr(config_obj, 'SESSION_COOKIE_SECURE', True)
    app.config['SESSION_COOKIE_HTTPONLY'] = getattr(config_obj, 'SESSION_COOKIE_HTTPONLY', True)
    app.config['SESSION_COOKIE_SAMESITE'] = getattr(config_obj, 'SESSION_COOKIE_SAMESITE', 'Strict')
    app.config['PERMANENT_SESSION_LIFETIME'] = getattr(config_obj, 'PERMANENT_SESSION_LIFETIME', timedelta(minutes=30))
    app.config['SESSION_COOKIE_NAME'] = 'cellapp_session'
    
    # Debug: Print session config in development
    if app.config.get('DEBUG'):
        print(f"[DEBUG] Session Config - SECURE: {app.config['SESSION_COOKIE_SECURE']}, "
              f"HTTPONLY: {app.config['SESSION_COOKIE_HTTPONLY']}, "
              f"SAMESITE: {app.config['SESSION_COOKIE_SAMESITE']}")
    
    # Initialize CSRF protection (must be after SECRET_KEY is set)
    csrf.init_app(app)
    
    # Exempt API routes from CSRF protection (standard practice for APIs)
    csrf.exempt(api_bp)
    
    # Initialize rate limiter
    limiter.init_app(app)
    
    # Security headers
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # HSTS - only if HTTPS is enabled
        if app.config.get('SESSION_COOKIE_SECURE'):
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # CSP - allow self and CDN resources
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "font-src 'self' https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https:; "
        )
        response.headers['Content-Security-Policy'] = csp
        
        return response
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    
    return app

# Create app instance
app = create_app()


if __name__ == "__main__":
    # NEVER use debug=True in production
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host="0.0.0.0", port=5001, debug=debug_mode)