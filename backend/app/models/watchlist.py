"""Watchlist and Hotlist Management Models for SentinelX."""

from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.alert import Alert


class WatchlistPriority(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class WatchlistCategory(str, Enum):
    STOLEN = "STOLEN"
    WANTED = "WANTED"
    SUSPICIOUS = "SUSPICIOUS"
    UNREGISTERED = "UNREGISTERED"
    VIP_ESCORT = "VIP_ESCORT"
    GENERAL = "GENERAL"


class Watchlist(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Categorized Watchlist container (e.g. 'Stolen Vehicles Ahmedabad Zone 1')."""

    __tablename__ = "watchlists"

    name: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    category: Mapped[str] = mapped_column(
        String(50), default=WatchlistCategory.STOLEN.value, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    entries: Mapped[List["WatchlistEntry"]] = relationship(
        "WatchlistEntry",
        back_populates="watchlist",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class WatchlistEntry(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Single vehicle entry within a watchlist."""

    __tablename__ = "watchlist_entries"

    watchlist_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("watchlists.id", ondelete="CASCADE"), index=True, nullable=False
    )
    registration_number: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    registration_normalized: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    category: Mapped[str] = mapped_column(
        String(50), default=WatchlistCategory.STOLEN.value, nullable=False
    )
    priority: Mapped[str] = mapped_column(
        String(20), default=WatchlistPriority.HIGH.value, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    watchlist: Mapped[Watchlist] = relationship(
        "Watchlist", back_populates="entries", lazy="selectin"
    )
    alerts: Mapped[List["Alert"]] = relationship(
        "Alert", back_populates="watchlist_entry", lazy="selectin"
    )
