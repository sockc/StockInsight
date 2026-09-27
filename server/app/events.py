from __future__ import annotations

from sqlalchemy import desc, or_, select

from .db import EventReactionRecord, EventRecord, SessionLocal
from .schemas import EventItem, EventsResponse


def _planned(symbol: str) -> EventsResponse:
    return EventsResponse(
        symbol=symbol,
        data_mode="schema_ready",
        items=[
            EventItem(
                id="v02-policy-source",
                time="V0.2",
                type="POLICY",
                title="接入政策事件源",
                summary="出口限制、关税、AI监管、半导体补贴、美联储政策；事件入库后自动计算1/5/10/20日市场反应。",
                importance="planned",
                affected_symbols=[symbol],
            ),
            EventItem(
                id="v02-earnings-source",
                time="V0.2",
                type="EARNINGS",
                title="接入财报预期差",
                summary="保存实际值、市场一致预期、指引差异，并区分事件内容和股价实际反应。",
                importance="planned",
                affected_symbols=[symbol],
            ),
        ],
    )


def event_response(symbol: str, limit: int = 50) -> EventsResponse:
    symbol = symbol.upper()
    if SessionLocal is None:
        return _planned(symbol)

    with SessionLocal() as session:
        stmt = (
            select(EventRecord)
            .where(EventRecord.affected_symbols.contains(symbol))
            .order_by(desc(EventRecord.event_time))
            .limit(max(1, min(limit, 100)))
        )
        events = list(session.scalars(stmt))
        if not events:
            return _planned(symbol)

        items: list[EventItem] = []
        for e in events:
            reaction = session.scalar(
                select(EventReactionRecord)
                .where(
                    EventReactionRecord.event_id == e.id,
                    EventReactionRecord.symbol == symbol,
                )
                .limit(1)
            )
            items.append(
                EventItem(
                    id=e.id,
                    time=e.event_time.isoformat(),
                    type=e.event_type,
                    title=e.title,
                    summary=e.summary,
                    importance=e.importance,
                    source=e.source,
                    affected_symbols=[x for x in e.affected_symbols.split(",") if x],
                    reaction1d_pct=reaction.reaction_1d_pct if reaction else None,
                    reaction5d_pct=reaction.reaction_5d_pct if reaction else None,
                    sector_relative1d_pct=reaction.sector_relative_1d_pct if reaction else None,
                )
            )
        return EventsResponse(symbol=symbol, items=items, data_mode="database")
