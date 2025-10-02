from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from ..models.report import ReportStatus, SeverityLevel


class ReportCreate(BaseModel):
    reported_url: Optional[str] = None
    reported_email: Optional[str] = None
    reported_phone: Optional[str] = None
    description: Optional[str] = None
    source: str = "user"


class ReportUpdate(BaseModel):
    status: Optional[ReportStatus] = None
    severity: Optional[SeverityLevel] = None
    description: Optional[str] = None


class ReportAttachmentCreate(BaseModel):
    file_url: str
    file_type: str
    mime_type: Optional[str] = None
    storage_provider: Optional[str] = None


class ReportAttachmentResponse(BaseModel):
    attachment_id: int
    file_url: str
    file_type: str
    mime_type: Optional[str] = None
    storage_provider: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReportIndicatorCreate(BaseModel):
    indicator_id: int
    relation: Optional[str] = None
    primary_flag: Optional[int] = None


class ReportIndicatorResponse(BaseModel):
    indicator_id: int
    relation: Optional[str] = None
    primary_flag: Optional[int] = None

    class Config:
        from_attributes = True


class ReportResponse(BaseModel):
    report_id: int
    user_id: int
    reported_url: Optional[str] = None
    reported_email: Optional[str] = None
    reported_phone: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None
    report_date: Optional[datetime] = None
    status: ReportStatus
    severity: Optional[SeverityLevel] = None
    attachments: List[ReportAttachmentResponse] = []
    indicators: List[ReportIndicatorResponse] = []

    class Config:
        from_attributes = True
