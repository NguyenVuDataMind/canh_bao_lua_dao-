from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class BlackListPhoneCreate(BaseModel):
    value: str
    description: Optional[str] = None


class BlackListPhoneOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    value: Optional[str] = None
    description: Optional[str] = None
    report_id: Optional[int] = None
    created: datetime
    updated: datetime


class BlackListURLCreate(BaseModel):
    domain: str
    description: Optional[str] = None
    source: Optional[str] = None


class BlackListURLOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    domain: str
    description: Optional[str] = None
    source: Optional[str] = None
    report_id: Optional[int] = None
    created: datetime
    updated: datetime


class ReportCreate(BaseModel):
    reported_url: Optional[str] = None
    reported_phone: Optional[str] = None
    reported_email: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    reported_url: Optional[str] = None
    reported_phone: Optional[str] = None
    reported_email: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None
    status: Optional[bool] = None
    user_id: Optional[UUID] = None
    created: datetime
    updated: datetime

