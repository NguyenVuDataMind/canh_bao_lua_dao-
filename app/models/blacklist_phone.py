from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import func
from sqlalchemy.sql.sqltypes import DateTime, String
from sqlalchemy import ForeignKey

from app.db import Base


class BlackListPhone(Base):
    __tablename__ = "blacklist_phone"

    id: Mapped[int] = mapped_column(primary_key=True)

    created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    value: Mapped[Optional[str]]
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    report_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("reports.id", ondelete="CASCADE"), nullable=True
    )

    report = relationship("Report", back_populates="phones")

    def __repr__(self) -> str:
        return f"BlackListPhone(id={self.id}, value={self.value!r})"

