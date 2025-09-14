# EV Charger Alert App

A single Streamlit app that monitors EV charging station availability and sends Discord notifications when slots become available. Designed for Streamlit Cloud deployment.

## Features

- 🔔 Toggle notifications on/off (default: off)
- 🕐 API endpoints accessible via query parameters
- 📱 Discord notifications when charging slots become available
- 🔄 Auto-disable notifications after sending an alert
- 🔍 Manual status checking anytime
- ☁️ Single app deployment - perfect for Streamlit Cloud

## Quick Setup for Streamlit Cloud

1. **Fork/Clone this repository**

2. **Deploy to Streamlit Cloud:**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub repository
   - Deploy the app

3. **Configure Discord Webhook in Streamlit Secrets:**
   - In your Streamlit Cloud dashboard, go to app settings
   - Add to secrets.toml:
   ```toml
   webhook_url = "your_discord_webhook_url_here"
   ```

4. **Your app is ready!** 🎉

## API Endpoints

Your deployed app provides API endpoints via query parameters:

### Available Endpoints:

**Check and Alert:**
```
https://your-app.streamlit.app/?api=check_alert
```

**Enable Notifications:**
```
https://your-app.streamlit.app/?api=enable_notifications
```

**Disable Notifications:**
```
https://your-app.streamlit.app/?api=disable_notifications
```

**Get Status:**
```
https://your-app.streamlit.app/?api=status
```

### Response Examples:

**Notifications disabled:**
```json
{
  "status": "notifications_disabled",
  "message": "Notifications are disabled"
}
```

**Alert sent:**
```json
{
  "status": "alert_sent",
  "message": "Alert sent for: 2 of 4 Available",
  "notifications_disabled": true
}
```

**No alert needed:**
```json
{
  "status": "no_alert_needed",
  "message": "Current status: All stations busy"
}
```

## Local Development

If you want to run locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run streamlit_app.py
```

## Files

- `streamlit_app.py` - Main Streamlit application with API endpoints
- `requirements.txt` - Python dependencies
- `README.md` - This file

## Configuration

### Streamlit Secrets (Recommended)
Add to your Streamlit Cloud secrets:
```toml
webhook_url = "your_discord_webhook_url"
```

### Query Parameter (Alternative)
You can also pass the webhook URL as a query parameter:
```
https://your-app.streamlit.app/?api=check_alert&webhook_url=your_url
```

## Deployment Notes

- ✅ **Single app** - No need for multiple services
- ✅ **Streamlit Cloud compatible** - Uses query parameters for API
- ✅ **Free hosting** - Works perfectly with Streamlit Cloud free tier
- ✅ **External scheduling** - Use free services like GitHub Actions
- ✅ **Persistent state** - Uses file-based storage for notification state
- ✅ **No background threads** - All logic triggered by external calls

## Monitoring

When a charging slot becomes available, you'll receive a Discord notification and the notifications will automatically turn off.

To re-enable notifications, either:
- Use the web interface, or
- Call the enable API: `https://your-app.streamlit.app/?api=enable_notifications`
