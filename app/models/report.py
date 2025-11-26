from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import func
from sqlalchemy.sql.sqltypes import DateTime

from app.db import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)

    created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    reported_url: Mapped[Optional[str]]

    reported_email: Mapped[Optional[str]]

    reported_phone: Mapped[Optional[str]]

    phones = relationship(
        "BlackListPhone", back_populates="report", cascade="all, delete-orphan")
    urls = relationship(
        "BlackListURL", back_populates="report", cascade="all, delete-orphan")

    description: Mapped[Optional[str]]

    source: Mapped[Optional[str]]

    status: Mapped[Optional[bool]]
