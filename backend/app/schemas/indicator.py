from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from ..models.indicator import IndicatorType, IndicatorStatus


class IndicatorCreate(BaseModel):
    type: IndicatorType
    value: str


class IndicatorUpdate(BaseModel):
    status: Optional[IndicatorStatus] = None
    risk_score: Optional[float] = None
    notes: Optional[str] = None


class IndicatorResponse(BaseModel):
    indicator_id: int
    type: IndicatorType
    value: str
    status: Optional[IndicatorStatus] = None
    risk_score: Optional[float] = None
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    source: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True
