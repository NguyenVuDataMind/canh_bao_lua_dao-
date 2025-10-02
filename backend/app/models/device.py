from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class Device(Base):
    __tablename__ = "devices"

    device_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    device_uuid = Column(String, unique=True, nullable=False)
    platform = Column(String)
    push_token = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_seen_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", back_populates="devices")
    gps_state = relationship("DeviceGPSState", back_populates="device", uselist=False, cascade="all, delete-orphan")
    location_telemetry = relationship("LocationTelemetry", back_populates="device")
    sos_requests = relationship("SOSRequest", back_populates="device")


class DeviceGPSState(Base):
    __tablename__ = "device_gps_state"

    device_id = Column(Integer, ForeignKey("devices.device_id"), primary_key=True)
    gps_enabled = Column(Integer)
    last_fix_ts = Column(DateTime(timezone=True))
    last_accuracy = Column(Float)

    # Relationships
    device = relationship("Device", back_populates="gps_state")


class LocationTelemetry(Base):
    __tablename__ = "location_telemetry"

    telemetry_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    device_id = Column(Integer, ForeignKey("devices.device_id"), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    accuracy_m = Column(Float)
    speed = Column(Float)
    ts = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", back_populates="location_telemetry")
    device = relationship("Device", back_populates="location_telemetry")
    sos_requests = relationship("SOSRequest", back_populates="last_location")


class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"

    contact_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    name = Column(String)
    phone = Column(String)
    relation = Column(String)
    method = Column(String)

    # Relationships
    user = relationship("User", back_populates="emergency_contacts")
