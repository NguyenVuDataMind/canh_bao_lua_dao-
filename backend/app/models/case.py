from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
from .report import SeverityLevel
import enum


class CaseStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Case(Base):
    __tablename__ = "cases"

    case_id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    category = Column(String)
    description = Column(Text)
    status = Column(Enum(CaseStatus), default=CaseStatus.DRAFT, nullable=False)
    severity = Column(Enum(SeverityLevel))
    created_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True))

    # Relationships
    created_by_user = relationship("User", back_populates="cases")
    indicators = relationship("CaseIndicator", back_populates="case", cascade="all, delete-orphan")
    attachments = relationship("CaseAttachment", back_populates="case", cascade="all, delete-orphan")
    labels = relationship("CaseLabel", back_populates="case", cascade="all, delete-orphan")
    lesson_cases = relationship("LessonCase", back_populates="case")
    datasets = relationship("Dataset", back_populates="case", cascade="all, delete-orphan")


class CaseIndicator(Base):
    __tablename__ = "case_indicators"

    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False, primary_key=True)
    indicator_id = Column(Integer, ForeignKey("indicators.indicator_id"), nullable=False, primary_key=True)
    role = Column(String)

    # Relationships
    case = relationship("Case", back_populates="indicators")
    indicator = relationship("Indicator", back_populates="cases")


class CaseAttachment(Base):
    __tablename__ = "case_attachments"

    case_attachment_id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    file_url = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    mime_type = Column(String)
    storage_provider = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    case = relationship("Case", back_populates="attachments")


class CaseLabel(Base):
    __tablename__ = "case_labels"

    case_label_id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    label = Column(String, nullable=False)

    # Relationships
    case = relationship("Case", back_populates="labels")

    __table_args__ = (
        {"extend_existing": True}
    )
