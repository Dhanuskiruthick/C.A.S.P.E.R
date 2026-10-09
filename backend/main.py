from fastapi import FastAPI, HTTPException, Header, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from schemas import SensorReading
from datetime import datetime
import sqlite3
import logging

logging.basicConfig(level=logging.ERROR)

app = FastAPI(title="C.A.S.P.E.R. - Smart Campus API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Internal Error on {request.method} {request.url.path}: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})

DB_NAME = "campus_data_v2.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS readings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT, temperature REAL, humidity REAL, current REAL, 
                        smoke_status TEXT, water_leak BOOLEAN, occupancy INTEGER, 
                        is_simulated BOOLEAN, status TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT, reason TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Keep hardware security so ESP32 code works
def verify_hardware(x_api_key: str = Header(...)):
    if x_api_key != "esp32-secret-key-2026":
        raise HTTPException(status_code=401, detail="Unauthorized hardware")

def detect_anomaly(temp, current, smoke, leak):
    if temp > 45 or current > 7 or smoke == "Warning" or leak:
        return "Critical", f"Danger: Temp {temp}C, Current {current}A, Smoke: {smoke}, Leak: {leak}"
    elif temp > 35:
        return "Warning", "Elevated temperature detected."
    return "Normal", None

@app.post("/api/v1/readings", dependencies=[Depends(verify_hardware)])
async def receive_reading(reading: SensorReading):
    status, alert_reason = detect_anomaly(reading.temperature, reading.current, reading.smoke_status, reading.water_leak)
    timestamp = datetime.utcnow().isoformat()
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO readings (timestamp, temperature, humidity, current, smoke_status, water_leak, occupancy, is_simulated, status) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (timestamp, reading.temperature, reading.humidity, reading.current, reading.smoke_status, reading.water_leak, reading.occupancy, reading.is_simulated, status))
    
    if status in ["Critical", "Warning"]:
        cursor.execute("INSERT INTO alerts (timestamp, reason) VALUES (?, ?)", (timestamp, alert_reason))
    
    conn.commit()
    conn.close()
    return {"message": "Reading stored", "status": status}

# Dashboard is now 100% public. No token required.
@app.get("/api/v1/dashboard")
async def get_dashboard():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT timestamp, temperature, humidity, current, smoke_status, water_leak, occupancy, is_simulated, status 
        FROM readings ORDER BY id DESC LIMIT 1
    """)
    latest_row = cursor.fetchone()
    
    cursor.execute("SELECT timestamp, reason FROM alerts ORDER BY id DESC LIMIT 10")
    alerts_rows = cursor.fetchall()
    conn.close()

    if not latest_row:
        return {"status": "Waiting for data...", "latest_reading": None, "recent_alerts": []}

    latest_reading = {
        "timestamp": latest_row[0], "temperature": latest_row[1], "humidity": latest_row[2],
        "current": latest_row[3], "smoke_status": latest_row[4], "water_leak": bool(latest_row[5]),
        "occupancy": latest_row[6], "is_simulated": bool(latest_row[7])
    }
    
    recent_alerts = [{"timestamp": row[0], "reason": row[1]} for row in alerts_rows]

    return {
        "status": latest_row[8],
        "latest_reading": latest_reading,
        "recent_alerts": recent_alerts
    }