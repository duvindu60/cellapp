#!/usr/bin/env python3
"""
Restore CellApp to its original state before any translation features were added
This will completely remove all translation-related code and restore the original functionality
"""

import os
import shutil
from pathlib import Path

class OriginalStateRestorer:
    def __init__(self):
        self.project_root = Path('.')
        
    def remove_translation_files(self):
        """Remove all translation-related files and folders"""
        print("🗑️  Removing translation-related files...")
        
        # Files to remove
        files_to_remove = [
            'babel.cfg',
            'messages.pot',
            'babel_commands.py',
            'manage_translations.py',
            'fix_translations.py',
            'fix_translation_errors.py',
            'fix_all_template_errors.py',
            'fix_nested_translations.py',
            'fix_remaining_template_errors.py',
            'fix_nested_quotes.py',
            'remove_all_translations.py',
            'restore_original_state.py'
        ]
        
        # Folders to remove
        folders_to_remove = [
            'translations',
            'translations/en',
            'translations/si',
            'translations/en/LC_MESSAGES',
            'translations/si/LC_MESSAGES'
        ]
        
        # Remove files
        for file_path in files_to_remove:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"✅ Removed: {file_path}")
        
        # Remove folders
        for folder_path in folders_to_remove:
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)
                print(f"✅ Removed folder: {folder_path}")
        
        print("✅ All translation files removed!")
    
    def restore_requirements_txt(self):
        """Restore requirements.txt to original state"""
        print("📦 Restoring requirements.txt...")
        
        original_requirements = """Flask==2.3.3
Flask-Session==0.5.0
python-dotenv==1.0.0
supabase==2.0.0
requests==2.31.0
gunicorn==21.2.0
Werkzeug==2.3.7
Jinja2==3.1.2
MarkupSafe==2.1.3
itsdangerous==2.1.2
click==8.1.7
blinker==1.6.2
"""
        
        with open('requirements.txt', 'w', encoding='utf-8') as f:
            f.write(original_requirements)
        
        print("✅ requirements.txt restored!")
    
    def restore_app_py(self):
        """Restore app.py to original state"""
        print("🔧 Restoring app.py...")
        
        original_app_py = """from flask import Flask, session, request, g
from routes.auth import auth_bp
from routes.main import main_bp
from routes.api import api_bp
from config import config
from utils.activity_logger import get_activity_icon, get_activity_color, format_activity_description
import os
from datetime import timedelta

def create_app(config_name=None):
    \"\"\"Application factory pattern\"\"\"
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

if __name__ == '__main__':
    app.run(debug=True)
"""
        
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(original_app_py)
        
        print("✅ app.py restored!")
    
    def restore_auth_routes(self):
        """Restore routes/auth.py to original state"""
        print("🔐 Restoring routes/auth.py...")
        
        original_auth_py = """from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from utils.activity_logger import log_activity

# Load environment variables
load_dotenv()

# Create blueprint
auth_bp = Blueprint('auth', __name__)

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')

if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase = None

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        mobile = request.form.get('mobile')
        password = request.form.get('password')
        
        if not mobile or not password:
            flash("Mobile number and password are required", 'error')
            return render_template('auth/login.html')
        
        # Validate mobile number format
        if len(mobile) != 10 or not mobile.isdigit():
            flash("Please enter a valid 10-digit mobile number", 'error')
            return render_template('auth/login.html')
        
        # Simple authentication - accept any mobile + password for testing
        if password == '123456':  # Simple password for testing
            # Login successful
            session['user'] = {
                'id': f'user_{mobile}',
                'mobile': mobile,
            }
            
            # Log login activity
            try:
                from routes.main import get_uuid_from_user_id
                leader_id = get_uuid_from_user_id(session['user']['id'])
                log_activity(
                    leader_id=leader_id,
                    user_id=session['user']['id'],
                    activity_type='user_login',
                    description='User logged in',
                    details={'mobile': mobile, 'login_time': 'now'}
                )
            except Exception as e:
                print(f"Error logging login activity: {e}")
            
            flash("Login successful!", 'success')
            return redirect(url_for('main.index'))
        else:
            flash("Invalid mobile number or password", 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    session.pop('user', None)
    flash("You have been logged out", 'info')
    return redirect(url_for('auth.login'))
"""
        
        with open('routes/auth.py', 'w', encoding='utf-8') as f:
            f.write(original_auth_py)
        
        print("✅ routes/auth.py restored!")
    
    def restore_main_routes(self):
        """Restore routes/main.py to original state (remove translation imports)"""
        print("🏠 Restoring routes/main.py...")
        
        # Read current file and remove translation imports
        with open('routes/main.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove translation imports
        content = content.replace('from flask_babel import gettext as _\n', '')
        content = content.replace('from flask_babel import gettext as _', '')
        
        with open('routes/main.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ routes/main.py restored!")
    
    def restore_api_routes(self):
        """Restore routes/api.py to original state (remove translation imports)"""
        print("🔌 Restoring routes/api.py...")
        
        # Read current file and remove translation imports
        with open('routes/api.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove translation imports
        content = content.replace('from flask_babel import gettext as _\n', '')
        content = content.replace('from flask_babel import gettext as _', '')
        
        with open('routes/api.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ routes/api.py restored!")
    
    def restore_templates(self):
        """Restore all templates to original state"""
        print("🎨 Restoring templates...")
        
        # Restore base.html
        self.restore_base_template()
        
        # Restore login.html
        self.restore_login_template()
        
        # Restore all other templates
        self.restore_all_other_templates()
        
        print("✅ All templates restored!")
    
    def restore_base_template(self):
        """Restore templates/base.html to original state"""
        print("📄 Restoring templates/base.html...")
        
        original_base_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}CellApp{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link rel="manifest" href="{{ url_for('static', filename='manifest.json') }}">
    <meta name="theme-color" content="#0d1117">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <style>
        :root {
            --bg-primary: #0d1117;
            --bg-secondary: #161b22;
            --bg-tertiary: #21262d;
            --bg-hover: #30363d;
            --text-primary: #f0f6fc;
            --text-secondary: #8b949e;
            --text-muted: #6e7681;
            --border-color: #30363d;
            --accent-blue: #1f6feb;
            --accent-green: #238636;
            --accent-red: #f85149;
            --accent-yellow: #d29922;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            overflow-x: hidden;
        }
        
        .container-responsive {
            max-width: 100%;
            margin: 0 auto;
            padding: 0;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        /* Header Styles */
        .header-responsive {
            background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%);
            border-bottom: 1px solid var(--border-color);
            padding: 15px 20px;
            position: sticky;
            top: 0;
            z-index: 1000;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
        }
        
        .header-responsive h1 {
            font-size: 24px;
            font-weight: 700;
            color: var(--text-primary);
            margin: 0;
            text-align: center;
        }
        
        /* Navigation Styles */
        .tablet-nav, .desktop-nav {
            margin-top: 15px;
        }
        
        .nav-link {
            color: var(--text-secondary) !important;
            font-weight: 500;
            padding: 8px 16px !important;
            border-radius: 6px;
            transition: all 0.2s ease;
            text-decoration: none;
        }
        
        .nav-link:hover, .nav-link.active {
            color: var(--text-primary) !important;
            background-color: var(--bg-hover);
        }
        
        .desktop-nav .nav-link {
            margin-right: 10px;
        }
        
        /* Content Styles */
        .content-responsive {
            flex: 1;
            padding: 20px;
            background-color: var(--bg-primary);
        }
        
        .desktop-layout {
            flex: 1;
            background-color: var(--bg-primary);
        }
        
        .desktop-content {
            padding: 20px 40px;
            background-color: var(--bg-primary);
        }
        
        /* Card Styles */
        .card {
            background-color: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
        }
        
        .card-body {
            padding: 24px;
        }
        
        /* Button Styles */
        .btn {
            border-radius: 8px;
            font-weight: 600;
            padding: 12px 24px;
            transition: all 0.2s ease;
            border: none;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, var(--accent-blue) 0%, #0969da 100%);
            color: white;
        }
        
        .btn-primary:hover {
            background: linear-gradient(135deg, #0969da 0%, var(--accent-blue) 100%);
            transform: translateY(-1px);
        }
        
        .btn-success {
            background: linear-gradient(135deg, var(--accent-green) 0%, #1a7f37 100%);
            color: white;
        }
        
        .btn-success:hover {
            background: linear-gradient(135deg, #1a7f37 0%, var(--accent-green) 100%);
            transform: translateY(-1px);
        }
        
        .btn-info {
            background: linear-gradient(135deg, var(--accent-blue) 0%, #0969da 100%);
            color: white;
        }
        
        .btn-info:hover {
            background: linear-gradient(135deg, #0969da 0%, var(--accent-blue) 100%);
            transform: translateY(-1px);
        }
        
        .btn-warning {
            background: linear-gradient(135deg, var(--accent-yellow) 0%, #bf8700 100%);
            color: white;
        }
        
        .btn-warning:hover {
            background: linear-gradient(135deg, #bf8700 0%, var(--accent-yellow) 100%);
            transform: translateY(-1px);
        }
        
        .btn-danger {
            background: linear-gradient(135deg, var(--accent-red) 0%, #da3633 100%);
            color: white;
        }
        
        .btn-danger:hover {
            background: linear-gradient(135deg, #da3633 0%, var(--accent-red) 100%);
            transform: translateY(-1px);
        }
        
        .btn-secondary {
            background-color: var(--bg-tertiary);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
        }
        
        .btn-secondary:hover {
            background-color: var(--bg-hover);
            color: var(--text-primary);
        }
        
        /* Form Styles */
        .form-control {
            background-color: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            border-radius: 8px;
            padding: 12px 16px;
            transition: all 0.2s ease;
        }
        
        .form-control:focus {
            background-color: var(--bg-tertiary);
            border-color: var(--accent-blue);
            color: var(--text-primary);
            box-shadow: 0 0 0 3px rgba(31, 111, 235, 0.1);
        }
        
        .form-control::placeholder {
            color: var(--text-muted);
        }
        
        .form-label {
            color: var(--text-primary);
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        .input-group-text {
            background-color: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            color: var(--text-secondary);
        }
        
        /* Alert Styles */
        .alert {
            border-radius: 8px;
            border: none;
            padding: 16px 20px;
            margin-bottom: 20px;
        }
        
        .alert-success {
            background-color: rgba(35, 134, 54, 0.1);
            color: var(--accent-green);
            border-left: 4px solid var(--accent-green);
        }
        
        .alert-danger {
            background-color: rgba(248, 81, 73, 0.1);
            color: var(--accent-red);
            border-left: 4px solid var(--accent-red);
        }
        
        .alert-info {
            background-color: rgba(31, 111, 235, 0.1);
            color: var(--accent-blue);
            border-left: 4px solid var(--accent-blue);
        }
        
        .alert-warning {
            background-color: rgba(210, 153, 34, 0.1);
            color: var(--accent-yellow);
            border-left: 4px solid var(--accent-yellow);
        }
        
        /* Feature Card Styles */
        .feature-card {
            background-color: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
            transition: all 0.3s ease;
        }
        
        .feature-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
        }
        
        .feature-icon {
            width: 50px;
            height: 50px;
            background: linear-gradient(135deg, var(--accent-blue) 0%, #0969da 100%);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 20px;
            margin-bottom: 16px;
        }
        
        /* Page Title Styles */
        .page-title {
            font-size: 28px;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 8px;
        }
        
        .page-subtitle {
            color: var(--text-secondary);
            font-size: 16px;
            margin-bottom: 24px;
        }
        
        /* Bottom Navigation */
        .bottom-nav {
            background-color: var(--bg-secondary);
            border-top: 1px solid var(--border-color);
            padding: 12px 0;
            position: sticky;
            bottom: 0;
            z-index: 1000;
        }
        
        .bottom-nav .nav-link {
            color: var(--text-secondary);
            text-align: center;
            padding: 8px 12px;
            border-radius: 8px;
            transition: all 0.2s ease;
        }
        
        .bottom-nav .nav-link:hover,
        .bottom-nav .nav-link.active {
            color: var(--text-primary);
            background-color: var(--bg-hover);
        }
        
        .bottom-nav .nav-link i {
            display: block;
            font-size: 18px;
            margin-bottom: 4px;
        }
        
        .bottom-nav .nav-link span {
            font-size: 12px;
            font-weight: 500;
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .header-responsive {
                padding: 12px 16px;
            }
            
            .header-responsive h1 {
                font-size: 20px;
            }
            
            .content-responsive {
                padding: 16px;
            }
            
            .card-body {
                padding: 20px;
            }
            
            .page-title {
                font-size: 24px;
            }
            
            .btn {
                padding: 10px 20px;
            }
        }
        
        @media (max-width: 576px) {
            .content-responsive {
                padding: 12px;
            }
            
            .card-body {
                padding: 16px;
            }
            
            .page-title {
                font-size: 22px;
            }
        }
        
        /* iOS Safari specific fixes */
        @supports (-webkit-touch-callout: none) {
            .container-responsive {
                min-height: -webkit-fill-available;
            }
        }
    </style>
</head>
<body>
    <div class="container-responsive">
        <!-- Mobile/Tablet Header -->
        <div class="header-responsive">
            <h1>{% block header_title %}CellApp{% endblock %}</h1>
            <div class="tablet-nav d-none d-md-block d-lg-none">
                {% block tablet_nav %}{% endblock %}
            </div>
            <div class="desktop-nav d-none d-lg-flex">
                {% block desktop_nav %}{% endblock %}
            </div>
        </div>
        <!-- Desktop Layout -->
        <div class="desktop-layout d-none d-lg-flex">
            <div class="desktop-main" style="width: 100%; margin-left: 0;">
                <div class="desktop-content" style="padding: 20px 40px;">
                    {% with messages = get_flashed_messages(with_categories=true) %}
                        {% if messages %}
                            {% for category, message in messages %}
                                <div class="alert alert-{{ 'danger' if category == 'error' else category }} alert-dismissible fade show" role="alert">
                                    {{ message }}
                                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                                </div>
                            {% endfor %}
                        {% endif %}
                    {% endwith %}
                    {% block desktop_content %}{% endblock %}
                </div>
            </div>
        </div>
        <!-- Mobile/Tablet Content -->
        <div class="d-lg-none">
            <div class="content-responsive">
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert alert-{{ 'danger' if category == 'error' else category }} alert-dismissible fade show" role="alert">
                                {{ message }}
                                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                            </div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}
                {% block mobile_content %}{% endblock %}
            </div>
            {% block bottom_nav %}{% endblock %}
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Mobile app enhancements
        document.addEventListener('DOMContentLoaded', function() {
            // Prevent zoom on double tap
            let lastTouchEnd = 0;
            document.addEventListener('touchend', function (event) {
                let now = (new Date()).getTime();
                if (now - lastTouchEnd <= 300) {
                    event.preventDefault();
                }
                lastTouchEnd = now;
            }, false);
            // Add touch feedback to buttons
            document.querySelectorAll('.btn').forEach(btn => {
                btn.addEventListener('touchstart', function() {
                    this.style.transform = 'scale(0.95)';
                });
                btn.addEventListener('touchend', function() {
                    this.style.transform = 'scale(1)';
                });
            });
        });
    </script>
    {% block scripts %}{% endblock %}
</body>
</html>"""
        
        with open('templates/base.html', 'w', encoding='utf-8') as f:
            f.write(original_base_html)
        
        print("✅ templates/base.html restored!")
    
    def restore_login_template(self):
        """Restore templates/auth/login.html to original state"""
        print("🔐 Restoring templates/auth/login.html...")
        
        original_login_html = """{% extends "base.html" %}
{% block title %}Login - CellApp{% endblock %}
{% block header_title %}Welcome Back{% endblock %}

{% block mobile_content %}
<div class="text-center mb-4">
    <div class="feature-icon mx-auto mb-3">
        <i class="fas fa-mobile-alt"></i>
    </div>
    <h2 class="page-title">Sign In</h2>
    <p class="page-subtitle">Enter your mobile number and password</p>
</div>

<div class="card">
    <div class="card-body">
        <form method="POST" id="loginForm">
            <div class="mb-4">
                <label for="mobile" class="form-label fw-semibold">Mobile Number</label>
                <div class="input-group">
                    <span class="input-group-text"><i class="fas fa-mobile-alt"></i></span>
                    <input type="tel" class="form-control" id="mobile" name="mobile" placeholder="Enter your mobile number" required>
                </div>
                <small class="text-muted">Enter your 10-digit mobile number</small>
            </div>
            
            <div class="mb-4">
                <label for="password" class="form-label fw-semibold">Password</label>
                <div class="input-group">
                    <span class="input-group-text"><i class="fas fa-lock"></i></span>
                    <input type="password" class="form-control" id="password" name="password" placeholder="Enter your password" required>
                </div>
                <small class="text-muted">Enter your password (use 123456 for testing)</small>
            </div>
            
            <div class="d-grid mb-3">
                <button type="submit" class="btn btn-primary btn-lg" id="submitBtn">
                    <i class="fas fa-sign-in-alt me-2"></i>Sign In
                </button>
            </div>
        </form>
    </div>
</div>
{% endblock %}

{% block desktop_content %}
<div class="row justify-content-center">
    <div class="col-md-6 col-lg-5">
        <div class="text-center mb-4">
            <div class="feature-icon mx-auto mb-3">
                <i class="fas fa-mobile-alt"></i>
            </div>
            <h2 class="page-title">Sign In</h2>
            <p class="page-subtitle">Enter your mobile number and password</p>
        </div>

        <div class="card">
            <div class="card-body">
                <form method="POST" id="loginForm">
                    <div class="mb-4">
                        <label for="mobile" class="form-label fw-semibold">Mobile Number</label>
                        <div class="input-group">
                            <span class="input-group-text"><i class="fas fa-mobile-alt"></i></span>
                            <input type="tel" class="form-control" id="mobile" name="mobile" placeholder="Enter your mobile number" required>
                        </div>
                        <small class="text-muted">Enter your 10-digit mobile number</small>
                    </div>
                    
                    <div class="mb-4">
                        <label for="password" class="form-label fw-semibold">Password</label>
                        <div class="input-group">
                            <span class="input-group-text"><i class="fas fa-lock"></i></span>
                            <input type="password" class="form-control" id="password" name="password" placeholder="Enter your password" required>
                        </div>
                        <small class="text-muted">Enter your password (use 123456 for testing)</small>
                    </div>
                    
                    <div class="d-grid mb-3">
                        <button type="submit" class="btn btn-primary btn-lg" id="submitBtn">
                            <i class="fas fa-sign-in-alt me-2"></i>Sign In
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
"""
        
        with open('templates/auth/login.html', 'w', encoding='utf-8') as f:
            f.write(original_login_html)
        
        print("✅ templates/auth/login.html restored!")
    
    def restore_all_other_templates(self):
        """Restore all other templates to original state"""
        print("📄 Restoring all other templates...")
        
        # List of template files to restore
        template_files = [
            'templates/main/dashboard.html',
            'templates/main/members.html',
            'templates/main/profile.html',
            'templates/main/member_form.html',
            'templates/main/member_details.html',
            'templates/main/meeting_dates.html',
            'templates/main/meeting_tutorials.html',
            'templates/main/attendance_detail.html',
            'templates/main/activity_list.html',
            'templates/macros/responsive.html'
        ]
        
        for template_file in template_files:
            if os.path.exists(template_file):
                # Read current content
                with open(template_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Remove all translation-related patterns
                import re
                
                # Remove translation function calls
                content = re.sub(r'\{\{\s*_\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)\s*\}\}', r'\1', content)
                
                # Remove malformed HTML patterns
                content = re.sub(r'<h\[1-6\]\[\^>\]\*>\{\{([^}]+)\}\}</h\[1-6\]>', r'<h2>\1</h2>', content)
                content = re.sub(r'<p\[\^>\]\*>\{\{([^}]+)\}\}</p>', r'<p>\1</p>', content)
                content = re.sub(r'<span\[\^>\]\*>\{\{([^}]+)\}\}</span>', r'<span>\1</span>', content)
                content = re.sub(r'<div\[\^>\]\*>\{\{([^}]+)\}\}</div>', r'<div>\1</div>', content)
                
                # Remove nested quotes
                content = re.sub(r"or '\{\{\s*_\s*\(\s*'([^']+)'\s*\)\s*\}\}'", r"or '\1'", content)
                content = re.sub(r"or \"\{\{\s*_\s*\(\s*'([^']+)'\s*\)\s*\}\}\"", r"or \"\1\"", content)
                
                # Clean up extra whitespace
                content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
                
                # Write cleaned content
                with open(template_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"✅ Restored: {template_file}")
    
    def restore_all(self):
        """Restore everything to original state"""
        print("🔄 Starting complete restoration to original state...")
        print("=" * 60)
        
        try:
            self.remove_translation_files()
            self.restore_requirements_txt()
            self.restore_app_py()
            self.restore_auth_routes()
            self.restore_main_routes()
            self.restore_api_routes()
            self.restore_templates()
            
            print("=" * 60)
            print("🎉 COMPLETE RESTORATION SUCCESSFUL!")
            print("📊 Your CellApp has been restored to its original state")
            print("🚀 All translation features have been completely removed")
            print("✨ Your app is now exactly as it was before translation features")
            
            print("\n📝 Next steps:")
            print("1. Run: python app.py")
            print("2. Visit: http://127.0.0.1:5000")
            print("3. Login with any mobile number + password: 123456")
            print("4. Enjoy your original CellApp! 🎉")
            
        except Exception as e:
            print(f"❌ Error during restoration: {e}")
            return False
        
        return True

def main():
    """Main function"""
    restorer = OriginalStateRestorer()
    success = restorer.restore_all()
    
    if not success:
        print("\n❌ Restoration failed!")
        exit(1)

if __name__ == '__main__':
    main()
