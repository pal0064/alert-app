from flask import Flask, jsonify, request
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# In-memory notification state
notification_enabled = {'enabled': False}

@app.route('/enable_alerts', methods=['POST'])
def enable_alerts():
    notification_enabled['enabled'] = True
    return jsonify({'message': 'Alerts enabled.'})

@app.route('/disable_alerts', methods=['POST'])
def disable_alerts():
    notification_enabled['enabled'] = False
    return jsonify({'message': 'Alerts disabled.'})

@app.route('/check_status', methods=['GET'])
def check_status():
    url = "https://chargehub.com/en/ev-charging-stations/united-states/pennsylvania/harrisburg/aaa-central-penn/electric-car-stations-near-me?locId=122977"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(response.text, "html.parser")
    status = None
    for div in soup.find_all("div"):
        if div.get_text(strip=True).endswith("Available"):
            status = div.get_text(strip=True)
            break
    if notification_enabled['enabled']:
        # Here, you would send a real alert (email, SMS, etc.)
        alert = f"Charger status: {status}"
    else:
        alert = "Notifications are disabled. No alert sent."
    return jsonify({'status': status, 'alert': alert})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
