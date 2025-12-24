from sqlalchemy import BigInteger, SmallInteger, Identity, Text, Boolean, Integer, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import date, datetime
from .base import Base


class GtfsMeta(Base):
    __tablename__ = "gtfs_meta"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    current_hash: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())


class StopEvent(Base):
    __tablename__ = "stop_events"

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    line_number: Mapped[str] = mapped_column(Text, nullable=False)
    stop_name: Mapped[str] = mapped_column(Text, nullable=False)
    stop_sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    direction_id: Mapped[int | None] = mapped_column(SmallInteger)
    planned_time: Mapped[datetime] = mapped_column(nullable=False)
    event_time: Mapped[datetime] = mapped_column(nullable=False)
    delay_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    vehicle_label: Mapped[str | None] = mapped_column(Text)
    is_estimated: Mapped[bool] = mapped_column(Boolean, server_default="false")
    headsign: Mapped[str | None] = mapped_column(Text)
    service_date: Mapped[date] = mapped_column(nullable=False)
    trip_id: Mapped[str] = mapped_column(Text, nullable=False)
    stop_id: Mapped[str] = mapped_column(Text, nullable=False)
    static_hash: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())

