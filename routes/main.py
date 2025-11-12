from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
from supabase import create_client, Client
from datetime import datetime, timedelta
import os
import hashlib
import re
from dotenv import load_dotenv
from utils.activity_logger import log_activity, get_recent_activities, format_activity_description, get_activity_icon, get_activity_color
from utils.device_detector import get_template_suffix
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

def get_tutorial_meeting_date_corrected():
    """Get the meeting date for tutorials - CORRECTED LOGIC:
    Tuesday 12:00 AM - 11:59 PM: Show current Tuesday
    Wednesday 12:00 AM: Switch to next Tuesday
    Wednesday - Monday: Show next Tuesday"""
    now = datetime.now()
    today = now.date()
    
    # Calculate days until next Tuesday
    days_until_tuesday = (1 - today.weekday()) % 7
    
    if days_until_tuesday == 0:  # Today is Tuesday
        # If it's Tuesday, check the time
        if now.hour == 23 and now.minute == 59:  # At 11:59 PM on Tuesday, switch to next Tuesday
            next_tuesday = today + timedelta(days=7)
        else:  # Before 11:59 PM on Tuesday, use current Tuesday
            next_tuesday = today
    else:
        # Wednesday through Monday, get the next Tuesday
        next_tuesday = today + timedelta(days=days_until_tuesday)
    
    return next_tuesday

def get_attendance_meeting_date_corrected():
    """Get the meeting date for attendance - CORRECTED LOGIC:
    Tuesday 12:00 AM - 11:59 PM: Show current Tuesday
    Wednesday 12:00 AM - Monday 11:59 PM: Show same Tuesday (current week)
    Tuesday 12:00 AM: Switch to new current Tuesday"""
    now = datetime.now()
    today = now.date()
    
    # Calculate days until next Tuesday
    days_until_tuesday = (1 - today.weekday()) % 7
    
    if days_until_tuesday == 0:  # Today is Tuesday
        # If it's Tuesday, always use current Tuesday for attendance
        attendance_tuesday = today
    elif days_until_tuesday == 1:  # Today is Monday
        # If it's Monday, check if it's before midnight (00:00)
        if now.hour == 0 and now.minute == 0:  # Exactly midnight
            # At Monday midnight, switch to next Tuesday
            attendance_tuesday = today + timedelta(days=1)
        else:
            # Before Monday midnight, use the same Tuesday from current week
            attendance_tuesday = today - timedelta(days=6)
    else:
        # Wednesday through Sunday, use the same Tuesday from current week
        # Calculate the most recent Tuesday (current week's Tuesday)
        if days_until_tuesday == 6:  # Wednesday
            attendance_tuesday = today - timedelta(days=1)  # Yesterday (Tuesday)
        elif days_until_tuesday == 5:  # Thursday
            attendance_tuesday = today - timedelta(days=2)  # 2 days ago (Tuesday)
        elif days_until_tuesday == 4:  # Friday
            attendance_tuesday = today - timedelta(days=3)  # 3 days ago (Tuesday)
        elif days_until_tuesday == 3:  # Saturday
            attendance_tuesday = today - timedelta(days=4)  # 4 days ago (Tuesday)
        elif days_until_tuesday == 2:  # Sunday
            attendance_tuesday = today - timedelta(days=5)  # 5 days ago (Tuesday)
    
    return attendance_tuesday

def get_past_tuesdays():
    """Calculate the past 4 Tuesday dates (including today if today is Tuesday)"""
    today = datetime.now()
    tuesdays = []
    # Find the most recent past Tuesday
    days_back = today.weekday() - 1  # Tuesday is 1
    if days_back < 0:  # If today is Monday (0), go back 6 days
        days_back += 7
    elif days_back == 0:  # If today is Tuesday, start from today (0 days back)
        days_back = 0
    else:  # If today is Wednesday or later, go back to the most recent Tuesday
        days_back = days_back
    # Get the 4 most recent past Tuesdays (including today if it's Tuesday)
    for i in range(4):
        tuesday = today - timedelta(days=days_back + (i * 7))
        tuesdays.append(tuesday.strftime("%B %d, %Y"))
    return tuesdays

@main_bp.route('/')
def index():
    # Initialize default tutorial card data
    tutorial_card_data = {
        'upcoming_date': 'No date',
        'has_tutorials': False,
        'meeting_date_iso': None
    }
    
    if 'user' in session:
        # Get leader ID first (needed for all operations)
        session_user_id = session['user']['id']
        leader_id = get_uuid_from_user_id(session_user_id)
        
        try:
            # Initialize default values
            member_count = 0
            recent_activities = []
            next_meeting_date = get_tutorial_meeting_date_corrected()
            current_attendance_date = get_attendance_meeting_date_corrected()
            members_result = supabase.table('cell_members').select('id').eq('leader_id', leader_id).execute()
            member_count = len(members_result.data) if members_result.data else 0
            # Get recent activities
            recent_activities = get_recent_activities(leader_id, limit=5)
            print(f"Recent activities: {len(recent_activities)}")
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
            
            # Update tutorial card data with status
            tutorial_status = 'updated' if has_tutorials and not is_placeholder else 'not_updated'
            tutorial_card_data.update({
                'upcoming_date': next_meeting_formatted,
                'has_tutorials': has_tutorials,
                'is_placeholder': is_placeholder,
                'meeting_date_iso': next_meeting_date.isoformat(),
                'status': tutorial_status
            })
            
            # Get tutorial list for Quick Access - only from meetings table
            tutorial_list = []
            try:
                # Get meetings from meetings table
                meetings_result = supabase.table('meetings')\
                    .select('*')\
                    .order('meeting_date', desc=True)\
                    .limit(4)\
                    .execute()
                
                if meetings_result.data:
                    today = datetime.now().date()
                    
                    for meeting in meetings_result.data:
                        meeting_date = meeting.get('meeting_date')
                        if not meeting_date:
                            continue
                        
                        try:
                            # Parse meeting date
                            if isinstance(meeting_date, str):
                                try:
                                    parsed_date = datetime.strptime(meeting_date, "%Y-%m-%d").date()
                                except ValueError:
                                    try:
                                        parsed_date = datetime.strptime(meeting_date, "%Y-%m-%dT%H:%M:%S").date()
                                    except ValueError:
                                        parsed_date = datetime.strptime(meeting_date.split('T')[0], "%Y-%m-%d").date()
                            else:
                                parsed_date = meeting_date
                            
                            meeting_date_iso = parsed_date.isoformat()
                            
                            # Check for tutorial for this meeting date
                            tutorial_result = supabase.table('tutorials')\
                                .select('*')\
                                .eq('meeting_date', meeting_date_iso)\
                                .execute()
                            
                            has_tutorial = len(tutorial_result.data) > 0 if tutorial_result.data else False
                            is_placeholder_tutorial = False
                            tutorial_record = None
                            
                            if has_tutorial and tutorial_result.data:
                                tutorial_record = tutorial_result.data[0]
                                # Check if it's a placeholder (check title field)
                                is_placeholder_tutorial = tutorial_record.get('title') == 'No Tutorial Uploaded' or tutorial_record.get('title') == ''
                            
                            # Determine if this is upcoming or past
                            is_upcoming = parsed_date > today
                            
                            tutorial_list.append({
                                'date': parsed_date.strftime("%B %d, %Y"),
                                'date_iso': meeting_date_iso,
                                'has_tutorial': has_tutorial,
                                'is_placeholder': is_placeholder_tutorial,
                                'is_upcoming': is_upcoming,
                                'status': 'updated' if has_tutorial and not is_placeholder_tutorial else 'not_updated',
                                'tutorial_name': tutorial_record.get('title', 'No Tutorial') if has_tutorial else None,
                                'description': tutorial_record.get('description', '') if has_tutorial else None,
                                'sort_date': parsed_date
                            })
                        except Exception as date_error:
                            print(f"Error parsing meeting date {meeting_date}: {date_error}")
                            continue
                    
                    # Sort tutorials: upcoming first, then past tutorials (most recent first)
                    tutorial_list.sort(key=lambda x: (not x['is_upcoming'], -x['sort_date'].toordinal()))
            except Exception as e:
                print(f"Error fetching tutorial list: {e}")
                tutorial_list = []
        except Exception as e:
            print(f"Error fetching dashboard data: {e}")
            member_count = 0
            recent_activities = []
            latest_tutorial = None
            next_meeting_date = get_tutorial_meeting_date_corrected()
            tutorial_list = []
            attendance_list = []
            latest_attendance = None
        past_tuesdays = get_past_tuesdays()
        today = datetime.now()
        
        # Get attendance status for current week (using attendance-specific date logic)
        attendance_status = 'incomplete'
        latest_attendance = None
        
        try:
            # Get current week's Tuesday date using corrected attendance logic
            current_attendance_date = get_attendance_meeting_date_corrected()
            current_tuesday_str = current_attendance_date.strftime("%B %d, %Y")
            
            # Get all members for this leader
            members_result = supabase.table('cell_members').select('id').eq('leader_id', leader_id).execute()
            total_members = len(members_result.data) if members_result.data else 0
            
            if total_members > 0:
                # Get attendance records for current week
                member_ids = [member['id'] for member in members_result.data]
                attendance_result = supabase.table('attendance')\
                    .select('member_id')\
                    .eq('leader_id', leader_id)\
                    .eq('meeting_date', current_attendance_date.isoformat())\
                    .in_('member_id', member_ids)\
                    .execute()
                
                # Count how many members have attendance records
                attendance_count = len(attendance_result.data) if attendance_result.data else 0
                
                # Debug logging
                print(f"Current Attendance Date: {current_attendance_date.isoformat()}")
                print(f"Total members: {total_members}")
                print(f"Attendance records found: {attendance_count}")
                print(f"Attendance data: {attendance_result.data}")
                
                # Determine status based on completion
                if attendance_count == total_members:
                    attendance_status = 'complete'
                elif attendance_count > 0:
                    attendance_status = 'partial'
                else:
                    attendance_status = 'incomplete'
                
                print(f"Calculated attendance status: {attendance_status}")
            else:
                # No members found, set default status
                attendance_status = 'incomplete'
                print("No members found for this leader")
            
            # Set latest attendance data for display using current attendance date
            latest_attendance = {
                'meeting_date': current_tuesday_str,
                'meeting_date_iso': current_attendance_date.isoformat(),
                'status': attendance_status
            }
            
            # Get attendance list for Quick Access - only from meetings table
            attendance_list = []
            try:
                # Get meetings from meetings table
                meetings_result = supabase.table('meetings')\
                    .select('*')\
                    .order('meeting_date', desc=True)\
                    .limit(4)\
                    .execute()
                
                if meetings_result.data:
                    for meeting in meetings_result.data:
                        meeting_date = meeting.get('meeting_date')
                        if not meeting_date:
                            continue
                        
                        try:
                            # Parse meeting date
                            if isinstance(meeting_date, str):
                                try:
                                    parsed_date = datetime.strptime(meeting_date, "%Y-%m-%d").date()
                                except ValueError:
                                    try:
                                        parsed_date = datetime.strptime(meeting_date, "%Y-%m-%dT%H:%M:%S").date()
                                    except ValueError:
                                        parsed_date = datetime.strptime(meeting_date.split('T')[0], "%Y-%m-%d").date()
                            else:
                                parsed_date = meeting_date
                            
                            meeting_date_str = parsed_date.strftime("%B %d, %Y")
                            meeting_date_iso = parsed_date.isoformat()
                            
                            # Get attendance records for this meeting date
                            week_attendance_result = supabase.table('attendance')\
                                .select('member_id')\
                                .eq('leader_id', leader_id)\
                                .eq('meeting_date', meeting_date_iso)\
                                .in_('member_id', member_ids)\
                                .execute()
                            
                            week_attendance_count = len(week_attendance_result.data) if week_attendance_result.data else 0
                            
                            # Determine status for this meeting
                            if week_attendance_count == total_members:
                                week_status = 'complete'
                            elif week_attendance_count > 0:
                                week_status = 'partial'
                            else:
                                week_status = 'incomplete'
                            
                            attendance_list.append({
                                'date': meeting_date_str,
                                'date_iso': meeting_date_iso,
                                'status': week_status,
                                'count': week_attendance_count,
                                'total': total_members
                            })
                        except Exception as date_error:
                            print(f"Error parsing meeting date {meeting_date}: {date_error}")
                            continue
            except Exception as e:
                print(f"Error fetching attendance list: {e}")
                attendance_list = []
        except Exception as e:
            print(f"Error fetching attendance data: {e}")
            attendance_status = 'incomplete'
            latest_attendance = {
                'meeting_date': 'Error loading data',
                'meeting_date_iso': None,
                'status': 'incomplete'
            }
        
        try:
            template_name = f'main/dashboard{get_template_suffix()}.html'
            return render_template(template_name,
                                 user=session['user'], 
                                 next_meeting_date=next_meeting_date.strftime("%B %d, %Y"),
                                 next_meeting_date_obj=next_meeting_date,
                                 current_attendance_date=current_attendance_date.strftime("%B %d, %Y"),
                                 current_attendance_date_obj=current_attendance_date,
                                 member_count=member_count,
                                 recent_activities=recent_activities,
                                 tutorial_card=tutorial_card_data,
                                 tutorial_list=tutorial_list,
                                 attendance_list=attendance_list,
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
    template_name = f'main/profile{get_template_suffix()}.html'
    return render_template(template_name, user=session['user'])
@main_bp.route('/meeting-dates')
def meeting_dates():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    try:
        # Get leader ID
        session_user_id = session['user']['id']
        leader_id = get_uuid_from_user_id(session_user_id)
        
        # Query meetings from database
        # Note: meetings table does NOT have leader_id column, so we query all meetings
        meetings = []
        print(f"DEBUG: Fetching meetings from database...")
        
        try:
            # Query all meetings from meetings table (no leader_id filter since table doesn't have that column)
            print("DEBUG: Querying meetings table...")
            try:
                meetings_result = supabase.table('meetings')\
                    .select('*')\
                    .order('meeting_date', desc=True)\
                    .limit(20)\
                    .execute()
                
                print(f"DEBUG: Meetings found: {len(meetings_result.data) if meetings_result.data else 0}")
            except Exception as order_error:
                print(f"DEBUG: Error with order clause, trying without order: {order_error}")
                # Try without order clause
                meetings_result = supabase.table('meetings')\
                    .select('*')\
                    .limit(20)\
                    .execute()
                print(f"DEBUG: Meetings found (no order): {len(meetings_result.data) if meetings_result.data else 0}")
            
            if meetings_result.data:
                print(f"DEBUG: Processing {len(meetings_result.data)} meetings...")
                # Process meetings from meetings table
                for meeting in meetings_result.data:
                    meeting_date = meeting.get('meeting_date')
                    meeting_name = meeting.get('meeting_name', 'Cell Meeting')
                    meeting_number = meeting.get('meeting_number')
                    print(f"DEBUG: Processing meeting - ID: {meeting.get('id')}, Date: {meeting_date}, Name: {meeting_name}, Number: {meeting_number}")
                    
                    if meeting_date:
                        try:
                            # Parse date if it's a string
                            if isinstance(meeting_date, str):
                                # Try different date formats
                                try:
                                    parsed_date = datetime.strptime(meeting_date, "%Y-%m-%d").date()
                                except ValueError:
                                    try:
                                        parsed_date = datetime.strptime(meeting_date, "%Y-%m-%dT%H:%M:%S").date()
                                    except ValueError:
                                        parsed_date = datetime.strptime(meeting_date.split('T')[0], "%Y-%m-%d").date()
                            else:
                                parsed_date = meeting_date
                            
                            meetings.append({
                                'date': parsed_date.strftime("%B %d, %Y"),
                                'date_iso': parsed_date.isoformat(),
                                'date_obj': parsed_date,  # Store date object for sorting
                                'meeting_type': meeting_name,  # Use meeting_name from database
                                'description': f"Meeting #{meeting_number}" if meeting_number else '',  # Use meeting_number as description
                                'id': meeting.get('id'),
                                'meeting_number': meeting_number,
                                'is_upcoming': False  # Will be set later
                            })
                            print(f"DEBUG: Successfully added meeting: {parsed_date.strftime('%B %d, %Y')} - {meeting_name}")
                        except Exception as e:
                            print(f"Error parsing meeting date: {e}, meeting_date value: {meeting_date}, type: {type(meeting_date)}")
                            continue
                    else:
                        print(f"DEBUG: Meeting {meeting.get('id')} has no meeting_date field")
            else:
                print("DEBUG: No meetings data returned from query")
        except Exception as e:
            print(f"Error querying meetings table: {e}")
            import traceback
            traceback.print_exc()
            # Fallback: Get unique meeting dates from attendance table
            try:
                attendance_result = supabase.table('attendance')\
                    .select('meeting_date')\
                    .eq('leader_id', leader_id)\
                    .order('meeting_date', desc=True)\
                    .execute()
                
                if attendance_result.data:
                    # Get unique meeting dates
                    unique_dates = set()
                    for record in attendance_result.data:
                        meeting_date = record.get('meeting_date')
                        if meeting_date:
                            unique_dates.add(meeting_date)
                    
                    # Convert to list and sort
                    for date_str in sorted(unique_dates, reverse=True)[:20]:
                        try:
                            parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                            meetings.append({
                                'date': parsed_date.strftime("%B %d, %Y"),
                                'date_iso': parsed_date.isoformat(),
                                'date_obj': parsed_date,  # Store date object for sorting
                                'meeting_type': 'Cell Meeting',
                                'description': '',
                                'id': None,
                                'is_upcoming': False  # Will be set later
                            })
                        except Exception as e:
                            print(f"Error parsing attendance date: {e}")
                            continue
            except Exception as e2:
                print(f"Error querying attendance table: {e2}")
        
        # If no meetings found, use fallback to past Tuesdays
        if not meetings:
            print("No meetings found in database, using calculated Tuesdays as fallback")
            past_tuesdays = get_past_tuesdays()
            for date_str in past_tuesdays:
                try:
                    parsed_date = datetime.strptime(date_str, "%B %d, %Y").date()
                    meetings.append({
                        'date': date_str,
                        'date_iso': parsed_date.isoformat(),
                        'meeting_type': 'Cell Meeting',
                        'description': '',
                        'id': None
                    })
                except Exception as e:
                    print(f"Error parsing fallback date: {e}")
        
        # Identify upcoming meeting (latest date) and mark others as recent
        if meetings:
            # Sort by date to find the latest
            meetings.sort(key=lambda x: x['date_obj'], reverse=True)
            # Mark the first one (latest) as upcoming
            if len(meetings) > 0:
                meetings[0]['is_upcoming'] = True
                print(f"DEBUG: Upcoming meeting: {meetings[0]['date']}")
            # Mark others as recent
            for meeting in meetings[1:]:
                meeting['is_upcoming'] = False
        
        print(f"DEBUG: Final meetings count: {len(meetings)}")
        for i, meeting in enumerate(meetings, 1):
            status = "UPCOMING" if meeting.get('is_upcoming') else "RECENT"
            print(f"DEBUG: Meeting {i}: {meeting['date']} - {meeting['meeting_type']} ({status})")
        
        template_name = f'main/meeting_dates{get_template_suffix()}.html'
        return render_template(template_name, 
                             user=session['user'],
                             meetings=meetings)
    except Exception as e:
        print(f"Error fetching meeting dates: {e}")
        import traceback
        traceback.print_exc()
        flash('Error loading meeting dates', 'error')
        # Fallback to calculated Tuesdays
        past_tuesdays = get_past_tuesdays()
        meetings = []
        for date_str in past_tuesdays:
            try:
                parsed_date = datetime.strptime(date_str, "%B %d, %Y").date()
                meetings.append({
                    'date': date_str,
                    'date_iso': parsed_date.isoformat(),
                    'date_obj': parsed_date,  # Store date object for sorting
                    'meeting_type': 'Cell Meeting',
                    'description': '',
                    'id': None,
                    'is_upcoming': False  # Will be set later
                })
            except Exception as e:
                print(f"Error parsing fallback date: {e}")
        
        # Identify upcoming meeting (latest date) and mark others as recent
        if meetings:
            # Sort by date to find the latest
            meetings.sort(key=lambda x: x['date_obj'], reverse=True)
            # Mark the first one (latest) as upcoming
            if len(meetings) > 0:
                meetings[0]['is_upcoming'] = True
            # Mark others as recent
            for meeting in meetings[1:]:
                meeting['is_upcoming'] = False
        
        template_name = f'main/meeting_dates{get_template_suffix()}.html'
        return render_template(template_name, 
                             user=session['user'],
                             meetings=meetings)

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
        
        template_name = f'main/attendance_detail{get_template_suffix()}.html'
        return render_template(template_name, 
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
        try:
            member_result = supabase.table('cell_members').select('name').eq('id', member_id).eq('leader_id', leader_id).execute()
            member_name = member_result.data[0]['name'] if member_result.data and len(member_result.data) > 0 else 'Unknown'
        except Exception as e:
            print(f"Error fetching member name: {e}")
            member_name = 'Unknown'
        
        # Get meeting_number from meetings table based on meeting_date
        meeting_number = None
        try:
            meeting_result = supabase.table('meetings').select('meeting_number').eq('meeting_date', meeting_date_formatted).limit(1).execute()
            if meeting_result.data and len(meeting_result.data) > 0:
                meeting_number = meeting_result.data[0].get('meeting_number')
        except Exception as e:
            print(f"Error fetching meeting_number: {e}")
            # If meeting not found, try to get the latest meeting number or use a default
            # For now, we'll let it fail if meeting_number is required
        
        # Handle attendance update
        if status == 'clear':
            # Delete existing attendance record
            try:
                existing_result = supabase.table('attendance').select('id').eq('leader_id', leader_id).eq('member_id', member_id).eq('meeting_date', meeting_date_formatted).execute()
                if existing_result.data and len(existing_result.data) > 0:
                    result = supabase.table('attendance').delete().eq('id', existing_result.data[0]['id']).execute()
                    # Delete operations in Supabase return the deleted record or empty list
                    # If no error was raised, the delete was successful
                    # Log activity
                    try:
                        log_activity(
                            leader_id=leader_id,
                            user_id=session_user_id,
                            activity_type='attendance_marked',
                            description=f'Cleared attendance for {member_name} for {meeting_date}',
                            details={'member_id': member_id, 'meeting_date': meeting_date_formatted}
                        )
                    except Exception as log_error:
                        print(f"Error logging activity: {log_error}")
                    
                    return jsonify({'success': True, 'message': f'Attendance cleared for {member_name}'})
                else:
                    return jsonify({'success': False, 'message': 'No attendance record to clear'}), 400
            except Exception as delete_error:
                print(f"Error deleting attendance: {delete_error}")
                return jsonify({'success': False, 'message': 'Error clearing attendance'}), 500
        else:
            # Insert or update attendance record
            # meeting_number is required by the schema
            if meeting_number is None:
                return jsonify({'success': False, 'message': 'Meeting not found. Cannot mark attendance.'}), 400
            
            attendance_data = {
                'leader_id': leader_id,
                'member_id': member_id,
                'meeting_date': meeting_date_formatted,
                'meeting_number': meeting_number,
                'status': status
            }
            
            # Check if record exists
            existing_result = supabase.table('attendance').select('id').eq('leader_id', leader_id).eq('member_id', member_id).eq('meeting_date', meeting_date_formatted).execute()
            
            if existing_result.data and len(existing_result.data) > 0:
                # Update existing record
                result = supabase.table('attendance').update({
                    'status': status,
                    'meeting_number': meeting_number  # Update meeting_number in case it changed
                }).eq('id', existing_result.data[0]['id']).execute()
            else:
                # Insert new record
                result = supabase.table('attendance').insert(attendance_data).execute()
            
            if result.data and len(result.data) > 0:
                # Log activity
                try:
                    log_activity(
                        leader_id=leader_id,
                        user_id=session_user_id,
                        activity_type='attendance_marked',
                        description=f'Marked {member_name} as {status} for {meeting_date}',
                        details={'member_id': member_id, 'meeting_date': meeting_date_formatted, 'status': status}
                    )
                except Exception as log_error:
                    print(f"Error logging activity: {log_error}")
                
                return jsonify({'success': True, 'message': f'{member_name} marked as {status}'})
            else:
                print(f"Error: No data returned from attendance insert/update. Result: {result}")
                return jsonify({'success': False, 'message': 'Error saving attendance. Please try again.'}), 500
        
    except Exception as e:
        print(f"Error updating attendance: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error updating attendance: {str(e)}'}), 500

@main_bp.route('/bulk_update_attendance/<meeting_date>', methods=['POST'])
def bulk_update_attendance(meeting_date):
    """Bulk update attendance for multiple members at once"""
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    try:
        # Get attendance data from JSON
        data = request.get_json()
        attendance_list = data.get('attendance', [])  # List of {member_id, status}
        
        if not attendance_list:
            return jsonify({'success': False, 'message': 'No attendance data provided'}), 400
        
        # Get leader ID
        session_user_id = session['user']['id']
        leader_id = get_uuid_from_user_id(session_user_id)
        
        # Convert meeting_date string to proper date format
        try:
            parsed_date = datetime.strptime(meeting_date, "%B %d, %Y").date()
            meeting_date_formatted = parsed_date.isoformat()
        except ValueError:
            meeting_date_formatted = meeting_date
        
        # Get meeting_number from meetings table
        meeting_number = None
        try:
            meeting_result = supabase.table('meetings').select('meeting_number').eq('meeting_date', meeting_date_formatted).limit(1).execute()
            if meeting_result.data and len(meeting_result.data) > 0:
                meeting_number = meeting_result.data[0].get('meeting_number')
        except Exception as e:
            print(f"Error fetching meeting_number: {e}")
        
        if meeting_number is None:
            return jsonify({'success': False, 'message': 'Meeting not found. Cannot mark attendance.'}), 400
        
        # Process each attendance record
        success_count = 0
        error_count = 0
        errors = []
        
        for attendance_item in attendance_list:
            member_id = attendance_item.get('member_id')
            status = attendance_item.get('status')  # 'present' or 'absent'
            
            if not member_id or not status:
                error_count += 1
                continue
            
            try:
                # Check if record exists
                existing_result = supabase.table('attendance').select('id').eq('leader_id', leader_id).eq('member_id', member_id).eq('meeting_date', meeting_date_formatted).execute()
                
                attendance_data = {
                    'leader_id': leader_id,
                    'member_id': member_id,
                    'meeting_date': meeting_date_formatted,
                    'meeting_number': meeting_number,
                    'status': status
                }
                
                if existing_result.data and len(existing_result.data) > 0:
                    # Update existing record
                    result = supabase.table('attendance').update({
                        'status': status,
                        'meeting_number': meeting_number
                    }).eq('id', existing_result.data[0]['id']).execute()
                else:
                    # Insert new record
                    result = supabase.table('attendance').insert(attendance_data).execute()
                
                if result.data and len(result.data) > 0:
                    success_count += 1
                else:
                    error_count += 1
                    errors.append(f"Member {member_id}")
            except Exception as e:
                error_count += 1
                errors.append(f"Member {member_id}: {str(e)}")
                print(f"Error updating attendance for member {member_id}: {e}")
        
        # Log activity
        try:
            log_activity(
                leader_id=leader_id,
                user_id=session_user_id,
                activity_type='attendance_marked',
                description=f'Bulk updated attendance for {success_count} members for {meeting_date}',
                details={'meeting_date': meeting_date_formatted, 'success_count': success_count, 'error_count': error_count}
            )
        except Exception as log_error:
            print(f"Error logging activity: {log_error}")
        
        if error_count == 0:
            return jsonify({'success': True, 'message': f'Successfully updated attendance for {success_count} members'})
        else:
            return jsonify({
                'success': True, 
                'message': f'Updated {success_count} members, {error_count} errors',
                'errors': errors
            })
        
    except Exception as e:
        print(f"Error in bulk_update_attendance: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error updating attendance: {str(e)}'}), 500

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
        
        template_name = f'main/members{get_template_suffix()}.html'
        return render_template(template_name, members=members, user=session['user'])
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
    
    template_name = f'main/member_form{get_template_suffix()}.html'
    return render_template(template_name, user=session['user'], member=member, is_edit=bool(member_id))
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
            template_name = f'main/member_details{get_template_suffix()}.html'
            return render_template(template_name, member=member, user=session['user'])
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
        template_name = f'main/member_form{get_template_suffix()}.html'
        return render_template(template_name, 
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
            template_name = f'main/member_form{get_template_suffix()}.html'
            return render_template(template_name, 
                                 user=session['user'], 
                                 form_errors={'general': 'Failed to add member to database'})
    except Exception as e:
        error_msg = str(e)
        flash(f'Error adding member: {error_msg}', 'error')
        template_name = f'main/member_form{get_template_suffix()}.html'
        return render_template(template_name, 
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
        
        # Check if this is the next meeting date (use corrected tutorial logic)
        next_meeting_date = get_tutorial_meeting_date_corrected()
        is_next_week = parsed_date == next_meeting_date
        
        template_name = f'main/meeting_tutorials{get_template_suffix()}.html'
        return render_template(template_name, 
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

@main_bp.route('/tutorials-list')
def tutorials_list():
    """Show all tutorials with status - only for meetings in meetings table"""
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    
    try:
        # Get leader ID
        session_user_id = session['user']['id']
        leader_id = get_uuid_from_user_id(session_user_id)
        
        # Get tutorial list from meetings table
        tutorial_list = []
        try:
            # Get all meetings from meetings table
            meetings_result = supabase.table('meetings')\
                .select('*')\
                .order('meeting_date', desc=True)\
                .limit(20)\
                .execute()
            
            if not meetings_result.data:
                print("No meetings found in database for tutorials")
                template_name = f'main/tutorials_list{get_template_suffix()}.html'
                return render_template(template_name,
                                     tutorial_list=[],
                                     user=session['user'])
            
            today = datetime.now().date()
            
            # Process each meeting from the meetings table
            for meeting in meetings_result.data:
                meeting_date = meeting.get('meeting_date')
                if not meeting_date:
                    continue
                
                # Parse meeting date
                try:
                    if isinstance(meeting_date, str):
                        try:
                            parsed_date = datetime.strptime(meeting_date, "%Y-%m-%d").date()
                        except ValueError:
                            try:
                                parsed_date = datetime.strptime(meeting_date, "%Y-%m-%dT%H:%M:%S").date()
                            except ValueError:
                                parsed_date = datetime.strptime(meeting_date.split('T')[0], "%Y-%m-%d").date()
                    else:
                        parsed_date = meeting_date
                    
                    meeting_date_iso = parsed_date.isoformat()
                    
                    # Check for tutorial for this meeting date
                    tutorial_result = supabase.table('tutorials')\
                        .select('*')\
                        .eq('meeting_date', meeting_date_iso)\
                        .execute()
                    
                    has_tutorial = len(tutorial_result.data) > 0 if tutorial_result.data else False
                    is_placeholder_tutorial = False
                    tutorial_record = None
                    
                    if has_tutorial and tutorial_result.data:
                        tutorial_record = tutorial_result.data[0]
                        # Check if it's a placeholder (check title field instead of tutorial_name)
                        is_placeholder_tutorial = tutorial_record.get('title') == 'No Tutorial Uploaded' or tutorial_record.get('title') == ''
                    
                    # Determine if this is upcoming or past
                    is_upcoming = parsed_date > today
                    
                    tutorial_list.append({
                        'date': parsed_date.strftime("%B %d, %Y"),
                        'date_iso': meeting_date_iso,
                        'has_tutorial': has_tutorial,
                        'is_placeholder': is_placeholder_tutorial,
                        'is_upcoming': is_upcoming,
                        'status': 'updated' if has_tutorial and not is_placeholder_tutorial else 'not_updated',
                        'tutorial_name': tutorial_record.get('title', 'No Tutorial') if has_tutorial else None,
                        'description': tutorial_record.get('description', '') if has_tutorial else None,
                        'sort_date': parsed_date  # Add sort_date for sorting
                    })
                except Exception as date_error:
                    print(f"Error parsing meeting date {meeting_date}: {date_error}")
                    continue
            
            # Sort tutorials: upcoming first, then past tutorials (most recent first)
            tutorial_list.sort(key=lambda x: (not x['is_upcoming'], -x['sort_date'].toordinal()))
            
        except Exception as e:
            print(f"Error fetching tutorial list: {e}")
            import traceback
            traceback.print_exc()
            tutorial_list = []
        
        template_name = f'main/tutorials_list{get_template_suffix()}.html'
        return render_template(template_name,
                             tutorial_list=tutorial_list,
                             user=session['user'])
    except Exception as e:
        print(f"Error fetching tutorials list: {e}")
        import traceback
        traceback.print_exc()
        flash('Error loading tutorials list', 'error')
        return redirect(url_for('main.index'))

@main_bp.route('/attendance-list')
def attendance_list():
    """Show all attendance records with status - only for meetings in meetings table"""
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    
    try:
        # Get leader ID
        session_user_id = session['user']['id']
        leader_id = get_uuid_from_user_id(session_user_id)
        
        # Get attendance list from meetings table
        attendance_list = []
        try:
            # Get all meetings from meetings table
            meetings_result = supabase.table('meetings')\
                .select('*')\
                .order('meeting_date', desc=True)\
                .limit(20)\
                .execute()
            
            if not meetings_result.data:
                print("No meetings found in database")
                template_name = f'main/attendance_list{get_template_suffix()}.html'
                return render_template(template_name,
                                     attendance_list=[],
                                     user=session['user'])
            
            # Get all members for this leader
            members_result = supabase.table('cell_members').select('id').eq('leader_id', leader_id).execute()
            total_members = len(members_result.data) if members_result.data else 0
            
            if total_members > 0:
                member_ids = [member['id'] for member in members_result.data]
                
                # Process each meeting from the meetings table
                for meeting in meetings_result.data:
                    meeting_date = meeting.get('meeting_date')
                    if not meeting_date:
                        continue
                    
                    # Parse meeting date
                    try:
                        if isinstance(meeting_date, str):
                            try:
                                parsed_date = datetime.strptime(meeting_date, "%Y-%m-%d").date()
                            except ValueError:
                                try:
                                    parsed_date = datetime.strptime(meeting_date, "%Y-%m-%dT%H:%M:%S").date()
                                except ValueError:
                                    parsed_date = datetime.strptime(meeting_date.split('T')[0], "%Y-%m-%d").date()
                        else:
                            parsed_date = meeting_date
                        
                        meeting_date_str = parsed_date.strftime("%B %d, %Y")
                        meeting_date_iso = parsed_date.isoformat()
                        
                        # Get attendance records for this meeting date
                        week_attendance_result = supabase.table('attendance')\
                            .select('member_id')\
                            .eq('leader_id', leader_id)\
                            .eq('meeting_date', meeting_date_iso)\
                            .in_('member_id', member_ids)\
                            .execute()
                        
                        week_attendance_count = len(week_attendance_result.data) if week_attendance_result.data else 0
                        
                        # Determine status for this meeting
                        if week_attendance_count == total_members:
                            week_status = 'complete'
                        elif week_attendance_count > 0:
                            week_status = 'partial'
                        else:
                            week_status = 'incomplete'
                        
                        # Check if this is an upcoming meeting (future dates only, not today)
                        today = datetime.now().date()
                        is_upcoming = parsed_date > today  # Only future dates, not today
                        
                        attendance_list.append({
                            'date': meeting_date_str,
                            'date_iso': meeting_date_iso,
                            'date_obj': parsed_date,  # Store date object for sorting
                            'status': week_status,
                            'count': week_attendance_count,
                            'total': total_members,
                            'is_upcoming': is_upcoming
                        })
                    except Exception as date_error:
                        print(f"Error parsing meeting date {meeting_date}: {date_error}")
                        continue
            else:
                # If no members, still show meetings but with 0 attendance
                for meeting in meetings_result.data:
                    meeting_date = meeting.get('meeting_date')
                    if not meeting_date:
                        continue
                    
                    try:
                        if isinstance(meeting_date, str):
                            try:
                                parsed_date = datetime.strptime(meeting_date, "%Y-%m-%d").date()
                            except ValueError:
                                parsed_date = datetime.strptime(meeting_date.split('T')[0], "%Y-%m-%d").date()
                        else:
                            parsed_date = meeting_date
                        
                        meeting_date_str = parsed_date.strftime("%B %d, %Y")
                        meeting_date_iso = parsed_date.isoformat()
                        
                        # Check if this is an upcoming meeting (future dates only, not today)
                        today = datetime.now().date()
                        is_upcoming = parsed_date > today  # Only future dates, not today
                        
                        attendance_list.append({
                            'date': meeting_date_str,
                            'date_iso': meeting_date_iso,
                            'date_obj': parsed_date,  # Store date object for sorting
                            'status': 'incomplete',
                            'count': 0,
                            'total': 0,
                            'is_upcoming': is_upcoming
                        })
                    except Exception as date_error:
                        print(f"Error parsing meeting date {meeting_date}: {date_error}")
                        continue
            
            # Sort attendance list: upcoming first, then past (most recent first)
            if attendance_list:
                attendance_list.sort(key=lambda x: (not x.get('is_upcoming', False), -x.get('date_obj', datetime.now().date()).toordinal()))
        
        except Exception as e:
            print(f"Error fetching attendance list: {e}")
            import traceback
            traceback.print_exc()
            attendance_list = []
        
        template_name = f'main/attendance_list{get_template_suffix()}.html'
        return render_template(template_name,
                             attendance_list=attendance_list,
                             user=session['user'])
    except Exception as e:
        print(f"Error fetching attendance list: {e}")
        import traceback
        traceback.print_exc()
        flash('Error loading attendance list', 'error')
        return redirect(url_for('main.index'))


