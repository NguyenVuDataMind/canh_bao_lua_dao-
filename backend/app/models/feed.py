from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import enum


class ThreatFeedFormat(str, enum.Enum):
    CSV = "csv"
    TXT = "txt"
    JSON = "json"
    STIX = "stix"


class ThreatFeed(Base):
    __tablename__ = "threat_feeds"

    feed_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    source_url = Column(String, nullable=False)
    format = Column(Enum(ThreatFeedFormat), nullable=False)
    enabled = Column(Integer, default=1, nullable=False)
    last_fetched_at = Column(DateTime(timezone=True))

    # Relationships
    feed_items = relationship("FeedItem", back_populates="feed", cascade="all, delete-orphan")

    __table_args__ = (
        {"extend_existing": True}
    )


class FeedItem(Base):
    __tablename__ = "feed_items"

    feed_item_id = Column(Integer, primary_key=True, index=True)
    feed_id = Column(Integer, ForeignKey("threat_feeds.feed_id"), nullable=False)
    indicator_type = Column(String, nullable=False)
    indicator_value = Column(String, nullable=False)
    first_seen = Column(DateTime(timezone=True))
    last_seen = Column(DateTime(timezone=True))
    raw_line = Column(Text)

    # Relationships
    feed = relationship("ThreatFeed", back_populates="feed_items")
