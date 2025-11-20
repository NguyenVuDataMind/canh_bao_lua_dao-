from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict

from app.models.trusted_url import WhitelistMatchType


class TrustedURLBase(BaseModel):
    value: str = Field(..., description="URL hoặc pattern gốc để normalize")
    match_type: WhitelistMatchType = Field(
        default=WhitelistMatchType.EXACT,
        description="Chế độ so khớp: exact, prefix, wildcard",
    )
    source: Optional[str] = Field(None, description="Nguồn dữ liệu (vd: crawler)")
    description: Optional[str] = Field(None, description="Ghi chú thêm")
    is_active: bool = Field(default=True)


class TrustedURLCreate(TrustedURLBase):
    pass


class TrustedURLOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    normalized_pattern: str
    match_type: WhitelistMatchType
    source: Optional[str] = None
    description: Optional[str] = None
    raw_example: Optional[str] = None
    is_active: bool
    created: datetime
    updated: datetime


class TrustedURLUpdate(BaseModel):
    description: Optional[str] = None
    is_active: Optional[bool] = None
    source: Optional[str] = None


class URLWhitelistMatchResult(BaseModel):
    original_url: str
    normalized_url: str
    is_trusted: bool
    match_type: Optional[WhitelistMatchType] = None
    whitelist_entry_id: Optional[int] = None
    matched_pattern: Optional[str] = None
    reason: Optional[str] = None


class WhitelistCheckRequest(BaseModel):
    urls: List[str] = Field(..., min_length=1)


class WhitelistCheckResponse(BaseModel):
    results: List[URLWhitelistMatchResult]

