from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import os
import re
import asyncio
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


app = FastAPI(
    title="EV Charger Alert API",
    description="API for monitoring EV charger availability and sending Discord alerts",
    version="1.0.0"
)

# Global variable to track if background task is running
background_task_running = False

def get_webhook_url() -> str:
    """Get Discord webhook URL from environment variables"""
    webhook_url = os.getenv("WEBHOOK_URL")
    if not webhook_url:
        raise HTTPException(status_code=500, detail="Discord webhook URL not configured")
    return webhook_url

def get_charger_status_url() -> str:
    """Get charger status URL from environment variables"""
    status_url = os.getenv("CHARGER_STATUS_URL")
    if not status_url:
        raise HTTPException(status_code=500, detail="Charger status URL not configured")
    return status_url

def get_schedule_credentials() -> tuple[str, str]:
    """Get Cronhost API key and job ID from environment variables"""
    api_key = os.getenv("SCHEDULE_API_KEY")
    job_id = os.getenv("SCHEDULE_JOB_ID")
    if not api_key or not job_id:
        raise HTTPException(status_code=500, detail="Cronhost credentials not configured")
    return api_key, job_id

def toggle_schedule(enabled: bool) -> bool:
    """Enable or disable the Cronhost scheduled job"""
    try:
        api_key, job_id = get_schedule_credentials()
        url = f"https://cronho.st/api/v1/schedules/{job_id}/toggle"
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }
        data = {"enabled": enabled}
        
        response = requests.patch(url, headers=headers, json=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Failed to toggle schedule: {e}")
        return False

def send_discord_message(message: str) -> bool:
    """Send a message to Discord via webhook"""
    webhook_url = get_webhook_url()
    
    data = {
        "content": message,
        "username": "Charger Alert Bot"
    }
    
    try:
        response = requests.post(webhook_url, json=data, timeout=10)
        return response.status_code == 204
    except Exception as e:
        print(f"Failed to send Discord message: {e}")
        return False

def check_charger_status() -> str:
    """Check the charger status from the website"""
    url = get_charger_status_url()
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        
        for div in soup.find_all("div"):
            text = div.get_text(strip=True)
            if text.endswith("Available"):
                return text
        
        return "Status not found"
    except Exception as e:
        return f"Error checking status: {e}"

def is_charger_available(status_text: str) -> bool:
    """Check if charger has available slots based on status text"""
    if "Available" not in status_text:
        return False
    
    try:
        # Look for pattern like "2/4 Available" or "0/2 Available"
        match = re.search(r'(\d+)/(\d+)\s+Available', status_text)
        if match:
            available = int(match.group(1))
            total = int(match.group(2))
            return available > 0
        
        # If no pattern found but contains "Available", assume it's available
        return True
    except:
        return False

def save_notification_state(enabled: bool) -> None:
    """Save notification state to file"""
    state = {'notifications_enabled': enabled}
    try:
        with open('/tmp/notification_state.json', 'w') as f:
            json.dump(state, f)
    except Exception as e:
        print(f"Error saving notification state: {e}")

def load_notification_state() -> bool:
    """Load notification state from file"""
    try:
        with open('/tmp/notification_state.json', 'r') as f:
            state = json.load(f)
            return state.get('notifications_enabled', False)
    except FileNotFoundError:
        return False
    except Exception as e:
        print(f"Error loading notification state: {e}")
        return False

async def automated_charger_check():
    """Background task to check charger status every 10 minutes"""
    while True:
        try:
            # Wait 10 minutes (600 seconds)
            await asyncio.sleep(600)
            
            try:
                print(f"[{datetime.now()}] Running automated charger check...")
                
                # Call the same logic as the API endpoint
                result = await check_alert()
                
                # Log the result with automated prefix
                if result["status"] == "alert_sent":
                    print(f"[{datetime.now()}] Automated alert sent: {result['message']}")
                elif result["status"] == "notifications_disabled":
                    print(f"[{datetime.now()}] Automated check: {result['message']}")
                elif result["status"] == "no_alert_needed":
                    print(f"[{datetime.now()}] Automated check: {result['message']}")
                elif result["status"] == "alert_failed":
                    print(f"[{datetime.now()}] Automated check failed: {result['message']}")
                else:
                    print(f"[{datetime.now()}] Automated check result: {result}")
                    
            except Exception as check_error:
                print(f"[{datetime.now()}] Error in automated check cycle: {check_error}")
                # Continue the loop even if this cycle fails
                
        except Exception as sleep_error:
            print(f"[{datetime.now()}] Critical error in scheduler (will retry): {sleep_error}")
            # Even if sleep fails, wait a bit and try again
            try:
                await asyncio.sleep(60)  # Wait 1 minute before retrying
            except:
                pass

@app.on_event("startup")
async def startup_event():
    """Start background task on app startup"""
    global background_task_running
    if not background_task_running:
        background_task_running = True
        # Start the background task
        asyncio.create_task(automated_charger_check())
        print(f"[{datetime.now()}] Background charger monitoring started (checks every 10 minutes)")

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "EV Charger Alert API",
        "version": "1.0.0",
        "endpoints": {
            "check_alert": "/api/check_alert",
            "enable_notifications": "/api/enable_notifications", 
            "disable_notifications": "/api/disable_notifications",
            "notifications_status": "/api/notifications/status",
            "status": "/api/status"
        }
    }

@app.get("/api/check_alert")
async def check_alert() -> Dict[str, Any]:
    """Check charger status and send alert if needed"""
    # Load notification state
    notifications_enabled = load_notification_state()
    
    if not notifications_enabled:
        return {"status": "notifications_disabled", "message": "Notifications are disabled"}
    
    # Check charger status
    charger_status = check_charger_status()
    
    # Check if charging slot is actually available
    if is_charger_available(charger_status):
        message = f"🔋 **Charger Alert!** \n\nCharging slot is now available!\nStatus: {charger_status}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Send Discord message
        success = send_discord_message(message)
        
        if success:
            # Disable notifications after sending alert
            save_notification_state(False)
            return {
                "status": "alert_sent", 
                "message": f"Alert sent for: {charger_status}",
                "notifications_disabled": True
            }
        else:
            return {
                "status": "alert_failed",
                "message": f"Failed to send alert for: {charger_status}"
            }
    else:
        return {
            "status": "no_alert_needed", 
            "message": f"Current status: {charger_status}"
        }

@app.get("/api/enable_notifications")
async def enable_notifications() -> Dict[str, str]:
    """Enable notifications and Cronhost schedule"""
    save_notification_state(True)
    
    # Enable the Cronhost schedule
    schedule_enabled = toggle_schedule(True)
    
    if schedule_enabled:
        return {
            "status": "success", 
            "message": "Notifications enabled and schedule activated",
            "schedule_status": "enabled"
        }
    else:
        return {
            "status": "partial_success", 
            "message": "Notifications enabled but failed to activate schedule",
            "schedule_status": "failed"
        }

@app.get("/api/disable_notifications") 
async def disable_notifications() -> Dict[str, str]:
    """Disable notifications and Cronhost schedule"""
    save_notification_state(False)
    
    # Disable the Cronhost schedule
    schedule_disabled = toggle_schedule(False)
    
    if schedule_disabled:
        return {
            "status": "success", 
            "message": "Notifications disabled and schedule deactivated",
            "schedule_status": "disabled"
        }
    else:
        return {
            "status": "partial_success", 
            "message": "Notifications disabled but failed to deactivate schedule",
            "schedule_status": "failed"
        }

@app.get("/api/notifications/status")
async def get_notification_status() -> Dict[str, Any]:
    """Get only the notification status (lightweight endpoint)"""
    notifications_enabled = load_notification_state()
    
    return {
        "notifications_enabled": notifications_enabled,
        "timestamp": int(datetime.now().timestamp())
    }

@app.get("/api/status")
async def get_status() -> Dict[str, Any]:
    """Get current status of notifications and charger"""
    notifications_enabled = load_notification_state()
    charger_status = check_charger_status()
    
    return {
        "notifications_enabled": notifications_enabled,
        "charger_status": charger_status,
        "charger_available": is_charger_available(charger_status),
        "timestamp": int(datetime.now().timestamp())
    }

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)