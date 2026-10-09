from pydantic import BaseModel, Field

class SensorReading(BaseModel):
    temperature: float = Field(..., ge=-20, le=100, description="Temperature in Celsius")
    current: float = Field(..., ge=0, le=50, description="Current in Amperes")
    smoke_status: str
    is_simulated: bool = False