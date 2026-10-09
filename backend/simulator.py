import time
import requests
import random

URL = "http://localhost:8000/api/v1/readings"
HEADERS = {"x-api-key": "esp32-secret-key-2026"}

print("Starting ESP32 Simulator...")

while True:
    # Simulate normal readings most of the time, occasionally spike to abnormal
    is_abnormal = random.random() > 0.8 
    
    payload = {
        "temperature": round(random.uniform(45.0, 55.0) if is_abnormal else random.uniform(25.0, 32.0), 1),
        "current": round(random.uniform(8.0, 12.0) if is_abnormal else random.uniform(2.0, 5.0), 2),
        "smoke_status": "Warning" if is_abnormal else "Normal",
        "is_simulated": True
    }
    
    try:
        response = requests.post(URL, json=payload, headers=HEADERS)
        print(f"Sent: {payload} | Status: {response.json().get('status')}")
    except Exception as e:
        print(f"Connection failed: {e}")
        
    time.sleep(3) # Send data every 3 seconds