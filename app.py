from flask import Flask, session, request, g
from routes.auth import auth_bp
from routes.main import main_bp
from routes.api import api_bp
from config import config
from utils.activity_logger import get_activity_icon, get_activity_color, format_activity_description
import os
from datetime import timedelta

def create_app(config_name=None):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    config_name = config_name or os.getenv('FLASK_ENV', 'default')
    app.config.from_object(config[config_name])
    
    # Session configuration
    app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)  # 1 hour
    app.config['SESSION_COOKIE_NAME'] = 'cellapp_session'
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    
    # Make activity logger functions available in templates
    app.jinja_env.globals.update(
        get_activity_icon=get_activity_icon,
        get_activity_color=get_activity_color,
        format_activity_description=format_activity_description
    )
    
    return app

# Create app instance
app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
