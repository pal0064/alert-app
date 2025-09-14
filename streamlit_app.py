import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json

# Configure page
st.set_page_config(
    page_title="EV Charger Alert",
    page_icon="🔋",
    layout="centered"
)

def send_discord_message(message):
    """Send a message to Discord via webhook"""
    webhook_url = st.secrets["webhook_url"]
    
    data = {
        "content": message,
        "username": "Charger Alert Bot"
    }
    
    try:
        st.info("Sending Discord message via webhook...")
        response = requests.post(webhook_url, json=data)
        if response.status_code == 204:
            st.info("Discord message sent successfully")
        else:
            st.error(f"Discord API error: {response.status_code}")
    except Exception as e:
        st.error(f"Failed to send Discord message: {e}")

def check_charger_status():
    """Check the charger status from the website"""
    url = st.secrets["charger_status_url"]
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")
        
        for div in soup.find_all("div"):
            text = div.get_text(strip=True)
            if text.endswith("Available"):
                return text
        
        return "Status not found"
    except Exception as e:
        return f"Error checking status: {e}"

def is_charger_available(status_text):
    """Check if charger has available slots based on status text"""
    if "Available" not in status_text:
        return False
    
    try:
        # Look for pattern like "2/4 Available" or "0/2 Available"
        import re
        match = re.search(r'(\d+)/(\d+)\s+Available', status_text)
        if match:
            available = int(match.group(1))
            total = int(match.group(2))
            return available > 0
        
        # If no pattern found but contains "Available", assume it's available
        return True
    except:
        return False

def check_and_alert():
    """API endpoint function to check charger status and send alert if needed"""
    # Load notification state from session state or file
    try:
        with open('notification_state.json', 'r') as f:
            state = json.load(f)
            notifications_enabled = state.get('notifications_enabled', False)
    except FileNotFoundError:
        notifications_enabled = False
    
    if not notifications_enabled:
        return {"status": "notifications_disabled", "message": "Notifications are disabled"}
    
    # Check charger status
    charger_status = check_charger_status()
    
    # Check if charging slot is actually available (not just contains "Available" text)
    if is_charger_available(charger_status):
        message = f"🔋 **Charger Alert!** \n\nCharging slot is now available!\nStatus: {charger_status}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        success, result_message = send_discord_message(message)
        
        if success:
            # Turn off notifications after sending alert
            save_notification_state(False)
            
            return {
                "status": "alert_sent", 
                "message": f"Alert sent for: {charger_status}",
                "notifications_disabled": True
            }
        else:
            return {"status": "alert_failed", "message": result_message}
    else:
        return {
            "status": "no_alert_needed", 
            "message": f"Current status: {charger_status}"
        }

def save_notification_state(enabled):
    """Save notification state to file"""
    state = {'notifications_enabled': enabled}
    with open('notification_state.json', 'w') as f:
        json.dump(state, f)

def load_notification_state():
    """Load notification state from file"""
    try:
        with open('notification_state.json', 'r') as f:
            state = json.load(f)
            return state.get('notifications_enabled', False)
    except FileNotFoundError:
        return False

# Handle API endpoint requests
query_params = st.query_params
if query_params.get("api") == "check_alert":
    # API endpoint logic
    result = check_and_alert()
    st.json(result)
    st.stop()
elif query_params.get("api") == "enable_notifications":
    # Enable notifications API
    save_notification_state(True)
    st.json({"status": "success", "message": "Notifications enabled"})
    st.stop()
elif query_params.get("api") == "disable_notifications":
    # Disable notifications API
    save_notification_state(False)
    st.json({"status": "success", "message": "Notifications disabled"})
    st.stop()
elif query_params.get("api") == "status":
    # Status check API
    notifications_enabled = load_notification_state()
    charger_status = check_charger_status()
    st.json({
        "notifications_enabled": notifications_enabled,
        "charger_status": charger_status,
        "timestamp": datetime.now().isoformat()
    })
    st.stop()

# Initialize session state
if 'notifications_enabled' not in st.session_state:
    st.session_state.notifications_enabled = load_notification_state()

if 'last_alert' not in st.session_state:
    st.session_state.last_alert = "No alerts sent"

# Streamlit UI
st.title("🔋 EV Charger Alert App")
st.markdown("---")

# API endpoint info
st.sidebar.header("🔗 API Endpoints")
st.sidebar.markdown("""
**Available API endpoints:**

**Check and Alert:**
```
?api=check_alert
```

**Enable Notifications:**
```
?api=enable_notifications
```

**Disable Notifications:**
```
?api=disable_notifications
```

**Get Status:**
```
?api=status
```

**Example usage:**
```bash
# Check and send alert if needed
curl "https://your-app.streamlit.app/?api=check_alert"

# Enable notifications
curl "https://your-app.streamlit.app/?api=enable_notifications"
```
""")

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Configuration")
st.sidebar.markdown("""
**Discord Webhook Setup:**
1. Add your Discord webhook URL to Streamlit secrets
2. Key name: `webhook_url`
3. Or pass it as query parameter: `&webhook_url=your_url`
""")

# Notification toggle
st.header("📱 Notification Settings")
col1, col2 = st.columns(2)

with col1:
    if st.button("🔔 Enable Notifications", type="primary"):
        st.session_state.notifications_enabled = True
        save_notification_state(True)
        st.success("Notifications enabled! Use the API endpoint to check for alerts.")

with col2:
    if st.button("🔕 Disable Notifications"):
        st.session_state.notifications_enabled = False
        save_notification_state(False)
        st.success("Notifications disabled!")

# Current status
st.markdown("---")
st.header("📊 Current Status")

status_col1, status_col2 = st.columns(2)

with status_col1:
    notification_status = "🟢 ON" if st.session_state.notifications_enabled else "🔴 OFF"
    st.metric("Notifications", notification_status)

with status_col2:
    st.metric("Last Alert", st.session_state.last_alert)

# Manual check
st.markdown("---")
st.header("🔍 Manual Check")

if st.button("Check Charger Status Now", type="secondary"):
    st.session_state.show_status = True

if st.session_state.get('show_status', False):
    with st.spinner("Checking charger status..."):
        status = check_charger_status()
        
    st.info(f"**Current Status:** {status}")
    
    # If available and notifications are on, offer to send alert
    if is_charger_available(status) and st.session_state.notifications_enabled:
        if st.button("Send Discord Alert Now", key="manual_alert"):
            message = f"🔋 **Manual Charger Alert!** \n\nCharging slot is available!\nStatus: {status}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            send_discord_message(message)
            st.session_state.notifications_enabled = False
            save_notification_state(False)
            st.session_state.last_alert = f"Manual alert sent at {datetime.now().strftime('%H:%M:%S')}"
            st.session_state.show_status = False  # Hide the status after sending
            st.rerun()

# Information
st.markdown("---")
st.header("ℹ️ How it works")
st.markdown("""
1. **Enable notifications** to start automatic monitoring
2. The app checks charger status **every 15 minutes** when notifications are on
3. When a charging slot becomes **available**, you'll get a Discord notification
4. **Notifications automatically turn off** after sending an alert
5. You can also **manually check** the status anytime
""")

# Footer
st.markdown("---")
st.caption("EV Charger Alert App | Checks ChargeHub for availability")
