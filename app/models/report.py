from datetime import datetime

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

    reported_url: Mapped[str | None]

    reported_email: Mapped[str | None]

    reported_phone: Mapped[str | None]

    phones = relationship(
        "ReportedPhone", back_populates="report", cascade="all, delete-orphan")

    description: Mapped[str | None]

    source: Mapped[str | None]

    status: Mapped[bool | None]

    severity: Mapped[str | None]
