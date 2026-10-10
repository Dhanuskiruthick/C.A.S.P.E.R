from fastapi import FastAPI, HTTPException, Header, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import sqlite3
import logging

logging.basicConfig(level=logging.ERROR)

app = FastAPI(title="C.A.S.P.E.R. - Smart Campus API")

# --- CORS Configuration ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global Exception Handler ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Internal Error on {request.method} {request.url.path}: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})

# --- Pydantic Schema for ESP32 JSON Payload ---
class SensorReading(BaseModel):
    temperature: float
    humidity: float
    current: float
    smoke_status: str
    water_leak: bool
    occupancy: int
    is_simulated: bool

DB_NAME = "campus_data_v2.db"

# --- Database Initialization ---
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

# --- Hardware Security ---
def verify_hardware(x_api_key: str = Header(...)):
    if x_api_key != "esp32-secret-key-2026":
        raise HTTPException(status_code=401, detail="Unauthorized hardware")

# --- Threshold Logic (100% Synced with ESP32) ---
def detect_anomaly(temp, current, smoke, leak):
    # TEMP_DANGER_C = 45.0
    # CURRENT_DANGER_A = 30.0
    
    # 1. Check for Critical / Danger State
    if temp >= 45.0 or current >= 30.0 or smoke == "Warning" or leak:
        reasons = []
        if temp >= 45.0: reasons.append(f"High Temp ({temp}°C)")
        if current >= 30.0: reasons.append(f"High Current ({current}A)")
        if smoke == "Warning": reasons.append("Smoke Detected")
        if leak: reasons.append("Water Leak Detected")
        
        alert_message = " | ".join(reasons)
        return "Critical", alert_message

    # 2. Check for Warning State
    elif temp >= 35.0:
        return "Warning", f"Elevated Temperature ({temp}°C)"

    # 3. Normal State
    return "Normal", None

# --- POST Endpoint: Receive Data from ESP32 ---
@app.post("/api/v1/readings", dependencies=[Depends(verify_hardware)])
async def receive_reading(reading: SensorReading):
    status, alert_reason = detect_anomaly(
        reading.temperature, reading.current, reading.smoke_status, reading.water_leak
    )
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

# --- GET Endpoint: Live Dashboard Data (Public) ---
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

# --- GET Endpoint: Historical Data for the Archive UI ---
@app.get("/api/v1/history")
async def get_history(start: str, end: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT timestamp, temperature, humidity, current, smoke_status, water_leak, occupancy, status 
        FROM readings 
        WHERE timestamp >= ? AND timestamp <= ?
        ORDER BY id DESC LIMIT 200
    """, (start + "T00:00:00", end + "T23:59:59"))
    rows = cursor.fetchall()
    conn.close()

    history = []
    for row in rows:
        history.append({
            "timestamp": row[0], "temperature": row[1], "humidity": row[2],
            "current": row[3], "smoke": row[4], "leak": bool(row[5]),
            "occupancy": row[6], "status": row[7]
        })
    return {"records": history}