from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from schemas import SensorReading, LoginRequest
from datetime import datetime
import sqlite3



# 1. CHANGE DB NAME to v2 to force a fresh schema creation
DB_NAME = "campus_data_v2.db" 

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Added humidity, water_leak, and occupancy columns
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

# ... [Keep verify_hardware, verify_admin, login, and detect_anomaly functions] ...

@app.post("/api/v1/readings", dependencies=[Depends(verify_hardware)])
async def receive_reading(reading: SensorReading):
    status, alert_reason = detect_anomaly(reading.temperature, reading.current)
    # AI team can expand detect_anomaly() later to use the new fields
    
    timestamp = datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Updated INSERT statement
    cursor.execute("""
        INSERT INTO readings (timestamp, temperature, humidity, current, smoke_status, water_leak, occupancy, is_simulated, status) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (timestamp, reading.temperature, reading.humidity, reading.current, reading.smoke_status, reading.water_leak, reading.occupancy, reading.is_simulated, status))
    
    if status == "Critical":
        cursor.execute("INSERT INTO alerts (timestamp, reason) VALUES (?, ?)", (timestamp, alert_reason))
    
    conn.commit()
    conn.close()
    return {"message": "Expanded reading stored permanently", "status": status}

@app.get("/api/v1/dashboard", dependencies=[Depends(verify_admin)])
async def get_dashboard():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Updated SELECT statement
    cursor.execute("""
        SELECT timestamp, temperature, humidity, current, smoke_status, water_leak, occupancy, is_simulated, status 
        FROM readings ORDER BY id DESC LIMIT 1
    """)
    latest_row = cursor.fetchone()
    
    cursor.execute("SELECT timestamp, reason FROM alerts ORDER BY id DESC LIMIT 5")
    alerts_rows = cursor.fetchall()
    conn.close()

    if not latest_row:
        return {"status": "Waiting for data...", "latest_reading": None, "recent_alerts": []}

    # Map the fetched row correctly
    latest_reading = {
        "timestamp": latest_row[0], 
        "temperature": latest_row[1], 
        "humidity": latest_row[2],
        "current": latest_row[3],
        "smoke_status": latest_row[4], 
        "water_leak": bool(latest_row[5]),
        "occupancy": latest_row[6],
        "is_simulated": bool(latest_row[7])
    }
    
    recent_alerts = [{"timestamp": row[0], "reason": row[1]} for row in alerts_rows]

    return {
        "status": latest_row[8],
        "latest_reading": latest_reading,
        "recent_alerts": recent_alerts
    }