from datetime import datetime

from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.functions import func

from app.db import Base


class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "users"

    created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    # custom fields
    full_name: Mapped[str] = mapped_column(nullable=True)
    phone_e164: Mapped[str] = mapped_column(nullable=True, unique=True)
    role: Mapped[str] = mapped_column(nullable=False, default="user")
    risk_score: Mapped[float] = mapped_column(nullable=False, default=0.0)
    gender: Mapped[str] = mapped_column(nullable=True)
    birth_year: Mapped[int] = mapped_column(nullable=True)
    email_verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    last_access_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    risk_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    otp_code: Mapped[str] = mapped_column(nullable=True)

    def __repr__(self):
        return f"User(id={self.id!r}, name={self.email!r})"
