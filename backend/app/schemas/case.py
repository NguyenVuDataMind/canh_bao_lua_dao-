from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from ..models.case import CaseStatus
from ..models.report import SeverityLevel


class CaseCreate(BaseModel):
    title: str
    category: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[SeverityLevel] = None


class CaseUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    status: Optional[CaseStatus] = None
    severity: Optional[SeverityLevel] = None


class CaseIndicatorCreate(BaseModel):
    indicator_id: int
    role: Optional[str] = None


class CaseIndicatorResponse(BaseModel):
    indicator_id: int
    role: Optional[str] = None

    class Config:
        from_attributes = True


class CaseAttachmentCreate(BaseModel):
    file_url: str
    file_type: str
    mime_type: Optional[str] = None
    storage_provider: Optional[str] = None


class CaseAttachmentResponse(BaseModel):
    case_attachment_id: int
    file_url: str
    file_type: str
    mime_type: Optional[str] = None
    storage_provider: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CaseLabelCreate(BaseModel):
    label: str


class CaseLabelResponse(BaseModel):
    case_label_id: int
    label: str

    class Config:
        from_attributes = True


class CaseResponse(BaseModel):
    case_id: int
    title: str
    category: Optional[str] = None
    description: Optional[str] = None
    status: CaseStatus
    severity: Optional[SeverityLevel] = None
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    indicators: List[CaseIndicatorResponse] = []
    attachments: List[CaseAttachmentResponse] = []
    labels: List[CaseLabelResponse] = []

    class Config:
        from_attributes = True
