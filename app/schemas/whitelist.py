from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


class WhiteListURLBase(BaseModel):
    domain: str = Field(..., description="Domain để thêm vào whitelist")
    company: Optional[str] = Field(None, description="Tên công ty sở hữu domain")
    source: Optional[str] = Field(None, description="Nguồn dữ liệu (vd: tinnhiemmang)")


class WhiteListURLCreate(WhiteListURLBase):
    pass


class WhiteListURLOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    domain: str
    company: Optional[str] = None
    first_seen: date
    last_seen: date
    source: Optional[str] = None


class WhiteListURLUpdate(BaseModel):
    company: Optional[str] = None
    source: Optional[str] = None


class URLWhitelistMatchResult(BaseModel):
    original_url: str
    normalized_url: str
    is_trusted: bool
    match_type: Optional[str] = None  # Giữ lại để tương thích, nhưng không dùng nữa
    whitelist_entry_id: Optional[int] = None
    matched_pattern: Optional[str] = None
    reason: Optional[str] = None


class WhitelistCheckRequest(BaseModel):
    urls: List[str] = Field(..., min_length=1)


class WhitelistCheckResponse(BaseModel):
    results: List[URLWhitelistMatchResult]

