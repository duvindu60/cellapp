from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from supabase import create_client, Client
import os
import bcrypt
<<<<<<< HEAD
import time
import logging
=======
>>>>>>> 20dac40646ecb456f1bdc39aa36c2952699ee397
from dotenv import load_dotenv
from utils.activity_logger import log_activity
from utils.device_detector import get_template_suffix

# Load environment variables
load_dotenv()

# Create blueprint
auth_bp = Blueprint('auth', __name__)

<<<<<<< HEAD
# Configure secure logging
logger = logging.getLogger(__name__)

=======
>>>>>>> 20dac40646ecb456f1bdc39aa36c2952699ee397
# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')

if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase = None

<<<<<<< HEAD
# Import limiter from app (will be set during blueprint registration)
from flask import current_app

def get_limiter():
    """Get the limiter instance from the app"""
    try:
        from app import limiter
        return limiter
    except:
        return None

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Rate limiting decorator would be applied here if using Flask-Limiter
    # Applied via app-level configuration
    
    if request.method == 'POST':
        mobile = request.form.get('mobile', '').strip()
        password = request.form.get('password', '')
        
        # Start timing for constant-time response
        start_time = time.time()
        
        # Default values for timing attack prevention
        login_successful = False
        user_data = None
        dummy_hash = b'$2b$12$dummyhashfortimingatttackprevention1234567890'
=======
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        mobile = request.form.get('mobile')
        password = request.form.get('password')
>>>>>>> 20dac40646ecb456f1bdc39aa36c2952699ee397
        
        if not mobile or not password:
            flash("Mobile number and password are required", 'error')
            template_name = f'auth/login{get_template_suffix()}.html'
            return render_template(template_name)
        
        # Validate mobile number format
        if len(mobile) != 10 or not mobile.isdigit():
<<<<<<< HEAD
            # Perform dummy bcrypt check for timing consistency
            bcrypt.checkpw(b'dummy', dummy_hash)
            flash("Invalid mobile number or password", 'error')
=======
            flash("Please enter a valid 10-digit mobile number", 'error')
>>>>>>> 20dac40646ecb456f1bdc39aa36c2952699ee397
            template_name = f'auth/login{get_template_suffix()}.html'
            return render_template(template_name)
        
        try:
<<<<<<< HEAD
            # Fetch user by phone_number and role_id
=======
            # Fetch user by phone_number and role_id (without password check)
>>>>>>> 20dac40646ecb456f1bdc39aa36c2952699ee397
            user_result = supabase.table('users').select('*').eq('role_id', 4).eq('phone_number', mobile).execute()
            
            if user_result.data and len(user_result.data) > 0:
                user_data = user_result.data[0]
                stored_password = user_data.get('password', '')
                
                # Verify password using bcrypt
<<<<<<< HEAD
                if stored_password:
                    try:
                        if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                            login_successful = True
                    except Exception:
                        login_successful = False
                else:
                    # Perform dummy check for timing consistency
                    bcrypt.checkpw(b'dummy', dummy_hash)
            else:
                # User not found - perform dummy bcrypt check for timing consistency
                bcrypt.checkpw(b'dummy', dummy_hash)
            
            if login_successful and user_data:
                user_id = user_data.get('id')
                
                # Clear old session and regenerate to prevent session fixation
                old_session_data = dict(session)
                session.clear()
                
                # Store user info in new session
                session.permanent = True
                session['user'] = {
                    'id': user_id,
                    'mobile': mobile,
                    'name': user_data.get('name', 'User'),
                    'email': user_data.get('email', ''),
                    'role_id': user_data.get('role_id')
                }
                
                # Log login activity (without sensitive data)
                try:
                    log_activity(
                        leader_id=user_id,
                        user_id=user_id,
                        activity_type='user_login',
                        description='User logged in successfully',
                        user_role='leader',
                        user_name=session['user'].get('name', 'User'),
                        source='cell_app',
                        platform='mobile' if get_template_suffix() else 'web',
                        details={'login_method': 'password'}  # No PII
                    )
                except Exception as e:
                    logger.error(f"Failed to log login activity: {str(e)}")
                
                flash("Login successful!", 'success')
                return redirect(url_for('main.index'))
            else:
                # Log failed login attempt (for security monitoring)
                logger.warning(f"Failed login attempt for mobile: {mobile[:3]}***{mobile[-2:]}")
                
                # Generic error message to prevent user enumeration
                flash("Invalid mobile number or password", 'error')
                
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            flash("An error occurred during login. Please try again.", 'error')
        
        # Ensure minimum response time to prevent timing attacks (300ms)
        elapsed = time.time() - start_time
        if elapsed < 0.3:
            time.sleep(0.3 - elapsed)
=======
                if stored_password and bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                    # Password is correct
                    user_id = user_data.get('id')
                    
                    # Store user info in session
                    session['user'] = {
                        'id': user_id,
                        'mobile': mobile,
                        'name': user_data.get('name', 'User'),
                        'email': user_data.get('email', ''),
                        'role_id': user_data.get('role_id')
                    }
                    
                    # Log login activity
                    try:
                        log_activity(
                            leader_id=user_id,
                            user_id=user_id,
                            activity_type='user_login',
                            description='User logged in',
                            user_role='leader',
                            user_name=session['user'].get('name', 'User'),
                            source='cell_app',
                            platform='mobile' if mobile else 'web',
                            details={'mobile': mobile, 'login_time': 'now'}
                        )
                    except Exception as e:
                        print(f"Error logging activity: {e}")
                    
                    flash("Login successful!", 'success')
                    return redirect(url_for('main.index'))
                else:
                    # Password is incorrect
                    flash("Invalid mobile number or password", 'error')
            else:
                # User not found
                flash("Invalid mobile number or password", 'error')
        except Exception as e:
            print(f"Error during login: {e}")
            flash("An error occurred during login. Please try again.", 'error')
>>>>>>> 20dac40646ecb456f1bdc39aa36c2952699ee397
    
    template_name = f'auth/login{get_template_suffix()}.html'
    return render_template(template_name)

<<<<<<< HEAD
@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout endpoint - POST only for CSRF protection"""
    user_id = session.get('user', {}).get('id')
    
    # Log logout activity before clearing session
    if user_id:
        try:
            log_activity(
                leader_id=user_id,
                user_id=user_id,
                activity_type='user_logout',
                description='User logged out',
                user_role='leader',
                user_name=session.get('user', {}).get('name', 'User'),
                source='cell_app',
                platform='mobile' if get_template_suffix() else 'web',
                details={}
            )
        except Exception as e:
            logger.error(f"Failed to log logout activity: {str(e)}")
    
    session.clear()
    flash("You have been logged out", 'info')
    return redirect(url_for('auth.login'))

# Fallback GET route for backward compatibility (redirects to login with warning)
@auth_bp.route('/logout', methods=['GET'])
def logout_get():
    """Deprecated GET logout - redirects to login"""
    flash("Please use the logout button to sign out securely", 'warning')
    return redirect(url_for('auth.login'))
=======
@auth_bp.route('/logout')
def logout():
    session.pop('user', None)
    flash("You have been logged out", 'info')
    return redirect(url_for('auth.login'))
>>>>>>> 20dac40646ecb456f1bdc39aa36c2952699ee397
