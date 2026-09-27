import os
from datetime import datetime

from sqlalchemy import DateTime, Float, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL", "").strip()


class Base(DeclarativeBase):
    pass


class EventRecord(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    event_type: Mapped[str] = mapped_column(String(40), index=True)
    importance: Mapped[str] = mapped_column(String(16), default="normal")
    title: Mapped[str] = mapped_column(String(300))
    summary: Mapped[str] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(300), nullable=True)
    affected_symbols: Mapped[str] = mapped_column(Text, default="")
    affected_industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    affected_region: Mapped[str | None] = mapped_column(String(100), nullable=True)


class EventReactionRecord(Base):
    __tablename__ = "event_reactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(80), index=True)
    symbol: Mapped[str] = mapped_column(String(20), index=True)
    reaction_5m_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    reaction_30m_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    reaction_1h_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    reaction_1d_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    reaction_5d_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    reaction_10d_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    reaction_20d_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    sector_relative_1d_pct: Mapped[float | None] = mapped_column(Float, nullable=True)


class PolicyExposureRecord(Base):
    __tablename__ = "policy_exposure"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), index=True)
    category: Mapped[str] = mapped_column(String(60), index=True)
    direct_exposure: Mapped[float | None] = mapped_column(Float, nullable=True)
    customer_exposure: Mapped[float | None] = mapped_column(Float, nullable=True)
    sector_exposure: Mapped[float | None] = mapped_column(Float, nullable=True)
    sentiment_exposure: Mapped[float | None] = mapped_column(Float, nullable=True)
    rationale: Mapped[str] = mapped_column(Text, default="")


engine = create_engine(DATABASE_URL, pool_pre_ping=True) if DATABASE_URL else None
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False) if engine else None


def init_db() -> None:
    if engine is not None:
        Base.metadata.create_all(engine)
