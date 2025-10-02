from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import enum


class ReportStatus(str, enum.Enum):
    OPEN = "open"
    VALIDATED = "validated"
    DISMISSED = "dismissed"


class SeverityLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Report(Base):
    __tablename__ = "reports"

    report_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    reported_url = Column(String)
    reported_email = Column(String)
    reported_phone = Column(String)
    description = Column(Text)
    source = Column(String)
    report_date = Column(DateTime(timezone=True))
    status = Column(Enum(ReportStatus), default=ReportStatus.OPEN, nullable=False)
    severity = Column(Enum(SeverityLevel))

    # Relationships
    user = relationship("User", back_populates="reports")
    attachments = relationship("ReportAttachment", back_populates="report", cascade="all, delete-orphan")
    indicators = relationship("ReportIndicator", back_populates="report", cascade="all, delete-orphan")
    scan_results = relationship("ScanResult", back_populates="report")


class ReportAttachment(Base):
    __tablename__ = "report_attachments"

    attachment_id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.report_id"), nullable=False)
    file_url = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    mime_type = Column(String)
    storage_provider = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    report = relationship("Report", back_populates="attachments")


class ReportIndicator(Base):
    __tablename__ = "report_indicators"

    report_id = Column(Integer, ForeignKey("reports.report_id"), nullable=False, primary_key=True)
    indicator_id = Column(Integer, ForeignKey("indicators.indicator_id"), nullable=False, primary_key=True)
    relation = Column(String)
    primary_flag = Column(Integer)

    # Relationships
    report = relationship("Report", back_populates="indicators")
    indicator = relationship("Indicator", back_populates="reports")
