import enum
from datetime import datetime

from sqlalchemy import Enum as SAEnum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.functions import func
from sqlalchemy.sql.sqltypes import Boolean, DateTime, String

from app.db import Base


class WhitelistMatchType(str, enum.Enum):
    EXACT = "exact"
    PREFIX = "prefix"
    WILDCARD = "wildcard"


class TrustedURL(Base):
    __tablename__ = "trusted_urls"
    __table_args__ = (
        UniqueConstraint(
            "normalized_pattern", "match_type", name="uq_trusted_urls_pattern_match"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    normalized_pattern: Mapped[str] = mapped_column(String, nullable=False, index=True)
    match_type: Mapped[WhitelistMatchType] = mapped_column(
        SAEnum(WhitelistMatchType), nullable=False, default=WhitelistMatchType.EXACT
    )
    source: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    raw_example: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:
        return (
            f"TrustedURL(id={self.id}, pattern={self.normalized_pattern}, "
            f"type={self.match_type})"
        )

