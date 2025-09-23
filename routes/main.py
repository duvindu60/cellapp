from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from supabase import create_client, Client
from datetime import datetime, timedelta
import os
import hashlib
import re
from dotenv import load_dotenv
from utils.activity_logger import log_activity, get_recent_activities, get_todays_activities, format_activity_description, get_activity_icon, get_activity_color
# Load environment variables
load_dotenv()
# Helper function to convert user ID to UUID format
def get_uuid_from_user_id(user_id):
    """Convert a user ID to a UUID-like format for database compatibility"""
    hash_object = hashlib.md5(user_id.encode())
    hex_digest = hash_object.hexdigest()
    return f"{hex_digest[:8]}-{hex_digest[8:12]}-{hex_digest[12:16]}-{hex_digest[16:20]}-{hex_digest[20:32]}"
# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')
if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase = None
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
def check_incomplete_attendance(leader_id, user_id):
    """Check for incomplete attendance and log activities"""
    try:
        # Get all past Tuesdays (last 4 weeks)
        past_tuesdays = get_past_tuesdays()
        # Get all members for this leader
        members_result = supabase.table('cell_members').select('id').eq('leader_id', leader_id).execute()
        total_members = len(members_result.data) if members_result.data else 0
        if total_members == 0:
            return
        # Check each past Tuesday for incomplete attendance
        for tuesday_date in past_tuesdays:
            try:
                # Convert date string to database format
                parsed_date = datetime.strptime(tuesday_date, "%B %d, %Y").date()
                meeting_date_formatted = parsed_date.isoformat()
                # Count attendance records for this date
                attendance_result = supabase.table('attendance').select('id').eq('leader_id', leader_id).eq('meeting_date', meeting_date_formatted).execute()
                attendance_count = len(attendance_result.data) if attendance_result.data else 0
                # If attendance is incomplete (less than total members)
                if attendance_count < total_members:
                    missing_count = total_members - attendance_count
                    # Check if we already logged this incomplete attendance
                    existing_log = supabase.table('activities').select('id').eq('leader_id', leader_id).eq('activity_type', 'attendance_incomplete').eq('details->meeting_date', tuesday_date).execute()
                    if not existing_log.data:  # Only log if not already logged
                        log_activity(
                            leader_id=leader_id,
                            user_id=user_id,
                            activity_type='attendance_incomplete',
                            description=f'Incomplete attendance for {tuesday_date}',
                            details={
                                'meeting_date': tuesday_date,
                                'total_members': total_members,
                                'attendance_count': attendance_count,
                                'missing_count': missing_count
                            }
                        )
            except Exception as e:
                print(f"Error checking attendance for {tuesday_date}: {e}")
                continue
    except Exception as e:
        print(f"Error checking incomplete attendance: {e}")
@main_bp.route('/')
def index():
    if 'user' in session:
        try:
            # Get member count for the current leader
            session_user_id = session['user']['id']
            leader_id = get_uuid_from_user_id(session_user_id)
            members_result = supabase.table('cell_members').select('id').eq('leader_id', leader_id).execute()
            member_count = len(members_result.data) if members_result.data else 0
            # Get recent activities and today's activities
            recent_activities = get_recent_activities(leader_id, limit=5)
            todays_activities = get_todays_activities(leader_id)
            # Check for incomplete attendance and log it
            check_incomplete_attendance(leader_id, session_user_id)
            # Get latest tutorial for next meeting
            next_meeting_date = get_next_meeting_date()
            # Fetch latest tutorial for next meeting
            try:
                tutorials_result = supabase.table('tutorials')\
                    .select('*')\
                    .eq('meeting_date', next_meeting_date.isoformat())\
                    .order('uploaded_at')\
                    .limit(1)\
                    .execute()
                latest_tutorial = tutorials_result.data[0] if tutorials_result.data else None
            except Exception as e:
                print(f"Error fetching latest tutorial: {e}")
                latest_tutorial = None
            # Fetch latest attendance data
            latest_attendance = None
            try:
                # Get all attendance records for this leader
                attendance_result = supabase.table('attendance')\
                    .select('meeting_date, status')\
                    .eq('leader_id', leader_id)\
                    .execute()
                if attendance_result.data:
                    # Group by meeting date and calculate totals
                    from collections import defaultdict
                    attendance_by_date = defaultdict(lambda: {'present': 0, 'absent': 0, 'total': 0})
                    for record in attendance_result.data:
                        date = record['meeting_date']
                        status = record['status']
                        attendance_by_date[date]['total'] += 1
                        if status == 'present':
                            attendance_by_date[date]['present'] += 1
                        elif status == 'absent':
                            attendance_by_date[date]['absent'] += 1
                    # Get the most recent date
                    if attendance_by_date:
                        latest_date = max(attendance_by_date.keys())
                        latest_data = attendance_by_date[latest_date]
                        latest_attendance = {
                            'meeting_date': latest_date,
                            'present_count': latest_data['present'],
                            'absent_count': latest_data['absent'],
                            'total_members': latest_data['total']
                        }
                        print(f"Latest attendance data: {latest_attendance}")
                else:
                    latest_attendance = None
                    print("No attendance records found")
                print(f"Leader ID: {leader_id}")
            except Exception as e:
                print(f"Error fetching latest attendance: {e}")
                latest_attendance = None
            # If no attendance data, create a fallback with the most recent Tuesday
            if not latest_attendance:
                from datetime import datetime, timedelta
                today = datetime.now()
                # Get the most recent Tuesday
                days_since_tuesday = (today.weekday() - 1) % 7
                if days_since_tuesday == 0 and today.weekday() == 1:  # Today is Tuesday
                    recent_tuesday = today.date()
                else:
                    recent_tuesday = (today - timedelta(days=days_since_tuesday)).date()
                # Create fallback attendance data
                latest_attendance = {
                    'meeting_date': recent_tuesday.strftime('%B %d, %Y'),
                    'present_count': 0,
                    'absent_count': 0,
                    'total_members': member_count,
                    'is_fallback': True,
                    'is_complete': False
                }
                print(f"Using fallback attendance data: {latest_attendance}")
            else:
                # Determine if attendance is complete
                present_count = latest_attendance.get('present_count', 0)
                absent_count = latest_attendance.get('absent_count', 0)
                total_members = latest_attendance.get('total_members', 0)
                # Attendance is complete if present + absent = total members
                is_complete = (present_count + absent_count) == total_members and total_members > 0
                latest_attendance['is_complete'] = is_complete
        except Exception as e:
            print(f"Error fetching dashboard data: {e}")
            member_count = 0
            recent_activities = []
            todays_activities = []
            latest_tutorial = None
            latest_attendance = None
            next_meeting_date = get_next_meeting_date()
        # Ensure latest_attendance is never None - create fallback if needed
        if not latest_attendance:
            from datetime import datetime, timedelta
            today = datetime.now()
            # Get the most recent Tuesday
            days_since_tuesday = (today.weekday() - 1) % 7
            if days_since_tuesday == 0 and today.weekday() == 1:  # Today is Tuesday
                recent_tuesday = today.date()
            else:
                recent_tuesday = (today - timedelta(days=days_since_tuesday)).date()
            # Create fallback attendance data
            latest_attendance = {
                'meeting_date': recent_tuesday.strftime('%B %d, %Y'),
                'present_count': 0,
                'absent_count': 0,
                'total_members': member_count,
                'is_fallback': True,
                'is_complete': False
            }
            print(f"Using final fallback attendance data: {latest_attendance}")
        else:
            # Ensure completion status is set for existing data
            if 'is_complete' not in latest_attendance:
                present_count = latest_attendance.get('present_count', 0)
                absent_count = latest_attendance.get('absent_count', 0)
                total_members = latest_attendance.get('total_members', 0)
                is_complete = (present_count + absent_count) == total_members and total_members > 0
                latest_attendance['is_complete'] = is_complete
        past_tuesdays = get_past_tuesdays()
        today = datetime.now().date()
        return render_template('main/dashboard.html',
                             user=session['user'], 
                             next_meeting_date=next_meeting_date.strftime("%B %d, %Y"),
                             member_count=member_count,
                             recent_activities=recent_activities,
                             todays_activities=todays_activities,
                             latest_tutorial=latest_tutorial,
                             latest_attendance=latest_attendance,
                             current_week_date=next_meeting_date.strftime("%B %d, %Y") if latest_tutorial else None,
                             week_1_date=past_tuesdays[0],
                             week_2_date=past_tuesdays[1],
                             week_3_date=past_tuesdays[2],
                             week_4_date=past_tuesdays[3],
                             today=today)
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
        # Calculate attendance completion status for each meeting date
        attendance_status = {}
        for i, meeting_date in enumerate(past_tuesdays):
            try:
                # Convert meeting_date string to proper date format
                from datetime import datetime
                parsed_date = datetime.strptime(meeting_date, "%B %d, %Y").date()
                meeting_date_formatted = parsed_date.isoformat()
                # Get members who were created BEFORE or ON this meeting date
                # This ensures attendance counts are accurate for each specific date
                members_result = supabase.table('cell_members').select('id').eq('leader_id', leader_id).lte('created_at', meeting_date_formatted + 'T23:59:59').execute()
                members = members_result.data if members_result.data else []
                total_members = len(members)
                # Get attendance count for this meeting date
                if total_members > 0:
                    member_ids = [member['id'] for member in members]
                    attendance_result = supabase.table('attendance').select('id').eq('leader_id', leader_id).eq('meeting_date', meeting_date_formatted).in_('member_id', member_ids).execute()
                    marked_count = len(attendance_result.data) if attendance_result.data else 0
                    # Determine if attendance is complete
                    is_complete = marked_count == total_members
                    attendance_status[meeting_date] = {
                        'is_complete': is_complete,
                        'marked_count': marked_count,
                        'total_members': total_members
                    }
                else:
                    attendance_status[meeting_date] = {
                        'is_complete': True,  # No members means "complete"
                        'marked_count': 0,
                        'total_members': 0
                    }
            except Exception as e:
                print(f"Error checking attendance for {meeting_date}: {e}")
                attendance_status[meeting_date] = {
                    'is_complete': False,
                    'marked_count': 0,
                    'total_members': 0
                }
        return render_template('main/meeting_dates.html', 
                             user=session['user'],
                             week_1_date=past_tuesdays[0],
                             week_2_date=past_tuesdays[1],
                             week_3_date=past_tuesdays[2],
                             week_4_date=past_tuesdays[3],
                             attendance_status=attendance_status)
    except Exception as e:
        print(f"Error fetching meeting dates: {e}")
        flash('Error loading meeting dates', 'error')
        past_tuesdays = get_past_tuesdays()
        return render_template('main/meeting_dates.html', 
                             user=session['user'],
                             week_1_date=past_tuesdays[0],
                             week_2_date=past_tuesdays[1],
                             week_3_date=past_tuesdays[2],
                             week_4_date=past_tuesdays[3],
                             attendance_status={})
@main_bp.route('/attendance/<meeting_date>')
def attendance_detail(meeting_date):
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    try:
        # Get leader ID
        session_user_id = session['user']['id']
        leader_id = get_uuid_from_user_id(session_user_id)
        # Convert meeting_date string to proper date format
        from datetime import datetime
        try:
            # Parse the date string (e.g., "September 16, 2025")
            parsed_date = datetime.strptime(meeting_date, "%B %d, %Y").date()
            meeting_date_formatted = parsed_date.isoformat()  # Convert to YYYY-MM-DD format
        except ValueError:
            # If parsing fails, use the original string
            meeting_date_formatted = meeting_date
        # Get members who were created BEFORE or ON the meeting date
        # This prevents newly added members from appearing in past meetings
        members_result = supabase.table('cell_members').select('*').eq('leader_id', leader_id).lte('created_at', meeting_date_formatted + 'T23:59:59').execute()
        members = members_result.data if members_result.data else []
        # Get attendance data from database
        attendance_data = {}
        if members:
            # Initialize all members as absent by default
            for member in members:
                attendance_data[member['id']] = {
                    'present': False,
                    'absent': True
                }
            # Try to get attendance data from database
            try:
                member_ids = [member['id'] for member in members]
                attendance_result = supabase.table('attendance').select('*').eq('leader_id', leader_id).eq('meeting_date', meeting_date_formatted).in_('member_id', member_ids).execute()
                # Update with actual attendance data
                if attendance_result.data:
                    for record in attendance_result.data:
                        member_id = record['member_id']
                        status = record['status']
                        attendance_data[member_id] = {
                            'present': status == 'present',
                            'absent': status == 'absent'
                        }
            except Exception as db_error:
                print(f"Database error (attendance table might not exist): {db_error}")
                # Continue with default absent status for all members
        return render_template('main/attendance_detail.html', 
                             user=session['user'],
                             meeting_date=meeting_date,
                             members=members,
                             attendance_data=attendance_data)
    except Exception as e:
        print(f"Error fetching attendance data: {e}")
        flash('Error loading attendance data', 'error')
        return redirect(url_for('main.meeting_dates'))
@main_bp.route('/update_attendance/<meeting_date>', methods=['POST'])
def update_attendance(meeting_date):
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    try:
        member_id = request.form.get('member_id')
        attendance_status = request.form.get('status')  # 'present', 'absent'
        if not member_id or not attendance_status:
            flash('Invalid attendance data', 'error')
            return redirect(url_for('main.attendance_detail', meeting_date=meeting_date))
        # Get leader ID
        session_user_id = session['user']['id']
        leader_id = get_uuid_from_user_id(session_user_id)
        # Convert meeting_date string to proper date format
        from datetime import datetime
        try:
            # Parse the date string (e.g., "September 16, 2025")
            parsed_date = datetime.strptime(meeting_date, "%B %d, %Y").date()
            meeting_date_formatted = parsed_date.isoformat()  # Convert to YYYY-MM-DD format
        except ValueError:
            # If parsing fails, use the original string
            meeting_date_formatted = meeting_date
        # Get member name for activity log
        member_result = supabase.table('cell_members').select('name').eq('id', member_id).eq('leader_id', leader_id).execute()
        member_name = member_result.data[0]['name'] if member_result.data else 'Unknown'
        # Try to save attendance data to database
        try:
            # Check if attendance record already exists
            existing_result = supabase.table('attendance').select('id, status').eq('leader_id', leader_id).eq('member_id', member_id).eq('meeting_date', meeting_date_formatted).execute()
            attendance_data = {
                'leader_id': leader_id,
                'member_id': member_id,
                'meeting_date': meeting_date_formatted,
                'status': attendance_status
            }
            if existing_result.data:
                # Update existing record
                old_status = existing_result.data[0]['status']
                result = supabase.table('attendance').update({'status': attendance_status}).eq('id', existing_result.data[0]['id']).execute()
                if result.data:
                    # Log activity for update
                    log_activity(
                        leader_id=leader_id,
                        user_id=session_user_id,
                        activity_type='attendance_updated',
                        description=f'Changed {member_name} from {old_status} to {attendance_status} for {meeting_date}',
                        details={
                            'member_name': member_name,
                            'member_id': member_id,
                            'meeting_date': meeting_date,
                            'old_status': old_status,
                            'new_status': attendance_status
                        }
                    )
                    flash(f'Attendance updated to {attendance_status}', 'success')
                else:
                    flash('Error updating attendance', 'error')
            else:
                # Insert new record
                result = supabase.table('attendance').insert(attendance_data).execute()
                if result.data:
                    # Log activity for new attendance
                    log_activity(
                        leader_id=leader_id,
                        user_id=session_user_id,
                        activity_type='attendance_marked',
                        description=f'Marked {member_name} as {attendance_status} for {meeting_date}',
                        details={
                            'member_name': member_name,
                            'member_id': member_id,
                            'meeting_date': meeting_date,
                            'status': attendance_status
                        }
                    )
                    flash(f'Attendance marked as {attendance_status}', 'success')
                else:
                    flash('Error saving attendance', 'error')
        except Exception as db_error:
            print(f"Database error (attendance table might not exist): {db_error}")
            flash('Attendance table not set up yet. Please create the attendance table in your database.', 'warning')
        # Log attendance sheet update activity
        try:
            # Count total members and present members for this meeting
            total_members_result = supabase.table('cell_members').select('id').eq('leader_id', leader_id).execute()
            total_members = len(total_members_result.data) if total_members_result.data else 0
            present_result = supabase.table('attendance').select('id').eq('leader_id', leader_id).eq('meeting_date', meeting_date_formatted).eq('status', 'present').execute()
            present_count = len(present_result.data) if present_result.data else 0
            log_activity(
                leader_id=leader_id,
                user_id=session_user_id,
                activity_type='attendance_sheet_updated',
                description=f'Updated attendance sheet for {meeting_date}',
                details={
                    'meeting_date': meeting_date,
                    'total_members': total_members,
                    'present_count': present_count,
                    'updated_member': member_name,
                    'updated_status': attendance_status
                }
            )
        except Exception as log_error:
            print(f"Error logging attendance sheet update: {log_error}")
        return redirect(url_for('main.attendance_detail', meeting_date=meeting_date))
    except Exception as e:
        print(f"Error updating attendance: {e}")
        flash('Error updating attendance', 'error')
        return redirect(url_for('main.attendance_detail', meeting_date=meeting_date))
@main_bp.route('/members')
def members():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    try:
        # Get cell members for this leader
        session_user_id = session['user']['id']
        leader_id = get_uuid_from_user_id(session_user_id)
        result = supabase.table('cell_members').select('*').eq('leader_id', leader_id).execute()
        members = result.data if result.data else []
        return render_template('main/members.html', members=members, user=session['user'])
    except Exception as e:
        error_msg = str(e)
        if "relation" in error_msg.lower() and "does not exist" in error_msg.lower():
            flash('Database table not found. Please run the database migration first.', 'error')
        elif "row-level security" in error_msg.lower():
            flash('Database access denied. Please check your permissions.', 'error')
        else:
            flash(f'Error loading members: {error_msg}', 'error')
        return redirect(url_for('main.index'))
@main_bp.route('/member/form')
def member_form():
    """Display the member form page"""
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    return render_template('main/member_form.html', user=session['user'])
@main_bp.route('/member/<member_id>')
def member_details(member_id):
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    try:
        # Get specific member details
        session_user_id = session['user']['id']
        leader_id = get_uuid_from_user_id(session_user_id)
        result = supabase.table('cell_members').select('*').eq('id', member_id).eq('leader_id', leader_id).execute()
        if result.data:
            member = result.data[0]
            return render_template('main/member_details.html', member=member, user=session['user'])
        else:
            flash('Member not found', 'error')
            return redirect(url_for('main.members'))
    except Exception as e:
        flash('Error loading member details', 'error')
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
    """Display tutorials for a specific meeting date"""
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    try:
        # Convert meeting_date from URL format to database format
        from datetime import datetime
        try:
            # Parse the date string (e.g., "September 16, 2025")
            parsed_date = datetime.strptime(meeting_date, "%B %d, %Y").date()
            meeting_date_formatted = parsed_date.isoformat()  # Convert to YYYY-MM-DD format
        except ValueError:
            # If parsing fails, use the original string
            meeting_date_formatted = meeting_date
        # Fetch tutorials for this meeting date
        tutorials_result = supabase.table('tutorials')\
            .select('*')\
            .eq('meeting_date', meeting_date_formatted)\
            .order('uploaded_at')\
            .execute()
        tutorials = tutorials_result.data if tutorials_result.data else []
        return render_template('main/meeting_tutorials.html', 
                             user=session['user'],
                             meeting_date=meeting_date,
                             tutorials=tutorials)
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
        tutorial_data = {
            'leader_id': leader_id,
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
    """Display activity list page with sorting and filtering"""
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    try:
        # Get leader ID
        session_user_id = session['user']['id']
        leader_id = get_uuid_from_user_id(session_user_id)
        # Get all activities for this leader
        activities_result = supabase.table('activities').select('*').eq('leader_id', leader_id).order('created_at', desc=True).execute()
        activities = activities_result.data if activities_result.data else []
        return render_template('main/activity_list.html',
                             activities=activities)
    except Exception as e:
        print(f"Error fetching activities: {e}")
        flash('Error loading activities', 'error')
        return redirect(url_for('main.index'))
@main_bp.route('/db_status')
def db_status():
    """Check database connection and table status"""
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    try:
        # Test basic connection
        result = supabase.table('cell_members').select('count').execute()
        return f"Database connected! Table accessible. Count: {len(result.data) if result.data else 0}"
    except Exception as e:
        return f"Database error: {str(e)}"
