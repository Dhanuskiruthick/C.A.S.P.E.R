from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ai.campus_safety import assess_reading


app = FastAPI(title="Smart Campus Safety AI")


# Allow requests from the Vercel dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://casper-one.vercel.app"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.get("/")
def home():
    return {"message": "Smart Campus Safety API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


class SensorReading(BaseModel):
    temperature_c: float
    humidity_pct: float = Field(ge=0, le=100)
    mq2_raw: float = Field(ge=0)
    water_leak: int = Field(ge=0, le=1)
    motion_detected: int = Field(ge=0, le=1)


@app.post("/api/ai/analyze")
def analyze_sensor_reading(reading: SensorReading):
    result = assess_reading(reading.model_dump())

    if result["status"] == "invalid":
        raise HTTPException(status_code=400, detail=result)

    result["timestamp"] = datetime.now(timezone.utc).isoformat()
    return result