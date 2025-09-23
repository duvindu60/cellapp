"""
Activity logging utility for tracking all app activities
"""

from supabase import create_client, Client
import os
from datetime import datetime
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_ANON_KEY")
supabase: Client = create_client(url, key) if url and key else None

# Debug: Check if Supabase is initialized
if not supabase:
    print("Warning: Supabase client not initialized in activity_logger.py")
    print(f"URL: {url}")
    print(f"Key: {'Present' if key else 'Missing'}")
else:
    print("✅ Supabase client initialized successfully in activity_logger.py")

def log_activity(
    leader_id: str,
    user_id: str,
    activity_type: str,
    description: str,
    details: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Log an activity to the database
    
    Args:
        leader_id: UUID of the leader
        user_id: User ID from session (not stored in DB due to table constraints)
        activity_type: Type of activity (member_added, attendance_marked, etc.)
        description: Human-readable description
        details: Optional additional details as JSON (not stored in DB due to table constraints)
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not supabase:
        print("Warning: Supabase client not initialized, activity not logged")
        return False
    
    # Map new activity types to allowed ones
    activity_type_mapping = {
        'user_login': 'profile_updated',  # Map login to profile update
        'member_added': 'member_added',
        'member_updated': 'member_updated', 
        'member_deleted': 'member_deleted',
        'attendance_marked': 'attendance_marked',
        'attendance_updated': 'attendance_updated',
        'attendance_sheet_updated': 'attendance_updated',  # Map to attendance_updated
        'tutorial_uploaded': 'tutorial_uploaded',
        'tutorial_updated': 'tutorial_uploaded',  # Map to tutorial_uploaded
        'attendance_incomplete': 'attendance_updated',  # Map to attendance_updated
        'meeting_created': 'profile_updated',  # Map to profile_updated
        'profile_updated': 'profile_updated'
    }
    
    # Use mapped activity type
    mapped_type = activity_type_mapping.get(activity_type, 'profile_updated')
    
    try:
        activity_data = {
            'leader_id': leader_id,
            'activity_type': mapped_type,
            'description': description,
            'created_at': datetime.now().isoformat()
        }
        
        result = supabase.table('activities').insert(activity_data).execute()
        return True
        
    except Exception as e:
        print(f"Error logging activity: {e}")
        return False

def get_recent_activities(leader_id: str, limit: int = 10) -> list:
    """
    Get recent activities for a leader
    
    Args:
        leader_id: UUID of the leader
        limit: Maximum number of activities to return
    
    Returns:
        list: List of recent activities
    """
    if not supabase:
        return []
    
    try:
        result = supabase.table('activities')\
            .select('*')\
            .eq('leader_id', leader_id)\
            .order('created_at', desc=True)\
            .limit(limit)\
            .execute()
        
        return result.data if result.data else []
        
    except Exception as e:
        print(f"Error fetching activities: {e}")
        return []

def get_todays_activities(leader_id: str) -> list:
    """
    Get today's activities for a leader
    
    Args:
        leader_id: UUID of the leader
    
    Returns:
        list: List of today's activities
    """
    if not supabase:
        return []
    
    try:
        from datetime import datetime, timedelta
        
        # Get today's date range
        today = datetime.now().date()
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())
        
        result = supabase.table('activities')\
            .select('*')\
            .eq('leader_id', leader_id)\
            .gte('created_at', start_of_day.isoformat())\
            .lte('created_at', end_of_day.isoformat())\
            .order('created_at', desc=True)\
            .execute()
        
        return result.data if result.data else []
        
    except Exception as e:
        print(f"Error fetching today's activities: {e}")
        return []

def format_activity_description(activity: dict) -> str:
    """
    Format activity for display in the UI
    
    Args:
        activity: Activity dictionary from database
    
    Returns:
        str: Formatted description
    """
    activity_type = activity.get('activity_type', '')
    details = activity.get('details', {})
    
    if activity_type == 'user_login':
        return "User logged in"
    
    elif activity_type == 'member_added':
        member_name = details.get('member_name', 'Unknown')
        return f"Added new member: {member_name}"
    
    elif activity_type == 'member_updated':
        member_name = details.get('member_name', 'Unknown')
        field = details.get('field', 'information')
        return f"Updated {member_name}'s {field}"
    
    elif activity_type == 'member_deleted':
        member_name = details.get('member_name', 'Unknown')
        return f"Removed member: {member_name}"
    
    elif activity_type == 'attendance_marked':
        meeting_date = details.get('meeting_date', 'Unknown')
        member_name = details.get('member_name', 'Unknown')
        status = details.get('status', 'Unknown')
        return f"Marked {member_name} as {status} for {meeting_date}"
    
    elif activity_type == 'attendance_updated':
        meeting_date = details.get('meeting_date', 'Unknown')
        member_name = details.get('member_name', 'Unknown')
        old_status = details.get('old_status', 'Unknown')
        new_status = details.get('new_status', 'Unknown')
        return f"Changed {member_name} from {old_status} to {new_status} for {meeting_date}"
    
    elif activity_type == 'attendance_sheet_updated':
        meeting_date = details.get('meeting_date', 'Unknown')
        total_members = details.get('total_members', 0)
        present_count = details.get('present_count', 0)
        return f"Updated attendance sheet for {meeting_date} ({present_count}/{total_members} present)"
    
    elif activity_type == 'tutorial_uploaded':
        tutorial_name = details.get('tutorial_name', 'Unknown')
        meeting_date = details.get('meeting_date', 'Unknown')
        return f"Uploaded tutorial: {tutorial_name} for {meeting_date}"
    
    elif activity_type == 'tutorial_updated':
        tutorial_name = details.get('tutorial_name', 'Unknown')
        meeting_date = details.get('meeting_date', 'Unknown')
        return f"Updated tutorial: {tutorial_name} for {meeting_date}"
    
    elif activity_type == 'attendance_incomplete':
        meeting_date = details.get('meeting_date', 'Unknown')
        missing_count = details.get('missing_count', 0)
        return f"⚠️ Incomplete attendance for {meeting_date} ({missing_count} members not marked)"
    
    elif activity_type == 'meeting_created':
        meeting_date = details.get('meeting_date', 'Unknown')
        return f"Created meeting for {meeting_date}"
    
    elif activity_type == 'profile_updated':
        return "Updated profile information"
    
    else:
        return activity.get('description', 'Unknown activity')

def get_activity_icon(activity_type: str) -> str:
    """
    Get FontAwesome icon for activity type
    
    Args:
        activity_type: Type of activity
    
    Returns:
        str: FontAwesome icon class
    """
    icon_map = {
        'user_login': 'fas fa-sign-in-alt',
        'member_added': 'fas fa-user-plus',
        'member_updated': 'fas fa-user-edit',
        'member_deleted': 'fas fa-user-times',
        'attendance_marked': 'fas fa-check-circle',
        'attendance_updated': 'fas fa-edit',
        'attendance_sheet_updated': 'fas fa-clipboard-list',
        'tutorial_uploaded': 'fas fa-file-upload',
        'tutorial_updated': 'fas fa-file-edit',
        'attendance_incomplete': 'fas fa-exclamation-triangle',
        'meeting_created': 'fas fa-calendar-plus',
        'profile_updated': 'fas fa-user-cog'
    }
    return icon_map.get(activity_type, 'fas fa-circle')

def get_activity_color(activity_type: str) -> str:
    """
    Get color for activity type
    
    Args:
        activity_type: Type of activity
    
    Returns:
        str: Color class or hex code
    """
    color_map = {
        'user_login': '#17a2b8',
        'member_added': '#28a745',
        'member_updated': '#17a2b8',
        'member_deleted': '#dc3545',
        'attendance_marked': '#28a745',
        'attendance_updated': '#ffc107',
        'attendance_sheet_updated': '#007bff',
        'tutorial_uploaded': '#6f42c1',
        'tutorial_updated': '#6f42c1',
        'attendance_incomplete': '#fd7e14',
        'meeting_created': '#007bff',
        'profile_updated': '#6c757d'
    }
    return color_map.get(activity_type, '#6c757d')