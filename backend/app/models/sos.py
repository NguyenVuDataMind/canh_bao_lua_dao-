from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import enum


class SOSStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class SOSRequest(Base):
    __tablename__ = "sos_requests"

    sos_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    device_id = Column(Integer, ForeignKey("devices.device_id"), nullable=False)
    triggered_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(Enum(SOSStatus), default=SOSStatus.PENDING, nullable=False)
    last_location_id = Column(Integer, ForeignKey("location_telemetry.telemetry_id"))
    notes = Column(Text)

    # Relationships
    user = relationship("User", back_populates="sos_requests")
    device = relationship("Device", back_populates="sos_requests")
    last_location = relationship("LocationTelemetry", back_populates="sos_requests")
    dispatch_logs = relationship("SOSDispatchLog", back_populates="sos_request", cascade="all, delete-orphan")


class SOSDispatchLog(Base):
    __tablename__ = "sos_dispatch_logs"

    dispatch_id = Column(Integer, primary_key=True, index=True)
    sos_id = Column(Integer, ForeignKey("sos_requests.sos_id"), nullable=False)
    sent_to = Column(String, nullable=False)
    payload = Column(Text)
    sent_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, nullable=False)
    error_message = Column(Text)

    # Relationships
    sos_request = relationship("SOSRequest", back_populates="dispatch_logs")
