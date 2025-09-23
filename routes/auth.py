from flask import Blueprint, render_template, request, redirect, url_for, session, flash
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
