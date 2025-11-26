from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class SOSRequestCreate(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy: Optional[float] = None


class SOSRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy: Optional[float] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    user_id: Optional[UUID] = None
    created: datetime

