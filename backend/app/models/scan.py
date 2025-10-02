from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import enum


class EngineType(str, enum.Enum):
    URLCHECK = "urlcheck"
    ANTIVIRUS = "antivirus"
    ML = "ml"


class VerdictType(str, enum.Enum):
    MALICIOUS = "malicious"
    SUSPICIOUS = "suspicious"
    CLEAN = "clean"
    ERROR = "error"


class ScanEngine(Base):
    __tablename__ = "scan_engines"

    engine_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    vendor = Column(String)
    version = Column(String)
    type = Column(Enum(EngineType))
    enabled = Column(Integer, default=1, nullable=False)

    # Relationships
    scan_results = relationship("ScanResult", back_populates="engine")

    __table_args__ = (
        {"extend_existing": True}
    )


class ScanResult(Base):
    __tablename__ = "scan_results"

    scan_id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.report_id"))
    indicator_id = Column(Integer, ForeignKey("indicators.indicator_id"), nullable=False)
    engine_id = Column(Integer, ForeignKey("scan_engines.engine_id"), nullable=False)
    verdict = Column(Enum(VerdictType), nullable=False)
    score = Column(Float)
    raw_json = Column(Text)
    scanned_at = Column(DateTime(timezone=True), nullable=False)

    # Relationships
    report = relationship("Report", back_populates="scan_results")
    indicator = relationship("Indicator", back_populates="scan_results")
    engine = relationship("ScanEngine", back_populates="scan_results")
