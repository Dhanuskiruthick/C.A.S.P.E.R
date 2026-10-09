from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from schemas import SensorReading
from datetime import datetime
import sqlite3

app = FastAPI(title="Smart Campus API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize SQLite Database
def init_db():
    conn = sqlite3.connect("campus_data.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS readings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT, temperature REAL, current REAL, 
                        smoke_status TEXT, is_simulated BOOLEAN, status TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT, reason TEXT)''')
    conn.commit()
    conn.close()

init_db()

def verify_hardware(x_api_key: str = Header(...)):
    if x_api_key != "esp32-secret-key-2026":
        raise HTTPException(status_code=401, detail="Unauthorized hardware")

# AI/ML Threshold Logic
def detect_anomaly(temp, current):
    if temp > 40 or current > 7:
        return "Critical", f"High values detected: Temp {temp}C, Current {current}A"
    return "Normal", None

@app.post("/api/v1/readings", dependencies=[Depends(verify_hardware)])
async def receive_reading(reading: SensorReading):
    status, alert_reason = detect_anomaly(reading.temperature, reading.current)
    timestamp = datetime.utcnow().isoformat()
    
    conn = sqlite3.connect("campus_data.db")
    cursor = conn.cursor()
    
    # Save reading
    cursor.execute("INSERT INTO readings (timestamp, temperature, current, smoke_status, is_simulated, status) VALUES (?, ?, ?, ?, ?, ?)",
                   (timestamp, reading.temperature, reading.current, reading.smoke_status, reading.is_simulated, status))
    
    # Save alert if abnormal
    if status == "Critical":
        cursor.execute("INSERT INTO alerts (timestamp, reason) VALUES (?, ?)", (timestamp, alert_reason))
    
    conn.commit()
    conn.close()
    
    return {"message": "Reading stored permanently", "status": status}

@app.get("/api/v1/dashboard")
async def get_dashboard():
    conn = sqlite3.connect("campus_data.db")
    cursor = conn.cursor()
    
    # Get latest reading
    cursor.execute("SELECT timestamp, temperature, current, smoke_status, is_simulated, status FROM readings ORDER BY id DESC LIMIT 1")
    latest_row = cursor.fetchone()
    
    # Get last 5 alerts
    cursor.execute("SELECT timestamp, reason FROM alerts ORDER BY id DESC LIMIT 5")
    alerts_rows = cursor.fetchall()
    conn.close()

    if not latest_row:
        return {"status": "Waiting for data...", "latest_reading": None, "recent_alerts": []}

    latest_reading = {
        "timestamp": latest_row[0], "temperature": latest_row[1], "current": latest_row[2],
        "smoke_status": latest_row[3], "is_simulated": bool(latest_row[4])
    }
    
    recent_alerts = [{"timestamp": row[0], "reason": row[1]} for row in alerts_rows]

    return {
        "status": latest_row[5],
        "latest_reading": latest_reading,
        "recent_alerts": recent_alerts
    }