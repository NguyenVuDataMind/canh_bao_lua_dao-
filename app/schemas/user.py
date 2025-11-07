import uuid
from typing import Optional

from fastapi_users import schemas


class UserRead(schemas.BaseUser[uuid.UUID]):
    full_name: Optional[str] = None
    phone_e164: Optional[str] = None
    role: str = "user"
    risk_score: float = 0.0
    gender: Optional[str] = None
    birth_year: Optional[int] = None
    email_verified_at: Optional[str] = None
    last_access_at: Optional[str] = None
    risk_updated_at: Optional[str] = None


class UserCreate(schemas.BaseUserCreate):
    full_name: Optional[str] = None
    phone_e164: Optional[str] = None
    role: str = "user"
    risk_score: float = 0.0
    gender: Optional[str] = None
    birth_year: Optional[int] = None
    email_verified_at: Optional[str] = None
    last_access_at: Optional[str] = None
    risk_updated_at: Optional[str] = None


class UserUpdate(schemas.BaseUserUpdate):
    full_name: Optional[str] = None
    phone_e164: Optional[str] = None
    role: str = "user"
    risk_score: float = 0.0
    gender: Optional[str] = None
    birth_year: Optional[int] = None
    email_verified_at: Optional[str] = None
    last_access_at: Optional[str] = None
    risk_updated_at: Optional[str] = None
