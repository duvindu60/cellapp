<<<<<<< HEAD
from flask import Flask, session
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
=======
from flask import Flask, session, request, g
>>>>>>> 20dac40646ecb456f1bdc39aa36c2952699ee397
from routes.auth import auth_bp
from routes.main import main_bp
from routes.api import api_bp
from config import config
import os
from datetime import timedelta

<<<<<<< HEAD
# Initialize extensions
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

=======
>>>>>>> 20dac40646ecb456f1bdc39aa36c2952699ee397
def create_app(config_name=None):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    config_name = config_name or os.getenv('FLASK_ENV', 'default')
    app.config.from_object(config[config_name])
    
<<<<<<< HEAD
    # Session configuration - secure defaults
    app.config['SESSION_COOKIE_SECURE'] = app.config.get('SESSION_COOKIE_SECURE', True)
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'  # Stronger CSRF protection
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)  # Reduced from 1 hour
    app.config['SESSION_COOKIE_NAME'] = 'cellapp_session'
    
    # Initialize CSRF protection
    csrf.init_app(app)
    
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
    
=======
    # Session configuration
    app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)  # 1 hour
    app.config['SESSION_COOKIE_NAME'] = 'cellapp_session'
    
>>>>>>> 20dac40646ecb456f1bdc39aa36c2952699ee397
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    
    return app

# Create app instance
app = create_app()


if __name__ == "__main__":
<<<<<<< HEAD
    # NEVER use debug=True in production
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host="0.0.0.0", port=5001, debug=debug_mode)
=======
    app.run(host="0.0.0.0", port=5001, debug=True)
>>>>>>> 20dac40646ecb456f1bdc39aa36c2952699ee397
