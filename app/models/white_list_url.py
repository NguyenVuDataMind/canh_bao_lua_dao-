from datetime import date
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Date, String, Integer

from app.db import Base


class WhiteListURL(Base):
    __tablename__ = "white_listurl"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    domain: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    company: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    first_seen: Mapped[date] = mapped_column(Date, nullable=False)
    last_seen: Mapped[date] = mapped_column(Date, nullable=False)
    source: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    def __repr__(self) -> str:
        return f"WhiteListURL(id={self.id}, domain={self.domain!r}, source={self.source!r})"

