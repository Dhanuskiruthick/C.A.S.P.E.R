from pydantic import BaseModel, Field

class SensorReading(BaseModel):
    temperature: float = Field(..., ge=-20, le=100)
    humidity: float = Field(..., ge=0, le=100)
    current: float = Field(..., ge=0, le=50)
    smoke_status: str
    water_leak: bool
    occupancy: int
    is_simulated: bool = False

class LoginRequest(BaseModel):
    username: str
    password: str