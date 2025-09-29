from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
from supabase import create_client, Client
from datetime import datetime, timedelta
import os
import hashlib
import re
from dotenv import load_dotenv
from utils.activity_logger import log_activity, get_recent_activities, get_todays_activities, format_activity_description, get_activity_icon, get_activity_color
# Load environment variables
load_dotenv()
# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')
if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase = None

# Helper function to convert user ID to UUID format
def get_uuid_from_user_id(user_id):
    """Get the leader_id from the leaders table based on user_id"""
    try:
        result = supabase.table('leaders').select('id').eq('user_id', user_id).execute()
        if result.data and len(result.data) > 0:
            return result.data[0]['id']
        else:
            # If no leader found, create one with a generated UUID
            print(f"No leader found for user_id: {user_id}, creating one...")
            import uuid
            leader_id = str(uuid.uuid4())
            leader_data = {
                'id': leader_id,
                'user_id': user_id,
                'name': 'Cell Leader',
                'email': ''
            }
            result = supabase.table('leaders').insert(leader_data).execute()
            if result.data:
                return result.data[0]['id']
            else:
                raise Exception("Failed to create leader record")
    except Exception as e:
        print(f"Error getting leader_id for user_id {user_id}: {e}")
        # Fallback to old method for backward compatibility
        hash_object = hashlib.md5(user_id.encode())
        hex_digest = hash_object.hexdigest()
        return f"{hex_digest[:8]}-{hex_digest[8:12]}-{hex_digest[12:16]}-{hex_digest[16:20]}-{hex_digest[20:32]}"
# Create blueprint
main_bp = Blueprint('main', __name__)
def get_past_tuesdays():
    """Calculate the past 4 Tuesday dates"""
    today = datetime.now()
    tuesdays = []
    # Find the most recent Tuesday
    days_back = today.weekday() - 1  # Tuesday is 1
    if days_back < 0:  # If today is Monday (0), go back 6 days
        days_back += 7
    elif days_back == 0:  # If today is Tuesday, use today
        days_back = 0
    else:  # If today is Wednesday or later, go back to the most recent Tuesday
        days_back = days_back
    # Get the 4 most recent Tuesdays
    for i in range(4):
        tuesday = today - timedelta(days=days_back + (i * 7))
        tuesdays.append(tuesday.strftime("%B %d, %Y"))
    return tuesdays
def get_next_meeting_date():
    """Get the next upcoming Tuesday meeting date, or today if today is Tuesday"""
    today = datetime.now().date()
    # Calculate days until next Tuesday
    days_until_tuesday = (1 - today.weekday()) % 7
    if days_until_tuesday == 0:  # Today is Tuesday
        # If today is Tuesday, return today's date
        next_tuesday = today
    else:
        # Get the next Tuesday
        next_tuesday = today + timedelta(days=days_until_tuesday)
    return next_tuesday
@main_bp.route('/')
def index():
    # Initialize default tutorial card data
    tutorial_card_data = {
        'upcoming_date': 'No date',
        'has_tutorials': False,
        'meeting_date_iso': None
    }
    
    if 'user' in session:
        try:
            # Initialize default values
            member_count = 0
            recent_activities = []
            todays_activities = []
            next_meeting_date = get_next_meeting_date()
            
            # Get member count for the current leader
            session_user_id = session['user']['id']
            leader_id = get_uuid_from_user_id(session_user_id)
            members_result = supabase.table('cell_members').select('id').eq('leader_id', leader_id).execute()
            member_count = len(members_result.data) if members_result.data else 0
            # Get recent activities and today's activities
            recent_activities = get_recent_activities(leader_id, limit=5)
            todays_activities = get_todays_activities(leader_id)
            print(f"Recent activities: {len(recent_activities)}")
            print(f"Today's activities: {len(todays_activities)}")
            if todays_activities:
                print(f"First today's activity: {todays_activities[0]}")
            # Use next meeting date for tutorial card
            next_meeting_formatted = next_meeting_date.strftime('%B %d, %Y')
            
            # Check if there are any tutorials for the next meeting
            try:
                # First, let's see what columns exist in the tutorials table
                print(f"Checking tutorials table structure...")
                test_query = supabase.table('tutorials').select('*').limit(1).execute()
                print(f"Tutorials table sample data: {test_query.data}")
                
                # Try querying without leader_id filter first
                tutorials_result = supabase.table('tutorials')\
                    .select('*')\
                    .eq('meeting_date', next_meeting_date.isoformat())\
                    .execute()
                
                has_tutorials = len(tutorials_result.data) > 0 if tutorials_result.data else False
                print(f"Next meeting date: {next_meeting_date.isoformat()}")
                print(f"Tutorials found for next meeting: {has_tutorials}")
                print(f"Tutorials data: {tutorials_result.data}")
                
                # For now, skip placeholder creation until we fix the column issue
                # We'll just show the status based on existing tutorials
                
            except Exception as e:
                print(f"Error checking tutorials: {e}")
                has_tutorials = False
            
            # Check if the tutorial is a placeholder (by checking tutorial name)
            is_placeholder = False
            if has_tutorials and tutorials_result.data:
                tutorial_record = tutorials_result.data[0]
                is_placeholder = tutorial_record.get('tutorial_name') == 'No Tutorial Uploaded'
            
            # Update tutorial card data
            tutorial_card_data.update({
                'upcoming_date': next_meeting_formatted,
                'has_tutorials': has_tutorials,
                'is_placeholder': is_placeholder,
                'meeting_date_iso': next_meeting_date.isoformat()
            })
        except Exception as e:
            print(f"Error fetching dashboard data: {e}")
            member_count = 0
            recent_activities = []
            todays_activities = []
            latest_tutorial = None
            next_meeting_date = get_next_meeting_date()
        past_tuesdays = get_past_tuesdays()
        today = datetime.now()
        
        # Get latest attendance data
        latest_attendance = None
        try:
            attendance_result = supabase.table('attendance').select('meeting_date').eq('leader_id', leader_id).order('meeting_date', desc=True).limit(1).execute()
            if attendance_result.data:
                attendance_data = attendance_result.data[0]
                # Format the date consistently
                if attendance_data['meeting_date']:
                    date_obj = datetime.strptime(attendance_data['meeting_date'], '%Y-%m-%d').date()
                    latest_attendance = {
                        'meeting_date': date_obj.strftime("%B %d, %Y"),
                        'meeting_date_iso': attendance_data['meeting_date']
                    }
        except Exception as e:
            print(f"Error fetching latest attendance: {e}")
        
        try:
            return render_template('main/dashboard.html',
                                 user=session['user'], 
                                 next_meeting_date=next_meeting_date.strftime("%B %d, %Y"),
                                 next_meeting_date_obj=next_meeting_date,
                                 member_count=member_count,
                                 recent_activities=recent_activities,
                                 todays_activities=todays_activities,
                                 tutorial_card=tutorial_card_data,
                                 current_week_date=next_meeting_date.strftime("%B %d, %Y"),
                                 week_1_date=past_tuesdays[0],
                                 week_2_date=past_tuesdays[1],
                                 week_3_date=past_tuesdays[2],
                                 week_4_date=past_tuesdays[3],
                                 latest_attendance=latest_attendance,
                                 today=today)
        except Exception as e:
            print(f"Error rendering dashboard template: {e}")
            flash('Error loading dashboard', 'error')
            return redirect(url_for('auth.login'))
    return redirect(url_for('auth.login'))
@main_bp.route('/profile')
def profile():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    return render_template('main/profile.html', user=session['user'])
@main_bp.route('/meeting-dates')
def meeting_dates():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    try:
        # Get leader ID
        session_user_id = session['user']['id']
        leader_id = get_uuid_from_user_id(session_user_id)
        past_tuesdays = get_past_tuesdays()
        return render_template('main/meeting_dates.html', 
                             user=session['user'],
                             week_1_date=past_tuesdays[0],
                             week_2_date=past_tuesdays[1],
                             week_3_date=past_tuesdays[2],
                             week_4_date=past_tuesdays[3])
    except Exception as e:
        print(f"Error fetching meeting dates: {e}")
        flash('Error loading meeting dates', 'error')
        past_tuesdays = get_past_tuesdays()
        return render_template('main/meeting_dates.html', 
                             user=session['user'],
                             week_1_date=past_tuesdays[0],
                             week_2_date=past_tuesdays[1],
                             week_3_date=past_tuesdays[2],
                             week_4_date=past_tuesdays[3])

@main_bp.route('/attendance/<meeting_date>')
def attendance_detail(meeting_date):
    """Display attendance page for a specific meeting date"""
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    
    try:
        # Get leader ID
        session_user_id = session['user']['id']
        leader_id = get_uuid_from_user_id(session_user_id)
        
        # Convert meeting_date string to proper date format
        from datetime import datetime
        try:
            parsed_date = datetime.strptime(meeting_date, "%B %d, %Y").date()
            meeting_date_formatted = parsed_date.isoformat()
        except ValueError:
            meeting_date_formatted = meeting_date
        
        # Get members for this leader
        members_result = supabase.table('cell_members').select('*').eq('leader_id', leader_id).execute()
        members = members_result.data if members_result.data else []
        
        # If no members found for current leader, try to get all members for testing
        if len(members) == 0:
            all_members_result = supabase.table('cell_members').select('*').execute()
            members = all_members_result.data if all_members_result.data else []
        
        # Get existing attendance data
        attendance_data = {}
        if members:
            try:
                member_ids = [member['id'] for member in members]
                attendance_result = supabase.table('attendance').select('*').eq('leader_id', leader_id).eq('meeting_date', meeting_date_formatted).in_('member_id', member_ids).execute()
                
                # Initialize all members as incomplete
                for member in members:
                    attendance_data[member['id']] = {
                        'present': False,
                        'absent': False,
                        'incomplete': True
                    }
                
                # Update with actual attendance data
                if attendance_result.data:
                    for record in attendance_result.data:
                        member_id = record['member_id']
                        status = record['status']
                        attendance_data[member_id] = {
                            'present': status == 'present',
                            'absent': status == 'absent',
                            'incomplete': False
                        }
            except Exception as e:
                print(f"Error fetching attendance data: {e}")
                # Initialize all as incomplete if error
                for member in members:
                    attendance_data[member['id']] = {
                        'present': False,
                        'absent': False,
                        'incomplete': True
                    }
        
        return render_template('main/attendance_detail.html', 
                             user=session['user'],
                             meeting_date=meeting_date,
                             members=members,
                             attendance_data=attendance_data)
    except Exception as e:
        print(f"Error in attendance_detail: {e}")
        flash('Error loading attendance page', 'error')
        return redirect(url_for('main.meeting_dates'))

@main_bp.route('/update_attendance/<meeting_date>', methods=['POST'])
def update_attendance(meeting_date):
    """Update attendance for a specific member and meeting date"""
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    try:
        member_id = request.form.get('member_id')
        status = request.form.get('status')  # 'present', 'absent', 'clear'
        
        if not member_id or not status:
            return jsonify({'success': False, 'message': 'Missing required data'}), 400
        
        # Get leader ID
        session_user_id = session['user']['id']
        leader_id = get_uuid_from_user_id(session_user_id)
        
        # Convert meeting_date string to proper date format
        from datetime import datetime
        try:
            parsed_date = datetime.strptime(meeting_date, "%B %d, %Y").date()
            meeting_date_formatted = parsed_date.isoformat()
        except ValueError:
            meeting_date_formatted = meeting_date
        
        # Get member name for logging
        member_result = supabase.table('cell_members').select('name').eq('id', member_id).eq('leader_id', leader_id).execute()
        member_name = member_result.data[0]['name'] if member_result.data else 'Unknown'
        
        # Handle attendance update
        if status == 'clear':
            # Delete existing attendance record
            existing_result = supabase.table('attendance').select('id').eq('leader_id', leader_id).eq('member_id', member_id).eq('meeting_date', meeting_date_formatted).execute()
            if existing_result.data:
                result = supabase.table('attendance').delete().eq('id', existing_result.data[0]['id']).execute()
                if result.data:
                    return jsonify({'success': True, 'message': f'Attendance cleared for {member_name}'})
                else:
                    return jsonify({'success': False, 'message': 'Error clearing attendance'}), 500
            else:
                return jsonify({'success': False, 'message': 'No attendance record to clear'}), 400
        else:
            # Insert or update attendance record
            attendance_data = {
                'leader_id': leader_id,
                'member_id': member_id,
                'meeting_date': meeting_date_formatted,
                'status': status
            }
            
            # Check if record exists
            existing_result = supabase.table('attendance').select('id').eq('leader_id', leader_id).eq('member_id', member_id).eq('meeting_date', meeting_date_formatted).execute()
            
            if existing_result.data:
                # Update existing record
                result = supabase.table('attendance').update({'status': status}).eq('id', existing_result.data[0]['id']).execute()
            else:
                # Insert new record
                result = supabase.table('attendance').insert(attendance_data).execute()
            
            if result.data:
                return jsonify({'success': True, 'message': f'{member_name} marked as {status}'})
            else:
                return jsonify({'success': False, 'message': 'Error saving attendance'}), 500
        
    except Exception as e:
        print(f"Error updating attendance: {e}")
        return jsonify({'success': False, 'message': 'Error updating attendance'}), 500

@main_bp.route('/members')
def members():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    try:
        # Get cell members for this leader
        session_user_id = session['user']['id']
        leader_id = get_uuid_from_user_id(session_user_id)
        
        # Get members for this specific leader
        result = supabase.table('cell_members').select('*').eq('leader_id', leader_id).execute()
        members = result.data if result.data else []
        
        # If no members found for current leader, show all members for testing
        if len(members) == 0:
            all_members = supabase.table('cell_members').select('*').execute()
            members = all_members.data if all_members.data else []
        
        return render_template('main/members.html', members=members, user=session['user'])
    except Exception as e:
        error_msg = str(e)
        print(f"Error in members route: {error_msg}")  # Enhanced logging
        
        if "relation" in error_msg.lower() and "does not exist" in error_msg.lower():
            flash('Database table not found. Please run the database migration first.', 'error')
        elif "row-level security" in error_msg.lower():
            flash('Database access denied. Please check your permissions.', 'error')
        elif "connection" in error_msg.lower():
            flash('Database connection failed. Please try again later.', 'error')
        elif "timeout" in error_msg.lower():
            flash('Request timed out. Please check your internet connection.', 'error')
        else:
            flash('Unable to load members. Please try again.', 'error')
        return redirect(url_for('main.index'))
@main_bp.route('/member/form')
def member_form():
    """Display the member form page"""
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    
    # Check if editing an existing member
    member_id = request.args.get('edit')
    member = None
    if member_id:
        try:
            session_user_id = session['user']['id']
            leader_id = get_uuid_from_user_id(session_user_id)
            result = supabase.table('cell_members').select('*').eq('id', member_id).eq('leader_id', leader_id).execute()
            if not result.data:
                # Try without leader filter for testing
                result = supabase.table('cell_members').select('*').eq('id', member_id).execute()
            if result.data:
                member = result.data[0]
        except Exception as e:
            print(f"Error loading member for edit: {e}")
    
    return render_template('main/member_form.html', user=session['user'], member=member, is_edit=bool(member_id))
@main_bp.route('/member/<member_id>')
def member_details(member_id):
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    
    try:
        # Get specific member details
        session_user_id = session['user']['id']
        leader_id = get_uuid_from_user_id(session_user_id)
        
        # Try to find member with leader filter first
        result = supabase.table('cell_members').select('*').eq('id', member_id).eq('leader_id', leader_id).execute()
        
        # If not found with leader filter, try without leader filter (for testing)
        if not result.data:
            result = supabase.table('cell_members').select('*').eq('id', member_id).execute()
        
        if result.data:
            member = result.data[0]
            return render_template('main/member_details.html', member=member, user=session['user'])
        else:
            flash('Member not found', 'error')
            return redirect(url_for('main.members'))
    except Exception as e:
        print(f"Error loading member details: {e}")
        flash(f'Error loading member details: {str(e)}', 'error')
        return redirect(url_for('main.members'))
@main_bp.route('/add_member', methods=['POST'])
def add_member():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    # Form validation
    form_errors = {}
    name = request.form.get('name', '').strip()
    age = request.form.get('age', '').strip()
    phone_number = request.form.get('phone_number', '').strip()
    # Validate required fields
    if not name:
        form_errors['name'] = 'Full name is required'
    elif not re.match(r'^[A-Za-z\s]{2,100}$', name):
        form_errors['name'] = 'Name must be 2-100 characters and contain only letters and spaces'
    # Validate age if provided
    if age:
        try:
            age_int = int(age)
            if age_int < 1 or age_int > 120:
                form_errors['age'] = 'Age must be between 1 and 120'
        except ValueError:
            form_errors['age'] = 'Age must be a valid number'
    # Validate phone number if provided
    if phone_number and not re.match(r'^[0-9]{10,15}$', phone_number):
        form_errors['phone_number'] = 'Phone number must be 10-15 digits'
    # If there are validation errors, return to form with errors
    if form_errors:
        return render_template('main/member_form.html', 
                             user=session['user'], 
                             form_errors=form_errors)
    try:
        session_user_id = session['user']['id']
        leader_id = get_uuid_from_user_id(session_user_id)
        # First, ensure the leader exists in the leaders table
        try:
            # Try to get the leader first
            leader_result = supabase.table('leaders').select('id').eq('id', leader_id).execute()
            if not leader_result.data:
                # Leader doesn't exist, create one
                leader_data = {
                    'id': leader_id,
                    'user_id': session_user_id,
                    'name': session['user'].get('name', 'Cell Leader'),
                    'email': session['user'].get('email', ''),
                    'created_at': 'now()'
                }
                leader_insert_result = supabase.table('leaders').insert(leader_data).execute()
                print(f"Leader created: {leader_insert_result.data}")
        except Exception as leader_error:
            # If leaders table doesn't exist or has issues, continue without it
            print(f"Leader creation warning: {leader_error}")
            # For now, let's try to insert the member anyway
            # This will help us debug the RLS issue
        # Prepare member data
        member_data = {
            'leader_id': leader_id,
            'name': name,
            'age': int(age) if age else None,
            'gender': request.form.get('gender') or None,
            'phone_number': phone_number or None,
            'ministry': request.form.get('ministry') or None,
            'zone': request.form.get('zone') or None
        }
        # Insert into database
        print(f"Attempting to insert member with leader_id: {leader_id}")
        print(f"Member data: {member_data}")
        # Try to insert the member
        result = supabase.table('cell_members').insert(member_data).execute()
        print(f"Insert result: {result.data}")
        if result.data:
            # Log activity
            log_activity(
                leader_id=leader_id,
                user_id=session_user_id,
                activity_type='member_added',
                description=f'Added new member: {name}',
                details={
                    'member_name': name,
                    'member_id': result.data[0]['id'] if result.data else None
                }
            )
            flash('Member added successfully!', 'success')
            return redirect(url_for('main.members'))
        else:
            flash('Error adding member to database', 'error')
            return render_template('main/member_form.html', 
                                 user=session['user'], 
                                 form_errors={'general': 'Failed to add member to database'})
    except Exception as e:
        error_msg = str(e)
        flash(f'Error adding member: {error_msg}', 'error')
        return render_template('main/member_form.html', 
                             user=session['user'], 
                             form_errors={'general': error_msg})
@main_bp.route('/update_member/<member_id>', methods=['POST'])
def update_member(member_id):
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    try:
        session_user_id = session['user']['id']
        leader_id = get_uuid_from_user_id(session_user_id)
        member_data = {
            'name': request.form.get('name'),
            'age': int(request.form.get('age')) if request.form.get('age') else None,
            'gender': request.form.get('gender') or None,
            'phone_number': request.form.get('phone_number') or None,
            'ministry': request.form.get('ministry') or None,
            'zone': request.form.get('zone') or None
        }
        result = supabase.table('cell_members').update(member_data).eq('id', member_id).eq('leader_id', leader_id).execute()
        # Log activity
        if result.data:
            log_activity(
                leader_id=leader_id,
                user_id=session_user_id,
                activity_type='member_updated',
                description=f'Updated member: {member_data["name"]}',
                details={
                    'member_name': member_data['name'],
                    'member_id': member_id
                }
            )
        flash('Member updated successfully!', 'success')
        return redirect(url_for('main.member_details', member_id=member_id))
    except Exception as e:
        print(f"Error updating member: {e}")
        flash(f'Error updating member: {str(e)}', 'error')
        return redirect(url_for('main.member_details', member_id=member_id))
@main_bp.route('/delete_member/<member_id>', methods=['POST'])
def delete_member(member_id):
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    try:
        session_user_id = session['user']['id']
        leader_id = get_uuid_from_user_id(session_user_id)
        # First get member details for logging
        member_result = supabase.table('cell_members').select('name').eq('id', member_id).eq('leader_id', leader_id).execute()
        if not member_result.data:
            flash('Member not found', 'error')
            return redirect(url_for('main.members'))
        member_name = member_result.data[0]['name']
        # Delete the member
        result = supabase.table('cell_members').delete().eq('id', member_id).eq('leader_id', leader_id).execute()
        # Log activity
        if result.data:
            log_activity(
                leader_id=leader_id,
                user_id=session_user_id,
                activity_type='member_deleted',
                description=f'Deleted member: {member_name}',
                details={
                    'member_name': member_name,
                    'member_id': member_id
                }
            )
        flash(f'Member {member_name} deleted successfully!', 'success')
        return redirect(url_for('main.members'))
    except Exception as e:
        print(f"Error deleting member: {e}")
        flash(f'Error deleting member: {str(e)}', 'error')
        return redirect(url_for('main.members'))
@main_bp.route('/meeting-tutorials/<meeting_date>')
def meeting_tutorials(meeting_date):
    """Display tutorial for specific meeting date or show 'No Tutorials' if none exists"""
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    try:
        # Get leader ID
        session_user_id = session['user']['id']
        leader_id = get_uuid_from_user_id(session_user_id)
        
        # Convert meeting_date from URL format to database format
        from datetime import datetime
        try:
            # Parse the date string (e.g., "September 16, 2025")
            parsed_date = datetime.strptime(meeting_date, "%B %d, %Y").date()
            meeting_date_formatted = parsed_date.isoformat()  # Convert to YYYY-MM-DD format
        except ValueError:
            # If parsing fails, use the original string
            meeting_date_formatted = meeting_date
        
        # Look for tutorial for this specific meeting date
        # Note: tutorials table doesn't have leader_id column, so we query by meeting_date only
        tutorial_result = supabase.table('tutorials')\
            .select('*')\
            .eq('meeting_date', meeting_date_formatted)\
            .execute()
        
        tutorials = tutorial_result.data if tutorial_result.data else []
        
        # Check if this is the next meeting date
        next_meeting_date = get_next_meeting_date()
        is_next_week = parsed_date == next_meeting_date
        
        return render_template('main/meeting_tutorials.html', 
                             user=session['user'],
                             meeting_date=meeting_date,
                             tutorials=tutorials,
                             is_next_week=is_next_week,
                             no_tutorial_uploaded=len(tutorials) == 0)
                                 
    except Exception as e:
        print(f"Error fetching tutorials: {e}")
        flash('Error loading tutorials', 'error')
        return redirect(url_for('main.index'))
@main_bp.route('/upload-tutorial/<meeting_date>', methods=['POST'])
def upload_tutorial(meeting_date):
    """Upload tutorial for a specific meeting date"""
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    try:
        tutorial_name = request.form.get('tutorial_name')
        tutorial_description = request.form.get('tutorial_description', '')
        if not tutorial_name:
            flash('Tutorial name is required', 'error')
            return redirect(url_for('main.meeting_tutorials', meeting_date=meeting_date))
        # Get leader ID
        session_user_id = session['user']['id']
        leader_id = get_uuid_from_user_id(session_user_id)
        # Convert meeting_date string to proper date format
        from datetime import datetime
        try:
            parsed_date = datetime.strptime(meeting_date, "%B %d, %Y").date()
            meeting_date_formatted = parsed_date.isoformat()
        except ValueError:
            meeting_date_formatted = meeting_date
        # Insert tutorial into database
        # Note: tutorials table doesn't have leader_id column, so we don't include it
        tutorial_data = {
            'tutorial_name': tutorial_name,
            'description': tutorial_description,
            'meeting_date': meeting_date_formatted,
            'uploaded_at': datetime.now().isoformat()
        }
        result = supabase.table('tutorials').insert(tutorial_data).execute()
        if result.data:
            # Log tutorial upload activity
            log_activity(
                leader_id=leader_id,
                user_id=session_user_id,
                activity_type='tutorial_uploaded',
                description=f'Uploaded tutorial: {tutorial_name} for {meeting_date}',
                details={
                    'tutorial_name': tutorial_name,
                    'meeting_date': meeting_date,
                    'description': tutorial_description
                }
            )
            flash('Tutorial uploaded successfully!', 'success')
        else:
            flash('Error uploading tutorial', 'error')
        return redirect(url_for('main.meeting_tutorials', meeting_date=meeting_date))
    except Exception as e:
        print(f"Error uploading tutorial: {e}")
        flash('Error uploading tutorial', 'error')
        return redirect(url_for('main.meeting_tutorials', meeting_date=meeting_date))
@main_bp.route('/activities')
def activity_list():
    """Display activity list page with today's activities only"""
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    try:
        # Get leader ID
        session_user_id = session['user']['id']
        leader_id = get_uuid_from_user_id(session_user_id)
        print(f"Fetching today's activities for leader_id: {leader_id}")
        
        # Get today's activities only
        activities = get_todays_activities(leader_id)
        print(f"Found {len(activities)} activities for today")
        
        from datetime import datetime
        today = datetime.now()
        
        return render_template('main/activity_list.html',
                             activities=activities,
                             user=session['user'],
                             today=today)
    except Exception as e:
        print(f"Error fetching today's activities: {e}")
        flash('Error loading today\'s activities', 'error')
        return redirect(url_for('main.index'))


