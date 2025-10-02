from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, Float
from sqlalchemy.orm import relationship
from ..core.database import Base
import enum


class IndicatorType(str, enum.Enum):
    URL = "url"
    DOMAIN = "domain"
    IP = "ip"
    EMAIL = "email"
    PHONE = "phone"
    HASH = "hash"


class IndicatorStatus(str, enum.Enum):
    MALICIOUS = "malicious"
    SUSPICIOUS = "suspicious"
    CLEAN = "clean"
    UNKNOWN = "unknown"


class Indicator(Base):
    __tablename__ = "indicators"

    indicator_id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum(IndicatorType), nullable=False)
    value = Column(String, nullable=False)
    status = Column(Enum(IndicatorStatus))
    risk_score = Column(Float)
    first_seen = Column(DateTime(timezone=True))
    last_seen = Column(DateTime(timezone=True))
    source = Column(String)
    notes = Column(Text)

    # Relationships
    reports = relationship("ReportIndicator", back_populates="indicator")
    cases = relationship("CaseIndicator", back_populates="indicator")
    scan_results = relationship("ScanResult", back_populates="indicator")

    __table_args__ = (
        {"extend_existing": True}
    )
