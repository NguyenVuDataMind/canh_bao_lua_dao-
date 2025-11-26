from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.functions import func
from sqlalchemy.sql.sqltypes import DateTime, String, Float

from app.db import Base


class SOSRequest(Base):
    __tablename__ = "sos_requests"

    id: Mapped[int] = mapped_column(primary_key=True)

    created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Vị trí GPS
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Độ chính xác GPS (mét)

    # Thông tin người dùng (nếu có)
    user_agent: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Trạng thái
    status: Mapped[Optional[str]] = mapped_column(String, nullable=True, server_default="pending")  # pending, responded, resolved
    notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Ghi chú từ admin

    def __repr__(self) -> str:
        return f"SOSRequest(id={self.id}, lat={self.latitude}, lng={self.longitude}, status={self.status})"

