import streamlit as st
import requests
from datetime import datetime, timezone, timedelta
import json
from streamlit_js import st_js_blocking

# Configure page
st.set_page_config(
    page_title="EV Charger Alert",
    page_icon="🔋",
    layout="centered"
)

def get_api_endpoint():
    """Get API endpoint from secrets"""
    return st.secrets["API_ENDPOINT"]

def get_user_timezone():
    """Get user's timezone using JavaScript"""
    try:
        timezone_info = st_js_blocking(code="""
            // Get timezone name (IANA format)
            return Intl.DateTimeFormat().resolvedOptions().timeZone;
        """)
        
        if timezone_info is not None:
            return timezone_info
        else:
            return None
    except Exception as e:
        print(f"Error getting timezone: {e}")
        return None

def format_timestamp_with_timezone(timestamp, user_tz_name=None):
    """Format timestamp with user's timezone"""
    if timestamp == "Unknown" or not isinstance(timestamp, (int, float)):
        return "Unknown"
    
    try:
        # Create datetime from UTC timestamp
        dt_utc = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        
        if user_tz_name:
            # Use pytz or zoneinfo to convert to user's timezone
            try:
                import pytz
                user_tz = pytz.timezone(user_tz_name)
                dt_local = dt_utc.astimezone(user_tz)
                # Get timezone abbreviation
                tz_abbr = dt_local.strftime("%Z")
                return dt_local.strftime(f"%m/%d/%Y %H:%M:%S {tz_abbr}")
            except ImportError:
                # Fallback if pytz not available
                try:
                    import zoneinfo
                    user_tz = zoneinfo.ZoneInfo(user_tz_name)
                    dt_local = dt_utc.astimezone(user_tz)
                    tz_abbr = dt_local.strftime("%Z")
                    return dt_local.strftime(f"%m/%d/%Y %H:%M:%S {tz_abbr}")
                except ImportError:
                    # Last fallback to system local time
                    dt_local = datetime.fromtimestamp(timestamp)
                    return dt_local.strftime(f"%m/%d/%Y %H:%M:%S Local")
        else:
            # Fall back to system local time
            dt_local = datetime.fromtimestamp(timestamp)
            return dt_local.strftime(f"%m/%d/%Y %H:%M:%S Local")
    except Exception as e:
        return f"Parse Error: {str(e)[:20]}"

def call_api(endpoint):
    """Call the Vercel API endpoint"""
    api_base = get_api_endpoint()
    try:
        response = requests.get(f"{api_base}{endpoint}", timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API error: {response.status_code}"}
    except Exception as e:
        return {"error": f"Failed to call API: {e}"}
    """Call the Vercel API endpoint"""
    api_base = get_api_endpoint()
    try:
        response = requests.get(f"{api_base}{endpoint}", timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API error: {response.status_code}"}
    except Exception as e:
        return {"error": f"Failed to call API: {e}"}

# Initialize session state
if 'notifications_enabled' not in st.session_state:
    # Get initial state from API
    status_result = call_api("/api/notifications/status")
    if "error" not in status_result:
        st.session_state.notifications_enabled = status_result.get("notifications_enabled", False)
    else:
        st.session_state.notifications_enabled = False

if 'last_alert' not in st.session_state:
    st.session_state.last_alert = "No alerts sent"

# Streamlit UI
st.title("🔋 EV Charger Alert App")
st.markdown("---")
# Notification toggle
st.header("📱 Notification Settings")
col1, col2 = st.columns(2)

with col1:
    if st.button("🔔 Enable Notifications", type="primary"):
        result = call_api("/api/enable_notifications")
        if "error" not in result:
            st.session_state.notifications_enabled = True
            st.success("Notifications enabled! The backend will check for alerts every 10 minutes.")
        else:
            st.error(f"Failed to enable notifications: {result['error']}")

with col2:
    if st.button("🔕 Disable Notifications"):
        result = call_api("/api/disable_notifications")
        if "error" not in result:
            st.session_state.notifications_enabled = False
            st.success("Notifications disabled!")
        else:
            st.error(f"Failed to disable notifications: {result['error']}")

# Current status
st.markdown("---")
st.header("📊 Current Status")

# Get notification status from lightweight API
notification_result = call_api("/api/notifications/status")

if "error" not in notification_result:
    notifications_enabled = notification_result.get("notifications_enabled", False)
    
    # Update session state
    st.session_state.notifications_enabled = notifications_enabled
    
    # Show notification status immediately
    status_col1, status_col2 = st.columns(2)
    
    with status_col1:
        notification_status = "🟢 ON" if notifications_enabled else "🔴 OFF"
        st.metric("Notifications", notification_status)
    
    with status_col2:
        # Show last update time from notification check in user's local timezone
        last_updated = notification_result.get("timestamp", "Unknown")
        
        # Get user's timezone using JavaScript
        user_tz_name = get_user_timezone()
        
        # Format timestamp with user's timezone
        formatted_time = format_timestamp_with_timezone(last_updated, user_tz_name)
        st.metric("Last Updated", formatted_time)
    
    # Only get full charger status if user wants to see it
    if st.button("🔍 Show Current Charger Status"):
        with st.spinner("Checking charger status..."):
            status_result = call_api("/api/status")
        
        if "error" not in status_result:
            charger_status = status_result.get("charger_status", "Unknown")
            charger_available = status_result.get("charger_available", False)
            
            # Show charger status
            availability_status = "🟢 Available" if charger_available else "🔴 Not Available"
            st.metric("Charger Status", availability_status)
            st.info(f"**Charger Details:** {charger_status}")
        else:
            st.error(f"Failed to get charger status: {status_result['error']}")
    
else:
    st.error(f"Failed to get notification status: {notification_result['error']}")

# Manual check and alert
st.markdown("---")
st.header("🔍 Manual Check & Alert")

if st.button("Check & Send Alert If Available", type="secondary"):
    with st.spinner("Checking charger status and sending alert if needed..."):
        result = call_api("/api/check_alert")
    
    if "error" not in result:
        status = result["status"]
        message = result["message"]
        
        if status == "alert_sent":
            st.success(f"🔋 **Alert Sent!** {message}")
            st.session_state.notifications_enabled = False
            st.session_state.last_alert = f"Alert sent at {datetime.now().strftime('%H:%M:%S')}"
        elif status == "notifications_disabled":
            st.info(f"ℹ️ {message}")
        elif status == "no_alert_needed":
            st.info(f"✅ {message}")
        elif status == "alert_failed":
            st.error(f"❌ {message}")
        else:
            st.info(f"Status: {message}")
    else:
        st.error(f"Failed to check status: {result['error']}")

# Information
st.markdown("---")
st.header("ℹ️ How it works")
st.markdown("""
1. **Enable notifications** to start automatic monitoring
2. The backend checks charger status **every 10 minutes** when notifications are on
3. When a charging slot becomes **available**, you'll get a Discord notification
4. **Notifications automatically turn off** after sending an alert
5. You can also **manually check** the status anytime using the button above
6. All processing is handled by the **Vercel FastAPI backend**
""")
