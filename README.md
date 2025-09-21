# EV Charger Alert API (Vercel)

A FastAPI-based application for monitoring EV charger availability and sending Discord alerts. This is a Vercel-compatible version of the Streamlit app.

## Features

- Monitor EV charger status from web scraping
- Send Discord webhook notifications when chargers become available
- Enable/disable notification system
- RESTful API endpoints
- Automatic notification disabling after alert sent

## API Endpoints

### GET `/`
Returns API information and available endpoints.

### GET `/api/check_alert`
Checks charger status and sends Discord alert if available slots are found.

**Response:**
```json
{
  "status": "alert_sent|no_alert_needed|notifications_disabled|alert_failed",
  "message": "Status description",
  "notifications_disabled": true  // Only when alert is sent
}
```

### POST `/api/enable_notifications`
Enables the notification system.

**Response:**
```json
{
  "status": "success",
  "message": "Notifications enabled"
}
```

### POST `/api/disable_notifications`
Disables the notification system.

**Response:**
```json
{
  "status": "success", 
  "message": "Notifications disabled"
}
```

### GET `/api/status`
Returns current system status.

**Response:**
```json
{
  "notifications_enabled": true,
  "charger_status": "2/4 Available",
  "charger_available": true,
  "timestamp": "2024-01-01T12:00:00"
}
```

### GET `/health`
Health check endpoint.

## Environment Variables

Set these in your Vercel environment settings:

- `WEBHOOK_URL`: Your Discord webhook URL
- `CHARGER_STATUS_URL`: URL to scrape for charger status

## Deployment

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Deploy to Vercel:
```bash
vercel deploy
```

3. Set environment variables in Vercel dashboard

## Usage Examples

```bash
# Check and send alert if needed
curl "https://your-app.vercel.app/api/check_alert"

# Enable notifications
curl -X POST "https://your-app.vercel.app/api/enable_notifications"

# Disable notifications  
curl -X POST "https://your-app.vercel.app/api/disable_notifications"

# Check status
curl "https://your-app.vercel.app/api/status"
```

## Automated Monitoring

You can set up automated monitoring using:
- Vercel Cron Jobs
- GitHub Actions
- External cron services
- Uptime monitoring services

Example with curl in a cron job:
```bash
# Check every 15 minutes
*/15 * * * * curl "https://your-app.vercel.app/api/check_alert"
```
